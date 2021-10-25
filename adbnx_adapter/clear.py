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

to_clear = {
    "account_new",
    "bank_new",
    "branch_new",
    "Class_new",
    "customer_new",
    "accountHolder_new",
    "Relationship_new",
    "transaction_new",
}

ma.clear(to_clear)
