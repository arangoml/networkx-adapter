import time
import json
import requests
import subprocess
from pathlib import Path
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter

PROJECT_DIR = Path(__file__).parent.parent.parent


def pytest_sessionstart():
    global con
    con = get_oasis_crendetials()
    print_connection_details(con)
    time.sleep(5)  # Enough for the oasis instance to be ready.

    global adbnx_adapter, imdb_adbnx_adapter, grid_adbnx_adapter, football_adbnx_adapter
    adbnx_adapter = ArangoDB_Networkx_Adapter(con)
    imdb_adbnx_adapter = IMDB_ArangoDB_Networkx_Adapter(con)
    grid_adbnx_adapter = Basic_Grid_ArangoDB_Networkx_Adapter(con)
    football_adbnx_adapter = Football_ArangoDB_Networkx_Adapter(con)

    arango_restore("examples/data/fraud_dump")
    arango_restore("examples/data/imdb_dump")

    edge_definitions = [
        {
            "edge_collection": "accountHolder",
            "from_vertex_collections": ["customer"],
            "to_vertex_collections": ["account"],
        },
        {
            "edge_collection": "transaction",
            "from_vertex_collections": ["account"],
            "to_vertex_collections": ["account"],
        },
    ]
    adbnx_adapter.db.create_graph("fraud-detection", edge_definitions=edge_definitions)


def pytest_sessionfinish(session, exitstatus):
    print_connection_details(con)


def get_oasis_crendetials() -> dict:
    url = "https://tutorials.arangodb.cloud:8529/_db/_system/tutorialDB/tutorialDB"
    request = requests.post(url, data=json.dumps("{}"))
    if request.status_code != 200:
        raise Exception("Error retrieving login data.")

    return json.loads(request.text)


def arango_restore(path_to_data):
    subprocess.check_call(
        f'arangorestore -c none --server.endpoint http+ssl://{con["hostname"]}:{con["port"]} --server.username {con["username"]} --server.database {con["dbName"]} --server.password {con["password"]} --default-replication-factor 3  --input-directory "{PROJECT_DIR}/{path_to_data}"',
        shell=True
    )


def print_connection_details(con):
    print('----------------------------------------')
    print("https://{}:{}".format(con["hostname"], con["port"]))
    print("Username: " + con["username"])
    print("Password: " + con["password"])
    print("Database: " + con["dbName"])
    print('----------------------------------------')


class IMDB_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def _prepare_nx_node(self, node: dict, col: str, atribs: set):
        node["bipartite"] = 0 if col == "Users" else 1
        return node["_id"]


class Basic_Grid_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def _identify_nx_node(self, id, node: dict, overwrite: bool) -> str:
        return "Node"  # Only one node collection in this dataset

    def _keyify_nx_node(self, id, node, col, overwrite: bool) -> str:
        return self._tuple_to_arangodb_key_helper(id)

    def _identify_nx_edge(self, from_node, to_node, e: dict, overwrite: bool) -> str:
        from_collection = self.adb_node_map.get(from_node)["collection"]
        to_collection = self.adb_node_map.get(to_node)["collection"]
        if from_collection == to_collection == "Node":
            return "to"

        return "Unknown_Edge"

    def _prepare_nx_node(self, node: dict, col: str, atribs: set):
        nx_id = tuple(
            int(n)
            for n in tuple(
                node["_key"],
            )
        )
        return nx_id


class Football_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def _identify_nx_node(self, id: str, node: dict, overwrite: bool) -> str:
        return "Team"  # Only one node collection in this dataset

    def _keyify_nx_node(self, id, node, collection, overwrite: bool) -> str:
        return self._string_to_arangodb_key_helper(id)

    def _identify_nx_edge(self, from_node, to_node, e: dict, overwrite: bool) -> str:
        from_collection = self.adb_node_map.get(from_node)["collection"]
        to_collection = self.adb_node_map.get(to_node)["collection"]
        if from_collection == to_collection == "Team":
            return "Played"

        return "Unknown_Edge"
