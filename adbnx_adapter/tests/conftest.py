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


def clear():
    for col in adbnx_adapter.db.collections():
        if col["system"] is False:
            adbnx_adapter.db.delete_collection(col["name"])

    for g in adbnx_adapter.db.graphs():
        adbnx_adapter.db.delete_graph(g["name"])


def pytest_sessionstart():
    docker_compose()
    clear()
    arango_restore("fraud_dump")
    arango_restore("imdb_dump")


def pytest_sessionfinish(session, exitstatus):
    clear()
    shut_down()


class IMDB_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    # We re-define how vertex pre-insertion should be treated, specifically for the IMDB dataset.
    def _prepare_nx_node(self, node: dict, col: str, atribs: set):
        node["bipartite"] = 0 if col == "Users" else 1  # The new change
        return node["_id"]  # This is standard

    # We're not interested in re-defining pre-insertion handling for edges, so we leave it be
    # def _prepare_nx_edge(self, edge: dict, col: str, atribs: set):
    #     return super()._prepare_nx_edge(edge, col, atribs)


class Basic_Grid_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def _identify_nx_node(self, id, node: dict) -> str:
        return "Node"  # Only one node collection in this dataset

    def _keyify_nx_node(self, id, node, col) -> str:
        return self._tuple_to_arangodb_key_helper(id)

    def _identify_nx_edge(self, from_node, to_node, edge: dict) -> str:
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
