#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Set, Tuple, Union

from arango import ArangoClient
from arango.cursor import Cursor
from arango.graph import Graph as ArangoDBGraph
from arango.result import Result

try:
    from cudf import DataFrame

    cudf = True
except ImportError as e:
    print(e)
    cudf = False
try:
    from cugraph import MultiGraph as cuGraphMultiGraph

    cugraph = True
except ImportError as e:
    print(e)
    cugraph = False
from networkx import MultiDiGraph
from networkx.classes.graph import Graph as NetworkXGraph
from networkx.classes.multidigraph import MultiDiGraph as NetworkXMultiDiGraph

from .abc import Abstract_ADBNX_Adapter
from .controller import ADBNX_Controller
from .typings import ArangoMetagraph, Json, NxData, NxId


class ADBNX_Adapter(Abstract_ADBNX_Adapter):
    """ArangoDB-NetworkX adapter.

    :param conn: Connection details to an ArangoDB instance.
    :type conn: adbnx_adapter.typings.Json
    :param controller: The ArangoDB-NetworkX controller, used to identify, keyify
        and prepare nodes & edges before insertion, optionally re-defined by the user
        if needed (otherwise defaults to ADBNX_Controller).
    :type controller: ADBNX_Controller
    :raise ValueError: If missing required keys in conn
    """

    def __init__(
        self,
        conn: Json,
        controller: ADBNX_Controller = ADBNX_Controller(),
    ):
        self.__validate_attributes("connection", set(conn), self.CONNECTION_ATRIBS)
        if issubclass(type(controller), ADBNX_Controller) is False:
            msg = "controller must inherit from ADBNX_Controller"
            raise TypeError(msg)

        username: str = conn["username"]
        password: str = conn["password"]
        db_name: str = conn["dbName"]
        host: str = conn["hostname"]
        protocol: str = conn.get("protocol", "https")
        port = str(conn.get("port", 8529))

        url = protocol + "://" + host + ":" + port

        print(f"Connecting to {url}")
        self.__db = ArangoClient(hosts=url).db(db_name, username, password, verify=True)
        self.__cntrl: ADBNX_Controller = controller

    def arangodb_to_networkx(
        self,
        name: str,
        metagraph: ArangoMetagraph,
        is_keep: bool = True,
        **query_options: Any,
    ) -> NetworkXMultiDiGraph:
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
            fetching documents from the ArangoDB instance.
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
        self.__validate_attributes("graph", set(metagraph), self.METAGRAPH_ATRIBS)

        # Maps ArangoDB vertex IDs to NetworkX node IDs
        adb_map: Dict[str, Dict[str, Union[NxId, str]]] = dict()

        nx_graph = MultiDiGraph(name=name)
        nx_nodes: List[Tuple[NxId, NxData]] = []
        nx_edges: List[Tuple[NxId, NxId, NxData]] = []

        adb_v: Json
        for col, atribs in metagraph["vertexCollections"].items():
            for adb_v in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                adb_id: str = adb_v["_id"]
                nx_id = self.__cntrl._prepare_arangodb_vertex(adb_v, col)
                adb_map[adb_id] = {"nx_id": nx_id, "collection": col}

                nx_nodes.append((nx_id, adb_v))

        adb_e: Json
        for col, atribs in metagraph["edgeCollections"].items():
            for adb_e in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                from_node_id: NxId = adb_map[adb_e["_from"]]["nx_id"]
                to_node_id: NxId = adb_map[adb_e["_to"]]["nx_id"]
                self.__cntrl._prepare_arangodb_edge(adb_e, col)

                nx_edges.append((from_node_id, to_node_id, adb_e))

        nx_graph.add_nodes_from(nx_nodes)
        nx_graph.add_edges_from(nx_edges)

        print(f"NetworkX: {name} created")
        return nx_graph

    def arangodb_collections_to_networkx(
        self,
        name: str,
        v_cols: Set[str],
        e_cols: Set[str],
        **query_options: Any,
    ) -> NetworkXMultiDiGraph:
        """Create a NetworkX graph from ArangoDB collections.

        :param name: The NetworkX graph name.
        :type name: str
        :param v_cols: A set of vertex collections to import to NetworkX.
        :type v_cols: Set[str]
        :param e_cols: A set of edge collections to import to NetworkX.
        :type e_cols: Set[str]
        :param query_options: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance.
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
    ) -> NetworkXMultiDiGraph:
        """Create a NetworkX graph from an ArangoDB graph.

        :param name: The ArangoDB graph name.
        :type name: str
        :param query_options: Keyword arguments to specify AQL query options when
            fetching documents from the ArangoDB instance.
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
        nx_graph: NetworkXGraph,
        edge_definitions: List[Json],
        batch_size: int = 1000,
        keyify_nodes: bool = False,
        keyify_edges: bool = False,
    ) -> ArangoDBGraph:
        """Create an ArangoDB graph from a NetworkX graph, and a set of edge
        definitions.

        :param name: The ArangoDB graph name.
        :type name: str
        :param nx_graph: The existing NetworkX graph.
        :type nx_graph: networkx.classes.graph.Graph
        :param edge_definitions: List of edge definitions, where each edge definition
            entry is a dictionary with fields "edge_collection",
            "from_vertex_collections" and "to_vertex_collections"
            (see below for example).
        :type edge_definitions: List[adbnx_adapter.typings.Json]
        :param batch_size: The maximum number of documents to insert at once
        :type batch_size: int
        :param keyify_nodes: If set to True, will create custom node keys based on the
            behavior of the ADBNX_Controller's _keyify_networkx_node() method.
            Otherwise, ArangoDB _key values for vertices will range from 0 to N-1,
            where N is the number of NetworkX nodes.
        :type keyify_nodes: bool
        :param keyify_edges: If set to True, will create custom edge keys based on
            the behavior of the ADBNX_Controller's _keyify_networkx_edge() method.
            Otherwise, ArangoDB _key values for edges will range from 0 to E-1,
            where E is the number of NetworkX edges.
        :type keyify_edges: bool
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
        for e_d in edge_definitions:
            self.__validate_attributes(
                "Edge Definitions", set(e_d), self.EDGE_DEFINITION_ATRIBS
            )

        nx_map = dict()  # Maps NetworkX node IDs to ArangoDB vertex IDs

        adb_v_cols = set()
        adb_e_cols = set()
        for e_d in edge_definitions:
            e_col: str = str(e_d["edge_collection"])
            adb_e_cols.add(e_col)

            if self.__db.has_collection(e_col) is False:
                self.__db.create_collection(e_col, edge=True)

            v_col: str
            for v_col in list(e_d["from_vertex_collections"]) + list(
                e_d["to_vertex_collections"]
            ):
                adb_v_cols.add(v_col)
                if self.__db.has_collection(v_col) is False:
                    self.__db.create_collection(v_col)

        is_homogeneous = len(adb_v_cols | adb_e_cols) == 2
        adb_v_col = adb_v_cols.pop() if is_homogeneous else None
        adb_e_col = adb_e_cols.pop() if is_homogeneous else None

        self.__db.delete_graph(name, ignore_missing=True)
        adb_graph: ArangoDBGraph = self.__db.create_graph(name, edge_definitions)
        adb_documents: DefaultDict[str, List[Json]] = defaultdict(list)

        nx_id: NxId
        nx_node: NxData
        for i, (nx_id, nx_node) in enumerate(nx_graph.nodes(data=True)):
            col = adb_v_col or self.__cntrl._identify_networkx_node(nx_id, nx_node)
            key = (
                self.__cntrl._keyify_networkx_node(nx_id, nx_node, col)
                if keyify_nodes
                else str(i)
            )

            nx_node["_id"] = col + "/" + key
            nx_map[nx_id] = {"adb_id": nx_node["_id"], "col": col, "key": key}

            self.__insert_adb_docs(col, adb_documents[col], nx_node, batch_size)

        from_node_id: NxId
        to_node_id: NxId
        nx_edge: NxData
        for i, (from_node_id, to_node_id, nx_edge) in enumerate(
            nx_graph.edges(data=True)
        ):
            from_n = {
                "nx_id": from_node_id,
                "col": nx_map[from_node_id]["col"],
                **nx_graph.nodes[from_node_id],
            }
            to_n = {
                "nx_id": to_node_id,
                "col": nx_map[from_node_id]["col"],
                **nx_graph.nodes[to_node_id],
            }

            col = adb_e_col or self.__cntrl._identify_networkx_edge(
                nx_edge, from_n, to_n
            )
            key = (
                self.__cntrl._keyify_networkx_edge(nx_edge, from_n, to_n, col)
                if keyify_edges
                else str(i)
            )

            nx_edge["_id"] = col + "/" + key
            nx_edge["_from"] = nx_map[from_node_id]["adb_id"]
            nx_edge["_to"] = nx_map[to_node_id]["adb_id"]

            self.__insert_adb_docs(col, adb_documents[col], nx_edge, batch_size)

        for col, doc_list in adb_documents.items():  # insert remaining documents
            self.__db.collection(col).import_bulk(doc_list, on_duplicate="replace")

        print(f"ArangoDB: {name} created")
        return adb_graph

    if cugraph is False or cudf is False:
        print(
            "You are currently solely using the NetworkX export functionality.",
            "Please note that modules 'cudf' and 'cugraph' are required to perform",
            "exports into cuGraph. ",
        )
    else:

        def arangodb_to_cugraph(
            self,
            name: str,
            metagraph: ArangoMetagraph,
            is_keep: bool = True,
            **query_options: Any,
        ) -> cuGraphMultiGraph(directed=True):  # type: ignore
            """Create a cuGraph graph from graph attributes.

            :param name: The cuGraph graph name.
            :type name: str
            :param metagraph: An object defining vertex & edge collections to import to
                cuGraph, along with their associated attributes to keep.
            :type metagraph: adbnx_adapter.typings.ArangoMetagraph
            :param is_keep: Only keep the document attributes specified in **metagraph**
                when importing to cuGraph (is True by default).
            :type is_keep: bool
            :param query_options: Keyword arguments to specify AQL query options when
                fetching documents from the ArangoDB instance.
            :type query_options: Any
            :return: A Multi-Directed cuGraph Graph.
            :rtype: cugraph.structure.graph_classes.MultiDiGraph
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
            self.__validate_attributes("graph", set(metagraph), self.METAGRAPH_ATRIBS)

            # Maps ArangoDB vertex IDs to cuGraph node IDs
            adb_map: Dict[str, Dict[str, Union[NxId, str]]] = dict()
            cg_edges: List[Tuple[NxId, NxId]] = []

            adb_v: Json
            for col, atribs in metagraph["vertexCollections"].items():
                for adb_v in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                    adb_id: str = adb_v["_id"]
                    nx_id = self.__cntrl._prepare_arangodb_vertex(adb_v, col)
                    adb_map[adb_id] = {"nx_id": nx_id, "collection": col}

            adb_e: Json
            for col, atribs in metagraph["edgeCollections"].items():
                for adb_e in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                    from_node_id: NxId = adb_map[adb_e["_from"]]["nx_id"]
                    to_node_id: NxId = adb_map[adb_e["_to"]]["nx_id"]
                    self.__cntrl._prepare_arangodb_edge(adb_e, col)
                    cg_edges.append((from_node_id, to_node_id))

            srcs = [s for (s, _) in cg_edges]
            dsts = [d for (_, d) in cg_edges]
            cg_graph = cuGraphMultiGraph(directed=True)
            cg_graph.from_cudf_edgelist(
                DataFrame({"source": srcs, "destination": dsts})
            )

            print(f"cuGraph: {name} created")
            return cg_graph

        def arangodb_collections_to_cugraph(
            self,
            name: str,
            v_cols: Set[str],
            e_cols: Set[str],
            **query_options: Any,
        ) -> cuGraphMultiGraph(directed=True):  # type: ignore
            """Create a cuGraph graph from ArangoDB collections.
            :param name: The cuGraph graph name.
            :type name: str
            :param v_cols: A set of vertex collections to import to cuGraph.
            :type v_cols: Set[str]
            :param e_cols: A set of edge collections to import to cuGraph.
            :type e_cols: Set[str]
            :param query_options: Keyword arguments to specify AQL query options when
                fetching documents from the ArangoDB instance.
            :type query_options: Any
            :return: A Multi-Directed cuGraph Graph.
            :rtype: cugraph.structure.graph_classes.MultiDiGraph
            """
            metagraph: ArangoMetagraph = {
                "vertexCollections": {col: set() for col in v_cols},
                "edgeCollections": {col: set() for col in e_cols},
            }

            return self.arangodb_to_cugraph(
                name, metagraph, is_keep=True, **query_options
            )

        def arangodb_graph_to_cugraph(
            self, name: str, **query_options: Any
        ) -> cuGraphMultiGraph(directed=True):  # type: ignore
            """Create a cuGraph graph from an ArangoDB graph.
            :param name: The ArangoDB graph name.
            :type name: str
            :param query_options: Keyword arguments to specify AQL query options when
                fetching documents from the ArangoDB instance.
            :type query_options: Any
            :return: A Multi-Directed cuGraph Graph.
            :rtype: cugraph.structure.graph_classes.MultiDiGraph
            """
            graph = self.__db.graph(name)
            v_cols = graph.vertex_collections()
            e_cols = {col["edge_collection"] for col in graph.edge_definitions()}

            return self.arangodb_collections_to_cugraph(
                name, v_cols, e_cols, **query_options
            )

    def __validate_attributes(
        self, type: str, attributes: Set[str], valid_attributes: Set[str]
    ) -> None:
        """Validates that a set of attributes includes the required valid
        attributes.

        :param type: The context of the attribute validation
            (e.g connection attributes, graph attributes, etc).
        :type type: str
        :param attributes: The provided attributes, possibly invalid.
        :type attributes: Set[str]
        :param valid_attributes: The valid attributes.
        :type valid_attributes: Set[str]
        :raise ValueError: If **valid_attributes** is not a subset of **attributes**
        """
        if valid_attributes.issubset(attributes) is False:
            missing_attributes = valid_attributes - attributes
            raise ValueError(f"Missing {type} attributes: {missing_attributes}")

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
        aql = f"""
            FOR doc IN {col}
                RETURN {is_keep} ?
                    MERGE(
                        KEEP(doc, {list(attributes)}),
                        {{"_id": doc._id}},
                        doc._from ? {{"_from": doc._from, "_to": doc._to}}: {{}}
                    )
                : doc
        """

        return self.__db.aql.execute(aql, **query_options)

    def __insert_adb_docs(
        self,
        col: str,
        col_docs: List[Json],
        doc: Json,
        batch_size: int,
    ) -> None:
        """Insert an ArangoDB document into a list. If the list exceeds
        batch_size documents, insert into the ArangoDB collection.

        :param col: The collection name
        :type col: str
        :param col_docs: The existing documents data belonging to the collection.
        :type col_docs: List[adbnx_adapter.typings.Json]
        :param doc: The current document to insert.
        :type doc: adbnx_adapter.typings.Json
        :param batch_size: The maximum number of documents to insert at once
        :type batch_size: int
        """
        col_docs.append(doc)

        if len(col_docs) >= batch_size:
            self.__db.collection(col).import_bulk(col_docs, on_duplicate="replace")
            col_docs.clear()
