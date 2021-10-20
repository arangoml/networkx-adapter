#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
@author: Joerg Schad
@author: Anthony Mahanna
"""

import dgl
from .arangodb_networkx_adapter import ArangoDB_Networkx_Adapter


class DGLArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def __init__(self, conn) -> None:
        super().__init__(conn)

    def create_dgl_graph(self, graph_name, graph_attributes: dict) -> dgl.DGLGraph:
        self.create_networkx_graph(graph_name, graph_attributes)
        return dgl.from_networkx(self.nx_graph)