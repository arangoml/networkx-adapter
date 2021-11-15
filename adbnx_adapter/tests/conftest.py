import io
import os
import time
import json
import zipfile
import requests
import subprocess
from pathlib import Path
import urllib.request as urllib

import networkx as nx
from adbnx_adapter.adbnx_controller import Base_ADBNX_Controller
from adbnx_adapter.adbnx_adapter import ArangoDB_Networkx_Adapter

PROJECT_DIR = Path(__file__).parent.parent.parent


def pytest_sessionstart():
    global con
    con = get_oasis_crendetials()
    print_connection_details(con)
    time.sleep(5)  # Enough for the oasis instance to be ready.

    global adbnx_adapter, imdb_adbnx_adapter, grid_adbnx_adapter, football_adbnx_adapter, karate_adbnx_adapter
    adbnx_adapter = ArangoDB_Networkx_Adapter(con)
    imdb_adbnx_adapter = ArangoDB_Networkx_Adapter(con, IMDB_ADBNX_Controller)
    grid_adbnx_adapter = ArangoDB_Networkx_Adapter(con, Grid_ADBNX_Controller)
    football_adbnx_adapter = ArangoDB_Networkx_Adapter(con, Football_ADBNX_Controller)
    karate_adbnx_adapter = ArangoDB_Networkx_Adapter(con, Karate_ADBNX_Controller)

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


def get_oasis_crendetials() -> dict:
    url = "https://tutorials.arangodb.cloud:8529/_db/_system/tutorialDB/tutorialDB"
    request = requests.post(url, data=json.dumps("{}"))
    if request.status_code != 200:
        raise Exception("Error retrieving login data.")

    return json.loads(request.text)


def arango_restore(path_to_data):
    restore_prefix = "./" if os.getenv("GITHUB_ACTIONS") else ""  # temporary hack

    subprocess.check_call(
        f'chmod -R 755 ./arangorestore && {restore_prefix}arangorestore -c none --server.endpoint http+ssl://{con["hostname"]}:{con["port"]} --server.username {con["username"]} --server.database {con["dbName"]} --server.password {con["password"]} --default-replication-factor 3  --input-directory "{PROJECT_DIR}/{path_to_data}"',
        cwd=f"{PROJECT_DIR}/adbnx_adapter/tests",
        shell=True,
    )


def print_connection_details(con):
    print("----------------------------------------")
    print("https://{}:{}".format(con["hostname"], con["port"]))
    print("Username: " + con["username"])
    print("Password: " + con["password"])
    print("Database: " + con["dbName"])
    print("----------------------------------------")


class IMDB_ADBNX_Controller(Base_ADBNX_Controller):
    def _prepare_adb_vertex(self, vertex: dict, collection: str):
        vertex["bipartite"] = 0 if collection == "Users" else 1
        return vertex["_id"]


class Grid_ADBNX_Controller(Base_ADBNX_Controller):
    def _prepare_adb_vertex(self, vertex: dict, collection: str):
        nx_id = tuple(
            int(n)
            for n in tuple(
                vertex["_key"],
            )
        )
        return nx_id

    def _identify_nx_node(self, id: tuple, node: dict, overwrite: bool) -> str:
        return "Grid_Node"  # Only one node collection in this dataset

    def _keyify_nx_node(
        self, id: tuple, node: dict, collection: str, overwrite: bool
    ) -> str:
        return self._tuple_to_arangodb_key_helper(id)

    def _identify_nx_edge(
        self, edge: dict, from_node: dict, to_node: dict, overwrite: bool
    ) -> str:
        from_collection = self.adb_map.get(from_node["id"])["collection"]
        to_collection = self.adb_map.get(to_node["id"])["collection"]

        if from_collection == to_collection == "Grid_Node":
            return "to"

        return "Unknown_Edge"


def get_grid_graph():
    return nx.grid_2d_graph(5, 5)


class Football_ADBNX_Controller(Base_ADBNX_Controller):
    def _identify_nx_node(self, id, node: dict, overwrite: bool) -> str:
        return "Football_Team"  # Only one node collection in this dataset=

    def _keyify_nx_node(self, id, node: dict, collection: str, overwrite: bool) -> str:
        return self._string_to_arangodb_key_helper(id)

    def _identify_nx_edge(
        self, edge: dict, from_node: dict, to_node: dict, overwrite: bool
    ) -> str:
        from_collection = self.adb_map.get(from_node["id"])["collection"]
        to_collection = self.adb_map.get(to_node["id"])["collection"]

        if from_collection == to_collection == "Football_Team":
            return "played"

        return "Unknown_Edge"


def get_football_graph():
    url = "http://www-personal.umich.edu/~mejn/netdata/football.zip"
    sock = urllib.urlopen(url)
    s = io.BytesIO(sock.read())
    sock.close()
    zf = zipfile.ZipFile(s)
    gml = zf.read("football.gml").decode()
    gml = gml.split("\n")[1:]
    return nx.parse_gml(gml)


class Karate_ADBNX_Controller(Base_ADBNX_Controller):
    def _identify_nx_node(self, id, node: dict, overwrite: bool) -> str:
        return "Karate_Student"

    def _identify_nx_edge(
        self, edge: dict, from_node: dict, to_node: dict, overwrite: bool
    ) -> str:
        from_collection = self.adb_map.get(from_node["id"])["collection"]
        to_collection = self.adb_map.get(to_node["id"])["collection"]

        if from_collection == to_collection == "Karate_Student":
            return "knows"

        return "Unknown_Edge"

    def _keyify_nx_node(self, id, node: dict, collection: str, overwrite: bool) -> str:
        return str(id)  # In this case the id is an integer


def get_karate_graph():
    karate_nx_g = nx.karate_club_graph()
    for id, node in karate_nx_g.nodes(data=True):
        node["degree"] = karate_nx_g.degree(id)

    return karate_nx_g
