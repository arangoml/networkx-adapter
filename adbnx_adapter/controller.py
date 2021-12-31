#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Tuple

from .abc import Abstract_ADBNX_Controller
from .typings import Json, NxData, NxId


class ADBNX_Controller(Abstract_ADBNX_Controller):
    """ArangoDB-NetworkX controller.

    Responsible for controlling how nodes & edges are handled when
    transitioning from ArangoDB to NetworkX, and vice-versa.

    You can derive your own custom ADBNX_Controller, but it is not
    necessary for Homogeneous graphs.
    """

    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> NxId:
        """Prepare an ArangoDB vertex before it gets inserted into the NetworkX
        graph.

        Given an ArangoDB vertex, you can modify it before it gets inserted
        into the NetworkX graph, and/or derive a custom node id for networkx to use.
        In most cases, it is only required to return the ArangoDB _id of the vertex.

        :param adb_vertex: The ArangoDB vertex object to (optionally) modify.
        :type adb_vertex: adbnx_adapter.typings.Json
        :param col: The ArangoDB collection the vertex belongs to.
        :type col: str
        :return: The ArangoDB _id attribute of the vertex.
        :rtype: str
        """
        adb_vertex_id: str = adb_vertex["_id"]
        return adb_vertex_id

    def _prepare_arangodb_edge(self, adb_edge: Json, col: str) -> NxId:
        """Prepare an ArangoDB edge before it gets inserted into the NetworkX
        graph.

        Given an ArangoDB edge, you can modify it before it gets inserted
        into the NetworkX graph. In most cases, it is only required to
        return the ArangoDB _id of the edge.

        :param adb_edge: The ArangoDB edge object to (optionally) modify.
        :type adb_edge: adbnx_adapter.typings.Json
        :param col: The ArangoDB collection the edge belongs to.
        :type col: str
        :return: The ArangoDB _id attribute of the edge.
        :rtype: str
        """
        adb_edge_id: str = adb_edge["_id"]
        return adb_edge_id

    def _identify_networkx_node(self, nx_node_id: NxId, nx_node: NxData) -> str:
        """Given a NetworkX node, identify what ArangoDB collection it should
        belong to.

        NOTE: You must override this function if your NetworkX graph is NOT Homogeneous
        or does NOT comply to ArangoDB standards (i.e the node IDs are not formatted
        like "{collection}/{key}").

        :param nx_node_id: The NetworkX ID of the node.
        :type nx_node_id: adbnx_adapter.typings.NxId
        :param nx_node: The NetworkX node object.
        :type nx_node: adbnx_adapter.typings.NxData
        :return: The ArangoDB collection name
        :rtype: str
        """
        # In this case, nx_node_id is already a valid ArangoDB _id
        adb_vertex_id: str = str(nx_node_id)
        return adb_vertex_id.split("/")[0]

    def _identify_networkx_edge(
        self,
        nx_edge: NxData,
        from_nx_node: NxData,
        to_nx_node: NxData,
    ) -> str:
        """Given a NetworkX edge, and its pair of nodes, identify what ArangoDB
        collection should it belong to.

        NOTE #1: You must override this function if your NetworkX graph is NOT
        Homogeneous or does NOT comply to ArangoDB standards
        (i.e the edge IDs are not formatted like "{collection}/{key}").

        NOTE #2: You can accesss the ID & Collection belonging to the
        **from_nx_node** & **to_nx_node** parameters via their "nx_id" & "col"
        attribute keys. E.g `from_collection = from_nx_node["col"]`

        :param nx_edge: The NetworkX edge object.
        :type nx_edge: adbnx_adapter.typings.NxData
        :param from_nx_node: The NetworkX node object representing the edge source.
        :type from_nx_node: adbnx_adapter.typings.NxData
        :param to_nx_node: The NetworkX node object representing the edge destination.
        :type to_nx_node: adbnx_adapter.typings.NxData
        :return: The ArangoDB collection name
        :rtype: str
        """
        # In this case, nx_edge["_id"] is already a valid ArangoDB _id
        adb_edge_id: str = nx_edge["_id"]
        return adb_edge_id.split("/")[0]

    def _keyify_networkx_node(self, nx_node_id: NxId, nx_node: NxData, col: str) -> str:
        """Given a NetworkX node, derive its valid ArangoDB key.

        NOTE: You must override this function if you want to create custom ArangoDB _key
        values for your NetworkX nodes or if your NetworkX graph does NOT comply to
        ArangoDB standards (i.e the node IDs are not formatted
        like "{collection}/{key}"). For more  info, see the **keyify_nodes**
        parameter of ADBNX_Adapter.networkx_to_arangodb()

        :param nx_node_id: The NetworkX node id.
        :type nx_node_id: adbnx_adapter.typings.NxId
        :param nx_node: The NetworkX node object.
        :type nx_node: adbnx_adapter.typings.NxData
        :param col: The ArangoDB collection the node belongs to.
        :type col: str
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        # In this case, nx_node_id is already a valid ArangoDB _id
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
        _key values for your NetworkX edges or if your NetworkX graph does NOT comply
        to ArangoDB standards (i.e the edge IDs are not formatted
        like "{collection}/{key}"). For more info, see the **keyify_edges**
        parameter of ADBNX_Adapter.networkx_to_arangodb()

        NOTE #2: You can accesss the ID & Collection belonging to the
        **from_nx_node** & **to_nx_node** parameters via their "nx_id" & "col"
        attribute keys. E.g `from_collection = from_nx_node["col"]`

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
        # In this case, nx_edge["_id"] is already a valid ArangoDB _id
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
