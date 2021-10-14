#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
@author: Anthony Mahanna
"""

import networkx as nx
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter


class IMDBArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):

    def __init__(self, conn) -> None:
        super().__init__(conn)

    def create_networkx_graph(self, graph_name, graph_attributes, **query_options):
        self.validate_attributes("graph", graph_attributes.keys(), self.GRAPH_ATRIBS)

        g = nx.DiGraph()
        for collection, attributes in graph_attributes.get("vertexCollections").items():
            for vertex in self.fetch_docs(collection, attributes, True, query_options):
                bip_key = 0 if collection == "Users" else 1
                g.add_node(vertex["_id"], attr_dict=vertex, bipartite=bip_key)

        for collection, attributes in graph_attributes.get("edgeCollections").items():
            for edge in self.fetch_docs(collection, attributes, True, query_options):
                g.add_edge(edge["_from"], edge["_to"], attr_dict=edge)

        print(f"Success: {graph_name} created")
        return g
