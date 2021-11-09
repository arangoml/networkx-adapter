#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
@author: Joerg Schad
@author: Anthony Mahanna
"""

import networkx as nx
from arango import ArangoClient
from .abc import ADBNX_Adapter

from arango.graph import Graph as ArangoDBGraph
from networkx.classes.graph import Graph as NetworkXGraph

try:  # Python +3.8
    from typing import final
except ImportError:  # Python 3.6, 3.7
    from overrides import final


class ArangoDB_Networkx_Adapter(ADBNX_Adapter):
    def __init__(self, conn: dict) -> None:
        self.__validate_attributes("connection", set(conn), self.CONNECTION_ATRIBS)

        username = conn["username"]
        password = conn["password"]
        db_name = conn["dbName"]
        port = str(conn.get("port", 8529))
        protocol = conn.get("protocol", "https")

        self.nx_graph: NetworkXGraph = None
        self.nx_node_map = dict()

        self.adb_graph: ArangoDBGraph = None
        self.adb_node_map = dict()

        url = protocol + "://" + conn["hostname"] + ":" + port
        print(f"Connecting to {url}")
        self.db = ArangoClient(hosts=url).db(db_name, username, password, verify=True)

    @final
    def create_networkx_graph(
        self, name: str, graph_attributes, is_keep=True, **query_options
    ):
        self.__validate_attributes("graph", set(graph_attributes), self.GRAPH_ATRIBS)

        self.nx_graph = nx.MultiDiGraph(name=name)

        for col, atribs in graph_attributes["vertexCollections"].items():
            for v in self.__fetch_arangodb_docs(col, atribs, is_keep, query_options):
                self.__insert_networkx_node(v["_id"], v, col, atribs)

        for col, atribs in graph_attributes["edgeCollections"].items():
            for e in self.__fetch_arangodb_docs(col, atribs, is_keep, query_options):
                from_id = self.nx_node_map.get(e["_from"])["_id"]
                to_id = self.nx_node_map.get(e["_to"])["_id"]
                self.__insert_networkx_edge(from_id, to_id, e, col, atribs)

        print(f"NetworkX: {name} created")
        return self.nx_graph

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
        overwrite=False,
        keyify_edges=False,
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

        self.adb_graph = self.db.create_graph(name, edge_definitions=edge_definitions)

        for id, node in nx_graph.nodes(data=True):
            col = self._identify_nx_node(id, node, overwrite)
            key = self._keyify_nx_node(id, node, col, overwrite)
            node["_id"] = col + "/" + key
            self.__insert_arangodb_vertex(id, node, col, key, overwrite)

        for from_node, to_node, edge in nx_graph.edges(data=True):
            col = self._identify_nx_edge(from_node, to_node, edge, overwrite)
            if keyify_edges:
                key = self._keyify_nx_edge(from_node, to_node, edge, col, overwrite)
                edge["_id"] = col + "/" + key

            self.__insert_arangodb_edge(from_node, to_node, edge, col, overwrite)

        print(f"ArangoDB: {name} created")
        return self.adb_graph

    @final
    def __validate_attributes(self, type, attributes: set, valid_attributes: set):
        if valid_attributes.issubset(attributes) is False:
            missing_attributes = valid_attributes - attributes
            raise ValueError(f"Missing {type} attributes: {missing_attributes}")

    @final
    def __fetch_arangodb_docs(
        self, col: str, attributes: set, is_keep: bool, query_options
    ):
        aql = f"""
            FOR doc IN {col}
                RETURN {is_keep} ? 
                    MERGE(KEEP(doc, {list(attributes)}), {{"_id": doc._id}}) : doc
        """

        return self.db.aql.execute(aql, **query_options)

    @final
    def _string_to_arangodb_key_helper(self, string: str) -> str:
        res = ""
        for s in string:
            if s.isalnum() or s in self.VALID_CHARS:
                res += s

        return res

    @final
    def _tuple_to_arangodb_key_helper(self, tup: tuple) -> str:
        string = "".join(map(str, tup))
        return self._string_to_arangodb_key_helper(string)

    @final
    def __insert_arangodb_vertex(self, id, v: dict, col: str, key: str, ow: bool):
        self.adb_node_map[id] = {"_id": v["_id"], "collection": col, "key": key}
        self.db.collection(col).insert(v, overwrite=ow, silent=True)

    @final
    def __insert_arangodb_edge(self, from_node, to_node, e: dict, col: str, ow: bool):
        e["_from"] = self.adb_node_map.get(from_node)["_id"]
        e["_to"] = self.adb_node_map.get(to_node)["_id"]
        self.db.collection(col).insert(e, overwrite=ow, silent=True)

    @final
    def __insert_networkx_node(self, adb_id: str, node: dict, col: str, atribs: set):
        nx_node_id = self._prepare_nx_node(node, col, atribs)

        self.nx_node_map[adb_id] = {"_id": nx_node_id, "collection": col}
        self.nx_graph.add_node(nx_node_id, **node)

    @final
    def __insert_networkx_edge(self, from_id, to_id, edge: dict, col: str, atribs: set):
        self._prepare_nx_edge(edge, col, atribs)
        self.nx_graph.add_edge(from_id, to_id, **edge)

    def _prepare_nx_node(self, node: dict, col: str, atribs: set):
        """
        Given access to an ArangoDB vertex, you can modify it before it gets inserted,
        and/or derive a custom node id for networkx to use.

        In most cases, no action is needed here.
        """
        return node["_id"]

    def _prepare_nx_edge(self, edge: dict, col: str, atribs: set):
        """
        Given access to an ArangoDB edge, you can modify it before it gets inserted here.

        In most cases, no action is needed.
        """
        pass

    def _identify_nx_node(self, id: str, node: dict, overwrite: bool) -> str:
        """
        Identify (based on id or node data) what collection this node belongs to.

        If you plan on doing NetworkX -> ArangoDB, you must override this function
        (unless your nx graph already complies to ArangoDB standards).
        """
        return id.split("/")[0] + ("" if overwrite else "_nx")

    def _identify_nx_edge(self, from_node, to_node, e: dict, overwrite: bool) -> str:
        """
        Identify (based on from, to, or edge data) what collection this edge belongs to.

        If you plan on doing NetworkX -> ArangoDB, you must override this function
        (unless your nx graph already complies to ArangoDB standards).
        """
        edge_id: str = e["_id"]
        return edge_id.split("/")[0] + ("" if overwrite else "_nx")

    def _keyify_nx_node(self, id: str, node: dict, col: str, ow: bool) -> str:
        """
        Create a key based off of the node id that ArangoDB will not complain about.

        If you plan on doing NetworkX -> ArangoDB, you must override this function
        (unless your nx graph already complies to ArangoDB standards).
        """
        return id.split("/")[1]

    def _keyify_nx_edge(self, from_node, to_node, e: dict, col: str, overwrite: bool):
        """
        Create a key based off of the edge id that ArangoDB will not complain about.

        If you plan on doing NetworkX -> ArangoDB, and you want to assign custom IDs to edges, you must override this function
        (unless your nx graph already complies to ArangoDB standards).
        """
        edge_id: str = e["_id"]
        return edge_id.split("/")[1]
