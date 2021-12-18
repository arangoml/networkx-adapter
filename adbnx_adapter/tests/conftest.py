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
from arango import ArangoClient

from adbnx_adapter.adbnx_controller import Base_ADBNX_Controller
from adbnx_adapter.adbnx_adapter import ArangoDB_Networkx_Adapter

PROJECT_DIR = Path(__file__).parent.parent.parent


def pytest_sessionstart():
    global con
    con = get_oasis_crendetials()
    # con = {
    #     "username": "root",
    #     "password": "openSesame",
    #     "hostname": "localhost",
    #     "port": 8529,
    #     "protocol": "http",
    #     "dbName": "_system",
    # }
    print_connection_details(con)
    time.sleep(5)  # Enough for the oasis instance to be ready.

    global adbnx_adapter, imdb_adbnx_adapter, grid_adbnx_adapter, football_adbnx_adapter
    adbnx_adapter = ArangoDB_Networkx_Adapter(con)
    imdb_adbnx_adapter = ArangoDB_Networkx_Adapter(con, IMDB_ADBNX_Controller)
    grid_adbnx_adapter = ArangoDB_Networkx_Adapter(con, Grid_ADBNX_Controller)
    football_adbnx_adapter = ArangoDB_Networkx_Adapter(con, Football_ADBNX_Controller)

    global db
    url = "https://" + con["hostname"] + ":" + str(con["port"])
    client = ArangoClient(hosts=url)
    db = client.db(con["dbName"], con["username"], con["password"], verify=True)

    arango_restore("examples/data/fraud_dump")
    arango_restore("examples/data/imdb_dump")

    db.create_graph(
        "fraud-detection",
        edge_definitions=[
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
        ],
    )


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


def get_grid_graph():
    return nx.grid_2d_graph(5, 5)


def get_football_graph():
    url = "http://www-personal.umich.edu/~mejn/netdata/football.zip"
    sock = urllib.urlopen(url)
    s = io.BytesIO(sock.read())
    sock.close()
    zf = zipfile.ZipFile(s)
    gml = zf.read("football.gml").decode()
    gml = gml.split("\n")[1:]
    return nx.parse_gml(gml)


def get_karate_graph():
    karate_nx_g = nx.karate_club_graph()
    for id, node in karate_nx_g.nodes(data=True):
        node["degree"] = karate_nx_g.degree(id)

    return karate_nx_g


class IMDB_ADBNX_Controller(Base_ADBNX_Controller):
    def _prepare_arangodb_vertex(self, vertex: dict, collection: str):
        vertex["bipartite"] = 0 if collection == "Users" else 1
        return vertex["_id"]


class Grid_ADBNX_Controller(Base_ADBNX_Controller):
    def _prepare_arangodb_vertex(self, vertex: dict, collection: str):
        nx_id = tuple(
            int(n)
            for n in tuple(
                vertex["_key"],
            )
        )
        return nx_id

    def _keyify_networkx_node(self, id: tuple, node: dict, collection: str) -> str:
        return self._tuple_to_arangodb_key_helper(id)


class Football_ADBNX_Controller(Base_ADBNX_Controller):
    def _keyify_networkx_node(self, id, node: dict, collection: str) -> str:
        return self._string_to_arangodb_key_helper(id)
