#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Tuple

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
        :type adb_vertex: Dict[str, Any]
        :param col: The ArangoDB collection the vertex belongs to.
        :type col: str
        """
        pass

    def _prepare_arangodb_edge(self, adb_edge: Json, col: str) -> None:
        """Prepare an ArangoDB edge before it gets inserted into the NetworkX
        graph.

        Given an ArangoDB edge, you can modify it before it gets inserted
        into the NetworkX graph.

        :param adb_edge: The ArangoDB edge object to (optionally) modify.
        :type adb_edge: Dict[str, Any]
        :param col: The ArangoDB collection the edge belongs to.
        :type col: str
        """
        pass

    def _identify_networkx_node(
        self, nx_node_id: NxId, nx_node: NxData, adb_v_cols: List[str]
    ) -> str:
        """Given a NetworkX node, and a list of ArangoDB vertex collections defined,
        identify which ArangoDB vertex collection **nx_node** should belong to.

        NOTE: You must override this function if len(**adb_v_cols**) > 1.

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
        m = f"""User must override this function,
        since there are {len(adb_v_cols)} vertex collections
        to choose from
        """
        raise NotImplementedError(m)

    def _identify_networkx_edge(
        self,
        nx_edge: NxData,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_map: Dict[NxId, str],
        adb_e_cols: List[str],
    ) -> str:
        """Given a NetworkX edge, its pair of nodes, and a list of ArangoDB
        edge collections defined, identify which ArangoDB edge collection **nx_edge**
        should belong to.

        NOTE #1: You must override this function if len(**adb_e_cols**) > 1.

        :param nx_edge: The NetworkX edge object.
        :type nx_edge: adbnx_adapter.typings.NxData
        :param from_node_id: The NetworkX ID of the node representing the source.
        :type from_node_id: adbnx_adapter.typings.NxId
        :param to_node_id: The NetworkX ID of the node representing the destination.
        :type to_node_id: adbnx_adapter.typings.NxId
        :param nx_map: A mapping of NetworkX node ids to ArangoDB vertex ids. You
            can use this to derive the ArangoDB _from and _to values of the edge.
            i.e, `nx_map[from_node_id]` will give you the ArangoDB _from value,
            and `nx_map[to_node_id]` will give you the ArangoDB _to value.
        :type nx_map: Dict[NxId, str]
        :param adb_e_cols: All ArangoDB edge collections specified
            by the **edge_definitions** parameter of
            ADBNX_Adapter.networkx_to_arangodb()
        :type adb_e_cols: List[str]
        :return: The ArangoDB collection name
        :rtype: str
        """
        m = f"""User must override this function,
        since there are {len(adb_e_cols)} edge collections
        to choose from.
        """
        raise NotImplementedError(m)

    def _keyify_networkx_node(
        self, i: int, nx_node_id: NxId, nx_node: NxData, col: str
    ) -> str:
        """Given a NetworkX node, derive its ArangoDB key.

        NOTE #1: You must override this function if you want to create custom ArangoDB
        _key values for your NetworkX nodes.

        NOTE #2: You are free to use `_string_to_arangodb_key_helper()` and
        `_tuple_to_arangodb_key_helper()` to derive a valid ArangoDB _key value.

        :param i: The index of the NetworkX node in the list of nodes.
        :type i: int
        :param nx_node_id: The NetworkX node id.
        :type nx_node_id: adbnx_adapter.typings.NxId
        :param nx_node: The NetworkX node object.
        :type nx_node: adbnx_adapter.typings.NxData
        :param col: The ArangoDB collection that **nx_node** belongs to.
        :type col: str
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        return str(i)

    def _keyify_networkx_edge(
        self,
        i: int,
        nx_edge: NxData,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_map: Dict[NxId, str],
        col: str,
    ) -> str:
        """Given a NetworkX edge, its collection, and its pair of nodes, derive
        its ArangoDB key.

        NOTE #1: You must override this function if you want to create custom ArangoDB
        _key values for your NetworkX edges.

        NOTE #2: You can use **nx_map** to derive the ArangoDB _from and _to values
        of the edge. i.e, `nx_map[from_node_id]` will give you the ArangoDB _from value,
        and `nx_map[to_node_id]` will give you the ArangoDB _to value.

        NOTE #3: You are free to use `_string_to_arangodb_key_helper()` and
        `_tuple_to_arangodb_key_helper()` to derive a valid ArangoDB _key value.

        :param i: The index of the NetworkX edge in the list of edges.
        :type i: int
        :param nx_edge: The NetworkX edge object.
        :type nx_edge: adbnx_adapter.typings.NxData
        :param from_node_id: The NetworkX ID of the node representing the source.
        :type from_node_id: adbnx_adapter.typings.NxId
        :param to_node_id: The NetworkX ID of the node representing the destination.
        :type to_node_id: adbnx_adapter.typings.NxId
        :param col: The ArangoDB collection that **nx_edge** belongs to.
        :type col: str
        :param nx_map: A mapping of NetworkX node ids to ArangoDB vertex ids. You
            can use this to derive the ArangoDB _from and _to values of the edge.
            i.e, nx_map[from_node_id] will give you the ArangoDB _from value,
            and nx_map[to_node_id] will give you the ArangoDB _to value.
        :type nx_map: Dict[NxId, str]
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        return str(i)

    def _prepare_networkx_node(self, nx_node: Json, col: str) -> None:
        """Optionally modify a NetworkX node before it gets inserted into the ArangoDB
        collection **col**.

        Given an ArangoDB representation of a NetworkX node (i.e {_key: ..., ...}),
        you can (optionally) modify the object before it gets inserted into its
        designated ArangoDB collection.

        NOTE: Do NOT rely on this method to modify the "_key" attribute or
        the "_id" attribute of **nx_node**. Use `_keyify_networkx_node()` instead.

        :param nx_node: The ArangoDB representation of the NetworkX node
            to (optionally) modify.
        :type nx_node: Dict[str, Any]
        :param col: The ArangoDB collection associated to the node.
        :type col: str
        """
        pass

    def _prepare_networkx_edge(self, nx_edge: Json, col: str) -> None:
        """Optionally modify a NetworkX edge before it gets inserted into the ArangoDB
        collection **col**.

        NOTE: Do NOT rely on this method to modify the "_key" attribute or
        the "_id" attribute of **nx_edge**. Use `_keyify_networkx_edge()` instead.

        :param nx_edge: The ArangoDB representation of the NetworkX edge
            to (optionally) modify.
        :type nx_edge: Dict[str, Any]
        :param col: The ArangoDB collection associated to the edge.
        :type col: str
        """
        pass

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


class ADBNX_Controller_Full_Cycle(ADBNX_Controller):
    """AragonDB-NetworkX controller for full-cycle operations.

    It preserves the original ArangoDB _id, _key, and collection
    values of the nodes and edges when transitioning from NetworkX to ArangoDB.

    Useful when combined with `on_duplicate='replace'` when going
    from ArangoDB -> NetworkX -> ArangoDB.
    """

    def _identify_networkx_node(
        self, nx_node_id: NxId, nx_node: NxData, adb_v_cols: List[str]
    ) -> str:
        return str(nx_node["_id"]).split("/")[0]

    def _identify_networkx_edge(
        self,
        nx_edge: NxData,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_map: Dict[NxId, str],
        adb_e_cols: List[str],
    ) -> str:
        return str(nx_edge["_id"]).split("/")[0]

    def _keyify_networkx_node(
        self, i: int, nx_node_id: NxId, nx_node: NxData, col: str
    ) -> str:
        return str(nx_node["_key"])

    def _keyify_networkx_edge(
        self,
        i: int,
        nx_edge: NxData,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_map: Dict[NxId, str],
        col: str,
    ) -> str:
        return str(nx_edge["_key"])
