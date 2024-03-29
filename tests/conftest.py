import io
import os
import subprocess
import urllib.request as urllib
import zipfile
from pathlib import Path
from typing import Any

import networkx as nx
from arango import ArangoClient
from arango.database import StandardDatabase
from networkx.classes import Graph as NXGraph
from networkx.classes import MultiGraph as NXMultiGraph

from adbnx_adapter import ADBNX_Adapter, ADBNX_Controller
from adbnx_adapter.typings import Json, NxData, NxId

PROJECT_DIR = Path(__file__).parent.parent

db: StandardDatabase
adbnx_adapter: ADBNX_Adapter
imdb_adbnx_adapter: ADBNX_Adapter
grid_adbnx_adapter: ADBNX_Adapter
football_adbnx_adapter: ADBNX_Adapter


def pytest_addoption(parser: Any) -> None:
    parser.addoption("--url", action="store", default="http://localhost:8529")
    parser.addoption("--dbName", action="store", default="_system")
    parser.addoption("--username", action="store", default="root")
    parser.addoption("--password", action="store", default="")


def pytest_configure(config: Any) -> None:
    con = {
        "url": config.getoption("url"),
        "username": config.getoption("username"),
        "password": config.getoption("password"),
        "dbName": config.getoption("dbName"),
    }

    print("----------------------------------------")
    print("URL: " + con["url"])
    print("Username: " + con["username"])
    print("Password: " + con["password"])
    print("Database: " + con["dbName"])
    print("----------------------------------------")

    global db
    db = ArangoClient(hosts=con["url"]).db(
        con["dbName"], con["username"], con["password"], verify=True
    )

    global adbnx_adapter, imdb_adbnx_adapter, grid_adbnx_adapter, football_adbnx_adapter
    adbnx_adapter = ADBNX_Adapter(db)
    imdb_adbnx_adapter = ADBNX_Adapter(db, IMDB_ADBNX_Controller())
    grid_adbnx_adapter = ADBNX_Adapter(db, Grid_ADBNX_Controller())
    football_adbnx_adapter = ADBNX_Adapter(db, Football_ADBNX_Controller())

    if db.has_graph("fraud-detection") is False:
        arango_restore(con, "examples/data/fraud_dump")
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

    if db.has_graph("imdb") is False:
        arango_restore(con, "examples/data/imdb_dump")
        db.create_graph(
            "imdb",
            edge_definitions=[
                {
                    "edge_collection": "Ratings",
                    "from_vertex_collections": ["Users"],
                    "to_vertex_collections": ["Movies"],
                },
            ],
        )


def arango_restore(con: Json, path_to_data: str) -> None:
    restore_prefix = "./assets/" if os.getenv("GITHUB_ACTIONS") else ""
    protocol = "http+ssl://" if "https://" in con["url"] else "tcp://"
    url = protocol + con["url"].partition("://")[-1]

    subprocess.check_call(
        f'chmod -R 755 ./assets/arangorestore && {restore_prefix}arangorestore \
            -c none --server.endpoint {url} --server.database {con["dbName"]} \
                --server.username {con["username"]} \
                    --server.password "{con["password"]}" \
                        --input-directory "{PROJECT_DIR}/{path_to_data}"',
        cwd=f"{PROJECT_DIR}/tests",
        shell=True,
    )


def get_drivers_graph() -> NXGraph:
    nx_g = NXGraph()
    nx_g.add_edge("P-John", "C-BMW")
    nx_g.add_edge("P-Mark", "C-Audi")
    return nx_g


def get_likes_graph() -> NXMultiGraph:
    nx_g = NXGraph()
    nx_g.add_edge("P-John", "P-Emily", _id="JE", likes=True)
    nx_g.add_edge("P-Emily", "P-John", _id="EJ", likes=False)
    return nx_g


def get_grid_graph(n: int) -> NXGraph:
    return nx.grid_2d_graph(n, n)


def get_football_graph() -> NXGraph:
    url = "http://www-personal.umich.edu/~mejn/netdata/football.zip"
    sock = urllib.urlopen(url)
    s = io.BytesIO(sock.read())
    sock.close()
    zf = zipfile.ZipFile(s)
    gml = zf.read("football.gml").decode()
    gml_list = gml.split("\n")[1:]
    return nx.parse_gml(gml_list)


class IMDB_ADBNX_Controller(ADBNX_Controller):
    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> None:
        adb_vertex["bipartite"] = 0 if col == "Users" else 1
        return


class Grid_ADBNX_Controller(ADBNX_Controller):
    def _prepare_arangodb_vertex(self, adb_vertex: Json, col: str) -> None:
        adb_vertex["_id"] = tuple(
            int(n)
            for n in tuple(
                adb_vertex["_key"],
            )
        )
        return

    def _keyify_networkx_node(
        self, i: int, nx_node_id: NxId, nx_node: NxData, col: str
    ) -> str:
        adb_v_key: str = self._tuple_to_arangodb_key_helper(nx_node_id)  # type: ignore
        return adb_v_key


class Football_ADBNX_Controller(ADBNX_Controller):
    def _keyify_networkx_node(
        self, i: int, nx_node_id: NxId, nx_node: NxData, col: str
    ) -> str:
        adb_v_key: str = self._string_to_arangodb_key_helper(str(nx_node_id))
        return adb_v_key
