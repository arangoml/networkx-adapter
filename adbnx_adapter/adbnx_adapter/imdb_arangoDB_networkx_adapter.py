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

    def insert_vertex(self, vertex: dict, collection: str, attributes: set):
        bip_key = 0 if collection == "Users" else 1
        self.nx_graph.add_node(vertex["_id"], attr_dict=vertex, bipartite=bip_key)
