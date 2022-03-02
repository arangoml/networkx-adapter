#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC
from typing import Any, List, Set

from arango.graph import Graph as ArangoDBGraph

try:
    from cugraph import MultiGraph as cuGraphMultiGraph

    cugraph = True
except ImportError:
    cugraph = False
from networkx.classes.graph import Graph as NetworkXGraph
from networkx.classes.multidigraph import MultiDiGraph

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
    ) -> MultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def arangodb_collections_to_networkx(
        self,
        name: str,
        v_cols: Set[str],
        e_cols: Set[str],
        **query_options: Any,
    ) -> MultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    if cugraph is False:
        pass
    else:

        def arangodb_to_cugraph(
            self,
            name: str,
            metagraph: ArangoMetagraph,
            is_keep: bool = True,
            **query_options: Any,
        ) -> cuGraphMultiGraph(directed=True):  # type: ignore
            raise NotImplementedError  # pragma: no cover

        def arangodb_collections_to_cugraph(
            self,
            name: str,
            v_cols: Set[str],
            e_cols: Set[str],
            **query_options: Any,
        ) -> cuGraphMultiGraph(directed=True):  # type: ignore
            raise NotImplementedError  # pragma: no cover

        def arangodb_graph_to_cugraph(
            self, name: str, **query_options: Any
        ) -> cuGraphMultiGraph(directed=True):  # type: ignore
            raise NotImplementedError  # pragma: no cover

    def arangodb_graph_to_networkx(
        self, name: str, **query_options: Any
    ) -> MultiDiGraph:
        raise NotImplementedError  # pragma: no cover

    def networkx_to_arangodb(
        self,
        name: str,
        nx_graph: NetworkXGraph,
        edge_definitions: List[Json],
        batch_size: int = 1000,
        keyify_nodes: bool = False,
        keyify_edges: bool = False,
    ) -> ArangoDBGraph:
        raise NotImplementedError  # pragma: no cover

    def __validate_attributes(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def __fetch_adb_docs(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def __insert_adb_docs(self) -> None:
        raise NotImplementedError  # pragma: no cover

    @property
    def CONNECTION_ATRIBS(self) -> Set[str]:
        return {"hostname", "username", "password", "dbName"}

    @property
    def METAGRAPH_ATRIBS(self) -> Set[str]:
        return {"vertexCollections", "edgeCollections"}

    @property
    def EDGE_DEFINITION_ATRIBS(self) -> Set[str]:
        return {"edge_collection", "from_vertex_collections", "to_vertex_collections"}


class Abstract_ADBNX_Controller(ABC):
    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> NxId:
        raise NotImplementedError  # pragma: no cover

    def _prepare_arangodb_edge(self, adb_edge: Json, col: str) -> NxId:
        raise NotImplementedError  # pragma: no cover

    def _identify_networkx_node(self, nx_node_id: NxId, nx_node: NxData) -> str:
        raise NotImplementedError  # pragma: no cover

    def _identify_networkx_edge(
        self,
        nx_edge: NxData,
        from_nx_node: NxData,
        to_nx_node: NxData,
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
