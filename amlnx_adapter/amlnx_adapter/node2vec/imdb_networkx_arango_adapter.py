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
from amlnx_adapter.graph_params import GraphParams


class IMDB_Networkx_Adapter(Networkx_Arango_Adapter):
    
    def __init__(self, graph_config = None, graph_desc_save_fp = "imdb_graph_descriptor.yaml"):
        
        self.cfg = None
        if graph_config is None:
            self.gdesc_file = graph_desc_save_fp
            self.cfg = self.read_data()
        else:
            valid_cfg = self.is_valid_config(graph_config)
            if not valid_cfg:
                print("Invalid config information provided, please check it and try again!")
                return
            else:
                self.cfg = None
                self.create_graph_config(graph_config)
                self.gdesc_file = graph_desc_save_fp
                self.save_graph_config()
            self.db = None
            self.emlg = None
            self.nxg = None
        
        
        
        return
    
    def read_data(self):
        file_name = os.path.join(os.path.dirname(__file__),
                                 self.gdesc_file)
        with open(file_name, "r") as file_descriptor:
            cfg = yaml.load(file_descriptor, Loader=yaml.FullLoader)
        return cfg
    
    def save_graph_config(self):
        file_name = os.path.join(os.path.dirname(__file__),
                                 self.gdesc_file)
        with open(file_name, "w") as file_descriptor:
            cfg = yaml.dump(self.cfg, file_descriptor)
        return cfg
    
    def create_graph_config(self, graph_params):
        
        gp = GraphParams()
        self.cfg = {
            'arangodb': {},
            'queries': {}
        }
        for key, value in graph_params.items():
            if key == gp.DB_DATA_QUERY:
                self.cfg['queries'][key] = value
            else:
                self.cfg['arangodb'][key] = value
        return  
    
    def is_valid_config(self, graph_config):
        gp = GraphParams()
        valid_config = True
        
        if not gp.DB_SERVICE_HOST in graph_config:
            print("managed service host is missing in supplied config")
            valid_config = False
        if not gp.DB_NAME in graph_config:
            print("DB name is missing in supplied config")
            valid_config = False
        if not gp.DB_SERVICE_PORT in graph_config:
            print("managed service port is missing in supplied config, using 8529")
            graph_config[gp.DB_SERVICE_PORT] = 8529
        if not gp.DB_USER_NAME in graph_config:
            print("User name is missing in supplied config")
            valid_config = False
        if not gp.DB_PASSWORD in graph_config:
            print("User password is not in supplied config")
            valid_config = False
        if not gp.DB_CONN_PROTOCOL in graph_config:
            print("conn protocol is not in supplied config, using https")
            graph_config[gp.DB_CONN_PROTOCOL] = 'https'
        if not gp.DB_DATA_QUERY in graph_config:
            print("query to load data is not provided")
            valid_config = False

        return valid_config
    
    def create_networkx_graph(self):
        self.set_db_connection()
        query = self.cfg['queries']['load_data']
                #get vertex names


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
    


         
    

