#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple, Union

from arango.cursor import Cursor
from arango.database import Database
from arango.graph import Graph as ADBGraph
from arango.result import Result
from networkx.classes.graph import Graph as NXGraph
from networkx.classes.multidigraph import MultiDiGraph as NXMultiDiGraph
from rich.progress import track
from rich.status import Status

from .abc import Abstract_ADBNX_Adapter
from .controller import ADBNX_Controller
from .typings import ArangoMetagraph, Json, NxData, NxId
from .utils import logger


class ADBNX_Adapter(Abstract_ADBNX_Adapter):
    """ArangoDB-NetworkX adapter.

    :param db: A python-arango database instance
    :type db: arango.database.Database
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
        db: Database,
        controller: ADBNX_Controller = ADBNX_Controller(),
        logging_lvl: Union[str, int] = logging.INFO,
    ):
        self.set_logging(logging_lvl)

        if issubclass(type(db), Database) is False:
            msg = "**db** parameter must inherit from arango.database.Database"
            raise TypeError(msg)

        if issubclass(type(controller), ADBNX_Controller) is False:
            msg = "**controller** parameter must inherit from ADBNX_Controller"
            raise TypeError(msg)

        self.__db = db
        self.__cntrl: ADBNX_Controller = controller

        logger.info(f"Instantiated ADBNX_Adapter with database '{db.name}'")

    @property
    def db(self) -> Database:
        return self.__db  # pragma: no cover

    @property
    def cntrl(self) -> ADBNX_Controller:
        return self.__cntrl  # pragma: no cover

    def set_logging(self, level: Union[int, str]) -> None:
        logger.setLevel(level)

    def arangodb_to_networkx(
        self,
        name: str,
        metagraph: ArangoMetagraph,
        is_keep: bool = True,
        **query_options: Any,
    ) -> NXMultiDiGraph:
        """Create a NetworkX graph from graph attributes.

        :param name: The NetworkX graph name.
        :type name: str
        :param metagraph: An object defining vertex & edge collections to import to
            NetworkX, along with their associated attributes to keep.
        :type metagraph: adbnx_adapter.typings.ArangoMetagraph
        :param is_keep: Only keep the document attributes specified in **metagraph**
            when importing to NetworkX (is True by default). Otherwise, all document
            attributes are included.
        :type is_keep: bool
        :param query_options: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.aql.AQL.execute
        :type query_options: Any
        :return: A Multi-Directed NetworkX Graph.
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

        nx_graph = NXMultiDiGraph(name=name)
        nx_nodes: List[Tuple[NxId, NxData]] = []
        nx_edges: List[Tuple[NxId, NxId, NxData]] = []

        # Maps ArangoDB vertex IDs to NetworkX node IDs
        adb_map: Dict[str, NxId] = dict()

        adb_v: Json
        for v_col, atribs in metagraph["vertexCollections"].items():
            logger.debug(f"Preparing '{v_col}' vertices")

            nx_nodes.clear()
            cursor = self.__fetch_adb_docs(v_col, atribs, is_keep, query_options)
            for adb_v in track(
                cursor,
                total=cursor.count(),
                description=v_col,
                complete_style="#079DE8",
                finished_style="#079DE8",
                disable=logger.level != logging.INFO,
            ):
                adb_id: str = adb_v["_id"]
                self.__cntrl._prepare_arangodb_vertex(adb_v, v_col)
                nx_id: str = adb_v["_id"]

                adb_map[adb_id] = nx_id
                nx_nodes.append((nx_id, adb_v))

            logger.debug(f"Inserting {len(nx_nodes)} '{v_col}' vertices")
            nx_graph.add_nodes_from(nx_nodes)

        adb_e: Json
        for e_col, atribs in metagraph["edgeCollections"].items():
            logger.debug(f"Preparing '{e_col}' edges")

            cursor = self.__fetch_adb_docs(e_col, atribs, is_keep, query_options)
            for adb_e in track(
                cursor,
                total=cursor.count(),
                description=e_col,
                complete_style="#FA7D05",
                finished_style="#FA7D05",
                disable=logger.level != logging.INFO,
            ):
                from_node_id: NxId = adb_map[adb_e["_from"]]
                to_node_id: NxId = adb_map[adb_e["_to"]]

                self.__cntrl._prepare_arangodb_edge(adb_e, e_col)
                nx_edges.append((from_node_id, to_node_id, adb_e))

            logger.debug(f"Inserting {len(nx_edges)} '{e_col}' edges")
            nx_graph.add_edges_from(nx_edges)

        logger.info(f"Created NetworkX '{name}' Graph")
        return nx_graph

    def arangodb_collections_to_networkx(
        self,
        name: str,
        v_cols: Set[str],
        e_cols: Set[str],
        **query_options: Any,
    ) -> NXMultiDiGraph:
        """Create a NetworkX graph from ArangoDB collections.

        :param name: The NetworkX graph name.
        :type name: str
        :param v_cols: A set of vertex collections to import to NetworkX.
        :type v_cols: Set[str]
        :param e_cols: A set of edge collections to import to NetworkX.
        :type e_cols: Set[str]
        :param query_options: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.aql.AQL.execute
        :type query_options: Any
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        metagraph: ArangoMetagraph = {
            "vertexCollections": {col: set() for col in v_cols},
            "edgeCollections": {col: set() for col in e_cols},
        }

        return self.arangodb_to_networkx(
            name, metagraph, is_keep=False, **query_options
        )

    def arangodb_graph_to_networkx(
        self, name: str, **query_options: Any
    ) -> NXMultiDiGraph:
        """Create a NetworkX graph from an ArangoDB graph.

        :param name: The ArangoDB graph name.
        :type name: str
        :param query_options: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.aql.AQL.execute
        :type query_options: Any
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        graph = self.__db.graph(name)
        v_cols = graph.vertex_collections()
        e_cols = {col["edge_collection"] for col in graph.edge_definitions()}

        return self.arangodb_collections_to_networkx(
            name, v_cols, e_cols, **query_options
        )

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
        :type edge_definitions: List[adbnx_adapter.typings.Json]
        :param keyify_nodes: If set to True, will create custom vertex keys based on the
            behavior of ADBNX_Controller._keyify_networkx_node(). Otherwise, ArangoDB
            _key values for vertices will range from 1 to N, where N is the number of
            NetworkX nodes.
        :type keyify_nodes: bool
        :param keyify_edges: If set to True, will create custom edge keys based on
            the behavior of ADBNX_Controller._keyify_networkx_edge().
            Otherwise, ArangoDB _key values for edges will range from 1 to E,
            where E is the number of NetworkX edges.
        :type keyify_edges: bool
        :param overwrite_graph: Overwrites the graph if it already exists.
            Does not drop associated collections.
        :type overwrite_graph: bool
        :param import_options: Keyword arguments to specify additional
            parameters for ArangoDB document insertion. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.collection.Collection.import_bulk
        :type import_options: Any
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

        if overwrite_graph:
            logger.debug("Overwrite graph flag is True. Deleting old graph.")
            self.__db.delete_graph(name, ignore_missing=True)

        if self.__db.has_graph(name):
            logger.debug(f"Graph {name} already exists")
            adb_graph = self.__db.graph(name)
        else:
            logger.debug(f"Creating graph {name}")
            adb_graph = self.__db.create_graph(name, edge_definitions)

        adb_v_cols: List[str] = adb_graph.vertex_collections()
        adb_e_cols: List[str] = [
            e_d["edge_collection"] for e_d in adb_graph.edge_definitions()
        ]

        has_one_vcol = len(adb_v_cols) == 1
        has_one_ecol = len(adb_e_cols) == 1
        logger.debug(f"Is graph '{name}' homogeneous? {has_one_vcol and has_one_ecol}")

        # Maps NetworkX node IDs to ArangoDB vertex IDs
        nx_map: Dict[NxId, Json] = dict()

        # Stores to-be-inserted ArangoDB documents by collection name
        adb_documents: DefaultDict[str, List[Json]] = defaultdict(list)

        nx_id: NxId
        nx_node: NxData
        logger.debug("Preparing NetworkX nodes")
        for i, (nx_id, nx_node) in enumerate(
            track(
                nx_graph.nodes(data=True),
                description="Nodes",
                complete_style="#97C423",
                finished_style="#97C423",
                disable=logger.level != logging.INFO,
            ),
            1,
        ):
            logger.debug(f"N{i}: {nx_id}")

            col = (
                adb_v_cols[0]
                if has_one_vcol
                else self.__cntrl._identify_networkx_node(nx_id, nx_node, adb_v_cols)
            )

            if not has_one_vcol and col not in adb_v_cols:
                msg = f"'{nx_id}' identified as '{col}', which is not in {adb_v_cols}"
                raise ValueError(msg)

            key = (
                self.__cntrl._keyify_networkx_node(nx_id, nx_node, col)
                if keyify_nodes
                else str(i)
            )

            adb_v_id = col + "/" + key
            nx_map[nx_id] = {
                "nx_id": nx_id,
                "adb_id": adb_v_id,
                "adb_col": col,
                "adb_key": key,
            }

            adb_documents[col].append({**nx_node, "_id": adb_v_id})

        self.__insert_adb_docs(adb_documents, import_options)
        adb_documents.clear()  # for memory purposes

        from_node_id: NxId
        to_node_id: NxId
        nx_edge: NxData
        logger.debug("Preparing NetworkX edges")
        for i, (from_node_id, to_node_id, nx_edge) in enumerate(
            track(
                nx_graph.edges(data=True),
                description="Edges",
                complete_style="#5E3108",
                finished_style="#5E3108",
                disable=logger.level != logging.INFO,
            ),
            1,
        ):
            edge_str = f"({from_node_id}, {to_node_id})"
            logger.debug(f"E{i}: {edge_str}")

            from_n = nx_map[from_node_id]
            to_n = nx_map[to_node_id]

            col = (
                adb_e_cols[0]
                if has_one_ecol
                else self.__cntrl._identify_networkx_edge(
                    nx_edge, from_n, to_n, adb_e_cols
                )
            )

            if not has_one_ecol and col not in adb_e_cols:
                msg = f"{edge_str} identified as '{col}', which is not in {adb_e_cols}"
                raise ValueError(msg)

            key = (
                self.__cntrl._keyify_networkx_edge(nx_edge, from_n, to_n, col)
                if keyify_edges
                else str(i)
            )

            adb_documents[col].append(
                {
                    **nx_edge,
                    "_id": col + "/" + key,
                    "_from": from_n["adb_id"],
                    "_to": to_n["adb_id"],
                }
            )

        self.__insert_adb_docs(adb_documents, import_options)

        logger.info(f"Created ArangoDB '{name}' Graph")
        return adb_graph

    def __fetch_adb_docs(
        self, col: str, attributes: Set[str], is_keep: bool, query_options: Any
    ) -> Result[Cursor]:
        """Fetches ArangoDB documents within a collection.

        :param col: The ArangoDB collection.
        :type col: str
        :param attributes: The set of document attributes.
        :type attributes: Set[str]
        :param is_keep: Only keep the attributes specified in **attributes** when
            returning the document. Otherwise, all document attributes are included.
        :type is_keep: bool
        :param query_options: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance.
        :type query_options: Any
        :return: Result cursor.
        :rtype: arango.cursor.Cursor
        """
        if is_keep:
            aql = f"""
                FOR doc IN @@col
                    RETURN MERGE(
                        KEEP(doc, {list(attributes)}),
                        {{"_id": doc._id}},
                        doc._from ? {{"_from": doc._from, "_to": doc._to}}: {{}}
                    )
            """
        else:
            aql = """
                FOR doc IN @@col
                    RETURN doc
            """

        return self.__db.aql.execute(
            aql, count=True, bind_vars={"@col": col}, **query_options
        )

    def __insert_adb_docs(
        self, adb_documents: DefaultDict[str, List[Json]], kwargs: Any
    ) -> None:
        """Insert ArangoDB documents into their ArangoDB collection.

        :param adb_documents: To-be-inserted ArangoDB documents
        :type adb_documents: DefaultDict[str, List[Json]]
        :param kwargs: Keyword arguments to specify additional
            parameters for ArangoDB document insertion. Full parameter list:
            https://docs.python-arango.com/en/main/specs.html#arango.collection.Collection.import_bulk
        """
        for col, doc_list in adb_documents.items():
            with Status(
                f"POST /_api/import '{col}' ({len(doc_list)})",
                spinner="aesthetic",
                spinner_style="cyan",
            ):
                result = self.__db.collection(col).import_bulk(doc_list, **kwargs)
                logger.debug(result)
