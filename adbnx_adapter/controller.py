#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, List, Tuple

from .abc import Abstract_ADBNX_Controller
from .typings import Json, NxData, NxId


class ADBNX_Controller(Abstract_ADBNX_Controller):
    """ArangoDB-NetworkX controller.

    Responsible for controlling how nodes & edges are handled when
    transitioning from ArangoDB to NetworkX, and vice-versa.

    You can derive your own custom ADBNX_Controller.
    """

    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> None:
        """Prepare an ArangoDB vertex before it gets inserted into the NetworkX
        graph.

        Given an ArangoDB vertex, you can modify it before it gets inserted
        into the NetworkX graph, and/or derive a custom node id for NetworkX
        to use by updating the "_id" attribute of the vertex (otherwise the
        vertex's current "_id" value will be used)

        :param adb_vertex: The ArangoDB vertex object to (optionally) modify.
        :type adb_vertex: adbnx_adapter.typings.Json
        :param col: The ArangoDB collection the vertex belongs to.
        :type col: str
        """
        return

    def _prepare_arangodb_edge(self, adb_edge: Json, col: str) -> None:
        """Prepare an ArangoDB edge before it gets inserted into the NetworkX
        graph.

        Given an ArangoDB edge, you can modify it before it gets inserted
        into the NetworkX graph.

        :param adb_edge: The ArangoDB edge object to (optionally) modify.
        :type adb_edge: adbnx_adapter.typings.Json
        :param col: The ArangoDB collection the edge belongs to.
        :type col: str
        """
        return

    def _identify_networkx_node(
        self, nx_node_id: NxId, nx_node: NxData, adb_v_cols: List[str]
    ) -> str:
        """Given a NetworkX node, and a list of ArangoDB vertex collections defined,
        identify which ArangoDB vertex collection it should belong to.

        NOTE: You must override this function if len(**adb_v_cols**) > 1
        OR **nx_node_id* does NOT comply to ArangoDB standards
        (i.e "{collection}/{key}").

        :param nx_node_id: The NetworkX ID of the node.
        :type nx_node_id: adbnx_adapter.typings.NxId
        :param nx_node: The NetworkX node object.
        :type nx_node: adbnx_adapter.typings.NxData
        :param adb_v_cols: All ArangoDB vertex collections specified
            by the **edge_definitions** parameter of networkx_to_arangodb()
        :type adb_v_cols: List[str]
        :return: The ArangoDB collection name
        :rtype: str
        """
        # In this case, we assume that **nx_node_id** is already a valid ArangoDB _id
        # Otherwise, user must override this function
        adb_vertex_id: str = str(nx_node_id)
        return adb_vertex_id.split("/")[0]

    def _identify_networkx_edge(
        self,
        nx_edge: NxData,
        from_nx_node: NxData,
        to_nx_node: NxData,
        adb_e_cols: List[str],
    ) -> str:
        """Given a NetworkX edge, its pair of nodes, and a list of ArangoDB
        edge collections defined, identify which ArangoDB edge collection it
        should belong to.

        NOTE #1: You must override this function if len(**adb_e_cols**) > 1
        OR **nx_edge["_id"]** does NOT comply to ArangoDB standards
        (i.e "{collection}/{key}").

        NOTE #2: The two nodes associated to the **nx_edge** can be accessed
        by the **from_nx_node** & **to_nx_node** parameters, and are guaranteed
        to have the following attributes: `{"nx_id", "adb_id", "adb_col", "adb_key"}`

        :param nx_edge: The NetworkX edge object.
        :type nx_edge: adbnx_adapter.typings.NxData
        :param from_nx_node: The NetworkX node object representing the edge source.
        :type from_nx_node: adbnx_adapter.typings.NxData
        :param to_nx_node: The NetworkX node object representing the edge destination.
        :type to_nx_node: adbnx_adapter.typings.NxData
        :param adb_e_cols: All ArangoDB edge collections specified
            by the **edge_definitions** parameter of
            ADBNX_Adapter.networkx_to_arangodb()
        :type adb_e_cols: List[str]
        :return: The ArangoDB collection name
        :rtype: str
        """
        # In this case, we assume that nx_edge["_id"] is already a valid ArangoDB _id
        # Otherwise, user must override this function
        adb_edge_id: str = nx_edge["_id"]
        return adb_edge_id.split("/")[0]

    def _keyify_networkx_node(self, nx_node_id: NxId, nx_node: NxData, col: str) -> str:
        """Given a NetworkX node, derive its valid ArangoDB key.

        NOTE: You must override this function if you want to create custom ArangoDB _key
        values from your NetworkX nodes. To enable the use of this method, enable the
        **keyify_nodes** parameter in ADBNX_Adapter.networkx_to_arangodb().

        :param nx_node_id: The NetworkX node id.
        :type nx_node_id: adbnx_adapter.typings.NxId
        :param nx_node: The NetworkX node object.
        :type nx_node: adbnx_adapter.typings.NxData
        :param col: The ArangoDB collection the node belongs to.
        :type col: str
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        # In this case, we assume that **nx_node_id** is already a valid ArangoDB _id
        # Otherwise, user must override this function
        adb_vertex_id: str = str(nx_node_id)
        return adb_vertex_id.split("/")[1]

    def _keyify_networkx_edge(
        self,
        nx_edge: NxData,
        from_nx_node: NxData,
        to_nx_node: NxData,
        col: str,
    ) -> str:
        """Given a NetworkX edge, its collection, and its pair of nodes, derive
        its valid ArangoDB key.

        NOTE #1: You must override this function if you want to create custom ArangoDB
        _key values from your NetworkX edges. To enable the use of this method, enable
        the **keyify_edges** parameter in ADBNX_Adapter.networkx_to_arangodb().

        NOTE #2: The two nodes associated to the **nx_edge** can be accessed
        by the **from_nx_node** & **to_nx_node** parameters, and are guaranteed
        to have the following attributes: `{"nx_id", "adb_id", "adb_col", "adb_key"}`

        :param nx_edge: The NetworkX edge object.
        :type nx_edge: adbnx_adapter.typings.NxData
        :param from_nx_node: The NetworkX node object representing the edge source.
        :type from_nx_node: adbnx_adapter.typings.NxData
        :param to_nx_node: The NetworkX node object representing the edge destination.
        :type to_nx_node: adbnx_adapter.typings.NxData
        :param col: The ArangoDB collection the edge belongs to.
        :type col: str
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        # In this case, we assume that nx_edge["_id"] is already a valid ArangoDB _id
        # Otherwise, user must override this function
        adb_edge_id: str = nx_edge["_id"]
        return adb_edge_id.split("/")[1]

    def _string_to_arangodb_key_helper(self, string: str) -> str:
        """Given a string, derive a valid ArangoDB _key string.

        :param string: A (possibly) invalid _key string value.
        :type string: str
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        res: str = ""
        for s in string:
            if s.isalnum() or s in self.VALID_KEY_CHARS:
                res += s

        return res

    def _tuple_to_arangodb_key_helper(self, tup: Tuple[Any, ...]) -> str:
        """Given a tuple, derive a valid ArangoDB _key string.

        :param tup: A tuple with non-None values.
        :type tup: Tuple[Any, ...]
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        string: str = "".join(map(str, tup))
        return self._string_to_arangodb_key_helper(string)
