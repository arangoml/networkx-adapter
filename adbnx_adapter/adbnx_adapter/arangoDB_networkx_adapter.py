#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
"""


from adbnx_adapter.arangodb_networkx_adapter_base import Networkx_Adapter_Base
import networkx as nx
from arango import ArangoClient


class ArangoDB_Networkx_Adapter(Networkx_Adapter_Base):

    def __init__(self, conn):
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

    def is_valid_graph_attributes(self, graph_config):
        valid_config = True

        if not 'vertexCollections' in graph_config:
            print("Graph attributes do not contain vertex collections")
            valid_config = False
        if not 'edgeCollections' in graph_config:
            print("Graph attributes do not contain edge collections")
            valid_config = False

        return valid_config

    def create_networkx_graph(self, graph_name, graph_attributes, **query_options):

        if self.is_valid_graph_attributes(graph_attributes):
            g = nx.DiGraph()
            for k, v in graph_attributes['vertexCollections'].items():
                query = "FOR doc in %s " % (k)
                cspl = [s + ':' + 'doc.' + s for s in v]
                cspl.append('_id: doc._id')
                csps = ','.join(cspl)
                query = query + "RETURN { " + csps + "}"

                cursor = self.db.aql.execute(query, **query_options)
                for doc in cursor:
                    g.add_node(doc['_id'], attr_dict=doc)

            for k, v in graph_attributes['edgeCollections'].items():
                query = "FOR doc in %s " % (k)
                cspl = [s + ':' + 'doc.' + s for s in v]
                cspl.append('_id: doc._id')
                csps = ','.join(cspl)
                query = query + "RETURN { " + csps + "}"

                cursor = self.db.aql.execute(query, **query_options)
                # breakpoint()
                for doc in cursor:
                    g.add_edge(doc['_from'], doc['_to'])

        return g
