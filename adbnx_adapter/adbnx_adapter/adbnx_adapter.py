#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
@author: Joerg Schad
@author: Anthony Mahanna
"""

from .abc import ADBNX_Adapter
from .adbnx_controller import Base_ADBNX_Controller

import networkx as nx
from arango import ArangoClient
from networkx.classes.graph import Graph as NetworkXGraph

try:  # Python +3.8
    from typing import final
except ImportError:  # Python 3.6, 3.7
    from overrides import final


class ArangoDB_Networkx_Adapter(ADBNX_Adapter):
    @final
    def __init__(
        self,
        conn: dict,
        cntrl: Base_ADBNX_Controller = Base_ADBNX_Controller(),
    ):
        self.__validate_attributes("connection", set(conn), self.CONNECTION_ATRIBS)

        username = conn["username"]
        password = conn["password"]
        db_name = conn["dbName"]
        port = str(conn.get("port", 8529))
        protocol = conn.get("protocol", "https")

        url = protocol + "://" + conn["hostname"] + ":" + port
        print(f"Connecting to {url}")
        self.db = ArangoClient(hosts=url).db(db_name, username, password, verify=True)

        if issubclass(type(cntrl), Base_ADBNX_Controller) is False:
            raise TypeError("cntrl must inherit from Base_ADBNX_Controller")

        self.cntrl: Base_ADBNX_Controller = cntrl

    @final
    def create_networkx_graph(
        self, name: str, graph_attributes, is_keep=True, **query_options
    ):
        self.__validate_attributes("graph", set(graph_attributes), self.GRAPH_ATRIBS)

        self.cntrl.nx_graph = nx.MultiDiGraph(name=name)

        for col, atribs in graph_attributes["vertexCollections"].items():
            for v in self.__fetch_arangodb_docs(col, atribs, is_keep, query_options):
                self.__insert_networkx_node(v["_id"], v, col)

        for col, atribs in graph_attributes["edgeCollections"].items():
            for e in self.__fetch_arangodb_docs(col, atribs, is_keep, query_options):
                self.__insert_networkx_edge(e, col)

        print(f"NetworkX: {name} created")
        return self.cntrl.nx_graph

    @final
    def create_networkx_graph_from_arangodb_collections(
        self,
        name: str,
        vertex_collections: set,
        edge_collections: set,
        **query_options,
    ):
        graph_attributes = {
            "vertexCollections": {col: {} for col in vertex_collections},
            "edgeCollections": {col: {} for col in edge_collections},
        }

        return self.create_networkx_graph(
            name, graph_attributes, is_keep=False, **query_options
        )

    @final
    def create_networkx_graph_from_arangodb_graph(self, name: str, **query_options):
        arango_graph = self.db.graph(name)
        v_cols = arango_graph.vertex_collections()
        e_cols = {col["edge_collection"] for col in arango_graph.edge_definitions()}

        return self.create_networkx_graph_from_arangodb_collections(
            name, v_cols, e_cols, **query_options
        )

    @final
    def create_arangodb_graph(
        self,
        name: str,
        original_nx_graph: NetworkXGraph,
        edge_definitions: list,
        overwrite: bool = False,
        keyify_edges: bool = False,
    ):
        """
        Here is an example entry for parameter **edge_definitions**:

        .. code-block:: python
        [
            {
                'edge_collection': 'teaches',
                'from_vertex_collections': ['person'],
                'to_vertex_collections': ['lecture']
            },
            {
                'edge_collection': 'attends',
                'from_vertex_collections': ['person'],
                'to_vertex_collections': ['lecture']
            }
        ]
        """
        nx_graph: NetworkXGraph = original_nx_graph.copy()

        for definition in edge_definitions:
            e_col = definition["edge_collection"]
            if self.db.has_collection(e_col) is False and overwrite is False:
                self.db.create_collection(e_col, edge=True)

            for v_col in (
                definition["from_vertex_collections"]
                + definition["to_vertex_collections"]
            ):
                if self.db.has_collection(v_col) is False and overwrite is False:
                    self.db.create_collection(v_col)

        if overwrite:
            self.db.delete_graph(name, ignore_missing=True)

        self.cntrl.adb_graph = self.db.create_graph(
            name, edge_definitions=edge_definitions
        )

        for id, node in nx_graph.nodes(data=True):
            col = self.cntrl._identify_nx_node(id, node, overwrite)
            key = self.cntrl._keyify_nx_node(id, node, col, overwrite)
            node["_id"] = col + "/" + key
            self.__insert_arangodb_vertex(id, node, col, key, overwrite)

        for from_node, to_node, edge in nx_graph.edges(data=True):
            col = self.cntrl._identify_nx_edge(from_node, to_node, edge, overwrite)
            if keyify_edges:
                key = self.cntrl._keyify_nx_edge(
                    from_node, to_node, edge, col, overwrite
                )
                edge["_id"] = col + "/" + key

            self.__insert_arangodb_edge(from_node, to_node, edge, col, overwrite)

        print(f"ArangoDB: {name} created")
        return self.cntrl.adb_graph

    @final
    def __validate_attributes(self, type: str, attributes: set, valid_attributes: set):
        if valid_attributes.issubset(attributes) is False:
            missing_attributes = valid_attributes - attributes
            raise ValueError(f"Missing {type} attributes: {missing_attributes}")

    @final
    def __fetch_arangodb_docs(
        self, col: str, attributes: set, is_keep: bool, query_options: dict
    ):
        aql = f"""
            FOR doc IN {col}
                RETURN {is_keep} ? 
                    MERGE(KEEP(doc, {list(attributes)}), {{"_id": doc._id}}) : doc
        """

        return self.db.aql.execute(aql, **query_options)

    @final
    def __insert_networkx_node(self, adb_id: str, node: dict, col: str):
        nx_id = self.cntrl._prepare_adb_vertex(node, col)
        self.cntrl.nx_map[adb_id] = {"_id": nx_id, "collection": col}

        self.cntrl.nx_graph.add_node(nx_id, **node)

    @final
    def __insert_networkx_edge(self, edge: dict, col: str):
        from_node_id = self.cntrl.nx_map.get(edge["_from"])["_id"]
        to_node_id = self.cntrl.nx_map.get(edge["_to"])["_id"]

        self.cntrl._prepare_adb_edge(edge, col)
        self.cntrl.nx_graph.add_edge(from_node_id, to_node_id, **edge)

    @final
    def __insert_arangodb_vertex(self, id, v: dict, col: str, key: str, ow: bool):
        self.cntrl.adb_map[id] = {"_id": v["_id"], "collection": col, "key": key}
        self.db.collection(col).insert(v, overwrite=ow, silent=True)

    @final
    def __insert_arangodb_edge(self, from_node, to_node, e: dict, col: str, ow: bool):
        e["_from"] = self.cntrl.adb_map.get(from_node)["_id"]
        e["_to"] = self.cntrl.adb_map.get(to_node)["_id"]
        self.db.collection(col).insert(e, overwrite=ow, silent=True)
