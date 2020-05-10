#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 15:43:03 2020

@author: admin2
"""

from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter

def test_conn():
    
    con = {'dbName': 'TUTol8ui4zxzp9bapncps99rd',\
 'username': 'TUTk2ykuy4dgrpafx6m0wrk8d',\
 'password': 'TUTmzj9wvl6foy8t7nmo7pxj',\
 'hostname': '5904e8d8a65f.arangodb.cloud',\
 'port': 8529}
    ma = ArangoDB_Networkx_Adapter(conn = con)
    fraud_detection_attributes = { 'vertexCollections': {'account': {'Balance', 'account_type', 'customer_id', 'rank'},\
       'bank': {'Country', 'Id', 'bank_id', 'bank_name'},\
       'branch':{'City', 'Country', 'Id', 'bank_id', 'branch_id', 'branch_name'},\
       'Class':{'concrete', 'label', 'name'},\
       'customer': {'Name', 'Sex', 'Ssn', 'rank'}},\
                              'edgeCollections' : {'accountHolder': {'_from', '_to'},\
       'Relationship': {'_from', '_to', 'label', 'name', 'relationshipType'},\
       'transaction': {'_from', '_to'}}}

    g = ma.create_networkx_graph(graph_name = 'FraudDetection',  graph_attributes =   fraud_detection_attributes)
    
    return g