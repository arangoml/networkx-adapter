import json
import networkx as nx
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter
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
ma = ArangoDB_Networkx_Adapter(conn=con)
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

# ma = IMDBArangoDB_Networkx_Adapter(conn=con)
# imdb_attributes = {
#     "vertexCollections": {"Users": {}, "Movies": {}},
#     "edgeCollections": {"Ratings": {"_from", "_to", "ratings"}},
# }

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

# g = ma.create_networkx_graph(graph_name="IMDBGraph", graph_attributes=imdb_attributes)


#nx.draw(g, with_labels=True)

first_node, *middle_nodes, last_node = g.nodes(data=True)
print("\n-------- Sample Nodes --------")
print(json.dumps(first_node, indent=2))
print(json.dumps(last_node, indent=2))

first_edge, *middle_edges, last_edge = g.edges(data=True)
print("\n-------- Sample Edges --------")
print(json.dumps(first_edge, indent=2))
print(json.dumps(last_edge, indent=2))

print(g)