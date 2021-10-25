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

from typing import Union
from arango.graph import Graph as ArangoGraph
from networkx.classes.multigraph import MultiGraph
from networkx.classes.multidigraph import MultiDiGraph


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
        self.nx_graph: MultiDiGraph = None

    def clear(self, to_clear: set):
        for col in to_clear:
            self.db.delete_collection(col) if self.db.has_collection(col) else None

    def insert_nx_vertex(self, vertex: dict, collection: str, attributes: set):
        self.nx_graph.add_node(vertex["_id"], **vertex)

    def insert_nx_edge(self, edge: dict, collection: str, attributes: set):
        self.nx_graph.add_edge(edge["_from"], edge["_to"], **edge)

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

        return self.db.aql.execute(aql, count=True, **query_options)

    def create_networkx_graph_from_arango_graph(self, graph_name: str, **query_options):
        arango_graph = self.db.graph(graph_name)
        v_cols = arango_graph.vertex_collections()
        e_cols = arango_graph.edge_definitions()

        return self.create_networkx_graph_from_collections(
            graph_name, v_cols, e_cols, is_from_arango_graph=True, **query_options
        )

    def create_networkx_graph_from_collections(
        self,
        graph_name: str,
        vertex_collections: set,
        edge_collections: Union[set, list],
        is_from_arango_graph=False,
        **query_options,
    ):
        atribs = self.UNNECESSARY_DOCUMENT_ATTRIBUTES
        v_cols = {col: atribs for col in vertex_collections}
        e_cols = {
            (col["edge_collection"] if is_from_arango_graph else col): atribs
            for col in edge_collections
        }
        graph_attributes = {"vertexCollections": v_cols, "edgeCollections": e_cols}

        return self.create_networkx_graph(
            graph_name, graph_attributes, is_keep=False, **query_options
        )

    def create_networkx_graph(
        self, graph_name: str, graph_attributes, is_keep=True, **query_options
    ):
        self.validate_attributes("graph", graph_attributes.keys(), self.GRAPH_ATRIBS)

        self.nx_graph = nx.MultiDiGraph(name=graph_name)
        for collection, attributes in graph_attributes["vertexCollections"].items():
            for v in self.fetch_docs(collection, attributes, is_keep, query_options):
                self.insert_nx_vertex(v, collection, attributes)

        for collection, attributes in graph_attributes["edgeCollections"].items():
            for e in self.fetch_docs(collection, attributes, is_keep, query_options):
                self.insert_nx_edge(e, collection, attributes)

        print(f"Success: {graph_name} created")
        return self.nx_graph

    def insert_arango_doc(self, doc: dict, col: str, is_edge=False):
        if not self.db.has_collection(col):
            self.db.create_collection(col, edge=is_edge)

        print(f"Inserting {doc['_id']}")
        self.db.collection(col).insert(doc, silent=True)

    def create_arango_graph_from_networkx_graph(
        self, nx_graph: Union[MultiGraph, MultiDiGraph]
    ) -> ArangoGraph:
        print(f"Creating arango graph: {nx_graph.name + '_new'}")

        # nx_graph = nx.convert_node_labels_to_integers(nx_graph, ordering='sorted')
        if not nx_graph.is_directed():
            nx_graph = nx_graph.to_directed()

        edge_definitions = []
        nx_nodes = nx_graph.nodes(data=True)
        nx_edges = nx_graph.edges(data=True)

        id: str
        node: dict
        for id, node in nx_nodes:
            node = {"_id": id} if not node else node
            self.validate_attributes("vertex", node.keys(), self.ARANGO_VERTEX_ATRIBS)
            col, key = id.split("/")
            # Tempoaray measure to avoid conflict with existing arango graph data
            col += "_new"
            node["_id"] = col + "/" + key
            ##############################################
            self.insert_arango_doc(node, col)

        from_e: str
        to_e: str
        edge: dict
        for from_e, to_e, edge in nx_edges:
            self.validate_attributes("edge", edge.keys(), self.ARANGO_EDGE_ATRIBS)
            from_collection, from_key = from_e.split("/")
            to_collection, to_key = to_e.split("/")
            collection, key = edge["_id"].split("/")
            # Tempoaray measure to avoid conflict with existing arango graph data
            from_collection += "_new"
            edge["_from"] = from_collection + "/" + from_key

            to_collection += "_new"
            edge["_to"] = to_collection + "/" + to_key

            collection += "_new"
            edge["_id"] = collection + "/" + key
            ##############################################
            edge_definitions.append(
                {
                    "edge_collection": collection,
                    "from_vertex_collections": [from_collection],
                    "to_vertex_collections": [to_collection],
                }
            )
            self.insert_arango_doc(edge, collection, is_edge=True)

        e_d = list({e["edge_collection"]: e for e in edge_definitions}.values())
        return self.db.create_graph(nx_graph.name + "_new", edge_definitions=e_d)
