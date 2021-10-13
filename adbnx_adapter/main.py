import networkx as nx
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter

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
ma = ArangoDB_Networkx_Adapter(conn=con)

# Specify attributes to be imported
fraud_detection_attributes = {
    "vertexCollections": {
        "account": {"Balance", "account_type", "customer_id", "rank"},
        "bank": {"Country", "Id", "bank_id", "bank_name"},
        "branch": {"City", "Country", "Id", "bank_id", "branch_id", "branch_name"},
        "Class": {"concrete", "label", "name"},
        "customer": {"Name", "Sex", "Ssn", "rank"},
    },
    "edgeCollections": {
        "accountHolder": {"_from", "_to"},
        "Relationship": {"_from", "_to", "label", "name", "relationshipType"},
        "transaction": {"_from", "_to"},
    },
}
# include system collections in arangorestore
# Export networkX graph

g = ma.create_networkx_graph(
    graph_name="fraud-detection", graph_attributes=fraud_detection_attributes
)

# g = ma.create_networkx_graph_from_graph(
#     graph_name="fraud-detection", ttl=11
# )

# g = ma.create_networkx_graph_from_collections(
#     graph_name="fraud-detection",
#     vertex_collections={"account", "bank", "branch", "Class", "customer"},
#     edge_collections={"accountHolder", "Relationship", "transaction"},
# )

# You can also provide valid Python-Arango AQL query options to the command above, like such:
# g = ma.create_networkx_graph(graph_name = 'FraudDetection',  graph_attributes = attributes, ttl=1000, stream=True)

# Use networkX
nx.draw(g, with_labels=True)
print(g)

