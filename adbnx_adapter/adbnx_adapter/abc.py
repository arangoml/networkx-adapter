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

    def _insert_arangodb_doc():
        raise NotImplementedError()

    def __fetch_arangodb_docs():
        raise NotImplementedError()

    def _insert_networkx_vertex(self):
        raise NotImplementedError()

    def _insert_networkx_edge(self):
        raise NotImplementedError()

    # identify (based on id or node data) what collection this node belongs to
    def _identify_nx_node(self, id, node) -> str:
        """
        Must be implemented by user if translating nx to arangodb
        """
        raise NotImplementedError()

    # create a key based off of the node id that ArangoDB will not complain about
    def _keyify_nx_node(self, id, node, collection) -> str:
        """
        Must be implemented by user if translating nx to arangodb
        """
        raise NotImplementedError()

    # identify (based on from, to, or edge data) what collection this edge belongs to
    def _identify_nx_edge(self, id_map, from_node, to_node, edge) -> str:
        """
        Must be implemented by user if translating nx to arangodb
        """
        raise NotImplementedError()

    @property
    def CONNECTION_ATRIBS(self):
        return {"hostname", "username", "password", "dbName"}

    @property
    def GRAPH_ATRIBS(self):
        return {"vertexCollections", "edgeCollections"}

    @property
    def VALID_CHARS(self):
        return {
            "_",
            "-",
            ":",
            ".",
            "@",
            "(",
            ")",
            "+",
            ",",
            "=",
            ";",
            "$",
            "!",
            "*",
            "'",
            "%",
        }
