#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC
from typing import Any, Dict, List, Optional, Set, Union

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
        explicit_metagraph: bool = True,
        nx_graph: Optional[NXMultiDiGraph] = None,
        **adb_export_kwargs: Any,
    ) -> NXMultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def arangodb_collections_to_networkx(
        self,
        name: str,
        v_cols: Set[str],
        e_cols: Set[str],
        nx_graph: Optional[NXMultiDiGraph] = None,
        **adb_export_kwargs: Any,
    ) -> NXMultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def arangodb_graph_to_networkx(
        self,
        name: str,
        nx_graph: Optional[NXMultiDiGraph] = None,
        **adb_export_kwargs: Any,
    ) -> NXMultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def networkx_to_arangodb(
        self,
        name: str,
        nx_graph: NXGraph,
        edge_definitions: Optional[List[Json]] = None,
        orphan_collections: Optional[List[str]] = None,
        overwrite_graph: bool = False,
        batch_size: int = 1000,
        use_async: bool = False,
        **adb_import_kwargs: Any,
    ) -> ADBGraph:
        raise NotImplementedError  # pragma: no cover


class Abstract_ADBNX_Controller(ABC):
    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> None:
        raise NotImplementedError  # pragma: no cover

    def _prepare_arangodb_edge(self, adb_edge: Json, col: str) -> None:
        raise NotImplementedError  # pragma: no cover

    def _prepare_networkx_node(
        self, i: int, nx_node_id: Any, nx_node: NxData, adb_v_cols: List[str]
    ) -> tuple[str, str]:
        raise NotImplementedError  # pragma: no cover

    def _prepare_networkx_edge(
        self,
        i: int,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_edge: NxData,
        adb_e_cols: List[str],
        nx_map: Dict[Any, str],
    ) -> tuple[str, Union[str, None]]:
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
