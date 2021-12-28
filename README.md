# ArangoDB-Networkx Adapter
[![build](https://github.com/arangoml/networkx-adapter/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/arangoml/networkx-adapter/actions/workflows/build.yml)
[![CodeQL](https://github.com/arangoml/networkx-adapter/actions/workflows/analyze.yml/badge.svg?branch=master)](https://github.com/arangoml/networkx-adapter/actions/workflows/analyze.yml)
[![Coverage Status](https://coveralls.io/repos/github/arangoml/networkx-adapter/badge.svg?branch=master)](https://coveralls.io/github/arangoml/networkx-adapter)
[![Last commit](https://img.shields.io/github/last-commit/arangoml/networkx-adapter)](https://github.com/arangoml/networkx-adapter/commits/master)

[![PyPI version badge](https://img.shields.io/pypi/v/adbnx-adapter?color=3775A9&style=for-the-badge&logo=pypi&logoColor=FFD43B)](https://pypi.org/project/adbnx-adapter/)
[![Python versions badge](https://img.shields.io/pypi/pyversions/adbnx-adapter?color=3776AB&style=for-the-badge&logo=python&logoColor=FFD43B)](https://pypi.org/project/adbnx-adapter/)

[![License](https://img.shields.io/github/license/arangoml/networkx-adapter?color=9E2165&style=for-the-badge)](https://github.com/arangoml/networkx-adapter/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/static/v1?style=for-the-badge&label=code%20style&message=black&color=black)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=282661&label=Downloads&query=total_downloads&url=https://api.pepy.tech/api/projects/adbnx-adapter)](https://pepy.tech/project/adbnx-adapter)

<a href="https://www.arangodb.com/" rel="arangodb.com">![](https://raw.githubusercontent.com/arangoml/networkx-adapter/1.0.0/examples/assets/logos/ArangoDB_logo.png)</a>

<a href="https://networkx.org/" rel="networkx.org">![](https://raw.githubusercontent.com/arangoml/networkx-adapter/1.0.0/examples/assets/logos/networkx_logo.svg)</a>

The ArangoDB-Networkx Adapter exports Graphs from ArangoDB, a multi-model Graph Database, into NetworkX, the swiss army knife for graph analysis with python, and vice-versa.



## About NetworkX

Networkx is a commonly used tool for analysis of network-data. If your analytics use cases require the use of all your graph data, for example, to summarize graph structure, or answer global path traversal queries, then using the ArangoDB Pregel API is recommended. If your analysis pertains to a subgraph, then you may be interested in getting the Networkx representation of the subgraph for one of the following reasons:

    1. An algorithm for your use case is available in Networkx.
    2. A library that you want to use for your use case works with Networkx Graphs as input.

##  Quickstart

Get Started on Colab: <a href="https://colab.research.google.com/github/arangoml/networkx-adapter/blob/master/examples/ArangoDB_NetworkX_Adapter.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

```py
# Import the ArangoDB-NetworkX Adapter
from adbnx_adapter.adapter import ADBNX_Adapter

# Import a sample graph from NetworkX
from networkx import grid_2d_graph

# This is the connection information for your ArangoDB instance
# (Let's assume that the ArangoDB fraud-detection data dump is imported to this endpoint)
con = {
    "hostname": "localhost",
    "protocol": "http",
    "port": 8529,
    "username": "root",
    "password": "rootpassword",
    "dbName": "_system",
}

# This instantiates your ADBNX Adapter with your connection credentials
adbnx_adapter = ADBNX_Adapter(con)

# ArangoDB to NetworkX via Graph
nx_fraud_graph = adbnx_adapter.arangodb_graph_to_networkx("fraud-detection")

# ArangoDB to NetworkX via Collections
nx_fraud_graph_2 = adbnx_adapter.arangodb_collections_to_networkx(
        "fraud-detection", 
        {"account", "bank", "branch", "Class", "customer"}, # Specify vertex collections
        {"accountHolder", "Relationship", "transaction"} # Specify edge collections
)

# ArangoDB to NetworkX via Metagraph
metagraph = {
    "vertexCollections": {
        "account": {"Balance", "account_type", "customer_id", "rank"},
        "customer": {"Name", "rank"},
    },
    "edgeCollections": {
        "transaction": {"transaction_amt", "sender_bank_id", "receiver_bank_id"},
        "accountHolder": {},
    },
}
nx_fraud_graph_3 = adbnx_adapter.arangodb_to_networkx("fraud-detection", metagraph)

# NetworkX to ArangoDB
nx_grid_graph = grid_2d_graph(5, 5)
adb_grid_edge_definitions = [
    {
        "edge_collection": "to",
        "from_vertex_collections": ["Grid_Node"],
        "to_vertex_collections": ["Grid_Node"],
    }
]
adb_grid_graph = adbnx_adapter.networkx_to_arangodb("Grid", nx_grid_graph, adb_grid_edge_definitions)
```

##  Development & Testing

Prerequisite: `arangorestore` must be installed

1. `git clone https://github.com/arangoml/networkx-adapter.git`
2. `cd networkx-adapter`
3. `python -m venv .venv`
4. `source .venv/bin/activate` (MacOS) or `.venv/scripts/activate` (Windows)
5. `pip install -e .[dev]`
6. `pytest`