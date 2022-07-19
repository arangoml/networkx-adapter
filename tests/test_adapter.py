from typing import Any, Dict, List, Optional, Set

import pytest
from arango.graph import Graph as ADBGraph
from networkx.classes.graph import Graph as NXGraph

from adbnx_adapter import ADBNX_Adapter, ADBNX_Controller
from adbnx_adapter.typings import ArangoMetagraph, Json, NxData, NxId

from .conftest import (
    adbnx_adapter,
    db,
    football_adbnx_adapter,
    get_drivers_graph,
    get_football_graph,
    get_grid_graph,
    get_likes_graph,
    grid_adbnx_adapter,
    imdb_adbnx_adapter,
)


def test_validate_constructor() -> None:
    bad_db: Dict[str, Any] = dict()

    class Bad_ADBNX_Controller:
        pass

    with pytest.raises(TypeError):
        ADBNX_Adapter(bad_db)

    with pytest.raises(TypeError):
        ADBNX_Adapter(db, Bad_ADBNX_Controller())  # type: ignore


@pytest.mark.parametrize(
    "adapter, name, metagraph",
    [
        (
            adbnx_adapter,
            "fraud-detection",
            {
                "vertexCollections": {
                    "account": {"Balance", "account_type", "customer_id", "rank"},
                    "bank": {"Country", "Id", "bank_id", "bank_name"},
                    "branch": {
                        "City",
                        "Country",
                        "Id",
                        "bank_id",
                        "branch_id",
                        "branch_name",
                    },
                    "Class": {"concrete", "label", "name"},
                    "customer": {"Name", "Sex", "Ssn", "rank"},
                },
                "edgeCollections": {
                    "accountHolder": {},
                    "Relationship": {"label", "name", "relationshipType"},
                    "transaction": {
                        "transaction_amt",
                        "sender_bank_id",
                        "receiver_bank_id",
                    },
                },
            },
        ),
        (
            imdb_adbnx_adapter,
            "IMDBGraph",
            {
                "vertexCollections": {"Users": {"Age", "Gender"}, "Movies": {}},
                "edgeCollections": {"Ratings": {"Rating"}},
            },
        ),
    ],
)
def test_adb_to_nx(
    adapter: ADBNX_Adapter, name: str, metagraph: ArangoMetagraph
) -> None:
    nx_g = adapter.arangodb_to_networkx(name, metagraph)
    assert_networkx_data(nx_g, metagraph, True)


@pytest.mark.parametrize(
    "adapter, name, v_cols, e_cols",
    [
        (
            adbnx_adapter,
            "fraud-detection",
            {"account", "bank", "branch", "Class", "customer"},
            {"accountHolder", "Relationship", "transaction"},
        )
    ],
)
def test_adb_collections_to_nx(
    adapter: ADBNX_Adapter, name: str, v_cols: Set[str], e_cols: Set[str]
) -> None:
    nx_g = adapter.arangodb_collections_to_networkx(
        name,
        v_cols,
        e_cols,
    )
    assert_networkx_data(
        nx_g,
        metagraph={
            "vertexCollections": {col: set() for col in v_cols},
            "edgeCollections": {col: set() for col in e_cols},
        },
    )


@pytest.mark.parametrize(
    "adapter, name, edge_definitions",
    [(adbnx_adapter, "fraud-detection", None)],
)
def test_adb_graph_to_nx(
    adapter: ADBNX_Adapter, name: str, edge_definitions: List[Json]
) -> None:
    # Re-create the graph if defintions are provided
    if edge_definitions:
        db.delete_graph(name, ignore_missing=True)
        db.create_graph(name, edge_definitions=edge_definitions)

    arango_graph = db.graph(name)
    v_cols = arango_graph.vertex_collections()
    e_cols = {col["edge_collection"] for col in arango_graph.edge_definitions()}

    nx_g = adapter.arangodb_graph_to_networkx(name)
    assert_networkx_data(
        nx_g,
        metagraph={
            "vertexCollections": {col: set() for col in v_cols},
            "edgeCollections": {col: set() for col in e_cols},
        },
    )


@pytest.mark.parametrize(
    "adapter, name, nx_g, edge_definitions, \
        keyify_nodes, keyify_edges, overwrite_graph, import_options",
    [
        (
            adbnx_adapter,
            "Grid",
            get_grid_graph(5),
            [
                {
                    "edge_collection": "to_v1",
                    "from_vertex_collections": ["Grid_Node_v1"],
                    "to_vertex_collections": ["Grid_Node_v1"],
                }
            ],
            False,
            False,
            True,
            {"overwrite": True},
        ),
        (
            adbnx_adapter,
            "Grid",
            get_grid_graph(25),
            None,
            False,
            False,
            False,
            {"on_duplicate": "replace"},
        ),
        (
            grid_adbnx_adapter,
            "Grid",
            get_grid_graph(1),
            [
                {
                    "edge_collection": "to_v2",
                    "from_vertex_collections": ["Grid_Node_v2"],
                    "to_vertex_collections": ["Grid_Node_v2"],
                }
            ],
            True,
            False,
            True,
            {"overwrite": True},
        ),
        (
            football_adbnx_adapter,
            "Football",
            get_football_graph(),
            [
                {
                    "edge_collection": "played",
                    "from_vertex_collections": ["Football_Team"],
                    "to_vertex_collections": ["Football_Team"],
                }
            ],
            True,
            False,
            True,
            {"batch_size": 300, "on_duplicate": "replace"},
        ),
    ],
)
def test_nx_to_adb(
    adapter: ADBNX_Adapter,
    name: str,
    nx_g: NXGraph,
    edge_definitions: Optional[List[Json]],
    keyify_nodes: bool,
    keyify_edges: bool,
    overwrite_graph: bool,
    import_options: Dict[str, Any],
) -> None:
    adb_g = adapter.networkx_to_arangodb(
        name,
        nx_g,
        edge_definitions,
        keyify_nodes,
        keyify_edges,
        overwrite_graph,
        **import_options,
    )
    assert_arangodb_data(adapter, nx_g, adb_g, keyify_nodes, keyify_edges)


def test_nx_to_adb_invalid_collections() -> None:
    nx_g_1 = get_drivers_graph()
    e_d_1 = [
        {
            "edge_collection": "drives",
            "from_vertex_collections": ["Person"],
            "to_vertex_collections": ["Car"],
        }
    ]
    # Raise ValueError on invalid vertex collection identification
    with pytest.raises(ValueError):
        adbnx_adapter.networkx_to_arangodb(
            "Drivers", nx_g_1, e_d_1, on_duplicate="replace"
        )

    nx_g_2 = get_likes_graph()
    e_d_2 = [
        {
            "edge_collection": "likes",
            "from_vertex_collections": ["Person"],
            "to_vertex_collections": ["Person"],
        },
        {
            "edge_collection": "dislikes",
            "from_vertex_collections": ["Person"],
            "to_vertex_collections": ["Person"],
        },
    ]
    # Raise ValueError on invalid edge collection identification
    with pytest.raises(ValueError):
        adbnx_adapter.networkx_to_arangodb(
            "Feelings", nx_g_2, e_d_2, on_duplicate="replace"
        )


def test_full_cycle_from_arangodb_with_existing_collections() -> None:
    name = "fraud-detection"
    original_fraud_adb_g = db.graph(name)
    edge_definitions = original_fraud_adb_g.edge_definitions()

    col: str
    original_doc_count = dict()
    for col in original_fraud_adb_g.vertex_collections():
        original_doc_count[col] = original_fraud_adb_g.vertex_collection(col).count()

    e_cols = {col["edge_collection"] for col in original_fraud_adb_g.edge_definitions()}
    for col in e_cols:
        original_doc_count[col] = original_fraud_adb_g.edge_collection(col).count()

    fraud_nx_g = adbnx_adapter.arangodb_graph_to_networkx(name)

    for _, node in fraud_nx_g.nodes(data=True):
        node["new_vertex_data"] = ["new", "vertex", "data", "here"]

    for _, _, edge in fraud_nx_g.edges(data=True):
        edge["new_edge_data"] = ["new", "edge", "data", "here"]

    updated_fraud_adb_g = adbnx_adapter.networkx_to_arangodb(
        name,
        fraud_nx_g,
        edge_definitions,
        keyify_nodes=True,
        keyify_edges=True,
        batch_size=50,
        on_duplicate="replace",
    )

    for col in updated_fraud_adb_g.vertex_collections():
        new_doc_count = updated_fraud_adb_g.vertex_collection(col).count()
        assert original_doc_count[col] == new_doc_count
        for vertex in updated_fraud_adb_g.vertex_collection(col):
            assert "new_vertex_data" in vertex

    e_cols = {col["edge_collection"] for col in updated_fraud_adb_g.edge_definitions()}
    for col in e_cols:
        new_doc_count = updated_fraud_adb_g.edge_collection(col).count()
        assert original_doc_count[col] == new_doc_count
        for edge in updated_fraud_adb_g.edge_collection(col):
            assert "new_edge_data" in edge


def test_full_cycle_from_arangodb_with_new_collections() -> None:
    name = "fraud-detection"
    original_fraud_adb_g = db.graph(name)
    fraud_nx_g = adbnx_adapter.arangodb_graph_to_networkx(name)

    edge_definitions = [
        {
            "edge_collection": "accountHolder_new",
            "from_vertex_collections": ["customer_new"],
            "to_vertex_collections": ["account_new"],
        },
        {
            "edge_collection": "transaction_new",
            "from_vertex_collections": ["account_new"],
            "to_vertex_collections": ["account_new"],
        },
    ]

    class Fraud_ADBNX_Controller(ADBNX_Controller):
        def _identify_networkx_node(
            self, nx_node_id: NxId, nx_node: NxData, adb_v_cols: List[str]
        ) -> str:
            adb_vertex_id: str = str(nx_node_id)
            return adb_vertex_id.split("/")[0] + "_new"

        def _identify_networkx_edge(
            self,
            nx_edge: NxData,
            from_nx_node: NxData,
            to_nx_node: NxData,
            adb_e_cols: List[str],
        ) -> str:
            adb_vertex_id: str = str(nx_edge["_id"])
            return adb_vertex_id.split("/")[0] + "_new"

    fraud_adbnx_adapter = ADBNX_Adapter(db, Fraud_ADBNX_Controller())

    new_fraud_adb_g = fraud_adbnx_adapter.networkx_to_arangodb(
        name + "_new",
        fraud_nx_g,
        edge_definitions,
        keyify_nodes=True,
        keyify_edges=True,
        on_duplicate="replace",
    )

    col: str
    for col in original_fraud_adb_g.vertex_collections():
        new_col = col + "_new"
        for vertex in original_fraud_adb_g.vertex_collection(col):
            assert new_fraud_adb_g.vertex_collection(new_col).has(vertex["_key"])

    e_cols = {col["edge_collection"] for col in original_fraud_adb_g.edge_definitions()}
    for col in e_cols:
        new_col = col + "_new"
        for edge in original_fraud_adb_g.edge_collection(col):
            assert new_fraud_adb_g.edge_collection(new_col).has(edge["_key"])


def test_full_cycle_from_networkx() -> None:
    name = "Grid_v3"
    if db.has_graph(name):
        db.delete_graph(name, drop_collections=True)

    original_grid_nx_g = get_grid_graph(5)
    grid_edge_definitions = [
        {
            "edge_collection": "to_v3",
            "from_vertex_collections": ["Grid_Node_v3"],
            "to_vertex_collections": ["Grid_Node_v3"],
        }
    ]

    grid_adbnx_adapter.networkx_to_arangodb(
        name, original_grid_nx_g, grid_edge_definitions, keyify_nodes=True
    )

    new_grid_nx_g = grid_adbnx_adapter.arangodb_graph_to_networkx(name)

    for id, _ in original_grid_nx_g.nodes(data=True):
        assert new_grid_nx_g.has_node(id)

    for from_node, to_node, _ in original_grid_nx_g.edges(data=True):
        assert new_grid_nx_g.has_edge(from_node, to_node)


def assert_networkx_data(
    nx_g: NXGraph, metagraph: ArangoMetagraph, is_keep: bool = False
) -> None:
    adb_vertex: Json
    for col, atribs in metagraph["vertexCollections"].items():
        for adb_vertex in db.collection(col):
            adb_id: str = adb_vertex["_id"]
            nx_node: NxData = nx_g.nodes[adb_id]

            if is_keep:
                for atrib in atribs:
                    if atrib in adb_vertex:
                        assert adb_vertex[atrib] == nx_node[atrib]
            else:
                assert adb_vertex == nx_node

    adb_edge: Json
    for col, atribs in metagraph["edgeCollections"].items():
        for adb_edge in db.collection(col):
            nx_edges: NxData = nx_g.get_edge_data(adb_edge["_from"], adb_edge["_to"])

            # (there can be multiple edges with the same _from & _to values)
            has_edge_match: bool = False
            if is_keep:
                for nx_edge in nx_edges.values():
                    has_edge_match = all(
                        [adb_edge[a] == nx_edge[a] for a in atribs if a in adb_edge]
                    )
                    if has_edge_match:
                        break
            else:
                for nx_edge in nx_edges.values():
                    has_edge_match = adb_edge == nx_edge
                    if has_edge_match:
                        break

            assert has_edge_match


def assert_arangodb_data(
    adapter: ADBNX_Adapter,
    nx_g: NXGraph,
    adb_g: ADBGraph,
    keyify_nodes: bool,
    keyify_edges: bool,
) -> None:
    nx_map = dict()

    adb_v_cols = adb_g.vertex_collections()
    adb_e_cols = [e_d["edge_collection"] for e_d in adb_g.edge_definitions()]

    has_one_vcol = len(adb_v_cols) == 1
    has_one_ecol = len(adb_e_cols) == 1

    for i, (nx_id, nx_node) in enumerate(nx_g.nodes(data=True), 1):
        col = (
            adb_v_cols[0]
            if has_one_vcol
            else adapter.cntrl._identify_networkx_node(nx_id, nx_node, adb_v_cols)
        )
        key = (
            adapter.cntrl._keyify_networkx_node(nx_id, nx_node, col)
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

        adb_vertex = adb_g.vertex_collection(col).get(key)
        for key, val in nx_node.items():
            assert val == adb_vertex[key]

    for from_node_id, to_node_id, nx_edge in nx_g.edges(data=True):
        from_node = {**nx_g.nodes[from_node_id], **nx_map[from_node_id]}
        to_node = {**nx_g.nodes[to_node_id], **nx_map[to_node_id]}

        col = (
            adb_e_cols[0]
            if has_one_ecol
            else adapter.cntrl._identify_networkx_edge(
                nx_edge, from_node, to_node, adb_e_cols
            )
        )
        adb_edges = adb_g.edge_collection(col).find(
            {
                "_from": nx_map[from_node_id]["adb_id"],
                "_to": nx_map[to_node_id]["adb_id"],
            }
        )

        # (there can be multiple edges with the same _from & _to values)
        has_edge_match: bool = False
        for adb_edge in adb_edges:
            has_edge_match = all([nx_edge[a] == adb_edge[a] for a in nx_edge.keys()])
            if has_edge_match:
                break

        assert has_edge_match
