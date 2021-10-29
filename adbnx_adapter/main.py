from dgl._deprecate.graph import DGLGraph
from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter
# from adbnx_adapter.dgl_arangoDB_networkx_adapter import DGLArangoDB_Networkx_Adapter # (removed for now)
import matplotlib.pyplot as plt
import dgl
import networkx as nx

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
# dgl_ma = DGLArangoDB_Networkx_Adapter(con) # (removed for now)


class IMDB_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    # We re-define how vertex insertion should be treated, specifically for the IMDB dataset.
    def _insert_nx_vertex(self, vertex: dict, collection: str, attributes: set):
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
# nx_g = ma.create_networkx_graph(
#     graph_name="fraud-detection", graph_attributes=fraud_detection_attributes
# )

# nx_g = ma.create_networkx_graph_from_arangodb_collections(
#     graph_name="fraud-detection",
#     vertex_collections={"account", "bank", "branch", "Class", "customer"},
#     edge_collections={"accountHolder", "Relationship", "transaction"},
# )

# nx_g = ma.create_networkx_graph_from_arangodb_graph(graph_name="fraud-detection")

# edge_definitions = [
#     {
#         "edge_collection": "accountHolder_nx",
#         "from_vertex_collections": ["customer_nx"],
#         "to_vertex_collections": ["account_nx"],
#     },
#     {
#         "edge_collection": "transaction_nx",
#         "from_vertex_collections": ["account_nx"],
#         "to_vertex_collections": ["account_nx"],
#     },
# ]

# arango_g = ma.create_arangodb_graph(
#     "Fraud-Detection-Nx", nx_g, edge_definitions, keyify_edges=True
# )

# ----------------------------------- IMDB -----------------------------------
# nx_g = imdb_ma.create_networkx_graph(graph_name="IMDBGraph", graph_attributes=imdb_attributes)

# ----------------------------------- DGL -----------------------------------
# nx_g = ma.create_networkx_graph(
#     graph_name="fraud-detection", graph_attributes=fraud_detection_attributes
# )
# dgl_g : DGLGraph = dgl.from_networkx(nx_g)

# --------------------------------- DGL OLD -----------------------------------
# nx_g, labels = dgl_ma.create_dgl_graph( # (removed for now)
#     graph_name='dgl_maraph',  graph_attributes=itsm_attributes
# )


# nx.draw(nx_g, with_labels=True)
# plt.show()
# print(f"\n{nx_g}")


# first_node, *middle_nodes, last_node = nx_g.nodes(data=True)
# print("\n-------- Sample Nodes --------")
# print(first_node)
# print(last_node)

# first_edge, *middle_edges, last_edge = nx_g.edges(data=True)
# print("\n-------- Sample Edges --------")
# print(first_edge)
# print(last_edge)

# G = nx.grid_2d_graph(5, 5)  # 5x5 grid
# # write edgelist to grid.edgelist
# nx.write_edgelist(G, path="grid.edgelist", delimiter=":")
# # read edgelist from grid.edgelist
# H = nx.read_edgelist(path="grid.edgelist", delimiter=":")

# print(G)

# edge_definitions = [
#     {
#         "edge_collection": "to",
#         "from_vertex_collections": ["Node"],
#         "to_vertex_collections": ["Node"],
#     }
# ]

# class Basic_Grid_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
#     def _identify_nx_node(self, id: str, node: dict) -> str:
#         return "Node"  # Only one node collection in this dataset

#     def _keyify_nx_node(self, id, node, collection) -> str:
#         return self._tuple_to_arangodb_key_helper(id)

#     def _identify_nx_edge(self, id_map: dict, from_node, to_node, edge: dict) -> str:
#         from_collection = id_map.get(from_node)["collection"]
#         to_collection = id_map.get(to_node)["collection"]
#         if (from_collection == to_collection == "Node"):
#             return "to"
#         else:
#             return "Unknown_Edge"


# basic_grid_ma = Basic_Grid_ArangoDB_Networkx_Adapter(conn=con)
# basic_grid_ma.create_arangodb_graph("Grid", G, edge_definitions)


# try:  # Python 3.x
#     import urllib.request as urllib
# except ImportError:  # Python 2.x
#     import urllib
# import io
# import zipfile

# import matplotlib.pyplot as plt
# import networkx as nx

# url = "http://www-personal.umich.edu/~mejn/netdata/football.zip"

# sock = urllib.urlopen(url)  # open URL
# s = io.BytesIO(sock.read())  # read into BytesIO "file"
# sock.close()

# zf = zipfile.ZipFile(s)  # zipfile object
# txt = zf.read("football.txt").decode()  # read info file
# gml = zf.read("football.gml").decode()  # read gml data
# # throw away bogus first line with # from mejn files
# gml = gml.split("\n")[1:]
# G = nx.parse_gml(gml)  # parse gml data

# options = {
#     "node_color": "black",
#     "node_size": 50,
#     "linewidths": 0,
#     "width": 0.1,
# }
# # nx.draw(G, **options)
# # plt.show()

# print(G)

# edge_definitions = [
#     {
#         "edge_collection": "Played",
#         "from_vertex_collections": ["Team"],
#         "to_vertex_collections": ["Team"],
#     }
# ]


# class Football_ArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
#     def _identify_nx_node(self, id: str, node: dict) -> str:
#         if "value" in node:
#             return "Team"  # Only one node collection in this dataset
#         else:
#             return "Unknown"

#     def _keyify_nx_node(self, id, node, collection) -> str:
#         return self._string_to_arangodb_key_helper(id)

#     def _identify_nx_edge(self, id_map: dict, from_node, to_node, edge: dict) -> str:
#         from_collection = id_map.get(from_node)["collection"]
#         to_collection = id_map.get(to_node)["collection"]
#         if from_collection == to_collection == "Team":
#             return "Played"
#         else:
#             return "Unknown_Edge"


# football_ma = Football_ArangoDB_Networkx_Adapter(conn=con)
# football_ma.create_arangodb_graph("Football", G, edge_definitions)
