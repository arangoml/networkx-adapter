#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 26 09:13:00 2019

@author: Rajiv Sambasivan
"""

import pandas as pd
from arango import ArangoClient
import time
import traceback
import uuid
from collections import OrderedDict



class ITSM_Dataloader:

    def __init__(self, conn, input_file = "data/pp_recoded_incident_event_log.csv",\
                 create_db = True, frac = 1.0):
        self.emlg = None
        self.db = None
        self.labels = list()
        self.vertex_list = None
        self.edge_dict = {}
        self.feature_dict = {}
        self.feature_data = None
        self.setup_schema()
        self.sampling_frac = frac
        self.replication_factor = None
        self.batch_vert_dict = None
        self.batch_edge_dict = None
        
        if self.is_valid_conn(conn):
            url = conn["hostname"]
            user_name = conn["username"]
            password = conn["password"]
            dbName = conn["dbName"]
            if 'port' in conn:
                port = str(conn['port'])
            else:
                port = '8529'
            if 'protocol' in conn:
                protocol = conn['protocol']
            else:
                protocol = "https"
            con_str = protocol + "://" + url + ":" + port
            client = ArangoClient(hosts=con_str)
            self.db = client.db(dbName, user_name, password)
        else:
            print(
                "The connection information you supplied is invalid, please check and try again!")

        
        if create_db:
            self.input_file = input_file
            self.create_graph()
            
            self.load_data()


        return
    
    def is_valid_conn(self, conn):
        valid_con_info = True

        if not "hostname" in conn:
            print("hostname is missing in connection")
        if not "username" in conn:
            print("Username is missing in connection")
            valid_con_info = False
        if not "password" in conn:
            print("Password is missing in connection")
            valid_con_info = False
        if not "dbName" in conn:
            print("Database is missing in connection")
            valid_con_info = False

        return valid_con_info


    def setup_schema(self):
        self.vertex_list = ['incident', 'support_org', 'customer', 'vendor']

        self.edge_dict = {'incident_support_org': {'from': 'incident', 'to': 'support_org'},\
                          'incident_customer': {'from': 'incident', 'to': 'customer'},\
                          'incident_vendor': {'from': 'incident', 'to': 'vendor'}}
        

        self.feature_dict['support_org'] = ['assignment_group', 'assigned_to']
        self.feature_dict['customer'] = ['opened_by']
        self.feature_dict['vendor'] = ['vendor']
        self.feature_data = {v : OrderedDict() for v in self.vertex_list}

        self.feature_dict['incident'] = ['D_sys_mod_count', 'D_reopen_count',\
'urgency','incident_state', 'u_symptom', 'impact', 'contact_type',\
                          'u_priority_confirmation', 'cmdb_ci', 'rfc',  'problem_id',\
                          'caused_by', 'location', 'knowledge', 'resolved_by', 'subcategory',\
                          'active', 'category', 'priority', 'reassigned']

        return

    
    def create_graph(self):
        self.emlg = self.db.create_graph('ITSMg')
    


        self.create_graph_vertices()
        self.create_graph_edges()
        return

    def create_graph_edges(self):

        for edge in self.edge_dict:
            src_vertex = self.edge_dict[edge]['from']
            dest_vertex = self.edge_dict[edge]['to']
            if not self.emlg.has_edge_definition(edge):
                self.db.create_collection(edge, edge = True,\
                                          replication_factor = self.replication_factor)
                self.emlg.create_edge_definition(edge_collection = edge,\
                                                      from_vertex_collections=[src_vertex],\
                                                      to_vertex_collections=[dest_vertex] )

        return

    def create_graph_vertices(self):
        for v in self.vertex_list:
            if not self.emlg.has_vertex_collection(v):
                self.db.create_collection(v, self.replication_factor)
                self.emlg.create_vertex_collection(v)
        return



    def id_sequence(self, vertex):
        id_dict = {v: 0 for v in self.vertex_list}
        while True:
            yield id_dict[vertex]
        id_dict[vertex] += 1


    def do_inserts(self):
        for v in self.vertex_list:
            batch_docs = self.batch_vert_dict[v]
            self.db.collection(v).insert_many(batch_docs)
            self.batch_vert_dict[v] = list()
        edge_names = [*self.edge_dict]
        
        for ename in edge_names:
            batch_edge_docs = self.batch_edge_dict[ename]
            self.db.collection(ename).insert_many(batch_edge_docs)
            self.batch_edge_dict[ename] = list()
        
        return
        

    
    def load_data(self):
        t0 = time.time()
        df = pd.read_csv(self.input_file)
        df = df.sample(frac = self.sampling_frac)
        num_rows = df.shape[0] - 1
        print("A dataset with %d rows is being used for this run" % (num_rows) )
        df = df.reset_index()

        node_val_ids = {v: dict() for v in self.vertex_list}
        vertex_colls = {v: self.emlg.vertex_collection(v) for v in self.vertex_list}
        edge_names = [*self.edge_dict]
        edge_colls = {ename: self.emlg.edge_collection(ename) for ename in edge_names}
        row_vertex_map = {'incident': 'number', 'support_org': 'assignment_group',\
                          'customer': 'opened_by', 'vendor': 'vendor'}
        batch_size = 500
        self.batch_vert_dict = {v : list() for v in self.vertex_list}
        self.batch_edge_dict = {ename: list() for ename in edge_names}
        batch_count = 0
        for row_index, row in df.iterrows():
            try:
                if row_index % 500 == 0:
                    print("Processing row: " + str(row_index))
                # insert the vertices
                record_vertex_keys = dict()
                
                for v in self.vertex_list:

                    the_vertex = dict()
                    row_val = row[row_vertex_map[v]]
                    #if not row_val in node_val_ids[v]:
                    the_vertex['node_id'] = str(uuid.uuid4().int >> 64)
                    the_vertex['_key'] = v.upper() + "-" + the_vertex['node_id']
                    node_val_ids[v][row_val] = the_vertex['_key']

                    self.load_vertex_attributes(row, the_vertex, v )
                    self.batch_vert_dict[v].append(the_vertex)
                    record_vertex_keys[v] = node_val_ids[v][row_val]
            

                #insert the edges
            
                for ename in edge_names:

                    from_vertex = self.edge_dict[ename]['from']
                    to_vertex = self.edge_dict[ename]['to']
                    edge_key = record_vertex_keys[from_vertex] + "-" + \
                    record_vertex_keys[to_vertex]
                    the_edge = {"_key" : edge_key,\
                                "_from": from_vertex + "/" + record_vertex_keys[from_vertex],\
                                "_to": to_vertex + "/" + record_vertex_keys[to_vertex]}
                    self.batch_edge_dict[ename].append(the_edge)
                    
                if row_index > 0 and (row_index % batch_size == 0):
                    self.do_inserts()
                    
                
                if num_rows % batch_size != 0:
                    if row_index == num_rows:
                        self.do_inserts()
                    
                    

            except Exception as e:
                traceback.print_exc()
                

            #breakpoint()


        t1 = time.time()
        et = float((t1 -t0) / 60)
        et = round(et, 2)
        print("Data load took " + str(et) + " minutes!.")
        print("Done loading data!")

        return

    def load_vertex_attributes(self, row, the_vertex, vertex_name):

        if vertex_name == 'incident':
            self.load_incident_attributes(row, the_vertex)
        if vertex_name == 'customer':
            self.load_customer_attributes(row, the_vertex)
        if vertex_name == 'support_org':
            self.load_support_org_attributes(row, the_vertex)
        if vertex_name == 'vendor':
            self.load_vendor_attributes(row, the_vertex)

        return

    def load_incident_attributes(self, row, the_vertex):
        subset_dict = row[self.feature_dict['incident']].to_dict()


        for a in subset_dict:
            the_vertex[a] = subset_dict[a]

        return

    def load_customer_attributes(self, row, the_vertex):

        subset_dict = row[self.feature_dict['customer']].to_dict()

        for a in subset_dict:
            the_vertex[a] = subset_dict[a]

        return

    def load_support_org_attributes(self, row, the_vertex):

        subset_dict = row[self.feature_dict['support_org']].to_dict()

        for a in subset_dict:
            the_vertex[a] = subset_dict[a]

        return

    def load_vendor_attributes(self, row, the_vertex):

        subset_dict = row[self.feature_dict['vendor']].to_dict()

        for a in subset_dict:
            the_vertex[a] = subset_dict[a]

        return

    def load_num_mods(self, row, the_vertex):

        return







