import io
import json
import os
import subprocess
import time
import urllib.request as urllib
import zipfile
from pathlib import Path

from arango import ArangoClient
from arango.database import StandardDatabase
from networkx import grid_2d_graph, karate_club_graph, parse_gml
from networkx.classes import Graph as NetworkXGraph
from requests import post

from adbnx_adapter.adapter import ADBNX_Adapter
from adbnx_adapter.controller import ADBNX_Controller
from adbnx_adapter.typings import Json, NxData, NxId

PROJECT_DIR = Path(__file__).parent.parent.parent

con: Json
adbnx_adapter: ADBNX_Adapter
imdb_adbnx_adapter: ADBNX_Adapter
grid_adbnx_adapter: ADBNX_Adapter
football_adbnx_adapter: ADBNX_Adapter
db: StandardDatabase


def pytest_sessionstart() -> None:
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
    adbnx_adapter = ADBNX_Adapter(con)
    imdb_adbnx_adapter = ADBNX_Adapter(con, IMDB_ADBNX_Controller)
    grid_adbnx_adapter = ADBNX_Adapter(con, Grid_ADBNX_Controller)
    football_adbnx_adapter = ADBNX_Adapter(con, Football_ADBNX_Controller)

    global db
    url = "https://" + con["hostname"] + ":" + str(con["port"])
    client = ArangoClient(hosts=url)
    db = client.db(con["dbName"], con["username"], con["password"], verify=True)

    arango_restore(con, "examples/data/fraud_dump")
    arango_restore(con, "examples/data/imdb_dump")

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


def get_oasis_crendetials() -> Json:
    url = "https://tutorials.arangodb.cloud:8529/_db/_system/tutorialDB/tutorialDB"
    request = post(url, data=json.dumps("{}"))
    if request.status_code != 200:
        raise Exception("Error retrieving login data.")

    creds: Json = json.loads(request.text)
    return creds


def arango_restore(con: Json, path_to_data: str) -> None:
    restore_prefix = "./assets/" if os.getenv("GITHUB_ACTIONS") else ""

    subprocess.check_call(
        f'chmod -R 755 ./assets/arangorestore && {restore_prefix}arangorestore \
            -c none --server.endpoint http+ssl://{con["hostname"]}:{con["port"]} \
                --server.username {con["username"]} --server.database {con["dbName"]} \
                    --server.password {con["password"]} \
                        --input-directory "{PROJECT_DIR}/{path_to_data}"',
        cwd=f"{PROJECT_DIR}/adbnx_adapter/tests",
        shell=True,
    )


def print_connection_details(con: Json) -> None:
    print("----------------------------------------")
    print("https://{}:{}".format(con["hostname"], con["port"]))
    print("Username: " + con["username"])
    print("Password: " + con["password"])
    print("Database: " + con["dbName"])
    print("----------------------------------------")


def get_grid_graph() -> NetworkXGraph:
    return grid_2d_graph(5, 5)


def get_football_graph() -> NetworkXGraph:
    url = "http://www-personal.umich.edu/~mejn/netdata/football.zip"
    sock = urllib.urlopen(url)
    s = io.BytesIO(sock.read())
    sock.close()
    zf = zipfile.ZipFile(s)
    gml = zf.read("football.gml").decode()
    gml_list = gml.split("\n")[1:]
    return parse_gml(gml_list)


def get_karate_graph() -> NetworkXGraph:
    karate_nx_g = karate_club_graph()
    for id, node in karate_nx_g.nodes(data=True):
        node["degree"] = karate_nx_g.degree(id)

    return karate_nx_g


class IMDB_ADBNX_Controller(ADBNX_Controller):
    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> NxId:
        adb_vertex["bipartite"] = 0 if col == "Users" else 1
        return super()._prepare_arangodb_vertex(adb_vertex, col)


class Grid_ADBNX_Controller(ADBNX_Controller):
    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> NxId:
        nx_node_id = tuple(
            int(n)
            for n in tuple(
                adb_vertex["_key"],
            )
        )
        return nx_node_id

    def _keyify_networkx_node(self, nx_node_id: NxId, nx_node: NxData, col: str) -> str:
        adb_v_key: str = self._tuple_to_arangodb_key_helper(nx_node_id)  # type: ignore
        return adb_v_key


class Football_ADBNX_Controller(ADBNX_Controller):
    def _keyify_networkx_node(self, nx_node_id: NxId, nx_node: NxData, col: str) -> str:
        adb_v_key: str = self._string_to_arangodb_key_helper(str(nx_node_id))
        return adb_v_key
