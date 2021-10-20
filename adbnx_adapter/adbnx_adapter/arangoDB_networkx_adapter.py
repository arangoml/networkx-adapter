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
from .abc import Networkx_Adapter


class ArangoDB_Networkx_Adapter(Networkx_Adapter):
    def __init__(self, conn: dict) -> None:
        self.validate_attributes("connection", conn.keys(), self.CONNECTION_ATRIBS)

        url = conn["hostname"]
        username = conn["username"]
        password = conn["password"]
        db_name = conn["dbName"]
        port = str(conn.get("port", 8529))
        protocol = conn.get("protocol", "https")

        con_str = protocol + "://" + url + ":" + port
        client = ArangoClient(hosts=con_str)

        self.db = client.db(db_name, username, password)
        self.nx_graph = nx.DiGraph()

    def insert_vertex(self, vertex: dict, collection: str, attributes: set):
        self.nx_graph.add_node(vertex["_id"], attr_dict=vertex)

    def insert_edge(self, edge: dict, collection: str, attributes: set):
        self.nx_graph.add_edge(edge["_from"], edge["_to"], attr_dict=edge)

    def validate_attributes(self, type, attributes: set, valid_attributes: set):
        if not valid_attributes <= attributes:
            missing_attributes = valid_attributes - attributes
            raise ValueError(f"Missing {type} attributes: {missing_attributes}")

    def fetch_docs(self, col: str, attributes: set, is_keep: bool, query_options):
        aql = f"""
            FOR doc IN {col}
                RETURN MERGE(
                    {'KEEP' if is_keep else 'UNSET'}(doc, {list(attributes)}), 
                    {{"_id": doc["_id"]}}
                )
        """

        return self.db.aql.execute(aql, **query_options)

    def create_networkx_graph_from_graph(self, graph_name: str, **query_options):
        arango_graph = self.db.graph(graph_name)

        atribs = self.UNNECESSARY_DOCUMENT_ATTRIBUTES
        v_cols = {c: atribs for c in arango_graph.vertex_collections()}
        e_cols = {c["edge_collection"]: atribs for c in arango_graph.edge_definitions()}

        graph_attributes = {"vertexCollections": v_cols, "edgeCollections": e_cols}

        return self.create_networkx_graph(
            graph_name, graph_attributes, is_keep=False, **query_options
        )

    def create_networkx_graph_from_collections(
        self,
        graph_name: str,
        vertex_collections: set,
        edge_collections: set,
        **query_options,
    ):
        atribs = self.UNNECESSARY_DOCUMENT_ATTRIBUTES
        v_cols = {col: atribs for col in vertex_collections}
        e_cols = {col: atribs for col in edge_collections}

        graph_attributes = {"vertexCollections": v_cols, "edgeCollections": e_cols}

        return self.create_networkx_graph(
            graph_name, graph_attributes, is_keep=False, **query_options
        )

    def create_networkx_graph(
        self, graph_name: str, graph_attributes, is_keep=True, **query_options
    ):
        self.validate_attributes("graph", graph_attributes.keys(), self.GRAPH_ATRIBS)

        self.nx_graph.clear()
        for collection, attributes in graph_attributes["vertexCollections"].items():
            for v in self.fetch_docs(collection, attributes, is_keep, query_options):
                self.insert_vertex(v, collection, attributes)

        for collection, attributes in graph_attributes["edgeCollections"].items():
            for e in self.fetch_docs(collection, attributes, is_keep, query_options):
                self.insert_edge(e, collection, attributes)

        print(f"Success: {graph_name} created")
        return self.nx_graph
