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
from networkx.classes import graph
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
        if is_keep:
            attributes.add("_id")

        aql = f"""
            FOR doc IN {col}
                RETURN {'KEEP' if is_keep else 'UNSET'}(doc, {list(attributes)})
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

    def create_networkx_graph_from_arango_graph(self, graph_name: str, **query_options):
        arango_graph = self.db.graph(graph_name)
        attributes = self.UNNECESSARY_DOCUMENT_ATTRIBUTES

        g = nx.DiGraph()
        for collection in arango_graph.vertex_collections():
            for vertex in self.fetch_docs(collection, attributes, False, query_options):
                g.add_node(vertex["_id"], attr_dict=vertex)

        for collection in arango_graph.edge_definitions():
            for edge in self.fetch_docs(collection["edge_collection"], attributes, False, query_options):
                g.add_edge(edge["_from"], edge["_to"], attr_dict=edge)

        print(f"Success: {graph_name} created")
        return g
