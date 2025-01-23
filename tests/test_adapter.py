from typing import Any, Dict, List, Optional, Set, Union

import pytest
from arango.graph import Graph as ADBGraph
from networkx.classes.graph import Graph as NXGraph

from adbnx_adapter import ADBNX_Adapter, ADBNX_Controller, ADBNX_Controller_Full_Cycle
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
    "adapter, name, metagraph, batch_size",
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
            1,
        ),
        (
            imdb_adbnx_adapter,
            "IMDBGraph",
            {
                "vertexCollections": {"Users": {"Age", "Gender"}, "Movies": {}},
                "edgeCollections": {"Ratings": {"Rating"}},
            },
            None,
        ),
    ],
)
def test_adb_to_nx(
    adapter: ADBNX_Adapter,
    name: str,
    metagraph: ArangoMetagraph,
    batch_size: Optional[int],
) -> None:
    nx_g = adapter.arangodb_to_networkx(name, metagraph, batch_size=batch_size)
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
    [(adbnx_adapter, "fraud-detection", [])],
)
def test_adb_graph_to_nx(
    adapter: ADBNX_Adapter, name: str, edge_definitions: List[Json]
) -> None:
    # Re-create the graph if defintions are provided
    if len(edge_definitions) > 0:
        db.delete_graph(name, ignore_missing=True)
        db.create_graph(name, edge_definitions=edge_definitions)

    graph = db.graph(name)
    v_cols: Set[str] = graph.vertex_collections()
    edge_definitions = graph.edge_definitions()
    e_cols: Set[str] = {c["edge_collection"] for c in edge_definitions}

    nx_g = adapter.arangodb_graph_to_networkx(name)
    assert_networkx_data(
        nx_g,
        metagraph={
            "vertexCollections": {col: set() for col in v_cols},
            "edgeCollections": {col: set() for col in e_cols},
        },
    )


@pytest.mark.parametrize(
    "adapter, name, nx_g, edge_definitions, orphan_collections, \
        overwrite_graph, adb_import_kwargs",
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
            None,
            True,
            {"overwrite": True},
        ),
        (
            adbnx_adapter,
            "Grid",
            get_grid_graph(25),
            None,
            None,
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
            None,
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
            None,
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
    orphan_collections: Optional[List[str]],
    overwrite_graph: bool,
    adb_import_kwargs: Dict[str, Any],
) -> None:
    adb_g = adapter.networkx_to_arangodb(
        name,
        nx_g,
        edge_definitions,
        orphan_collections,
        overwrite_graph,
        **adb_import_kwargs,
    )
    assert_arangodb_data(adapter, nx_g, adb_g)


def test_nx_to_adb_invalid_collections() -> None:
    db.delete_graph("Drivers", ignore_missing=True, drop_collections=True)

    nx_g_1 = get_drivers_graph()
    e_d_1 = [
        {
            "edge_collection": "drives",
            "from_vertex_collections": ["Person"],
            "to_vertex_collections": ["Car"],
        }
    ]
    # Raise NotImplementedError on missing vertex collection identification
    with pytest.raises(NotImplementedError):
        adbnx_adapter.networkx_to_arangodb("Drivers", nx_g_1, e_d_1)

    class Custom_ADBNX_Controller(ADBNX_Controller):
        def _prepare_networkx_node(
            self, i: int, nx_node_id: Any, nx_node: NxData, adb_v_cols: List[str]
        ) -> tuple[str, str]:
            return "invalid_vertex_collection", str(i)

    custom_adbnx_adapter = ADBNX_Adapter(db, Custom_ADBNX_Controller())

    # Raise ValueError on invalid vertex collection identification
    with pytest.raises(ValueError):
        custom_adbnx_adapter.networkx_to_arangodb("Drivers", nx_g_1, e_d_1)

    db.delete_graph("Drivers", ignore_missing=True, drop_collections=True)
    db.delete_graph("Feelings", ignore_missing=True, drop_collections=True)

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

    # Raise NotImplementedError on missing edge collection identification
    with pytest.raises(NotImplementedError):
        adbnx_adapter.networkx_to_arangodb("Feelings", nx_g_2, e_d_2)

    db.delete_graph("Feelings", ignore_missing=True, drop_collections=True)

    class Custom_ADBNX_Controller_2(ADBNX_Controller):
        def _prepare_networkx_node(
            self, i: int, nx_node_id: Any, nx_node: NxData, adb_v_cols: List[str]
        ) -> tuple[str, str]:
            return "Person", str(i)

        def _prepare_networkx_edge(
            self,
            i: int,
            from_node_id: NxId,
            to_node_id: NxId,
            nx_edge: Json,
            adb_e_cols: List[str],
            nx_map: Dict[Any, str],
        ) -> tuple[str, Union[str, None]]:
            return "invalid_edge_collection", None

    custom_adbnx_adapter = ADBNX_Adapter(db, Custom_ADBNX_Controller_2())

    # Raise ValueError on invalid edge collection identification
    with pytest.raises(ValueError):
        custom_adbnx_adapter.networkx_to_arangodb("Feelings", nx_g_2, e_d_2)

    db.delete_graph("Feelings", ignore_missing=True, drop_collections=True)


def test_full_cycle_from_arangodb_with_existing_collections() -> None:
    name = "fraud-detection"
    original_fraud_adb_g = db.graph(name)
    edge_definitions: List[Json] = original_fraud_adb_g.edge_definitions()

    col: str
    original_doc_count = dict()
    for col in original_fraud_adb_g.vertex_collections():
        original_doc_count[col] = original_fraud_adb_g.vertex_collection(col).count()

    e_cols = {e_d["edge_collection"] for e_d in edge_definitions}
    for col in e_cols:
        original_doc_count[col] = original_fraud_adb_g.edge_collection(col).count()

    fraud_nx_g = adbnx_adapter.arangodb_graph_to_networkx(name)

    for _, node in fraud_nx_g.nodes(data=True):
        node["new_vertex_data"] = ["new", "vertex", "data", "here"]

    for _, _, edge in fraud_nx_g.edges(data=True):
        edge["new_edge_data"] = ["new", "edge", "data", "here"]

    fraud_adbnx_adapter = ADBNX_Adapter(db, ADBNX_Controller_Full_Cycle())
    updated_fraud_adb_g = fraud_adbnx_adapter.networkx_to_arangodb(
        name,
        fraud_nx_g,
        edge_definitions,
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
    db.delete_graph(name + "_new", ignore_missing=True, drop_collections=True)

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

    class ADBNX_Controller_Full_Cycle_New_Collections(ADBNX_Controller_Full_Cycle):
        def _prepare_networkx_node(
            self, i: int, nx_node_id: Any, nx_node: NxData, adb_v_cols: List[str]
        ) -> tuple[str, str]:
            split = str(nx_node_id).split("/")
            return split[0] + "_new", str(i)

        def _prepare_networkx_edge(
            self,
            i: int,
            from_node_id: NxId,
            to_node_id: NxId,
            nx_edge: Json,
            adb_e_cols: List[str],
            nx_map: Dict[Any, str],
        ) -> tuple[str, Union[str, None]]:
            split = str(nx_edge["_id"]).split("/")
            return split[0] + "_new", None

    fraud_adbnx_adapter = ADBNX_Adapter(
        db, ADBNX_Controller_Full_Cycle_New_Collections()
    )
    new_fraud_adb_g = fraud_adbnx_adapter.networkx_to_arangodb(
        name + "_new",
        fraud_nx_g,
        edge_definitions,
    )

    col: str
    for col in original_fraud_adb_g.vertex_collections():
        new_col = f"{col}_new"

        original_col_count = original_fraud_adb_g.vertex_collection(col).count()
        new_col_count = new_fraud_adb_g.vertex_collection(new_col).count()
        assert original_col_count == new_col_count

        for vertex in original_fraud_adb_g.vertex_collection(col):
            assert new_fraud_adb_g.vertex_collection(new_col).has(vertex["_key"])

    original_edge_definitions = original_fraud_adb_g.edge_definitions()
    e_cols = {e_d["edge_collection"] for e_d in original_edge_definitions}

    for col in e_cols:
        new_col = f"{col}_new"

        original_col_count = original_fraud_adb_g.vertex_collection(col).count()
        new_col_count = new_fraud_adb_g.vertex_collection(new_col).count()
        assert original_col_count == new_col_count

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
        name,
        original_grid_nx_g,
        grid_edge_definitions,
    )

    new_grid_nx_g = grid_adbnx_adapter.arangodb_graph_to_networkx(name)

    for id, _ in original_grid_nx_g.nodes(data=True):
        assert new_grid_nx_g.has_node(id)

    for from_node, to_node, _ in original_grid_nx_g.edges(data=True):
        assert new_grid_nx_g.has_edge(from_node, to_node)


def assert_networkx_data(
    nx_g: NXGraph, metagraph: ArangoMetagraph, explicit_metagraph: bool = False
) -> None:
    adb_vertex: Json
    for col, atribs in metagraph["vertexCollections"].items():
        for adb_vertex in db.collection(col):
            adb_id: str = adb_vertex["_id"]
            nx_node: NxData = nx_g.nodes[adb_id]

            if explicit_metagraph:
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
            if explicit_metagraph:
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
) -> None:
    nx_map: dict[str, str] = dict()

    adb_v_cols: List[str] = adb_g.vertex_collections()
    adb_e_cols: List[str] = [c["edge_collection"] for c in adb_g.edge_definitions()]

    adb_vertex: Json
    for i, (nx_id, nx_node) in enumerate(nx_g.nodes(data=True), 1):
        col, key = adapter.cntrl._prepare_networkx_node(i, nx_id, nx_node, adb_v_cols)

        adb_vertex = adb_g.vertex_collection(col).get(key)
        for key, val in nx_node.items():
            assert val == adb_vertex[key]

    for i, (from_node_id, to_node_id, nx_edge) in enumerate(nx_g.edges(data=True), 1):
        col, key = adapter.cntrl._prepare_networkx_edge(  # type: ignore
            i, from_node_id, to_node_id, nx_edge, adb_e_cols, nx_map
        )

        adb_edges = adb_g.edge_collection(col).find(
            {
                "_from": nx_map[from_node_id],
                "_to": nx_map[to_node_id],
            }
        )

        # (there can be multiple edges with the same _from & _to values)
        has_edge_match: bool = False
        for adb_edge in adb_edges:
            has_edge_match = all([nx_edge[a] == adb_edge[a] for a in nx_edge.keys()])
            if has_edge_match:
                break

        assert has_edge_match
