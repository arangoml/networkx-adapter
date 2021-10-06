#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
"""


from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter
import networkx as nx


class IMDBArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):

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
                    if k == "Users":
                        bip_key = 0
                    else:
                        bip_key = 1
                    g.add_node(doc['_id'], attr_dict=doc, bipartite=bip_key)

            for k, v in graph_attributes['edgeCollections'].items():
                query = "FOR doc in %s " % (k)
                cspl = [s + ':' + 'doc.' + s for s in v]
                cspl.append('_id: doc._id')
                csps = ','.join(cspl)
                query = query + "RETURN { " + csps + "}"

                cursor = self.db.aql.execute(query, **query_options)

                for doc in cursor:
                    g.add_edge(doc['_from'], doc['_to'])

        return g
