#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 11:38:31 2020

@author: Rajiv Sambasivan
@author: Joerg Schad
@author: Anthony Mahanna
"""

from abc import ABC


class Networkx_Adapter_Base(ABC):
    _CONNECTION_ATRIBS = {"hostname", "username", "password", "dbName"}
    _GRAPH_ATRIBS = {"vertexCollections", "edgeCollections"}
    _UNNECESSARY_DOCUMENT_ATTRIBUTES = {"_key", "_rev"}

    @property
    def CONNECTION_ATRIBS(self):
        return self._CONNECTION_ATRIBS

    @property
    def GRAPH_ATRIBS(self):
        return self._GRAPH_ATRIBS

    @property
    def UNNECESSARY_DOCUMENT_ATTRIBUTES(self):
        return self._UNNECESSARY_DOCUMENT_ATTRIBUTES

    def create_networkx_graph():
        pass

    def insert_vertex():
        pass

    def insert_edge():
        pass
