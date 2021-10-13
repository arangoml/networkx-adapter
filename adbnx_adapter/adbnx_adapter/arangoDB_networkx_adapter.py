#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
@author Joerg Schad
@author Anthony Mahanna
"""

import networkx as nx
from arango import ArangoClient
from .arangodb_networkx_adapter_base import Networkx_Adapter_Base


class ArangoDB_Networkx_Adapter(Networkx_Adapter_Base):
    CONNECTION_ATRIBS = {"hostname", "username", "password", "dbName"}
    GRAPH_ATRIBS = {"vertexCollections", "edgeCollections"}
    UNNECESSARY_DOCUMENT_ATTRIBUTES = {"_key", "_rev"}

    def __init__(self, conn) -> None:
        super().__init__()
        self.validate_attributes("connection", conn.keys(), self.CONNECTION_ATRIBS)

        url = conn.get("hostname")
        username = conn.get("username")
        password = conn.get("password")
        db_name = conn.get("dbName")

        port = str(conn.get("port", 8529))
        protocol = conn.get("protocol", "https")

        con_str = protocol + "://" + url + ":" + port
        client = ArangoClient(hosts=con_str)
        self.db = client.db(db_name, username, password)

    def validate_attributes(self, type, attributes: set, valid_attributes: set):
        if not valid_attributes <= attributes:
            missing_attributes = valid_attributes - attributes
            raise ValueError(f"Missing {type} attributes: {missing_attributes}")

    def fetch_docs(self, col: str, attributes: set[str], is_keep: bool, query_options):
        aql = f"""
            FOR doc IN {col}
                RETURN MERGE(
                    {'KEEP' if is_keep else 'UNSET'}(doc, {list(attributes)}), 
                    {{"_id": doc["_id"]}}
                )
        """

        return self.db.aql.execute(aql, **query_options)

    def create_networkx_graph(self, graph_name: str, graph_attributes, **query_options):
        self.validate_attributes("graph", graph_attributes.keys(), self.GRAPH_ATRIBS)

        g = nx.DiGraph()
        for collection, attributes in graph_attributes.get("vertexCollections").items():
            for vertex in self.fetch_docs(collection, attributes, True, query_options):
                g.add_node(vertex["_id"], attr_dict=vertex)

        for collection, attributes in graph_attributes.get("edgeCollections").items():
            for edge in self.fetch_docs(collection, attributes, True, query_options):
                g.add_edge(edge["_from"], edge["_to"], attr_dict=edge)

        print(f"Success: {graph_name} created")
        return g

    def create_networkx_graph_from_graph(self, graph_name: str, **query_options):
        arango_graph = self.db.graph(graph_name)
        v_cols = arango_graph.vertex_collections()
        e_cols = {col["edge_collection"] for col in arango_graph.edge_definitions()}

        return self.create_networkx_graph_from_collections(
            graph_name, v_cols, e_cols, **query_options
        )

    def create_networkx_graph_from_collections(
        self,
        graph_name: str,
        vertex_collections: set[str],
        edge_collections: set[str],
        **query_options,
    ):
        attributes = self.UNNECESSARY_DOCUMENT_ATTRIBUTES

        g = nx.DiGraph()
        for collection in vertex_collections:
            for vertex in self.fetch_docs(collection, attributes, False, query_options):
                g.add_node(vertex["_id"], attr_dict=vertex)

        for collection in edge_collections:
            for edge in self.fetch_docs(collection, attributes, False, query_options):
                g.add_edge(edge["_from"], edge["_to"], attr_dict=edge)

        print(f"Success: {graph_name} created")
        return g
