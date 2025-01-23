#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Tuple, Union

from .abc import Abstract_ADBNX_Controller
from .typings import Json, NxData, NxId


class ADBNX_Controller(Abstract_ADBNX_Controller):
    """ArangoDB-NetworkX controller.

    Responsible for controlling how nodes & edges are handled when
    transitioning from ArangoDB to NetworkX, and vice-versa.

    You can derive your own custom ADBNX_Controller.
    """

    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> None:
        """ArangoDB --> NetworkX: UDF to prepare an ArangoDB vertex before it gets
        inserted into the NetworkX graph.

        Given an ArangoDB vertex, you can modify it in-place before it gets inserted
        into the NetworkX graph, and/or derive a custom node id for NetworkX
        to use by updating the "_id" attribute of the vertex (otherwise the
        vertex's current "_id" value will be used)

        :param adb_vertex: The ArangoDB vertex object to (optionally) modify.
        :type adb_vertex: Dict[str, Any]
        :param col: The ArangoDB collection the vertex belongs to.
        :type col: str
        """
        pass

    def _prepare_arangodb_edge(self, adb_edge: NxData, col: str) -> None:
        """ArangoDB --> NetworkX: UDF to prepare an ArangoDB edge before it gets
        inserted into the NetworkX graph.

        Given an ArangoDB edge, you can modify it in-place before it gets inserted
        into the NetworkX graph.

        :param adb_edge: The ArangoDB edge object to (optionally) modify.
        :type adb_edge: Dict[Any, Any]
        :param col: The ArangoDB collection the edge belongs to.
        :type col: str
        """
        pass

    def _prepare_networkx_node(
        self, i: int, nx_node_id: Any, nx_node: NxData, adb_v_cols: List[str]
    ) -> tuple[str, str]:
        """NetworkX --> ArangoDB: UDF to prepare a NetworkX node before it gets
        inserted into ArangoDB. This method must return a tuple of two values:
        - (1) the ArangoDB collection that this node belongs to (required).
        - (2) the ArangoDB _key value of the node (required).

        NOTE: You are free to use `_string_to_arangodb_key_helper()` and
        `_tuple_to_arangodb_key_helper()` to derive a valid ArangoDB _key value.

        :param i: The 1-based index of the NetworkX node in the list of nodes.
            Useful for generating unique _key values.
        :type i: int
        :param nx_node_id: The NetworkX ID of the node.
        :type nx_node_id: Any
        :param nx_node:  The NetworkX node object, optionally modifiable.
        :type nx_node: Dict[Any, Any]
        :param adb_v_cols: All ArangoDB vertex collections specified
            by the **edge_definitions** parameter of networkx_to_arangodb()
        :type adb_v_cols: List[str]
        :return: A tuple of two values: (1) the ArangoDB collection that this node
            belongs to, and (2) the ArangoDB _key value of the node.
        :rtype: Tuple[Union[str, None], Union[str, None]]
        """
        if len(adb_v_cols) == 1:
            return adb_v_cols[0], str(nx_node_id)

        m = f"""User must override this function,
        since there are {len(adb_v_cols)} vertex collections
        to choose from.
        """

        raise NotImplementedError(m)

    def _prepare_networkx_edge(
        self,
        i: int,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_edge: Json,
        adb_e_cols: List[str],
        nx_map: Dict[Any, str],
    ) -> tuple[str, Union[str, None]]:
        """NetworkX --> ArangoDB: UDF to prepare a NetworkX edge before it gets
        inserted into ArangoDB. This method must return a tuple of two values:
        - (1) the ArangoDB collection that this edge belongs to (required).
        - (2) the ArangoDB _key value of the edge (optional).

        If 2) is None, an auto-generated ArangoDB _key value will be used.

        NOTE #1: You are free to use `_string_to_arangodb_key_helper()` and
        `_tuple_to_arangodb_key_helper()` to derive a valid ArangoDB _key value.

        NOTE #2: You can use **nx_map** to derive the ArangoDB _from and _to values
        of the edge. i.e, `nx_map[from_node_id]` will give you the ArangoDB _from value,
        and `nx_map[to_node_id]` will give you the ArangoDB _to value.

        :param i: The 1-based index of the NetworkX edge in the list of edges.
            Useful for generating unique _key values.
        :type i: int
        :param from_node_id: The NetworkX ID of the node representing the source.
        :type from_node_id: Any
        :param to_node_id: The NetworkX ID of the node representing the destination.
        :type to_node_id: Any
        :param nx_edge: The NetworkX edge object, optionally modifiable.
        :type nx_edge: Dict[str, Any]
        :param adb_e_cols: All ArangoDB edge collections specified
            by the **edge_definitions** parameter of networkx_to_arangodb()
        :type adb_e_cols: List[str]
        :param nx_map: A mapping of NetworkX node ids to ArangoDB vertex ids. You
            can use this to derive the ArangoDB _from and _to values of the edge.
            i.e, nx_map[from_node_id] will give you the ArangoDB _from value,
            and nx_map[to_node_id] will give you the ArangoDB _to value.
        :type nx_map: Dict[NxId, str]
        :return: A tuple of two values: (1) the ArangoDB collection that this edge
            belongs to, and (2) the ArangoDB _key value of the edge.
        :rtype: Tuple[Union[str, None], Union[str, None]]
        """
        if len(adb_e_cols) == 1:
            return adb_e_cols[0], None

        m = f"""User must override this function,
        since there are {len(adb_e_cols)} edge collections
        to choose from.
        """

        raise NotImplementedError(m)

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

    def _prepare_networkx_node(
        self, i: int, nx_node_id: Any, nx_node: NxData, adb_v_cols: List[str]
    ) -> tuple[str, str]:
        split_id = str(nx_node["_id"]).split("/")
        return split_id[0], split_id[1]

    def _prepare_networkx_edge(
        self,
        i: int,
        from_node_id: NxId,
        to_node_id: NxId,
        nx_edge: NxData,
        adb_e_cols: List[str],
        nx_map: Dict[Any, str],
    ) -> tuple[str, Union[str, None]]:
        split_id = str(nx_edge["_id"]).split("/")
        return split_id[0], split_id[1]
