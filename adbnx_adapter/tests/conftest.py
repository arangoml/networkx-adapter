import pytest
import subprocess
from pathlib import Path
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter

ROOT_DIR = Path(__file__).parent.parent.parent


def docker_compose():
    proc = subprocess.Popen(
        "docker-compose up -d",
        stdout=subprocess.PIPE,
        cwd=f"{ROOT_DIR}/adbnx_adapter/tests",
        shell=True,
    )
    proc.wait()


def arango_restore(path_to_data):
    proc = subprocess.Popen(
        f'arangorestore -c none --server.username root --server.database _system --server.password rootpassword --default-replication-factor 3  --input-directory "{path_to_data}" --include-system-collections true',
        cwd=f"{ROOT_DIR}/examples/data/",
        shell=True,
    )
    proc.wait()


def shut_down():
    proc = subprocess.Popen("docker rm --force adbnx_adapter_arangodb", shell=True)
    proc.wait()


def pytest_sessionstart():
    docker_compose()
    arango_restore("fraud_dump")
    arango_restore("imdb_dump")


def pytest_sessionfinish(session, exitstatus):
    for col in adbnx_adapter.db.collections():
        if col["system"] is False:
            adbnx_adapter.db.delete_collection(col["name"])

    for g in adbnx_adapter.db.graphs():
        adbnx_adapter.db.delete_graph(g["name"])

    shut_down()


class IMDB_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    # We re-define how vertex insertion should be treated, specifically for the IMDB dataset.
    def _insert_networkx_vertex(self, vertex: dict, collection: str, attributes: set):
        self.nx_node_map[vertex["_id"]] = {
            "_id": vertex["_id"],
            "collection": collection,
        }
        bip_key = 0 if collection == "Users" else 1
        self.nx_graph.add_node(vertex["_id"], **vertex, bipartite=bip_key)


class Basic_Grid_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def _identify_nx_node(self, id, node: dict) -> str:
        return "Node"  # Only one node collection in this dataset

    def _keyify_nx_node(self, id, node, collection) -> str:
        return self._tuple_to_arangodb_key_helper(id)

    def _identify_nx_edge(self, from_node, to_node, edge: dict) -> str:
        from_collection = self.adb_node_map.get(from_node)["collection"]
        to_collection = self.adb_node_map.get(to_node)["collection"]
        if from_collection == to_collection == "Node":
            return "to"

        return "Unknown_Edge"

    def _insert_networkx_vertex(self, vertex: dict, collection: str, attributes: set):
        nx_id = tuple(
            int(n)
            for n in tuple(
                vertex["_key"],
            )
        )
        self.nx_node_map[vertex["_id"]] = {"_id": nx_id, "collection": collection}
        self.nx_graph.add_node(nx_id, **vertex)


class Football_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def _identify_nx_node(self, id: str, node: dict) -> str:
        return "Team"  # Only one node collection in this dataset

    def _keyify_nx_node(self, id, node, collection) -> str:
        return self._string_to_arangodb_key_helper(id)

    def _identify_nx_edge(self, from_node, to_node, edge: dict) -> str:
        from_collection = self.adb_node_map.get(from_node)["collection"]
        to_collection = self.adb_node_map.get(to_node)["collection"]
        if from_collection == to_collection == "Team":
            return "Played"

        return "Unknown_Edge"


conn = {
    "dbName": "_system",
    "username": "root",
    "password": "rootpassword",
    "hostname": "localhost",
    "protocol": "http",
    "port": 8529,
}

adbnx_adapter = ArangoDB_Networkx_Adapter(conn)
imdb_adbnx_adapter = IMDB_ArangoDB_Networkx_Adapter(conn)
grid_adbnx_adapter = Basic_Grid_ArangoDB_Networkx_Adapter(conn)
football_adbnx_adapter = Football_ArangoDB_Networkx_Adapter(conn)
