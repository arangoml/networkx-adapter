#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 11:38:31 2020

@author: Rajiv Sambasivan
@author: Joerg Schad
@author: Anthony Mahanna
"""

from abc import ABC


class Networkx_Adapter(ABC):
    def __init__(self):
        raise NotImplementedError()

    def create_networkx_graph(self):
        raise NotImplementedError()

    def validate_attributes(self):
        raise NotImplementedError()

    def insert_vertex(self):
        raise NotImplementedError()

    def insert_edge(self):
        raise NotImplementedError()

    @property
    def CONNECTION_ATRIBS(self):
        return {"hostname", "username", "password", "dbName"}

    @property
    def GRAPH_ATRIBS(self):
        return {"vertexCollections", "edgeCollections"}

    @property
    def UNNECESSARY_DOCUMENT_ATTRIBUTES(self):
        return {"_key", "_rev"}
