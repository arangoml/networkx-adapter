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

    def arangodb_to_networkx(self):
        raise NotImplementedError()  # pragma: no cover

    def arangodb_collections_to_networkx(self):
        raise NotImplementedError()  # pragma: no cover

    def arangodb_graph_to_networkx(self):
        raise NotImplementedError()  # pragma: no cover

    def networkx_to_arangodb(self):
        raise NotImplementedError()  # pragma: no cover

    def __validate_attributes(self):
        raise NotImplementedError()  # pragma: no cover

    def __fetch_adb_docs(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_adb_vertex(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_adb_edge(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_nx_node(self):
        raise NotImplementedError()  # pragma: no cover

    def __insert_nx_edge(self):
        raise NotImplementedError()  # pragma: no cover

    @property
    def CONNECTION_ATRIBS(self):
        return {"hostname", "username", "password", "dbName"}

    @property
    def GRAPH_ATRIBS(self):
        return {"vertexCollections", "edgeCollections"}


class ADBNX_Controller(ABC):
    def __init__(self):
        raise NotImplementedError()  # pragma: no cover

    def _prepare_arangodb_vertex(self, vertex: dict, collection: str):
        raise NotImplementedError()  # pragma: no cover

    def _prepare_arangodb_edge(self, edge: dict, collection: str):
        raise NotImplementedError()  # pragma: no cover

    def _identify_networkx_node(self, id, node: dict, overwrite: bool) -> str:
        raise NotImplementedError()  # pragma: no cover

    def _identify_networkx_edge(
        self, edge: dict, from_node: dict, to_node: dict, overwrite: bool
    ) -> str:
        raise NotImplementedError()  # pragma: no cover

    def _keyify_networkx_node(
        self, id, node: dict, collection: str, overwrite: bool
    ) -> str:
        raise NotImplementedError()  # pragma: no cover

    def _keyify_networkx_edge(
        self,
        edge: dict,
        from_node: dict,
        to_node: dict,
        collection: str,
        overwrite: bool,
    ):
        raise NotImplementedError()  # pragma: no cover

    @property
    def VALID_KEY_CHARS(self):
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
