#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
"""
import json
import yaml
import os
from amlnx_adapter.arangoml_networkx_adapter import Networkx_Arango_Adapter
import networkx as nx
import numpy as np
import torch as th
import dgl
from arango import ArangoClient
from amlnx_adapter.dgl.custom_http_client import CustomHTTPClient


class DGL_Networkx_Arango_Adapter(Networkx_Arango_Adapter):
    
    def __init__(self, graph_desc_fp = "graph_descriptor.yaml", load_from_db = True):
        file_exists = os.path.exists(graph_desc_fp)
        if not file_exists:
            print("Graph descriptor file does not exist, please check and try again !")
        self.gdesc_file = graph_desc_fp
        self.cfg = self.get_conn_config()
        self.db = None
        self.emlg = None
        self.load_from_db = load_from_db
        
        
        return
    
    def create_networkx_graph(self):
        if self.load_from_db:
            self.set_db_connection()
            labels, graph = self.create_dgl_graph_from_db()
        else:
            labels, graph = self.create_dgl_graph_from_data_dump()
        
        return labels, graph
    
    def get_conn_config(self):
        #file_name = os.path.join(os.path.dirname(__file__), self.gdesc_file)
        with open(self.gdesc_file, "r") as file_descriptor:
            cfg = yaml.load(file_descriptor, Loader=yaml.FullLoader)
        return cfg
    

   
        
    def load_from_data_files(self):
        #load the edges
        edge_names = [*self.cfg['edge_data']]
        fgraph = {ename : nx.DiGraph() for ename in edge_names}
        rgraph = {ename : nx.DiGraph() for ename in edge_names}
        if 'data_dir' not in self.cfg:
            print("Loading data from a data files requires you to specify a data directory \
                  in the graph descriptor file")
            return
        data_dir = self.cfg['data_dir']
        if not os.path.exists(data_dir):
            print("Data directory is not valid, please check and try again!")
            
        labels = []
        for k,v in self.cfg['edge_data'].items():
            edge_file = v
            file_name = os.path.join(data_dir, edge_file)
            with open(file_name, 'r') as json_file:
                json_data = json.load(json_file)
            from_list = [doc['_from'] for doc in json_data]
            to_list = [doc['_to'] for doc in json_data]
            edge_list = [(doc['_from'], doc['_to']) for doc in json_data]
            rev_edge_list = [(doc['_to'], doc['_from']) for doc in json_data]
            fg = fgraph[k]
            rg = rgraph[k]
            fg.add_nodes_from(from_list, bipartite = 0 )
            fg.add_nodes_from(to_list, bipartite = 1 )
            fg.add_edges_from(edge_list)
            rg.add_nodes_from(to_list, bipartite = 0 )
            rg.add_nodes_from(from_list, bipartite = 1 )
            rg.add_edges_from(rev_edge_list)
        
        # set the properties by iterating vertex collections.
        vnames = [*self.cfg['vertex_data']]
        exclude_attr = self.cfg['exclude_attributes']['all']
        node_data = {v: list() for v in vnames}
        
        for vertex_name, data_file_name in self.cfg['vertex_data'].items():
            if vertex_name in self.cfg['exclude_attributes']:
                exclude_attr = exclude_attr + self.cfg['exclude_attributes'][vertex_name]
            file_name = os.path.join(data_dir, data_file_name)
            with open(file_name, 'r') as json_file:
                json_data = json.load(json_file)
            # iterate over the vertex data and set the properties in the associated graph
            for doc in json_data:
                updated_doc = {attrib: value for attrib, value\
                               in doc.items() if attrib not in exclude_attr}
                ndata = np.fromiter(updated_doc.values(), dtype = int)
                
                if vertex_name == 'incident':
                    labels.append(doc['reassigned'])
               
                #vdata = th.from_numpy(ndata)
                node_data[vertex_name].append(ndata)
                for ename, egraph in fgraph.items():
                    if vertex_name in ename:
                        egraph.nodes[doc["_id"]].update(updated_doc) 
                for ename, egraph in rgraph.items():
                    if vertex_name in ename:
                        egraph.nodes[doc["_id"]].update(updated_doc)
                        
        
                        
        return fgraph, rgraph, node_data, labels
        

    
    def create_dgl_graph_from_data_dump(self):
        fgraph, rgraph, node_data, labels = self.load_from_data_files()
        vnames = [*self.cfg['vertex_data']]
        edge_names = [*self.cfg['edge_data']]
        dict_desc = dict()
        for ename in edge_names:
            tokens = ename.split('-')
            rename = tokens[1] + '-' + tokens[0]
            fgk = ( tokens[0],  ename, tokens[1] )
            rgk = (tokens[1], rename, tokens[0])
            dict_desc[fgk] = fgraph[ename]
            dict_desc[rgk] = rgraph[ename]
        
        
        g = dgl.heterograph(dict_desc)
        
        for v in vnames:
            rndata = np.asarray(node_data[v])
            v_data = th.from_numpy(rndata)
            g.nodes[v].data['f'] = v_data
        
        return labels, g
    
    
    
    def create_dgl_graph_from_db(self):
        vnames = [*self.cfg['vertex_data']]
        edge_names = [*self.cfg['edge_data']]
        query = self.cfg['queries']['load_data']

        cursor = self.db.aql.execute(query)
        sgdata = {ename : nx.DiGraph() for ename in edge_names}
        rsgdata = {ename : nx.DiGraph() for ename in edge_names}
        labels = []
        exclude_attr = self.cfg['exclude_attributes']['all']
        node_data = {v: list() for v in vnames}
        for doc in cursor:
            labels.append(doc['reassigned'])
            # set up the forward and reverse graphs and set up the node attributes
            for ename in edge_names:
                etoks = ename.split(self.cfg['edge_sep'])
                from_vertex = etoks[0]
                to_vertex = etoks[1]
                node_id_from = doc[from_vertex]['node_id']
                node_id_to = doc[to_vertex]['node_id']
                ndata_from = doc[from_vertex]
                ndata_to = doc[to_vertex]
                #exclude the attributes we are note interested in
                ndata_from = {k: v for k, v in ndata_from.items() if k not in exclude_attr}
                if from_vertex in self.cfg['exclude_attributes']:
                    vertex_excl = self.cfg['exclude_attributes'][from_vertex]
                    ndata_from = {k: v for k, v in ndata_from.items() if k not in vertex_excl}
                ndata_to = {k: v for k, v in ndata_to.items() if k not in exclude_attr}
                if to_vertex in self.cfg['exclude_attributes']:
                    vertex_excl = self.cfg['exclude_attributes'][from_vertex]
                    ndata_to = {k: v for k, v in ndata_to.items() if k not in vertex_excl}
                
                sg = sgdata[ename]
                sg.add_node(node_id_from, bipartite = 0)
                sg.add_node(node_id_to, bipartite = 1)
                sg.add_edge(node_id_from, node_id_to)
                sg.nodes[node_id_from].update(ndata_from)
                sg.nodes[node_id_to].update(ndata_to)
                rsg = rsgdata[ename]
                rsg.add_node(node_id_from, bipartite = 1)
                rsg.add_node(node_id_to, bipartite = 0)
                rsg.add_edge(node_id_to, node_id_from)
                rsg.nodes[node_id_from].update(ndata_from)
                rsg.nodes[node_id_to].update(ndata_to)
            
            for vertex in vnames:
                ndata = doc[vertex]
                ndata = {k: v for k, v in ndata.items() if k not in exclude_attr}
                if vertex in self.cfg['exclude_attributes']:
                    vexcl = self.cfg['exclude_attributes'][vertex]
                    ndata = {k: v for k, v in ndata.items() if k not in vexcl}
                
                ndvalues = np.fromiter(ndata.values(), dtype = int)
                node_data[vertex].append(ndvalues)
        
        dict_desc = dict()
        for ename in edge_names:
            tokens = ename.split(self.cfg['edge_sep'])
            rename = tokens[1] + self.cfg['edge_sep'] + tokens[0]
            fgk = ( tokens[0],  ename, tokens[1] )
            rgk = (tokens[1], rename, tokens[0])
            dict_desc[fgk] = sgdata[ename]
            dict_desc[rgk] = rsgdata[ename]

        g = dgl.heterograph(dict_desc)
        print("Preparing Node feature data... ")

        #breakpoint()
        for v in vnames:
            rndata = np.asarray(node_data[v], dtype = int)
            v_data = th.from_numpy(rndata)
            g.nodes[v].data['f'] = v_data

        print("Done setting feature data in dgl graph!")



        return labels, g
    
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
        self.emlg = self.db.graph('ITSMg')
        
        return
    


         
    

