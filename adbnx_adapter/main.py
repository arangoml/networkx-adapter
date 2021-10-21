import json
import networkx as nx
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter
from adbnx_adapter.dgl_arangoDB_networkx_adapter import DGLArangoDB_Networkx_Adapter
import matplotlib.pyplot as plt

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
dgl_ma = DGLArangoDB_Networkx_Adapter(con)

class IMDB_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    # We re-define how vertex insertion should be treated, specifically for the IMDB dataset.
    def insert_vertex(self, vertex: dict, collection: str, attributes: set):
        bip_key = 0 if collection == "Users" else 1
        self.nx_graph.add_node(vertex["_id"], attr_dict=vertex, bipartite=bip_key)

imdb_ma = IMDB_ArangoDB_Networkx_Adapter(conn=con)

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

imdb_attributes = {
    "vertexCollections": {"Users": {}, "Movies": {}},
    "edgeCollections": {"Ratings": {"_from", "_to", "ratings"}},
}

vcols = {
    "incident": {
        "D_sys_mod_count",
        "D_sys_mod_count",
        "D_reopen_count",
        "urgency",
        "incident_state",
        "u_symptom",
        "impact",
        "contact_type",
        "u_priority_confirmation",
        "cmdb_ci",
        "rfc",
        "problem_id",
        "caused_by",
        "location",
        "knowledge",
        "resolved_by",
        "subcategory",
        "active",
        "category",
        "priority",
        "reassigned",
        "node_id",
    },
    "support_org": {"assigned_to", "assignment_group", "node_id"},
    "customer": {"opened_by", "node_id"},
    "vendor": {"vendor", "node_id"},
}
ecols = {
    "incident_support_org": {"_from", "_to"},
    "incident_customer": {"_from", "_to"},
    "incident_vendor": {"_from", "_to"},
}

itsm_attributes = {"vertexCollections": vcols, "edgeCollections": ecols}

# ----------------------------------- Fraud Detection -----------------------------------
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

# ----------------------------------- IMDB -----------------------------------
# g = imdb_ma.create_networkx_graph(graph_name="IMDBGraph", graph_attributes=imdb_attributes)

# ----------------------------------- DGL -----------------------------------
# g = dgl_ma.create_dgl_graph(
#     graph_name='dgl_maraph',  graph_attributes=itsm_attributes
# )

# --------------------------------- DGL OLD -----------------------------------
# g, labels = dgl_ma.create_dgl_graph(
#     graph_name='dgl_maraph',  graph_attributes=itsm_attributes
# )


# nx.draw(g, with_labels=True)
print(f"\n{g}")

first_node, *middle_nodes, last_node = g.nodes(data=True)
print("\n-------- Sample Nodes --------")
print(first_node)
print(last_node)

first_edge, *middle_edges, last_edge = g.edges(data=True)
print("\n-------- Sample Edges --------")
print(first_edge)
print(last_edge)