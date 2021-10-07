# ArangoDB-Networkx Adapter

<center>
<img src="examples/assets/logos/networkx_logo.svg" width=50% >
</center>
<center>
<img src="examples/assets/logos/ArangoDB_logo.png" width=50% >
</center>

The ArangoDB-Networkx Adapter export Graphs from ArangoDB, a multi-model Graph Database into NetworkX, the swiss army knife for graph analysis with python.


##  Quickstart

To get started quickly you just use this setup free jupyter notebook: <a href="https://colab.research.google.com/github/arangoml/networkx-adapter/blob/master/examples/ArangoDB_NetworkxAdapter.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

To get started in custom code:
```bash
pip install adbnx_adapter
```

``` python
import networkx as nx
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter

# Specify the connection to the ArangoDB Database
con = {'dbName': 'YOURDBNAME',
 'username': 'YOURUSERNAME',
 'password': 'YOURPASSOWRD',
 'hostname': 'instance.arangodb.cloud',
 'port': 8529}

# Create Adapter instance
ma = ArangoDB_Networkx_Adapter(conn = con)

# Specify attributes to be imported
attributes = { 'vertexCollections':
                                  {'account': {'Balance', 'account_type', 'customer_id', 'rank'}},\
                               'edgeCollections' :
                                  {'accountHolder': {'_from', '_to'},\
                                   'transaction': {'_from', '_to'}}}

# Export networkX graph                                  
g = ma.create_networkx_graph(graph_name = 'FraudDetection',  graph_attributes = attributes)

# You can also provide valid Python-Arango AQL query options to the command above, like such:
# g = ma.create_networkx_graph(graph_name = 'FraudDetection',  graph_attributes = attributes, ttl=1000, stream=True)

# Use networkX
nx.draw(g, with_labels=True)
```

# Introduction

Networkx is a commonly used tool for analysis of network-data. If your analytics use cases require the use of all your graph data, for example, to summarize graph structure, or answer global path traversal queries, then using the ArangoDB Pregel API is recommended. If your analysis pertains to a subgraph, then you may be interested in getting the Networkx representation of the subgraph for one of the following reasons:

    1. An algorithm for your use case is available in Networkx.
    2. A library that you want to use for your use case works with Networkx Graphs as input.


Check the DGL folder for an implementation of a Networkx-Adapter for the Deep Graph Library.
