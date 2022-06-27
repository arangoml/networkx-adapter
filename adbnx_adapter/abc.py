#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC
from typing import Any, List, Optional, Set

from arango.graph import Graph as ADBGraph
from networkx.classes.graph import Graph as NXGraph
from networkx.classes.multidigraph import MultiGraph as NXMultiDiGraph

from .typings import ArangoMetagraph, Json, NxData, NxId


class Abstract_ADBNX_Adapter(ABC):
    def __init__(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def arangodb_to_networkx(
        self,
        name: str,
        metagraph: ArangoMetagraph,
        is_keep: bool = True,
        **query_options: Any,
    ) -> NXMultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def arangodb_collections_to_networkx(
        self,
        name: str,
        v_cols: Set[str],
        e_cols: Set[str],
        **query_options: Any,
    ) -> NXMultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def arangodb_graph_to_networkx(
        self, name: str, **query_options: Any
    ) -> NXMultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def networkx_to_arangodb(
        self,
        name: str,
        nx_graph: NXGraph,
        edge_definitions: Optional[List[Json]] = None,
        keyify_nodes: bool = False,
        keyify_edges: bool = False,
        overwrite_graph: bool = False,
        **import_options: Any,
    ) -> ADBGraph:
        raise NotImplementedError  # pragma: no cover

    def __fetch_adb_docs(self) -> None:
        raise NotImplementedError  # pragma: no cover


class Abstract_ADBNX_Controller(ABC):
    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> None:
        raise NotImplementedError  # pragma: no cover

    def _prepare_arangodb_edge(self, adb_edge: Json, col: str) -> None:
        raise NotImplementedError  # pragma: no cover

    def _identify_networkx_node(
        self, nx_node_id: NxId, nx_node: NxData, adb_v_cols: List[str]
    ) -> str:
        raise NotImplementedError  # pragma: no cover

    def _identify_networkx_edge(
        self,
        nx_edge: NxData,
        from_nx_node: NxData,
        to_nx_node: NxData,
        adb_e_cols: List[str],
    ) -> str:
        raise NotImplementedError  # pragma: no cover

    def _keyify_networkx_node(self, nx_node_id: NxId, nx_node: NxData, col: str) -> str:
        raise NotImplementedError  # pragma: no cover

    def _keyify_networkx_edge(
        self,
        nx_edge: NxData,
        from_nx_node: NxData,
        to_nx_node: NxData,
        col: str,
    ) -> str:
        raise NotImplementedError  # pragma: no cover

    @property
    def VALID_KEY_CHARS(self) -> Set[str]:
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
