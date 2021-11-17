from .abc import ADBNX_Controller

from arango.graph import Graph as ArangoDBGraph
from networkx.classes.graph import Graph as NetworkXGraph


class Base_ADBNX_Controller(ADBNX_Controller):
    """ArangoDB-NetworkX controller.

    Responsible for controlling how nodes & edges are handled when
    transitioning from ArangoDB to NetworkX, and vice-versa.
    """

    def __init__(self):
        self.nx_graph: NetworkXGraph = None
        self.nx_map = dict()  # Maps ArangoDB vertex IDs to NetworkX node IDs

        self.adb_graph: ArangoDBGraph = None
        self.adb_map = dict()  # Maps NetworkX node IDs to ArangoDB vertex IDs

    def _prepare_adb_vertex(self, vertex: dict, collection: str):
        """Prepare an ArangoDB vertex before it gets inserted into the NetworkX graph.

        Given an ArangoDB vertex, you can modify it before it gets inserted
        into the NetworkX graph, and/or derive a custom node id for networkx to use.

        In most cases, it is only required to return the ArangoDB _id of the vertex.

        :param vertex: The ArangoDB vertex object to (optionally) modify.
        :type vertex: dict
        :param collection: The ArangoDB collection the vertex belongs to.
        :type collection: str
        :return: The ArangoDB _id attribute of the vertex.
        :rtype: str
        """
        return vertex["_id"]

    def _prepare_adb_edge(self, edge: dict, collection: str):
        """Prepare an ArangoDB edge before it gets inserted into the NetworkX graph.

        Given an ArangoDB edge, you can modify it before it gets inserted
        into the NetworkX graph.

        In most cases, no action is needed.

        :param edge: The ArangoDB edge object to (optionally) modify.
        :type edge: dict
        :param collection: The ArangoDB collection the edge belongs to.
        :type collection: str
        """
        pass

    def _identify_nx_node(self, id, node: dict, overwrite: bool) -> str:
        """Given a NetworkX node, identify what ArangoDB collection it should belong to.

        NOTE: If your NetworkX graph does not comply to ArangoDB standards
        (i.e a node's ID is not "collection/key"), then you must override this function.

        :param id: The NetworkX ID of the node.
        :type id: Any
        :param node: The NetworkX node object.
        :type node: dict
        :param overwrite: Whether overwrite is enabled or not.
        :type overwrite: bool
        :return: The ArangoDB collection name
        :rtype: str
        """
        # In this case, id is already a valid ArangoDB _id
        adb_id: str = id
        return adb_id.split("/")[0] + ("" if overwrite else "_nx")

    def _identify_nx_edge(
        self, edge: dict, from_node: dict, to_node: dict, overwrite: bool
    ) -> str:
        """Given a NetworkX edge, its pair of nodes, and the overwrite boolean, identify what ArangoDB collection should it belong to.

        NOTE: If your NetworkX graph does not comply to ArangoDB standards
        (i.e a node's ID is not "collection/key"), then you must override this function.

        :param edge: The NetworkX edge object.
        :type edge: dict
        :param from_node: The NetworkX node object representing the edge source.
        :type from_node: dict
        :param to_node: The NetworkX node object representing the edge destination.
        :type to_node: dict
        :param overwrite: Whether overwrite is enabled or not.
        :type overwrite: bool
        :return: The ArangoDB collection name
        :rtype: str
        """
        # In this case, edge["_id"] is already a valid ArangoDB _id
        edge_id: str = edge["_id"]
        return edge_id.split("/")[0] + ("" if overwrite else "_nx")

    def _keyify_nx_node(self, id, node: dict, collection: str, overwrite: bool) -> str:
        """Given a NetworkX node, derive its valid ArangoDB key.

        NOTE: If your NetworkX graph does not comply to ArangoDB standards
        (i.e a node's ID is not "collection/key"), then you must override this function.

        :param node: The NetworkX node object.
        :type node: dict
        :param collection: The ArangoDB collection the node belongs to.
        :type collection: str
        :param overwrite: Whether overwrite is enabled or not.
        :type overwrite: bool
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        # In this case, id is already a valid ArangoDB _id
        adb_id: str = id
        return adb_id.split("/")[1]

    def _keyify_nx_edge(
        self,
        edge: dict,
        from_node: dict,
        to_node: dict,
        collection: str,
        overwrite: bool,
    ):
        """Given a NetworkX edge, its collection, its pair of nodes, and the overwrite boolean,
            derive its valid ArangoDB key.

        NOTE: If your NetworkX graph does not comply to ArangoDB standards
        (i.e a node's ID is not "collection/key"), then you must override this function.

        :param edge: The NetworkX edge object.
        :type edge: dict
        :param from_node: The NetworkX node object representing the edge source.
        :type from_node: dict
        :param to_node: The NetworkX node object representing the edge destination.
        :type to_node: dict
        :param collection: The ArangoDB collection the node belongs to.
        :type collection: str
        :param overwrite: Whether overwrite is enabled or not.
        :type overwrite: bool
        :return: The ArangoDB collection name
        :rtype: str
        """
        # In this case, edge["_id"] is already a valid ArangoDB _id
        edge_id: str = edge["_id"]
        return edge_id.split("/")[1]

    def _string_to_arangodb_key_helper(self, string: str) -> str:
        """Given a string, derive a valid ArangoDB _key string.

        :param string: A (possibly) invalid _key string value.
        :type string: str
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        res = ""
        for s in string:
            if s.isalnum() or s in self.VALID_KEY_CHARS:
                res += s

        return res

    def _tuple_to_arangodb_key_helper(self, tup: tuple) -> str:
        """Given a tuple, derive a valid ArangoDB _key string.

        :param tup: A tuple with non-None values.
        :type tup: tuple
        :return: A valid ArangoDB _key value.
        :rtype: str
        """
        string = "".join(map(str, tup))
        return self._string_to_arangodb_key_helper(string)
