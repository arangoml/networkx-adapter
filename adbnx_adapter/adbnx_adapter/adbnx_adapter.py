#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
@author: Joerg Schad
@author: Anthony Mahanna
"""

from .abc import ADBNX_Adapter
from .adbnx_controller import Base_ADBNX_Controller

import networkx as nx
from arango import ArangoClient
from collections import defaultdict

from networkx.classes.graph import Graph as NetworkXGraph
from arango.graph import Graph as ArangoDBGraph


class ArangoDB_Networkx_Adapter(ADBNX_Adapter):
    """ArangoDB-NetworkX adapter.

    :param conn: Connection details to an ArangoDB instance.
    :type conn: dict
    :param controller_class: The ArangoDB-NetworkX controller, used to identify, keyify and prepare nodes & edges before insertion, optionally re-defined by the user if needed (otherwise defaults to Base_ADBNX_Controller).
    :type controller_class: Base_ADBNX_Controller
    :raise ValueError: If missing required keys in conn
    """

    def __init__(
        self,
        conn: dict,
        controller_class: Base_ADBNX_Controller = Base_ADBNX_Controller,
    ):
        self.__validate_attributes("connection", set(conn), self.CONNECTION_ATRIBS)
        if issubclass(controller_class, Base_ADBNX_Controller) is False:
            msg = "controller_class must inherit from Base_ADBNX_Controller"
            raise TypeError(msg)

        username = conn["username"]
        password = conn["password"]
        db_name = conn["dbName"]

        protocol = conn.get("protocol", "https")
        host = conn["hostname"]
        port = str(conn.get("port", 8529))

        url = protocol + "://" + host + ":" + port

        print(f"Connecting to {url}")
        self.__db = ArangoClient(hosts=url).db(db_name, username, password, verify=True)
        self.__cntrl: Base_ADBNX_Controller = controller_class()

    def arangodb_to_networkx(
        self, name: str, metagraph: dict, is_keep=True, **query_options
    ):
        """Create a NetworkX graph from graph attributes.

        :param name: The NetworkX graph name.
        :type name: str
        :param metagraph: An object defining vertex & edge collections to import to NetworkX, along with their associated attributes to keep.
        :type metagraph: dict
        :param is_keep: Only keep the document attributes specified in **metagraph** when importing to NetworkX (is True by default). Otherwise, all document attributes are included.
        :type is_keep: bool
        :param query_options: Keyword arguments to specify AQL query options when fetching documents from the ArangoDB instance.
        :type query_options: **kwargs
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
                "accountHolder": {"_from", "_to"},
                "transaction": {"_from", "_to"},
            },
        }
        """
        self.__validate_attributes("graph", set(metagraph), self.METAGRAPH_ATRIBS)

        nx_graph = nx.MultiDiGraph(name=name)
        adb_map = dict()  # Maps ArangoDB vertex IDs to NetworkX node IDs

        nx_nodes: list = []
        nx_edges: list = []

        v: dict
        for col, atribs in metagraph["vertexCollections"].items():
            for v in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                adb_id = v["_id"]
                nx_id = self.__cntrl._prepare_arangodb_vertex(v, col)
                adb_map[adb_id] = {"nx_id": nx_id, "collection": col}

                v.pop("_rev", None)  # Remove system attribute
                nx_nodes.append((nx_id, v))
        e: dict
        for col, atribs in metagraph["edgeCollections"].items():
            for e in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                from_node_id = adb_map.get(e["_from"])["nx_id"]
                to_node_id = adb_map.get(e["_to"])["nx_id"]
                self.__cntrl._prepare_arangodb_edge(e, col)

                e.pop("_rev", None)  # Remove system attribute
                nx_edges.append((from_node_id, to_node_id, e))

        nx_graph.add_nodes_from(nx_nodes)
        nx_graph.add_edges_from(nx_edges)

        print(f"NetworkX: {name} created")
        return nx_graph

    def arangodb_collections_to_networkx(
        self,
        name: str,
        vertex_collections: set,
        edge_collections: set,
        **query_options,
    ):
        """Create a NetworkX graph from ArangoDB collections.

        :param name: The NetworkX graph name.
        :type name: str
        :param vertex_collections: A set of ArangoDB vertex collections to import to NetworkX.
        :type vertex_collections: set
        :param edge_collections: A set of ArangoDB edge collections to import to NetworkX.
        :type edge_collections: set
        :param query_options: Keyword arguments to specify AQL query options when fetching documents from the ArangoDB instance.
        :type query_options: **kwargs
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        metagraph = {
            "vertexCollections": {col: {} for col in vertex_collections},
            "edgeCollections": {col: {} for col in edge_collections},
        }

        return self.arangodb_to_networkx(
            name, metagraph, is_keep=False, **query_options
        )

    def arangodb_graph_to_networkx(self, name: str, **query_options):
        """Create a NetworkX graph from an ArangoDB graph.

        :param name: The ArangoDB graph name.
        :type name: str
        :param query_options: Keyword arguments to specify AQL query options when fetching documents from the ArangoDB instance.
        :type query_options: **kwargs
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
        edge_definitions: list,
        batch_size: int = 1000,
        keyify_edges: bool = False,
    ):
        """Create an ArangoDB graph from a NetworkX graph, and a set of edge definitions.

        :param name: The ArangoDB graph name.
        :type name: str
        :param nx_graph: The existing NetworkX graph.
        :type nx_graph: networkx.classes.graph.Graph
        :param edge_definitions: List of edge definitions, where each edge definition entry is a dictionary with fields "edge_collection", "from_vertex_collections" and "to_vertex_collections" (see below for example).
        :type edge_definitions: list[dict]
        :param batch_size: The maximum number of documents to insert at once
        :type batch_size: int
        :param keyify_edges: If set to True, will create custom edge IDs based on the behavior of the ADBNX_Controller's _keyify_networkx_edge() method. Otherwise, edge IDs will be randomly generated.
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

        adb_v_cols = set()
        adb_e_cols = set()
        for e_d in edge_definitions:
            e_col = e_d["edge_collection"]
            adb_e_cols.add(e_col)

            if self.__db.has_collection(e_col) is False:
                self.__db.create_collection(e_col, edge=True)

            for v_col in e_d["from_vertex_collections"] + e_d["to_vertex_collections"]:
                adb_v_cols.add(v_col)
                if self.__db.has_collection(v_col) is False:
                    self.__db.create_collection(v_col)

        is_homogeneous = len(adb_v_cols | adb_e_cols) == 2
        adb_v_col = adb_v_cols.pop() if is_homogeneous else None
        adb_e_col = adb_e_cols.pop() if is_homogeneous else None

        self.__db.delete_graph(name, ignore_missing=True)
        adb_graph: ArangoDBGraph = self.__db.create_graph(name, edge_definitions)
        adb_documents = defaultdict(list)
        nx_map = dict()  # Maps NetworkX node IDs to ArangoDB vertex IDs

        for nx_id, node in nx_graph.nodes(data=True):
            col = adb_v_col or self.__cntrl._identify_networkx_node(nx_id, node)
            key = self.__cntrl._keyify_networkx_node(nx_id, node, col)
            node["_id"] = col + "/" + key

            nx_map[nx_id] = {
                "adb_id": node["_id"],
                "col": col,
                "key": key,
            }

            self.__insert_adb_docs(col, adb_documents[col], node, batch_size)

        for from_node_id, to_node_id, edge in nx_graph.edges(data=True):
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

            col = adb_e_col or self.__cntrl._identify_networkx_edge(edge, from_n, to_n)
            if keyify_edges:
                key = self.__cntrl._keyify_networkx_edge(edge, from_n, to_n, col)
                edge["_id"] = col + "/" + key

            edge["_from"] = nx_map[from_node_id]["adb_id"]
            edge["_to"] = nx_map[to_node_id]["adb_id"]

            self.__insert_adb_docs(col, adb_documents[col], edge, batch_size)

        for col, doc_list in adb_documents.items():  # insert remaining documents
            self.__db.collection(col).import_bulk(doc_list, on_duplicate="replace")

        print(f"ArangoDB: {name} created")
        return adb_graph

    def __validate_attributes(self, type: str, attributes: set, valid_attributes: set):
        """Validates that a set of attributes includes the required valid attributes.

        :param type: The context of the attribute validation (e.g connection attributes, graph attributes, etc).
        :type type: str
        :param attributes: The provided attributes, possibly invalid.
        :type attributes: set
        :param valid_attributes: The valid attributes.
        :type valid_attributes: set
        :raise ValueError: If **valid_attributes** is not a subset of **attributes**
        """
        if valid_attributes.issubset(attributes) is False:
            missing_attributes = valid_attributes - attributes
            raise ValueError(f"Missing {type} attributes: {missing_attributes}")

    def __fetch_adb_docs(
        self, col: str, attributes: set, is_keep: bool, query_options: dict
    ):
        """Fetches ArangoDB documents within a collection.

        :param col: The ArangoDB collection.
        :type col: str
        :param attributes: The set of document attributes.
        :type attributes: set
        :param is_keep: Only keep the document attributes specified in **attributes** when returning the document. Otherwise, all document attributes are included.
        :type is_keep: bool
        :param query_options: Keyword arguments to specify AQL query options when fetching documents from the ArangoDB instance.
        :type query_options: **kwargs
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

    def __insert_adb_docs(self, col: str, col_docs: list, doc: dict, batch_size: int):
        """Insert an ArangoDB document into a list. If the list exceeds batch_size documents, insert into the ArangoDB collection.

        :param col: The collection name
        :type col: str
        :param col_docs: The existing documents data belonging to the collection.
        :type col_docs: list
        :param doc: The current document to insert.
        :type doc: dict
        :param batch_size: The maximum number of documents to insert at once
        :type batch_size: int
        """
        col_docs.append(doc)

        if len(col_docs) >= batch_size:
            self.__db.collection(col).import_bulk(col_docs, on_duplicate="replace")
            col_docs.clear()
