import pytest
import subprocess
from pathlib import Path
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter

conn = {
    "dbName": "_system",
    "username": "root",
    "password": "rootpassword",
    "hostname": "localhost",
    "protocol": "http",
    "port": 8529,
}

adbnx_adapter = ArangoDB_Networkx_Adapter(conn)

ROOT_DIR = Path(__file__).parent.parent.parent

def docker_compose():
    proc = subprocess.Popen(
        'docker-compose up -d',
        stdout=subprocess.PIPE,
        cwd=f"{ROOT_DIR}/adbnx_adapter/tests",
        shell=True
    )
    proc.wait()

def arango_restore(path_to_data):
    proc = subprocess.Popen(
        f'arangorestore -c none --server.username root --server.database _system --server.password rootpassword --default-replication-factor 3  --input-directory "{path_to_data}" --include-system-collections true',
        cwd=f"{ROOT_DIR}/examples/data/",
        shell=True
    )
    proc.wait()

def shut_down():
    proc = subprocess.Popen(
        'docker rm --force adbnx_adapter_arangodb',
        shell=True
    )
    proc.wait()

def pytest_sessionstart(session):
    docker_compose()


# def pytest_sessionfinish(session, exitstatus):
#     shut_down()