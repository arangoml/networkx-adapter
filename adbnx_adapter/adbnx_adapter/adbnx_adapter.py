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
from networkx.classes.graph import Graph as NetworkXGraph


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
        port = str(conn.get("port", 8529))
        protocol = conn.get("protocol", "https")

        url = protocol + "://" + conn["hostname"] + ":" + port
        print(f"Connecting to {url}")
        self.db = ArangoClient(hosts=url).db(db_name, username, password, verify=True)

        if issubclass(controller_class, Base_ADBNX_Controller) is False:
            msg = "controller_class must inherit from Base_ADBNX_Controller"  # pragma: no cover
            raise TypeError(msg)  # pragma: no cover

        self.cntrl: Base_ADBNX_Controller = controller_class()

    def create_networkx_graph(
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

        self.cntrl.nx_graph = nx.MultiDiGraph(name=name)

        for col, atribs in graph_attributes["vertexCollections"].items():
            for v in self.__fetch_arangodb_docs(col, atribs, is_keep, query_options):
                self.__insert_networkx_node(v["_id"], v, col)

        for col, atribs in graph_attributes["edgeCollections"].items():
            for e in self.__fetch_arangodb_docs(col, atribs, is_keep, query_options):
                self.__insert_networkx_edge(e, col)

        print(f"NetworkX: {name} created")
        return self.cntrl.nx_graph

    def create_networkx_graph_from_arangodb_collections(
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

        return self.create_networkx_graph(
            name, graph_attributes, is_keep=False, **query_options
        )

    def create_networkx_graph_from_arangodb_graph(self, name: str, **query_options):
        """Create a NetworkX graph from an ArangoDB graph.

        :param name: The ArangoDB graph name.
        :type name: str
        :param vertex_collections: A set of ArangoDB vertex collections to import to NetworkX.
        :param query_options: Keyword arguments to specify AQL query options when fetching documents from the ArangoDB instance.
        :type query_options: **kwargs
        :return: A Multi-Directed NetworkX Graph.
        :rtype: networkx.classes.multidigraph.MultiDiGraph
        """
        arango_graph = self.db.graph(name)
        v_cols = arango_graph.vertex_collections()
        e_cols = {col["edge_collection"] for col in arango_graph.edge_definitions()}

        return self.create_networkx_graph_from_arangodb_collections(
            name, v_cols, e_cols, **query_options
        )

    def create_arangodb_graph(
        self,
        name: str,
        original_nx_graph: NetworkXGraph,
        edge_definitions: list,
        overwrite: bool = False,
        keyify_edges: bool = False,
    ):
        """Create an ArangoDB graph from a NetworkX graph, and a set of edge definitions.

        :param name: The ArangoDB graph name.
        :type name: str
        :param original_nx_graph: The existing NetworkX graph.
        :type original_nx_graph: networkx.classes.graph.Graph
        :param edge_definitions: List of edge definitions, where each edge definition entry is a dictionary with fields "edge_collection", "from_vertex_collections" and "to_vertex_collections" (see below for example).
        :type edge_definitions: list[dict]
        :param overwrite: If set to True, overwrites existing ArangoDB collections with the NetworkX graph data. Otherwise, will not remove existing data from collections specified in **edge_definitions**.
        :type overwrite: bool
        :param keyify_edges: If set to True, will create custom edge IDs based on the behavior of the ADBNX_Controller's _keyify_nx_edge() method. Otherwise, edge IDs will be randomly generated.
        :type overwrite: bool
        :return: The ArangoDB Graph API wrapper.
        :rtype: arango.graph.Graph

        Here is an example entry for parameter **edge_definitions**:

        .. code-block:: python
        [
            {
                'edge_collection': 'teach',
                'from_vertex_collections': ['teachers'],
                'to_vertex_collections': ['lectures']
            }
        ]
        """
        nx_graph: NetworkXGraph = original_nx_graph.copy()

        for definition in edge_definitions:
            e_col = definition["edge_collection"]
            if self.db.has_collection(e_col):
                self.db.collection(e_col).truncate() if overwrite else None
            else:
                self.db.create_collection(e_col, edge=True)

            for v_col in (
                definition["from_vertex_collections"]
                + definition["to_vertex_collections"]
            ):
                if self.db.has_collection(v_col):
                    self.db.collection(v_col).truncate() if overwrite else None
                else:
                    self.db.create_collection(v_col)

        if overwrite:
            self.db.delete_graph(name, ignore_missing=True)

        self.cntrl.adb_graph = self.db.create_graph(
            name, edge_definitions=edge_definitions
        )

        for node_id, node in nx_graph.nodes(data=True):
            col = self.cntrl._identify_nx_node(node_id, node, overwrite)
            key = self.cntrl._keyify_nx_node(node_id, node, col, overwrite)
            node["_id"] = col + "/" + key
            self.__insert_arangodb_vertex(node_id, node, col, key, overwrite)

        for from_node_id, to_node_id, edge in nx_graph.edges(data=True):
            from_node = {"id": from_node_id, **nx_graph.nodes[from_node_id]}
            to_node = {"id": to_node_id, **nx_graph.nodes[to_node_id]}

            col = self.cntrl._identify_nx_edge(edge, from_node, to_node, overwrite)
            if keyify_edges:
                key = self.cntrl._keyify_nx_edge(
                    edge, from_node, to_node, col, overwrite
                )
                edge["_id"] = col + "/" + key

            self.__insert_arangodb_edge(edge, from_node, to_node, col, overwrite)

        print(f"ArangoDB: {name} created")
        return self.cntrl.adb_graph

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

    def __fetch_arangodb_docs(
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

    def __insert_networkx_node(self, adb_id: str, node: dict, col: str):
        """Insert a NetworkX node into the NetworkX graph.

        :param adb_id: The ArangoDB ID of the node.
        :type adb_id: str
        :param node: The node object to insert.
        :type node: dict
        :param col: The ArangoDB collection it came from.
        :type col: str
        """
        nx_id = self.cntrl._prepare_adb_vertex(node, col)
        self.cntrl.nx_map[adb_id] = {"_id": nx_id, "collection": col}

        self.cntrl.nx_graph.add_node(nx_id, **node)

    def __insert_networkx_edge(self, edge: dict, col: str):
        """Insert a NetworkX edge into the NetworkX graph.

        :param edge: The edge object to insert.
        :type edge: dict
        :param col: The ArangoDB collection it came from.
        :type col: str
        """
        from_node_id = self.cntrl.nx_map.get(edge["_from"])["_id"]
        to_node_id = self.cntrl.nx_map.get(edge["_to"])["_id"]

        self.cntrl._prepare_adb_edge(edge, col)
        self.cntrl.nx_graph.add_edge(from_node_id, to_node_id, **edge)

    def __insert_arangodb_vertex(self, id, v: dict, col: str, key: str, ow: bool):
        """Insert an ArangoDB vertex into an ArangoDB collection.

        :param id: The NetworkX ID of the vertex.
        :type id: Any
        :param v: The vertex object to insert.
        :type v: dict
        :param col: The ArangoDB collection the vertex belongs to.
        :type col: str
        :param key: The _key value of the vertex.
        :type key: str
        :param ow: If set to True, overwrite existing document with matching _id.
        :type ow: bool
        """
        self.cntrl.adb_map[id] = {"_id": v["_id"], "collection": col, "key": key}
        self.db.collection(col).insert(v, overwrite=ow, silent=True)

    def __insert_arangodb_edge(
        self, edge: dict, from_node: dict, to_node: dict, col: str, ow: bool
    ):
        """Insert an ArangoDB edge into an ArangoDB collection.

        :param edge: The edge object to insert.
        :type edge: dict
        :param from_node: The NetworkX node object representing the edge source.
        :type from_node: dict
        :param to_node: The NetworkX node object representing the edge destination.
        :type to_node: dict
        :param col: The ArangoDB collection the edge belongs to.
        :type col: str
        :param ow: If set to True, overwrite existing document with matching _id.
        :type ow: bool
        """
        edge["_from"] = self.cntrl.adb_map.get(from_node["id"])["_id"]
        edge["_to"] = self.cntrl.adb_map.get(to_node["id"])["_id"]
        self.db.collection(col).insert(edge, overwrite=ow, silent=True)
