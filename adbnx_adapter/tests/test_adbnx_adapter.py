import pytest
from conftest import (
    nx,
    ArangoDB_Networkx_Adapter,
    Base_ADBNX_Controller,
    get_grid_graph,
    get_football_graph,
    get_karate_graph,
    adbnx_adapter,
    imdb_adbnx_adapter,
    grid_adbnx_adapter,
    football_adbnx_adapter,
    con,
    db,
)

from arango.graph import Graph as ArangoGraph
from networkx.classes.graph import Graph as NxGraph


@pytest.mark.unit
def test_validate_attributes():
    bad_connection = {
        "dbName": "_system",
        "hostname": "localhost",
        "protocol": "http",
        "port": 8529,
        # "username": "root",
        # "password": "password",
    }

    with pytest.raises(ValueError):
        ArangoDB_Networkx_Adapter(bad_connection)


@pytest.mark.unit
def test_validate_controller_class():
    class Bad_ADBNX_Controller:
        pass

    with pytest.raises(TypeError):
        ArangoDB_Networkx_Adapter(con, Bad_ADBNX_Controller)


@pytest.mark.unit
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
                    "Relationship": {
                        "label",
                        "name",
                        "relationshipType",
                    },
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
def test_adb_to_nx(adapter: ArangoDB_Networkx_Adapter, name: str, metagraph: dict):
    assert_adapter_type(adapter)
    nx_g = adapter.arangodb_to_networkx(name, metagraph)
    assert_networkx_data(nx_g, metagraph, True)


@pytest.mark.unit
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
    adapter: ArangoDB_Networkx_Adapter, name: str, v_cols: set, e_cols: set
):
    assert_adapter_type(adapter)
    nx_g = adapter.arangodb_collections_to_networkx(
        name,
        v_cols,
        e_cols,
    )
    assert_networkx_data(
        nx_g,
        metagraph={
            "vertexCollections": {col: {} for col in v_cols},
            "edgeCollections": {col: {} for col in e_cols},
        },
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "adapter, name, edge_definitions",
    [(adbnx_adapter, "fraud-detection", None)],
)
def test_adb_graph_to_nx(
    adapter: ArangoDB_Networkx_Adapter, name: str, edge_definitions
):
    assert_adapter_type(adapter)

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
            "vertexCollections": {col: {} for col in v_cols},
            "edgeCollections": {col: {} for col in e_cols},
        },
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "adapter, name, nx_g, edge_definitions, batch_size, keyify_nodes",
    [
        (
            adbnx_adapter,
            "Grid",
            get_grid_graph(),
            [
                {
                    "edge_collection": "to_v1",
                    "from_vertex_collections": ["Grid_Node_v1"],
                    "to_vertex_collections": ["Grid_Node_v1"],
                }
            ],
            5,
            False,
        ),
        (
            grid_adbnx_adapter,
            "Grid",
            get_grid_graph(),
            [
                {
                    "edge_collection": "to_v2",
                    "from_vertex_collections": ["Grid_Node_v2"],
                    "to_vertex_collections": ["Grid_Node_v2"],
                }
            ],
            5,
            True,
        ),
        (
            adbnx_adapter,
            "Karate",
            get_karate_graph(),
            [
                {
                    "edge_collection": "knows",
                    "from_vertex_collections": ["Karate_Student"],
                    "to_vertex_collections": ["Karate_Student"],
                }
            ],
            1000,
            False,
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
            1000,
            True,
        ),
    ],
)
def test_nx_to_adb(
    adapter: ArangoDB_Networkx_Adapter,
    name: str,
    nx_g: NxGraph,
    edge_definitions: list,
    batch_size: int,
    keyify_nodes: bool,
):
    assert_adapter_type(adapter)
    adb_g = adapter.networkx_to_arangodb(
        name, nx_g, edge_definitions, batch_size, keyify_nodes
    )
    assert_arangodb_data(adapter, nx_g, adb_g, keyify_nodes)


@pytest.mark.unit
def test_full_cycle_from_arangodb_with_existing_collections():
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
        batch_size=50,
        keyify_nodes=True,
        keyify_edges=True,
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


@pytest.mark.unit
def test_full_cycle_from_arangodb_with_new_collections():
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

    class Fraud_ADBNX_Controller(Base_ADBNX_Controller):
        def _identify_networkx_node(self, id, node: dict) -> str:
            adb_id: str = id
            return adb_id.split("/")[0] + "_new"

        def _identify_networkx_edge(
            self, edge: dict, from_node: dict, to_node: dict
        ) -> str:
            edge_id: str = edge["_id"]
            return edge_id.split("/")[0] + "_new"

    fraud_adbnx_adapter = ArangoDB_Networkx_Adapter(con, Fraud_ADBNX_Controller)

    new_fraud_adb_g = fraud_adbnx_adapter.networkx_to_arangodb(
        name + "_new",
        fraud_nx_g,
        edge_definitions,
        keyify_nodes=True,
        keyify_edges=True,
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


@pytest.mark.unit
def test_full_cycle_from_networkx():
    name = "Grid"
    if db.has_graph(name):
        db.delete_graph(name, drop_collections=True)

    original_grid_nx_g = nx.grid_2d_graph(5, 5)
    grid_edge_definitions = [
        {
            "edge_collection": "to",
            "from_vertex_collections": ["Grid_Node"],
            "to_vertex_collections": ["Grid_Node"],
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


def assert_adapter_type(adapter: ArangoDB_Networkx_Adapter):
    assert type(adapter) is ArangoDB_Networkx_Adapter and issubclass(
        type(adapter._ArangoDB_Networkx_Adapter__cntrl), Base_ADBNX_Controller
    )


def assert_networkx_data(nx_g: NxGraph, metagraph: dict, is_keep=False):
    adb_vertex: dict
    for col, atribs in metagraph["vertexCollections"].items():
        for adb_vertex in db.collection(col):
            adb_id = adb_vertex["_id"]
            nx_node: dict = nx_g.nodes[adb_id]

            if is_keep:
                for atrib in atribs:
                    if atrib in adb_vertex:
                        assert adb_vertex[atrib] == nx_node[atrib]
            else:
                assert adb_vertex == nx_node

    adb_edge: dict
    for col, atribs in metagraph["edgeCollections"].items():
        for adb_edge in db.collection(col):
            nx_edges: dict = nx_g.get_edge_data(adb_edge["_from"], adb_edge["_to"])

            # (there can be multiple edges with the same _from & _to values)
            has_edge_match = False
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
    adapter: ArangoDB_Networkx_Adapter,
    nx_g: NxGraph,
    adb_g: ArangoGraph,
    keyify_nodes: bool,
):
    nx_map = dict()
    cntrl: Base_ADBNX_Controller = adapter._ArangoDB_Networkx_Adapter__cntrl

    edge_definitions = adb_g.edge_definitions()
    is_homogeneous = len(edge_definitions) == 1
    adb_v_col = (
        edge_definitions[0]["from_vertex_collections"][0] if is_homogeneous else None
    )
    adb_e_col = edge_definitions[0]["edge_collection"] if is_homogeneous else None

    nx_node: dict
    for i, (nx_id, nx_node) in enumerate(nx_g.nodes(data=True)):
        col = adb_v_col or cntrl._identify_networkx_node(nx_id, nx_node)
        key = (
            cntrl._keyify_networkx_node(nx_id, nx_node, col) if keyify_nodes else str(i)
        )
        nx_node["_id"] = col + "/" + key

        nx_map[nx_id] = {
            "adb_id": nx_node["_id"],
            "col": col,
            "key": key,
        }

        adb_vertex = adb_g.vertex_collection(col).get(key)
        for key, val in nx_node.items():
            assert val == adb_vertex[key]

    nx_edge: dict
    for from_node_id, to_node_id, nx_edge in nx_g.edges(data=True):
        from_node = {
            "nx_id": from_node_id,
            "col": nx_map[from_node_id]["col"],
            **nx_g.nodes[from_node_id],
        }
        to_node = {
            "nx_id": to_node_id,
            "col": nx_map[from_node_id]["col"],
            **nx_g.nodes[to_node_id],
        }

        col = adb_e_col or cntrl._identify_networkx_edge(nx_edge, from_node, to_node)
        adb_edges = adb_g.edge_collection(col).find(
            {
                "_from": nx_map.get(from_node_id)["adb_id"],
                "_to": nx_map.get(to_node_id)["adb_id"],
            }
        )

        # (there can be multiple edges with the same _from & _to values)
        has_edge_match = False
        for adb_edge in adb_edges:
            has_edge_match = all([nx_edge[a] == adb_edge[a] for a in nx_edge.keys()])
            if has_edge_match:
                break

        assert has_edge_match
