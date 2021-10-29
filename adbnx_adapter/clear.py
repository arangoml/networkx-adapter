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

ma = ArangoDB_Networkx_Adapter(conn=con)

col_to_clear = {"to", "Node", "Team", "Played"}

for col in col_to_clear:
    ma.db.delete_collection(col) if ma.db.has_collection(col) else None


graph_to_clear = {"Grid", "Football"}
for g in graph_to_clear:
    ma.db.delete_graph(g) if ma.db.has_graph(g) else None
