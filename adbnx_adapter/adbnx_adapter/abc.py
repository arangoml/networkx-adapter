#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Created on Thu Mar 26 11:38:31 2020.

@author: Rajiv Sambasivan @author: Joerg Schad @author: Anthony Mahanna
"""

from abc import ABC
from typing import Any

from arango.graph import Graph as ArangoDBGraph
from networkx.classes.graph import Graph as NetworkXGraph
from networkx.classes.multidigraph import MultiDiGraph


class Abstract_ADBNX_Adapter(ABC):
    def __init__(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def arangodb_to_networkx(
        self,
        name: str,
        metagraph: dict[str, dict[str, set[str]]],
        is_keep: bool = True,
        **query_options: Any,
    ) -> MultiDiGraph:
        raise NotImplementedError()  # pragma: no cover

    def arangodb_collections_to_networkx(
        self,
        name: str,
        v_cols: set[str],
        e_cols: set[str],
        **query_options: Any,
    ) -> MultiDiGraph:
        raise NotImplementedError()  # pragma: no cover

    def arangodb_graph_to_networkx(
        self, name: str, **query_options: Any
    ) -> MultiDiGraph:
        raise NotImplementedError()  # pragma: no cover

    def networkx_to_arangodb(
        self,
        name: str,
        nx_graph: NetworkXGraph,
        edge_definitions: list[dict[str, Any]],
        batch_size: int = 1000,
        keyify_nodes: bool = False,
        keyify_edges: bool = False,
    ) -> ArangoDBGraph:
        raise NotImplementedError()  # pragma: no cover

    def __validate_attributes(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def __fetch_adb_docs(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    def __insert_adb_docs(self) -> None:
        raise NotImplementedError()  # pragma: no cover

    @property
    def CONNECTION_ATRIBS(self) -> set[str]:
        return {"hostname", "username", "password", "dbName"}

    @property
    def METAGRAPH_ATRIBS(self) -> set[str]:
        return {"vertexCollections", "edgeCollections"}

    @property
    def EDGE_DEFINITION_ATRIBS(self) -> set[str]:
        return {"edge_collection", "from_vertex_collections", "to_vertex_collections"}


class Abstract_ADBNX_Controller(ABC):
    def _prepare_arangodb_vertex(self, adb_vertex: dict[str, Any], col: str) -> Any:
        raise NotImplementedError()  # pragma: no cover

    def _prepare_arangodb_edge(self, adb_edge: dict[str, Any], col: str) -> Any:
        raise NotImplementedError()  # pragma: no cover

    def _identify_networkx_node(self, nx_node_id: Any, nx_node: dict[str, Any]) -> str:
        raise NotImplementedError()  # pragma: no cover

    def _identify_networkx_edge(
        self,
        nx_edge: dict[str, Any],
        from_nx_node: dict[str, Any],
        to_nx_node: dict[str, Any],
    ) -> str:
        raise NotImplementedError()  # pragma: no cover

    def _keyify_networkx_node(
        self, nx_node_id: Any, nx_node: dict[str, Any], col: str
    ) -> str:
        raise NotImplementedError()  # pragma: no cover

    def _keyify_networkx_edge(
        self,
        nx_edge: dict[str, Any],
        from_nx_node: dict[str, Any],
        to_nx_node: dict[str, Any],
        col: str,
    ) -> str:
        raise NotImplementedError()  # pragma: no cover

    @property
    def VALID_KEY_CHARS(self) -> set[str]:
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
