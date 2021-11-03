<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
# ArangoDB-Networkx Adapter

<center>
<img src="examples/assets/logos/networkx_logo.svg" width=50% >
</center>
<center>
<img src="examples/assets/logos/ArangoDB_logo.png" width=50% >
</center>

The ArangoDB-Networkx Adapter exports Graphs from ArangoDB, a multi-model Graph Database, into NetworkX, the swiss army knife for graph analysis with python, and vice-versa.

## About NetworkX

Networkx is a commonly used tool for analysis of network-data. If your analytics use cases require the use of all your graph data, for example, to summarize graph structure, or answer global path traversal queries, then using the ArangoDB Pregel API is recommended. If your analysis pertains to a subgraph, then you may be interested in getting the Networkx representation of the subgraph for one of the following reasons:

    1. An algorithm for your use case is available in Networkx.
    2. A library that you want to use for your use case works with Networkx Graphs as input.


(OUTDATED) Check the DGL folder for an implementation of a Networkx-Adapter for the Deep Graph Library.


##  Quickstart

(OUTDATED) To get started quickly you just use this setup free jupyter notebook: <a href="https://colab.research.google.com/github/arangoml/networkx-adapter/blob/master/examples/ArangoDB_NetworkxAdapter.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

First, run an arangodb instance via docker:
```
docker run -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb/arangodb:3.8.2
```

Then, in another directory, restore some sample data:
```
cd networkx-adapter

arangorestore -c none --server.username root --server.database _system --server.password rootpassword --default-replication-factor 3  --input-directory "data/fraud_dump" --include-system-collections true 
```

In a python virtual environment, install the dependencies:
```bash
pip install adbnx_adapter matplotlib
```

In a python file, write the following:
``` python
import networkx as nx
import matplotlib.pyplot as plt
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter

# Specify the connection to the ArangoDB Database
conn = {
    "dbName": "_system",
    "username": "root",
    "password": "rootpassword",
    "hostname": "localhost",
    "protocol": "http",
    "port": 8529,
}

# Create Adapter instance
ma = ArangoDB_Networkx_Adapter(conn)

# Specify attributes to be imported
attributes = {
    "vertexCollections": {
        "account": {"Balance", "account_type", "customer_id", "rank"},
        "customer": {"Name", "Sex", "Ssn", "rank"},
    },
    "edgeCollections": {
        "accountHolder": {"_from", "_to"},
        "transaction": {"_from", "_to"},
    },
}

# Export networkX graph using graph attributes
g = ma.create_networkx_graph(graph_name="FraudDetection", graph_attributes=attributes)

# Export networkX graph using arangodb collections
g_from_arangodb_collections = ma.create_networkx_graph_from_arangodb_collections(
    graph_name="fraud-detection",
    vertex_collections={"account", "bank", "branch", "Class", "customer"},
    edge_collections={"accountHolder", "Relationship", "transaction"},
)

# Export networkX graph using arangodb graph
g_from_arangodb_graph = ma.create_networkx_graph_from_arangodb_graph(
    graph_name="fraud-detection"
)

# You can also provide valid Python-Arango AQL query options to the command above, like such:
g_with_aql_query_options = ma.create_networkx_graph(
    graph_name="FraudDetection", graph_attributes=attributes, ttl=1000, stream=True
)

# Use networkX
nx.draw(g, with_labels=True)
plt.show()
print(g)

first_node, *middle_nodes, last_node = g.nodes(data=True)
print("\n-------- Sample Nodes --------")
print(first_node)
print(last_node)

first_edge, *middle_edges, last_edge = g.edges(data=True)
print("\n-------- Sample Edges --------")
print(first_edge)
print(last_edge)
```

##  Development & Testing

Create your virtual environment:
1. `cd networkx-adapter`
2. `python -m venv .venv`
3. `source .venv/bin/activate` (MacOS) or `.venv/scripts/activate` (Windows)
4. `cd adbnx_adapter`
5. `pip install -e . pytest`
6. `pytest -s`
    * If you see `ModuleNotFoundError`, try closing & relaunching your virtual environment with `deactivate` & repeating Step 3.
