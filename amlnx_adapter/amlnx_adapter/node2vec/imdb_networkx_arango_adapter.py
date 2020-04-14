#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
"""

import yaml
import os
from amlnx_adapter.arangoml_networkx_adapter import Networkx_Arango_Adapter
import networkx as nx
from arango import ArangoClient
from amlnx_adapter.custom_http_client import CustomHTTPClient


class IMDB_Networkx_Arango_Adapter(Networkx_Arango_Adapter):
    
    def __init__(self, graph_desc_fp = "graph_descriptor.yaml", load_from_db = True):
        file_exists = os.path.exists(graph_desc_fp)
        if not file_exists:
            print("Graph descriptor file does not exist, please check and try again !")
        self.gdesc_file = graph_desc_fp
        self.cfg = self.get_conn_config()
        self.db = None
        self.emlg = None
        self.load_from_db = load_from_db
        self.nxg = None
        
        
        return
    
    def create_networkx_graph(self):
        self.set_db_connection()
        query = self.cfg['queries']['load_data']

        cursor = self.db.aql.execute(query)
        #sgdata = {ename : nx.DiGraph() for ename in edge_names}
        g = nx.DiGraph()
        for doc in cursor:

            g.add_node(doc['user'], bipartite = 0)
            g.add_node(doc['movie'], bipartite = 1)
            g.add_edge(doc['user'], doc['movie'], rating = doc['rating'] )
            # set up the forward and reverse graphs and set up the node attributes
            
        self.nxg = g
        return self.nxg
    
    def get_conn_config(self):
        #file_name = os.path.join(os.path.dirname(__file__), self.gdesc_file)
        with open(self.gdesc_file, "r") as file_descriptor:
            cfg = yaml.load(file_descriptor, Loader=yaml.FullLoader)
        return cfg

    
    def set_db_connection(self):
        db_conn_protocol = self.cfg['arangodb']['conn_protocol']
        db_srv_host = self.cfg['arangodb']['DB_service_host']
        db_srv_port = self.cfg['arangodb']['DB_service_port']

        
        
        host_connection = db_conn_protocol + "://" + db_srv_host + ":" + str(
            db_srv_port)
        ms_user_name = self.cfg['arangodb']['username']
        ms_password =  self.cfg['arangodb']['password']
        ms_dbName = self.cfg['arangodb']['dbName']
        print("Host Connection: %s " %(host_connection))
        client = ArangoClient(hosts= host_connection,\
                              http_client=CustomHTTPClient(username = ms_user_name,\
                                                           password = ms_password))
        

        db = client.db(ms_dbName, ms_user_name, ms_password)

        self.db = db
        self.emlg = self.db.graph('IMDBGraph')
        
        return
    


         
    

