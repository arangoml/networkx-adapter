import json
import networkx as nx
from adbnx_adapter.imdb_arangoDB_networkx_adapter import IMDBArangoDB_Networkx_Adapter

# Specify the connection to the ArangoDB Database
con = {
    "dbName": "_system",
    "username": "root",
    "password": "rootpassword",
    "hostname": "localhost",
    "protocol": "http",
    "port": 8529,
}

# Create Adapter instance
ma = IMDBArangoDB_Networkx_Adapter(conn=con)

# Specify attributes to be imported
imdb_attributes = {
    "vertexCollections": {"Users": {}, "Movies": {}},
    "edgeCollections": {"Ratings": {"_from", "_to", "ratings"}},
}

# include system collections in arangorestore
g = ma.create_networkx_graph(graph_name="IMDBGraph", graph_attributes=imdb_attributes)

# You can also provide valid Python-Arango AQL query options to the command above, like such:
# g = ma.create_networkx_graph(graph_name = 'FraudDetection',  graph_attributes = attributes, ttl=1000, stream=True)

# Use networkX
# nx.draw(g, with_labels=True)
print(g)
first, *middle, last = g.nodes(data=True)
print(json.dumps(first, indent=2))
print(json.dumps(last, indent=2))
