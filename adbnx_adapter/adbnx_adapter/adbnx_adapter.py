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

        username = conn["username"]
        password = conn["password"]
        db_name = conn["dbName"]

        protocol = conn.get("protocol", "https")
        host = conn["hostname"]
        port = str(conn.get("port", 8529))

        url = protocol + "://" + host + ":" + port
        print(f"Connecting to {url}")
        self.db = ArangoClient(hosts=url).db(db_name, username, password, verify=True)

        if issubclass(controller_class, Base_ADBNX_Controller) is False:
            msg = "controller_class must inherit from Base_ADBNX_Controller"
            raise TypeError(msg)

        self.cntrl: Base_ADBNX_Controller = controller_class()

    def arangodb_to_networkx(
        self, name: str, graph_attributes: dict, is_keep=True, **query_options
    ):
        """Create a NetworkX graph from graph attributes.

        :param name: The NetworkX graph name.
        :type name: str
        :param graph_attributes: An object defining vertex & edge collections to import to NetworkX, along with their associated attributes to keep.
        :type graph_attributes: dict
        :param is_keep: Only keep the document attributes specified in **graph_attributes** when importing to NetworkX (is True by default). Otherwise, all document attributes are included.
        :type is_keep: bool
        :param query_options: Keyword arguments to specify AQL query options when fetching documents from the ArangoDB instance.
        :type query_options: **kwargs
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        :raise ValueError: If missing required keys in graph_attributes

        Here is an example entry for parameter **graph_attributes**:

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
        self.__validate_attributes("graph", set(graph_attributes), self.GRAPH_ATRIBS)

        nx_graph = nx.MultiDiGraph(name=name)
        nodes: list = []
        edges: list = []

        for col, atribs in graph_attributes["vertexCollections"].items():
            for v in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                self.__insert_nx_node(v["_id"], v, col, nodes)

        for col, atribs in graph_attributes["edgeCollections"].items():
            for e in self.__fetch_adb_docs(col, atribs, is_keep, query_options):
                self.__insert_nx_edge(e, col, edges)

        nx_graph.add_nodes_from(nodes)
        nx_graph.add_edges_from(edges)

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
        graph_attributes = {
            "vertexCollections": {col: {} for col in vertex_collections},
            "edgeCollections": {col: {} for col in edge_collections},
        }

        return self.arangodb_to_networkx(
            name, graph_attributes, is_keep=False, **query_options
        )

    def arangodb_graph_to_networkx(self, name: str, **query_options):
        """Create a NetworkX graph from an ArangoDB graph.

        :param name: The ArangoDB graph name.
        :type name: str
        :param vertex_collections: A set of ArangoDB vertex collections to import to NetworkX.
        :param query_options: Keyword arguments to specify AQL query options when fetching documents from the ArangoDB instance.
        :type query_options: **kwargs
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        graph = self.db.graph(name)
        v_cols = graph.vertex_collections()
        e_cols = {col["edge_collection"] for col in graph.edge_definitions()}

        return self.arangodb_collections_to_networkx(
            name, v_cols, e_cols, **query_options
        )

    def networkx_to_arangodb(
        self,
        name: str,
        original_nx_graph: NetworkXGraph,
        edge_definitions: list,
        batch_size: int = 1000,
        keyify_edges: bool = False,
    ):
        """Create an ArangoDB graph from a NetworkX graph, and a set of edge definitions.

        :param name: The ArangoDB graph name.
        :type name: str
        :param original_nx_graph: The existing NetworkX graph.
        :type original_nx_graph: networkx.classes.graph.Graph
        :param edge_definitions: List of edge definitions, where each edge definition entry is a dictionary with fields "edge_collection", "from_vertex_collections" and "to_vertex_collections" (see below for example).
        :type edge_definitions: list[dict]
        :param batch_size: The maximum number of documents to insert at once
        :type batch_size: int
        :param keyify_edges: If set to True, will create custom edge IDs based on the behavior of the ADBNX_Controller's _keyify_nx_edge() method. Otherwise, edge IDs will be randomly generated.
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

        nx_graph: NetworkXGraph = original_nx_graph.copy()

        for definition in edge_definitions:
            e_col = definition["edge_collection"]

            if self.db.has_collection(e_col) is False:
                self.db.create_collection(e_col, edge=True)

            for v_col in (
                definition["from_vertex_collections"]
                + definition["to_vertex_collections"]
            ):
                if self.db.has_collection(v_col) is False:
                    self.db.create_collection(v_col)

        self.db.delete_graph(name, ignore_missing=True)
        adb_graph: ArangoDBGraph = self.db.create_graph(name, edge_definitions)
        adb_documents = defaultdict(list)

        for node_id, node in nx_graph.nodes(data=True):
            col = self.cntrl._identify_networkx_node(node_id, node)
            key = self.cntrl._keyify_networkx_node(node_id, node, col)
            node["_id"] = col + "/" + key

            self.__insert_adb_vertex(
                node_id, node, col, key, adb_documents[col], batch_size
            )

        for from_node_id, to_node_id, edge in nx_graph.edges(data=True):
            from_node = {"id": from_node_id, **nx_graph.nodes[from_node_id]}
            to_node = {"id": to_node_id, **nx_graph.nodes[to_node_id]}

            col = self.cntrl._identify_networkx_edge(edge, from_node, to_node)
            if keyify_edges:
                key = self.cntrl._keyify_networkx_edge(edge, from_node, to_node, col)
                edge["_id"] = col + "/" + key

            self.__insert_adb_edge(
                edge, from_node, to_node, col, adb_documents[col], batch_size
            )

        for col, doc_list in adb_documents.items():  # insert remaining documents
            self.db.collection(col).import_bulk(doc_list, on_duplicate="replace")

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
                    MERGE(KEEP(doc, {list(attributes)}), {{"_id": doc._id}}) : doc
        """

        return self.db.aql.execute(aql, **query_options)

    def __insert_nx_node(self, adb_id: str, node: dict, col: str, nodes: list):
        """Insert the NetworkX node into a list for batch insertion.

        :param adb_id: The ArangoDB ID of the node.
        :type adb_id: str
        :param node: The node object to insert.
        :type node: dict
        :param col: The ArangoDB collection it came from.
        :type col: str
        :param nodes: A list of NetworkX nodes.
        :type nodes: list
        """
        nx_id = self.cntrl._prepare_arangodb_vertex(node, col)
        self.cntrl.nx_map[adb_id] = {"_id": nx_id, "collection": col}
        nodes.append((nx_id, node))

    def __insert_nx_edge(self, edge: dict, col: str, edges: list):
        """Insert a NetworkX edge into a list for batch insertion.

        :param edge: The edge object to insert.
        :type edge: dict
        :param col: The ArangoDB collection it came from.
        :type col: str
        :param edges: A list of NetworkX edges.
        :type edges: list
        """
        from_node_id = self.cntrl.nx_map.get(edge["_from"])["_id"]
        to_node_id = self.cntrl.nx_map.get(edge["_to"])["_id"]

        self.cntrl._prepare_arangodb_edge(edge, col)
        edges.append((from_node_id, to_node_id, edge))

    def __insert_adb_vertex(
        self,
        nx_id,
        vertex: dict,
        col: str,
        key: str,
        v_col: list,
        batch_size: int,
    ):
        """Insert an ArangoDB vertex into a list. If the list exceeds batch_size documents, insert into the ArangoDB collection.

        :param id: The NetworkX ID of the vertex.
        :type id: Any
        :param vertex: The vertex object to insert.
        :type vertex: dict
        :param col: The ArangoDB collection the vertex belongs to.
        :type col: str
        :param key: The _key value of the vertex.
        :type key: str
        :param v_col: A group of vertexes belonging to the same collection
        :type v_col: list
        :param batch_size: The maximum number of documents to insert at once
        :type batch_size: int
        """
        self.cntrl.adb_map[nx_id] = {
            "_id": vertex["_id"],
            "collection": col,
            "key": key,
        }
        v_col.append(vertex)

        if len(v_col) >= batch_size:
            self.db.collection(col).import_bulk(v_col, on_duplicate="replace")
            v_col.clear()

    def __insert_adb_edge(
        self,
        edge: dict,
        from_node: dict,
        to_node: dict,
        col: str,
        e_col: list,
        batch_size: int,
    ):
        """Insert an ArangoDB edge into a list. If the list exceeds batch_size documents, insert into the ArangoDB collection.

        :param edge: The edge object to insert.
        :type edge: dict
        :param from_node: The NetworkX node object representing the edge source.
        :type from_node: dict
        :param to_node: The NetworkX node object representing the edge destination.
        :type to_node: dict
        :param col: The ArangoDB collection the edge belongs to.
        :type col: str
        :param e_col: A group of vertexes belonging to the same collection
        :type e_col: list
        :param batch_size: The maximum number of documents to insert at once
        :type batch_size: int
        """
        edge["_from"] = self.cntrl.adb_map.get(from_node["id"])["_id"]
        edge["_to"] = self.cntrl.adb_map.get(to_node["id"])["_id"]
        e_col.append(edge)

        if len(e_col) >= batch_size:
            self.db.collection(col).import_bulk(e_col, on_duplicate="replace")
            e_col.clear()
