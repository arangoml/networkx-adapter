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
        raise NotImplementedError()  # pragma: no cover

    def create_networkx_graph(self):
        raise NotImplementedError()  # pragma: no cover

    def create_networkx_graph_from_arangodb_collections(self):
        raise NotImplementedError()  # pragma: no cover

    def create_networkx_graph_from_arangodb_graph(self):
        raise NotImplementedError()  # pragma: no cover

    def create_arangodb_graph(self):
        raise NotImplementedError()  # pragma: no cover

    def __validate_attributes(self):
        raise NotImplementedError()  # pragma: no cover

    def __fetch_arangodb_docs(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_networkx_node(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_networkx_edge(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_arangodb_vertex(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_arangodb_edge(self):
        raise NotImplementedError()  # pragma: no cover

    def _prepare_nx_node(self):
        raise NotImplementedError()  # pragma: no cover

    def _prepare_nx_edge(self):
        raise NotImplementedError()  # pragma: no cover

    def _identify_nx_node(self):
        raise NotImplementedError()  # pragma: no cover

    def _identify_nx_edge(self):
        raise NotImplementedError()  # pragma: no cover

    def _keyify_nx_node(self):
        raise NotImplementedError()  # pragma: no cover

    def _keyify_nx_edge(self):
        raise NotImplementedError()  # pragma: no cover

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
