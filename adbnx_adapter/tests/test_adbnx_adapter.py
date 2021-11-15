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
    karate_adbnx_adapter,
)

from arango.graph import Graph as ArangoGraph
from networkx.classes.graph import Graph as NxGraph


@pytest.mark.unit
@pytest.mark.parametrize(
    "bad_connection",
    [
        {
            "dbName": "_system",
            "hostname": "localhost",
            "protocol": "http",
            "port": 8529,
            # "username": "root",
            # "password": "password",
        }
    ],
)
def test_validate_attributes(bad_connection):
    with pytest.raises(ValueError):
        ArangoDB_Networkx_Adapter(bad_connection)


@pytest.mark.unit
@pytest.mark.parametrize(
    "adapter, name, attributes",
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
                    "accountHolder": {"_from", "_to"},
                    "Relationship": {
                        "_from",
                        "_to",
                        "label",
                        "name",
                        "relationshipType",
                    },
                    "transaction": {"_from", "_to"},
                },
            },
        ),
        (
            imdb_adbnx_adapter,
            "IMDBGraph",
            {
                "vertexCollections": {"Users": {}, "Movies": {}},
                "edgeCollections": {"Ratings": {"_from", "_to", "ratings"}},
            },
        ),
    ],
)
def test_create_networkx_graph(
    adapter: ArangoDB_Networkx_Adapter, name: str, attributes: dict
):
    assert_adapter_type(adapter)
    nx_g = adapter.create_networkx_graph(name, attributes)
    assert_networkx_data(
        nx_g,
        attributes["vertexCollections"],
        attributes["edgeCollections"],
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "adapter, name, vcols, ecols",
    [
        (
            adbnx_adapter,
            "fraud-detection",
            {"account", "bank", "branch", "Class", "customer"},
            {"accountHolder", "Relationship", "transaction"},
        )
    ],
)
def test_create_networkx_graph_from_arangodb_collections(
    adapter: ArangoDB_Networkx_Adapter, name: str, vcols: set, ecols: set
):
    assert_adapter_type(adapter)
    nx_g = adapter.create_networkx_graph_from_arangodb_collections(
        name,
        vcols,
        ecols,
    )
    assert_networkx_data(nx_g, vcols, ecols)


@pytest.mark.unit
@pytest.mark.parametrize(
    "adapter, name, edge_definitions",
    [(adbnx_adapter, "fraud-detection", None)],
)
def test_create_networkx_graph_from_arangodb_graph(
    adapter: ArangoDB_Networkx_Adapter, name: str, edge_definitions
):
    assert_adapter_type(adapter)

    # Re-create the graph if defintions are provided
    if edge_definitions:
        adapter.db.delete_graph(name, ignore_missing=True)
        adapter.db.create_graph(name, edge_definitions=edge_definitions)

    arango_graph = adapter.db.graph(name)
    v_cols = arango_graph.vertex_collections()
    e_cols = {col["edge_collection"] for col in arango_graph.edge_definitions()}

    nx_g = adbnx_adapter.create_networkx_graph_from_arangodb_graph(name)
    assert_networkx_data(nx_g, v_cols, e_cols)


@pytest.mark.unit
@pytest.mark.parametrize(
    "adapter, name, nx_g, edge_definitions",
    [
        (
            grid_adbnx_adapter,
            "Grid",
            get_grid_graph(),
            [
                {
                    "edge_collection": "to",
                    "from_vertex_collections": ["Grid_Node"],
                    "to_vertex_collections": ["Grid_Node"],
                }
            ],
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
        ),
        (
            karate_adbnx_adapter,
            "Karate",
            get_karate_graph(),
            [
                {
                    "edge_collection": "knows",
                    "from_vertex_collections": ["Karate_Student"],
                    "to_vertex_collections": ["Karate_Student"],
                }
            ],
        ),
    ],
)
def test_create_arangodb_graph(
    adapter: ArangoDB_Networkx_Adapter,
    name: str,
    nx_g: NxGraph,
    edge_definitions: list,
):
    assert_adapter_type(adapter)
    adb_g = adapter.create_arangodb_graph(name, nx_g, edge_definitions)
    assert_arangodb_data(adapter, nx_g, adb_g)


@pytest.mark.unit
def test_full_cycle_from_arangodb():
    name = "fraud-detection"
    original_fraud_adb_g = adbnx_adapter.db.graph(name)
    fraud_nx_g = adbnx_adapter.create_networkx_graph_from_arangodb_graph(name)

    edge_definitions = [
        {
            "edge_collection": "accountHolder_nx",
            "from_vertex_collections": ["customer_nx"],
            "to_vertex_collections": ["account_nx"],
        },
        {
            "edge_collection": "transaction_nx",
            "from_vertex_collections": ["account_nx"],
            "to_vertex_collections": ["account_nx"],
        },
    ]

    new_name = name + "-nx"
    new_fraud_adb_g = adbnx_adapter.create_arangodb_graph(
        new_name, fraud_nx_g, edge_definitions, keyify_edges=True
    )

    col: str
    for col in original_fraud_adb_g.vertex_collections():
        new_col = col + "_nx"
        for vertex in original_fraud_adb_g.vertex_collection(col):
            assert new_fraud_adb_g.vertex_collection(new_col).has(vertex["_key"])

    e_cols = {col["edge_collection"] for col in original_fraud_adb_g.edge_definitions()}
    for col in e_cols:
        new_col = col + "_nx"
        for edge in original_fraud_adb_g.edge_collection(col):
            assert new_fraud_adb_g.edge_collection(new_col).has(edge["_key"])


@pytest.mark.unit
def test_full_cycle_from_arangodb_with_overwrite():
    name = "fraud-detection"
    original_fraud_adb_g = adbnx_adapter.db.graph(name)
    edge_definitions = original_fraud_adb_g.edge_definitions()

    col: str
    original_doc_count = dict()
    for col in original_fraud_adb_g.vertex_collections():
        original_doc_count[col] = original_fraud_adb_g.vertex_collection(col).count()

    e_cols = {col["edge_collection"] for col in original_fraud_adb_g.edge_definitions()}
    for col in e_cols:
        original_doc_count[col] = original_fraud_adb_g.edge_collection(col).count()

    fraud_nx_g = adbnx_adapter.create_networkx_graph_from_arangodb_graph(name)

    for _, node in fraud_nx_g.nodes(data=True):
        node["new_vertex_data"] = ["new", "vertex", "data", "here"]

    for _, _, edge in fraud_nx_g.edges(data=True):
        edge["new_edge_data"] = ["new", "edge", "data", "here"]

    updated_fraud_adb_g = adbnx_adapter.create_arangodb_graph(
        name, fraud_nx_g, edge_definitions, overwrite=True, keyify_edges=True
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
def test_full_cycle_from_networkx():
    name = "Grid"
    if grid_adbnx_adapter.db.has_graph(name):
        grid_adbnx_adapter.db.delete_graph(name, drop_collections=True)

    original_grid_nx_g = nx.grid_2d_graph(5, 5)
    grid_edge_definitions = [
        {
            "edge_collection": "to",
            "from_vertex_collections": ["Grid_Node"],
            "to_vertex_collections": ["Grid_Node"],
        }
    ]

    grid_adbnx_adapter.create_arangodb_graph(
        name, original_grid_nx_g, grid_edge_definitions
    )

    new_grid_nx_g = grid_adbnx_adapter.create_networkx_graph_from_arangodb_graph(name)

    for id, _ in original_grid_nx_g.nodes(data=True):
        assert new_grid_nx_g.has_node(id)

    for from_node, to_node, _ in original_grid_nx_g.edges(data=True):
        assert new_grid_nx_g.has_edge(from_node, to_node)


def assert_adapter_type(adapter: ArangoDB_Networkx_Adapter):
    assert type(adapter) is ArangoDB_Networkx_Adapter and issubclass(
        type(adapter.cntrl), Base_ADBNX_Controller
    )


def assert_networkx_data(nx_g: NxGraph, v_cols, e_cols):
    for col in v_cols:
        for vertex in adbnx_adapter.db.collection(col):
            assert nx_g.has_node(vertex["_id"])

    for col in e_cols:
        for edge in adbnx_adapter.db.collection(col):
            assert nx_g.has_edge(edge["_from"], edge["_to"])


def assert_arangodb_data(
    adapter: ArangoDB_Networkx_Adapter, nx_g: NxGraph, adb_g: ArangoGraph
):
    overwrite = False
    for id, node in nx_g.nodes(data=True):
        col = adapter.cntrl._identify_nx_node(id, node, overwrite)
        key = adapter.cntrl._keyify_nx_node(id, node, col, overwrite)
        assert adb_g.vertex_collection(col).has(key)

    for from_node_id, to_node_id, edge in nx_g.edges(data=True):
        from_node = {"id": from_node_id, **nx_g.nodes[from_node_id]}
        to_node = {"id": to_node_id, **nx_g.nodes[to_node_id]}

        col = adapter.cntrl._identify_nx_edge(edge, from_node, to_node, overwrite)
        assert adb_g.edge_collection(col).find(
            {
                "_from": adapter.cntrl.adb_map.get(from_node["id"])["_id"],
                "_to": adapter.cntrl.adb_map.get(to_node["id"])["_id"],
            }
        )
