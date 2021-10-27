#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 11:38:31 2020

@author: Rajiv Sambasivan
@author: Joerg Schad
@author: Anthony Mahanna
"""

from abc import ABC


class ADBNX_Adapter(ABC):
    def __init__(self):
        raise NotImplementedError()

    def create_networkx_graph(self):
        raise NotImplementedError()

    def create_networkx_graph_from_arangodb_collections(self):
        raise NotImplementedError()

    def create_networkx_graph_from_arangodb_graph(self):
        raise NotImplementedError()

    def create_arangodb_graph(self):
        raise NotImplementedError()

    def __validate_attributes(self):
        raise NotImplementedError()

    def __insert_networkx_vertex(self):
        raise NotImplementedError()

    def __insert_networkx_edge(self):
        raise NotImplementedError()

    def __insert_arangodb_doc():
        raise NotImplementedError()

    def __fetch_arangodb_docs():
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

    @property
    def ARANGO_VERTEX_ATRIBS(self):
        return {"_id"}

    @property
    def ARANGO_EDGE_ATRIBS(self):
        return self.ARANGO_VERTEX_ATRIBS.union({"_from", "_to"})
