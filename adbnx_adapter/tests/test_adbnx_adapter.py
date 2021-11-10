import pytest
from conftest import (
    ArangoDB_Networkx_Adapter,
    adbnx_adapter,
    imdb_adbnx_adapter,
    grid_adbnx_adapter,
    football_adbnx_adapter,
)

import networkx as nx
from arango.graph import Graph as ArangoGraph
from networkx.classes.graph import Graph as NxGraph
from networkx.classes.multidigraph import MultiDiGraph as NxMultiDiGraph

import io
import zipfile
import urllib.request as urllib


@pytest.mark.unit
@pytest.mark.parametrize(
    "bad_connection",
    [
        {
            "dbName": "_system",
            "hostname": "localhost",
            "protocol": "http",
            "port": 8529,
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

    if edge_definitions:
        adapter.db.delete_graph(name, ignore_missing=True)
        adapter.db.create_graph(name, edge_definitions=edge_definitions)

    arango_graph = adapter.db.graph(name)

    v_cols = arango_graph.vertex_collections()
    e_cols = {col["edge_collection"] for col in arango_graph.edge_definitions()}

    nx_g = adbnx_adapter.create_networkx_graph_from_arangodb_graph(name)
    assert_networkx_data(nx_g, v_cols, e_cols)


@pytest.mark.unit
def test_create_arangodb_graph_from_grid_graph():
    grid_nx_g = nx.grid_2d_graph(5, 5)
    grid_edge_definitions = [
        {
            "edge_collection": "to",
            "from_vertex_collections": ["Node"],
            "to_vertex_collections": ["Node"],
        }
    ]

    grid_adb_g = grid_adbnx_adapter.create_arangodb_graph(
        "Grid", grid_nx_g, grid_edge_definitions
    )
    assert_arangodb_data(grid_adbnx_adapter, grid_nx_g, grid_adb_g)


@pytest.mark.unit
def test_create_arangodb_graph_from_football_graph():
    url = "http://www-personal.umich.edu/~mejn/netdata/football.zip"
    sock = urllib.urlopen(url)
    s = io.BytesIO(sock.read())
    sock.close()
    zf = zipfile.ZipFile(s)
    gml = zf.read("football.gml").decode()
    gml = gml.split("\n")[1:]

    football_nx_g = nx.parse_gml(gml)
    football_edge_definitions = [
        {
            "edge_collection": "Played",
            "from_vertex_collections": ["Team"],
            "to_vertex_collections": ["Team"],
        }
    ]

    football_adb_g = football_adbnx_adapter.create_arangodb_graph(
        "Football", football_nx_g, football_edge_definitions
    )
    assert_arangodb_data(football_adbnx_adapter, football_nx_g, football_adb_g)


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
            "from_vertex_collections": ["Node"],
            "to_vertex_collections": ["Node"],
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


def assert_adapter_type(adapter):
    assert (
        type(adapter) is ArangoDB_Networkx_Adapter
        or issubclass(type(adapter), ArangoDB_Networkx_Adapter) is True
    )


def assert_networkx_data(nx_g: NxGraph, v_cols, e_cols):
    assert type(nx_g) in [NxGraph, NxMultiDiGraph]
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

    for from_node, to_node, edge in nx_g.edges(data=True):
        col = adapter.cntrl._identify_nx_edge(from_node, to_node, edge, overwrite)
        assert adb_g.edge_collection(col).find(
            {
                "_from": adapter.cntrl.adb_map.get(from_node)["_id"],
                "_to": adapter.cntrl.adb_map.get(to_node)["_id"],
            }
        )