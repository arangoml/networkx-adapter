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


class ArangoDB_Networkx_Adapter(ADBNX_Adapter):
    def __init__(self, conn: dict) -> None:
        self.__validate_attributes("connection", set(conn), self.CONNECTION_ATRIBS)

        url = conn["hostname"]
        username = conn["username"]
        password = conn["password"]
        db_name = conn["dbName"]
        port = str(conn.get("port", 8529))
        protocol = conn.get("protocol", "https")

        self.nx_graph: NetworkXGraph = None
        self.nx_node_map = dict()

        self.adb_graph: ArangoDBGraph = None
        self.adb_node_map = dict()

        con_str = protocol + "://" + url + ":" + port
        self.db = ArangoClient(hosts=con_str).db(db_name, username, password)

    def create_networkx_graph(
        self, name: str, graph_attributes, is_keep=True, **query_options
    ):
        self.__validate_attributes("graph", set(graph_attributes), self.GRAPH_ATRIBS)

        self.nx_graph = nx.MultiDiGraph(name=name)

        for col, attribs in graph_attributes["vertexCollections"].items():
            for v in self.__fetch_arangodb_docs(col, attribs, is_keep, query_options):
                self._insert_networkx_vertex(v, col, attribs)

        for col, attribs in graph_attributes["edgeCollections"].items():
            for e in self.__fetch_arangodb_docs(col, attribs, is_keep, query_options):
                self._insert_networkx_edge(e, col, attribs)

        print(f"NetworkX: {name} created")
        return self.nx_graph

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

    def create_networkx_graph_from_arangodb_graph(self, name: str, **query_options):
        arango_graph = self.db.graph(name)
        v_cols = arango_graph.vertex_collections()
        e_cols = {col["edge_collection"] for col in arango_graph.edge_definitions()}

        return self.create_networkx_graph_from_arangodb_collections(
            name, v_cols, e_cols, **query_options
        )

    def create_arangodb_graph(
        self,
        name: str,
        original_nx_graph: NetworkXGraph,
        edge_definitions: list[dict],
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
        nx_graph = original_nx_graph.copy()

        for definition in edge_definitions:
            e_col = definition["edge_collection"]
            if self.db.has_collection(e_col) is False:
                self.db.create_collection(e_col, edge=True)

            for v_col in (
                definition["from_vertex_collections"]
                + definition["to_vertex_collections"]
            ):
                if self.db.has_collection(v_col) is False:
                    self.db.create_collection(v_col)

        self.adb_graph = self.db.create_graph(name, edge_definitions=edge_definitions)

        for id, node in nx_graph.nodes(data=True):
            col = self._identify_nx_node(id, node)
            key = self._keyify_nx_node(id, node, col)
            node["_id"] = col + "/" + key
            self._insert_arangodb_vertex(id, node, col, key)

        for from_node, to_node, edge in nx_graph.edges(data=True):
            col = self._identify_nx_edge(from_node, to_node, edge)
            if keyify_edges:
                key = self._keyify_nx_edge(from_node, to_node, edge, col)
                edge["_id"] = col + "/" + key

            self._insert_arangodb_edge(from_node, to_node, edge, col)

        print(f"ArangoDB: {name} created")
        return self.adb_graph

    def __validate_attributes(self, type, attributes: set, valid_attributes: set):
        if valid_attributes.issubset(attributes) is False:
            missing_attributes = valid_attributes - attributes
            raise ValueError(f"Missing {type} attributes: {missing_attributes}")

    def _insert_networkx_vertex(self, vertex: dict, collection: str, attributes: set):
        self.nx_node_map[vertex["_id"]] = {
            "_id": vertex["_id"],
            "collection": collection,
        }
        self.nx_graph.add_node(vertex["_id"], **vertex)

    def _insert_networkx_edge(self, edge: dict, collection: str, attributes: set):
        from_id = self.nx_node_map.get(edge["_from"])["_id"]
        to_id = self.nx_node_map.get(edge["_to"])["_id"]
        self.nx_graph.add_edge(from_id, to_id, **edge)

    def _insert_arangodb_vertex(self, node_id, vertex: dict, col: str, key: str):
        self.adb_node_map[node_id] = {
            "_id": vertex["_id"],
            "collection": col,
            "key": key,
        }
        self.db.collection(col).insert(vertex, silent=True)

    def _insert_arangodb_edge(self, from_node, to_node, edge: dict, col: str):
        edge["_from"] = self.adb_node_map.get(from_node)["_id"]
        edge["_to"] = self.adb_node_map.get(to_node)["_id"]
        self.db.collection(col).insert(edge, silent=True)

    def __fetch_arangodb_docs(
        self, col: str, attributes: set, is_keep: bool, query_options
    ):
        aql = f"""
            FOR doc IN {col}
                RETURN {is_keep} ? 
                    MERGE(KEEP(doc, {list(attributes)}), {{"_id": doc._id}}) : doc
        """

        return self.db.aql.execute(aql, count=True, **query_options)

    def _string_to_arangodb_key_helper(self, string: str) -> str:
        res = ""
        for s in string:
            if s.isalnum() or s in self.VALID_CHARS:
                res += s

        return res

    def _tuple_to_arangodb_key_helper(self, tup: tuple) -> str:
        string = "".join(map(str, tup))
        return self._string_to_arangodb_key_helper(string)
