#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Set, Tuple, Union

from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.graph import Graph as ADBGraph
from networkx.classes.graph import Graph as NXGraph
from networkx.classes.multidigraph import MultiDiGraph as NXMultiDiGraph
from rich.console import Group
from rich.live import Live
from rich.progress import Progress

from .abc import Abstract_ADBNX_Adapter
from .controller import ADBNX_Controller
from .typings import ArangoMetagraph, Json, NxData, NxId
from .utils import (
    get_bar_progress,
    get_export_spinner_progress,
    get_import_spinner_progress,
    logger,
)


class ADBNX_Adapter(Abstract_ADBNX_Adapter):
    """ArangoDB-NetworkX adapter.

    :param db: A python-arango database instance
    :type db: arango.database.StandardDatabase
    :param controller: The ArangoDB-NetworkX controller, used to identify, keyify
        and prepare nodes & edges before insertion, optionally re-defined by the user
        if needed (otherwise defaults to ADBNX_Controller).
    :type controller: ADBNX_Controller
    :param logging_lvl: Defaults to logging.INFO. Other useful options are
        logging.DEBUG (more verbose), and logging.WARNING (less verbose).
    :type logging_lvl: str | int
    :raise ValueError: If invalid parameters
    """

    def __init__(
        self,
        db: StandardDatabase,
        controller: ADBNX_Controller = ADBNX_Controller(),
        logging_lvl: Union[str, int] = logging.INFO,
    ):
        self.set_logging(logging_lvl)

        if issubclass(type(db), StandardDatabase) is False:
            msg = "**db** parameter must inherit from arango.database.StandardDatabase"
            raise TypeError(msg)

        if issubclass(type(controller), ADBNX_Controller) is False:
            msg = "**controller** parameter must inherit from ADBNX_Controller"
            raise TypeError(msg)

        self.__db = db
        self.__async_db = db.begin_async_execution(return_result=False)

        self.__cntrl: ADBNX_Controller = controller
        self.__prepare_adb_vertex_method_is_empty = (
            controller.__class__._prepare_arangodb_vertex
            is ADBNX_Controller._prepare_arangodb_vertex
        )

        logger.info(f"Instantiated ADBNX_Adapter with database '{db.name}'")

    @property
    def db(self) -> StandardDatabase:
        return self.__db  # pragma: no cover

    @property
    def cntrl(self) -> ADBNX_Controller:
        return self.__cntrl  # pragma: no cover

    def set_logging(self, level: Union[int, str]) -> None:
        logger.setLevel(level)

    ################################
    # Public: ArangoDB -> NetworkX #
    ################################

    def arangodb_to_networkx(
        self,
        name: str,
        metagraph: ArangoMetagraph,
        explicit_metagraph: bool = True,
        nx_graph: Optional[NXMultiDiGraph] = None,
        **adb_export_kwargs: Any,
    ) -> NXMultiDiGraph:
        """Create a NetworkX graph from graph attributes.

        :param name: The NetworkX graph name.
        :type name: str
        :param metagraph: An object defining vertex & edge collections to import to
            NetworkX, along with their associated attributes to keep.
        :type metagraph: adbnx_adapter.typings.ArangoMetagraph
        :param explicit_metagraph: Only keep the document attributes specified in
            **metagraph** when importing to NetworkX (is True by default). Otherwise,
            all document attributes are included. Defaults to True.
        :type explicit_metagraph: bool
        :param adb_export_kwargs: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.aql.AQL.execute
        :type adb_export_kwargs: Any
        :param nx_graph: An existing NetworkX graph to append to (optional).
        :type nx_graph: networkx.classes.multidigraph.MultiDiGraph | None
        :return: A Multi-Directed NetworkX Graph containing the ArangoDB data.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        :raise ValueError: If missing required keys in metagraph

        Here is an example entry for parameter **metagraph**:

        .. code-block:: python
        {
            "vertexCollections": {
                "account": {"Balance", "account_type", "customer_id", "rank"},
                "bank": {"Country", "Id", "bank_id", "bank_name"},
                "customer": {"Name", "Sex", "Ssn", "rank"},
            },
            "edgeCollections": {
                "accountHolder": {},
                "transaction": {
                    "transaction_amt", "receiver_bank_id", "sender_bank_id"
                },
            },
        }
        """
        logger.debug(f"--arangodb_to_networkx('{name}')--")

        # Create a new NetworkX graph if one is not provided
        nx_graph = nx_graph if nx_graph is not None else NXMultiDiGraph(name=name)

        # This maps the ArangoDB vertex IDs to NetworkX node IDs
        adb_map: Dict[str, NxId] = dict()

        ######################
        # Vertex Collections #
        ######################

        for v_col, atribs in metagraph["vertexCollections"].items():
            logger.debug(f"Preparing '{v_col}' vertices")

            # 1. Fetch ArangoDB vertices
            v_col_cursor, v_col_size = self.__fetch_adb_docs(
                v_col, False, atribs, explicit_metagraph, **adb_export_kwargs
            )

            # 2. Process ArangoDB vertices
            self.__process_adb_cursor(
                "#079DE8",
                v_col_cursor,
                v_col_size,
                self.__process_adb_vertex,
                v_col,
                adb_map,
                nx_graph,
            )

        ####################
        # Edge Collections #
        ####################

        for e_col, atribs in metagraph.get("edgeCollections", {}).items():
            logger.debug(f"Preparing '{e_col}' edges")

            # 1. Fetch ArangoDB edges
            e_col_cursor, e_col_size = self.__fetch_adb_docs(
                e_col, True, atribs, explicit_metagraph, **adb_export_kwargs
            )

            # 2. Process ArangoDB edges
            self.__process_adb_cursor(
                "#FA7D05",
                e_col_cursor,
                e_col_size,
                self.__process_adb_edge,
                e_col,
                adb_map,
                nx_graph,
            )

        logger.info(f"Created NetworkX '{name}' Graph")
        return nx_graph

    def arangodb_collections_to_networkx(
        self,
        name: str,
        v_cols: Set[str],
        e_cols: Set[str],
        nx_graph: Optional[NXMultiDiGraph] = None,
        **adb_export_kwargs: Any,
    ) -> NXMultiDiGraph:
        """Create a NetworkX graph from ArangoDB collections.

        :param name: The NetworkX graph name.
        :type name: str
        :param v_cols: A set of vertex collections to import to NetworkX.
        :type v_cols: Set[str]
        :param e_cols: A set of edge collections to import to NetworkX.
        :type e_cols: Set[str]
        :param nx_graph: An existing NetworkX graph to append to (optional).
        :type nx_graph: networkx.classes.multidigraph.MultiDiGraph | None
        :param adb_export_kwargs: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.aql.AQL.execute
        :type adb_export_kwargs: Any
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        metagraph: ArangoMetagraph = {
            "vertexCollections": {col: set() for col in v_cols},
            "edgeCollections": {col: set() for col in e_cols},
        }

        return self.arangodb_to_networkx(
            name,
            metagraph,
            explicit_metagraph=False,
            nx_graph=nx_graph,
            **adb_export_kwargs,
        )

    def arangodb_graph_to_networkx(
        self,
        name: str,
        nx_graph: Optional[NXMultiDiGraph] = None,
        **adb_export_kwargs: Any,
    ) -> NXMultiDiGraph:
        """Create a NetworkX graph from an ArangoDB graph.

        :param name: The ArangoDB graph name.
        :type name: str
        :param nx_graph: An existing NetworkX graph to append to (optional).
        :type nx_graph: networkx.classes.multidigraph.MultiDiGraph | None
        :param adb_export_kwargs: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.aql.AQL.execute
        :type adb_export_kwargs: Any
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        graph = self.__db.graph(name)
        v_cols: Set[str] = graph.vertex_collections()
        edge_definitions: List[Json] = graph.edge_definitions()
        e_cols: Set[str] = {c["edge_collection"] for c in edge_definitions}

        return self.arangodb_collections_to_networkx(
            name, v_cols, e_cols, nx_graph, **adb_export_kwargs
        )

    ################################
    # Public: NetworkX -> ArangoDB #
    ################################

    def networkx_to_arangodb(
        self,
        name: str,
        nx_graph: NXGraph,
        edge_definitions: Optional[List[Json]] = None,
        orphan_collections: Optional[List[str]] = None,
        overwrite_graph: bool = False,
        batch_size: Optional[int] = None,
        use_async: bool = False,
        **adb_import_kwargs: Any,
    ) -> ADBGraph:
        """Create an ArangoDB graph from a NetworkX graph, and a set of edge
        definitions.

        :param name: The ArangoDB graph name.
        :type name: str
        :param nx_graph: The existing NetworkX graph.
        :type nx_graph: networkx.classes.graph.Graph
        :param edge_definitions: List of edge definitions, where each edge
            definition entry is a dictionary with fields "edge_collection",
            "from_vertex_collections" and "to_vertex_collections" (see below
            for example). Can be omitted if the graph already exists.
        :type edge_definitions: List[Dict[str, Any]]
        :param orphan_collections: A list of vertex collections that will be stored as
            orphans in the ArangoDB graph. Can be omitted if the graph already exists.
        :type orphan_collections: List[str]
        :param overwrite_graph: Overwrites the graph if it already exists.
            Does not drop associated collections.
        :type overwrite_graph: bool
        :param batch_size: If specified, runs the ArangoDB Data Ingestion
            process for every **batch_size** NetworkX nodes/edges within **nx_graph**.
            Defaults to `len(nx_nodes)` & `len(nx_edges)`.
        :type batch_size: int | None
        :param use_async: Performs asynchronous ArangoDB ingestion if enabled.
            Defaults to False.
        :type use_async: bool
        :param adb_import_kwargs: Keyword arguments to specify additional
            parameters for ArangoDB document insertion. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.collection.Collection.import_bulk
        :type adb_import_kwargs: Any
        :return: The ArangoDB Graph API wrapper.
        :rtype: arango.graph.Graph

        Here is an example entry for parameter **edge_definitions**:

        .. code-block:: python
        [
            {
                "edge_collection": "teach",
                "from_vertex_collections": ["teachers"],
                "to_vertex_collections": ["lectures"]
            }
        ]
        """
        logger.debug(f"--networkx_to_arangodb('{name}')--")

        adb_graph = self.__create_adb_graph(
            name, overwrite_graph, edge_definitions, orphan_collections
        )

        adb_v_cols: List[str] = adb_graph.vertex_collections()
        adb_e_cols: List[str] = [
            c["edge_collection"] for c in adb_graph.edge_definitions()
        ]

        has_one_v_col = len(adb_v_cols) == 1
        has_one_e_col = len(adb_e_cols) == 1
        logger.debug(f"Is '{name}' homogeneous? {has_one_v_col and has_one_e_col}")

        # This maps NetworkX node IDs to ArangoDB vertex IDs
        nx_map: Dict[NxId, str] = dict()

        # Stores to-be-inserted ArangoDB documents by collection name
        adb_docs: DefaultDict[str, List[Json]] = defaultdict(list)

        spinner_progress = get_import_spinner_progress("    ")

        ##################
        # NetworkX Nodes #
        ##################

        nx_id: NxId
        nx_node: NxData

        nx_nodes = nx_graph.nodes(data=True)
        node_batch_size = batch_size or len(nx_nodes)

        bar_progress = get_bar_progress("(NX → ADB): Nodes", "#97C423")
        bar_progress_task = bar_progress.add_task("Nodes", total=len(nx_nodes))

        with Live(Group(bar_progress, spinner_progress)):
            for i, (nx_id, nx_node) in enumerate(nx_nodes, 1):
                bar_progress.advance(bar_progress_task)

                # 1. Process NetworkX node
                self.__process_nx_node(
                    i,
                    nx_id,
                    nx_node,
                    nx_map,
                    adb_docs,
                    adb_v_cols,
                    has_one_v_col,
                )

                # 2. Insert batch of nodes
                if i % node_batch_size == 0:
                    self.__insert_adb_docs(
                        spinner_progress, adb_docs, use_async, **adb_import_kwargs
                    )

            # Insert remaining nodes
            self.__insert_adb_docs(
                spinner_progress, adb_docs, use_async, **adb_import_kwargs
            )

        ##################
        # NetworkX Edges #
        ##################

        from_node_id: NxId
        to_node_id: NxId
        nx_edge: NxData

        nx_edges = nx_graph.edges(data=True)
        edge_batch_size = batch_size or len(nx_edges)

        bar_progress = get_bar_progress("(NX → ADB): Edges", "#5E3108")
        bar_progress_task = bar_progress.add_task("Edges", total=len(nx_edges))

        with Live(Group(bar_progress, spinner_progress)):
            for i, (from_node_id, to_node_id, nx_edge) in enumerate(nx_edges, 1):
                bar_progress.advance(bar_progress_task)

                # 1. Process NetworkX edge
                self.__process_nx_edge(
                    i,
                    from_node_id,
                    to_node_id,
                    nx_edge,
                    nx_map,
                    adb_docs,
                    adb_e_cols,
                    has_one_e_col,
                )

                # 2. Insert batch of edges
                if i % edge_batch_size == 0:
                    self.__insert_adb_docs(
                        spinner_progress, adb_docs, use_async, **adb_import_kwargs
                    )

            # Insert remaining edges
            self.__insert_adb_docs(
                spinner_progress, adb_docs, use_async, **adb_import_kwargs
            )

        logger.info(f"Created ArangoDB '{name}' Graph")
        return adb_graph

    #################################
    # Private: ArangoDB -> NetworkX #
    #################################

    def __fetch_adb_docs(
        self,
        col: str,
        is_edge: bool,
        attributes: Set[str],
        explicit_metagraph: bool,
        **adb_export_kwargs: Any,
    ) -> Tuple[Cursor, int]:
        """ArangoDB -> NetworkX: Fetches ArangoDB documents within a collection.

        :param col: The ArangoDB collection.
        :type col: str
        :param is_edge: True if **col** is an edge collection.
        :type is_edge: bool
        :param attributes: The set of document attributes.
        :type attributes: Set[str]
        :param explicit_metagraph: If True, only return the set of **attributes**
            specified when fetching the documents of the collection **col**.
            If False, all document attributes are included.
        :type explicit_metagraph: bool
        :param adb_export_kwargs: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance.
        :type adb_export_kwargs: Any
        :return: The document cursor along with the total collection size.
        :rtype: Tuple[arango.cursor.Cursor, int]
        """
        aql_return_value = "doc"
        if explicit_metagraph:
            default_keys = ["_id", "_key"]
            default_keys += ["_from", "_to"] if is_edge else []
            aql_return_value = f"KEEP(doc, {list(attributes) + default_keys})"

        col_size: int = self.__db.collection(col).count()

        with get_export_spinner_progress(f"ADB Export: '{col}' ({col_size})") as p:
            p.add_task(col)

            cursor: Cursor = self.__db.aql.execute(
                f"FOR doc IN @@col RETURN {aql_return_value}",
                bind_vars={"@col": col},
                **{**adb_export_kwargs, **{"stream": True}},
            )

            return cursor, col_size

    def __process_adb_cursor(
        self,
        progress_color: str,
        cursor: Cursor,
        col_size: int,
        process_adb_doc: Callable[..., None],
        col: str,
        adb_map: Dict[str, NxId],
        nx_graph: NXMultiDiGraph,
    ) -> None:
        """ArangoDB -> NetworkX: Processes the ArangoDB Cursors for vertices and edges.

        :param progress_color: The progress bar color.
        :type progress_color: str
        :param cursor: The ArangoDB cursor for the current **col**.
        :type cursor: arango.cursor.Cursor
        :param process_adb_doc: The function to process the cursor data.
        :type process_adb_doc: Callable
        :param col: The ArangoDB collection for the current **cursor**.
        :type col: str
        :param col_size: The size of **col**.
        :type col_size: int
        :param adb_map: Maps ArangoDB vertex IDs to NetworkX node IDs.
        :type adb_map: Dict[str, adbnx_adapter.typings.NxId]
        :param nx_graph: The NetworkX graph.
        :type nx_graph: networkx.classes.multidigraph.MultiDiGraph
        """

        progress = get_bar_progress(f"(ADB → NX): '{col}'", progress_color)
        progress_task_id = progress.add_task(col, total=col_size)

        with Live(Group(progress)):
            while not cursor.empty():
                for doc in cursor.batch():
                    progress.advance(progress_task_id)

                    process_adb_doc(doc, col, adb_map, nx_graph)

                cursor.batch().clear()
                if cursor.has_more():
                    cursor.fetch()

    def __process_adb_vertex(
        self,
        adb_v: Json,
        v_col: str,
        adb_map: Dict[str, NxId],
        nx_graph: NXMultiDiGraph,
    ) -> None:
        """ArangoDB -> NetworkX: Processes an ArangoDB vertex.

        :param adb_v: The ArangoDB vertex.
        :type adb_v: Dict[str, Any]
        :param v_col: The ArangoDB vertex collection.
        :type v_col: str
        :param adb_map: Maps ArangoDB vertex IDs to NetworkX node IDs.
        :type adb_map: Dict[str, adbnx_adapter.typings.NxId]
        :param nx_graph: The NetworkX graph.
        :type nx_graph: networkx.classes.multidigraph.MultiDiGraph
        """
        if not self.__prepare_adb_vertex_method_is_empty:
            adb_id: str = adb_v["_id"]
            self.__cntrl._prepare_arangodb_vertex(adb_v, v_col)
            nx_id: str = adb_v["_id"]

            if adb_id != nx_id:
                adb_map[adb_id] = nx_id

        nx_graph.add_node(adb_v["_id"], **adb_v)

    def __process_adb_edge(
        self,
        adb_e: Json,
        e_col: str,
        adb_map: Dict[str, NxId],
        nx_graph: NXMultiDiGraph,
    ) -> None:
        """ArangoDB -> NetworkX: Processes an ArangoDB edge.

        :param adb_e: The ArangoDB edge.
        :type adb_e: Dict[str, Any]
        :param e_col: The ArangoDB edge collection.
        :type e_col: str
        :param adb_map: Maps ArangoDB vertex IDs to NetworkX node IDs.
        :type adb_map: Dict[str, adbnx_adapter.typings.NxId]
        :param nx_graph: The NetworkX graph.
        :type nx_graph: networkx.classes.multidigraph.MultiDiGraph
        """
        from_node_id: NxId = adb_map.get(adb_e["_from"], adb_e["_from"])
        to_node_id: NxId = adb_map.get(adb_e["_to"], adb_e["_to"])

        self.__cntrl._prepare_arangodb_edge(adb_e, e_col)
        nx_graph.add_edge(from_node_id, to_node_id, **adb_e)

    #################################
    # Private: NetworkX -> ArangoDB #
    #################################

    def __create_adb_graph(
        self,
        name: str,
        overwrite_graph: bool,
        edge_definitions: Optional[List[Json]] = None,
        orphan_collections: Optional[List[str]] = None,
    ) -> ADBGraph:
        """NetworkX -> ArangoDB: Creates the ArangoDB graph.

        :param name: The ArangoDB graph name.
        :type name: str
        :param overwrite_graph: Overwrites the graph if it already exists.
        :type overwrite_graph: bool
        :param edge_definitions: ArangoDB edge definitions.
        :type edge_definitions: List[Dict[str, Any]]
        :param orphan_collections: ArangoDB orphan collections.
        :type orphan_collections: List[str]
        :return: The ArangoDB Graph API wrapper.
        :rtype: arango.graph.Graph
        """
        if overwrite_graph:
            logger.debug("Overwrite graph flag is True. Deleting old graph.")
            self.__db.delete_graph(name, ignore_missing=True)

        if self.__db.has_graph(name):
            logger.debug(f"Graph {name} already exists")
            return self.__db.graph(name)

        else:
            logger.debug(f"Creating graph {name}")
            return self.__db.create_graph(
                name,
                edge_definitions,
                orphan_collections,
            )

    def __process_nx_node(
        self,
        i: int,
        nx_id: NxId,
        nx_node: NxData,
        nx_map: Dict[NxId, str],
        adb_docs: DefaultDict[str, List[Json]],
        adb_v_cols: List[str],
        has_one_v_col: bool,
    ) -> None:
        """NetworkX -> ArangoDB: Processes a NetworkX node.

        :param i: The node index.
        :type i: int
        :param nx_id: The NetworkX node ID.
        :type nx_id: adbnx_adapter.typings.NxId
        :param nx_node: The NetworkX node data.
        :type nx_node: adbnx_adapter.typings.NxData
        :param nx_map: Maps NetworkX node IDs to ArangoDB vertex IDs.
        :type nx_map: Dict[adbnx_adapter.typings.NxId, str]
        :param adb_docs: To-be-inserted ArangoDB documents.
        :type adb_docs: DefaultDict[str, List[Dict[str, Any]]]
        :param adb_v_cols: The ArangoDB vertex collections.
        :type adb_v_cols: List[str]
        :param has_one_v_col: True if the Graph has one Vertex collection.
        :type has_one_v_col: bool
        """
        logger.debug(f"N{i}: {nx_id}")

        col = (
            adb_v_cols[0]
            if has_one_v_col
            else self.__cntrl._identify_networkx_node(nx_id, nx_node, adb_v_cols)
        )

        if not has_one_v_col and col not in adb_v_cols:
            msg = f"'{nx_id}' identified as '{col}', which is not in {adb_v_cols}"
            raise ValueError(msg)

        key = self.__cntrl._keyify_networkx_node(i, nx_id, nx_node, col)

        adb_id = f"{col}/{key}"
        nx_node["_id"] = adb_id
        nx_node["_key"] = key

        nx_map[nx_id] = adb_id

        self.__cntrl._prepare_networkx_node(nx_node, col)
        adb_docs[col].append(nx_node)

    def __process_nx_edge(
        self,
        i: int,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_edge: NxData,
        nx_map: Dict[NxId, str],
        adb_docs: DefaultDict[str, List[Json]],
        adb_e_cols: List[str],
        has_one_e_col: bool,
    ) -> None:
        """NetworkX -> ArangoDB: Processes a NetworkX edge.

        :param i: The edge index.
        :type i: int
        :param from_node_id: The NetworkX ID of the source node.
        :type from_node_id: adbnx_adapter.typings.NxId
        :param to_node_id: The NetworkX ID of the target node.
        :type to_node_id: adbnx_adapter.typings.NxId
        :param nx_edge: The NetworkX edge data.
        :type nx_edge: Dict[str, Any]
        :param nx_map: Maps NetworkX node IDs to ArangoDB vertex IDs.
        :type nx_map: Dict[adbnx_adapter.typings.NxId, str]
        :param adb_docs: To-be-inserted ArangoDB documents.
        :type adb_docs: DefaultDict[str, List[Dict[str, Any]]]
        :param adb_e_cols: The ArangoDB edge collections.
        :type adb_e_cols: List[str]
        :param has_one_e_col: True if the Graph has one Edge collection.
        :type has_one_e_col: bool
        """
        edge_str = f"({from_node_id}, {to_node_id})"
        logger.debug(f"E{i}: {edge_str}")

        col = (
            adb_e_cols[0]
            if has_one_e_col
            else self.__cntrl._identify_networkx_edge(
                nx_edge,
                from_node_id,
                to_node_id,
                nx_map,
                adb_e_cols,
            )
        )

        if not has_one_e_col and col not in adb_e_cols:
            msg = f"{edge_str} identified as '{col}', which is not in {adb_e_cols}"
            raise ValueError(msg)

        key = self.__cntrl._keyify_networkx_edge(
            i,
            nx_edge,
            from_node_id,
            to_node_id,
            nx_map,
            col,
        )

        nx_edge["_id"] = f"{col}/{key}"
        nx_edge["_key"] = key
        nx_edge["_from"] = nx_map[from_node_id]
        nx_edge["_to"] = nx_map[to_node_id]

        self.__cntrl._prepare_networkx_edge(nx_edge, col)
        adb_docs[col].append(nx_edge)

    def __insert_adb_docs(
        self,
        spinner_progress: Progress,
        adb_docs: DefaultDict[str, List[Json]],
        use_async: bool,
        **adb_import_kwargs: Any,
    ) -> None:
        """NetworkX -> ArangoDB: Insert the ArangoDB documents.

        :param spinner_progress: The spinner progress bar.
        :type spinner_progress: rich.progress.Progress
        :param adb_docs: To-be-inserted ArangoDB documents
        :type adb_docs: DefaultDict[str, List[Json]]
        :param use_async: Performs asynchronous ArangoDB ingestion if enabled.
        :type use_async: bool
        :param adb_import_kwargs: Keyword arguments to specify additional
            parameters for ArangoDB document insertion. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.collection.Collection.import_bulk
        :param adb_import_kwargs: Any
        """
        if len(adb_docs) == 0:
            return

        db = self.__async_db if use_async else self.__db

        # Avoiding "RuntimeError: dictionary changed size during iteration"
        adb_cols = list(adb_docs.keys())

        for col in adb_cols:
            doc_list = adb_docs[col]

            action = f"ADB Import: '{col}' ({len(doc_list)})"
            spinner_progress_task = spinner_progress.add_task("", action=action)

            result = db.collection(col).import_bulk(doc_list, **adb_import_kwargs)
            logger.debug(result)

            del adb_docs[col]

            spinner_progress.stop_task(spinner_progress_task)
            spinner_progress.update(spinner_progress_task, visible=False)
