import io
import logging
import os
import subprocess
import urllib.request as urllib
import zipfile
from pathlib import Path
from typing import Any

from arango import ArangoClient
from arango.database import StandardDatabase
from networkx import grid_2d_graph, parse_gml
from networkx.classes import Graph as NetworkXGraph

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
    adbnx_adapter = ADBNX_Adapter(db, logging_lvl=logging.DEBUG)
    imdb_adbnx_adapter = ADBNX_Adapter(
        db, IMDB_ADBNX_Controller(), logging_lvl=logging.DEBUG
    )
    grid_adbnx_adapter = ADBNX_Adapter(
        db, Grid_ADBNX_Controller(), logging_lvl=logging.DEBUG
    )
    football_adbnx_adapter = ADBNX_Adapter(
        db, Football_ADBNX_Controller(), logging_lvl=logging.DEBUG
    )

    arango_restore(con, "examples/data/fraud_dump")
    arango_restore(con, "examples/data/imdb_dump")

    # Create Fraud Detection Graph
    adbnx_adapter.db.delete_graph("fraud-detection", ignore_missing=True)
    adbnx_adapter.db.create_graph(
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


def arango_restore(con: Json, path_to_data: str) -> None:
    restore_prefix = "./assets/" if os.getenv("GITHUB_ACTIONS") else ""
    protocol = "http+ssl://" if "https://" in con["url"] else "tcp://"
    url = protocol + con["url"].partition("://")[-1]
    # A small hack to work around empty passwords
    password = f"--server.password {con['password']}" if con["password"] else ""

    subprocess.check_call(
        f'chmod -R 755 ./assets/arangorestore && {restore_prefix}arangorestore \
            -c none --server.endpoint {url} --server.database {con["dbName"]} \
                --server.username {con["username"]} {password} \
                    --input-directory "{PROJECT_DIR}/{path_to_data}"',
        cwd=f"{PROJECT_DIR}/tests",
        shell=True,
    )


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
