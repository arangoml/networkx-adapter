#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
"""


from adbnx_adapter.arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter
import networkx as nx
import torch as th
import numpy as np
import dgl


class DGLArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):

    def create_networkx_graph(self, graph_name, graph_attributes, **query_options):

        if self.is_valid_graph_attributes(graph_attributes):
            edge_names = []
            redge_names = []
            for k, v in graph_attributes['edgeCollections'].items():
                edge_names.append(k)
                ens = k.split('_', 1)
                redge = ens[1] + '_' + ens[0]
                redge_names.append(redge)

            sgdata = {ename: nx.DiGraph() for ename in edge_names}
            rsgdata = {ename: nx.DiGraph() for ename in redge_names}
            nxg = nx.DiGraph()
            labels = []
            node_data = {}

            print("Loading edge data...")

            for k, v in graph_attributes['edgeCollections'].items():
                query = "FOR doc in %s " % (k)
                cspl = [s + ':' + 'doc.' + s for s in v]
                cspl.append('_id: doc._id')
                csps = ','.join(cspl)
                query = query + "RETURN { " + csps + "}"
                sgraph = sgdata[k]
                ens = k.split('_', 1)
                redge = ens[1] + '_' + ens[0]
                rsgraph = rsgdata[redge]
                cursor = self.db.aql.execute(query, **query_options)
                for doc in cursor:
                    nfrom = doc['_from']
                    nto = doc['_to']
                    sgraph.add_edge(nfrom, nto)
                    sgraph.nodes[nfrom]['bipartite'] = 0
                    sgraph.nodes[nto]['bipartite'] = 1
                    rsgraph.add_edge(nto, nfrom)
                    rsgraph.nodes[nfrom]['bipartite'] = 1
                    rsgraph.nodes[nto]['bipartite'] = 0

            print("Loading vertex data...")
            vnames = []
            for k, v in graph_attributes['vertexCollections'].items():
                vnames.append(k)
                node_data[k] = list()
                query = "FOR doc in %s " % (k)
                cspl = [s + ':' + 'doc.' + s for s in v]
                cspl.append('_id: doc._id')
                csps = ','.join(cspl)
                query = query + "RETURN { " + csps + "}"

                cursor = self.db.aql.execute(query, **query_options)
                for doc in cursor:
                    exclude_attr = ['_id', '_key', 'node_id']
                    if k == 'incident':
                        exclude_attr.append('reassigned')
                        labels.append(doc['reassigned'])
                    sdata = {k: v for k, v in doc.items()
                             if k not in exclude_attr}
                    ndvalues = np.fromiter(sdata.values(), dtype=int)
                    #rndata = np.asarray(ndvalues, dtype = int)
                    #v_data = th.from_numpy(rndata)
                    node_data[k].append(ndvalues)

            print("Creating DGL Heterograph...")
            dict_desc = dict()
            for ename in edge_names:
                ens = ename.split('_', 1)
                redge = ens[1] + '_' + ens[0]
                fgk = (ens[0],  ename, ens[1])
                dict_desc[fgk] = nxg
                rgk = (ens[1], redge, ens[0])
                dict_desc[fgk] = sgdata[ename]
                dict_desc[rgk] = rsgdata[redge]

            g = dgl.heterograph(dict_desc)

            for v in vnames:
                rndata = np.asarray(node_data[v], dtype=int)
                v_data = th.from_numpy(rndata)
                g.nodes[v].data['f'] = v_data

        return g, labels

    def create_dgl_graph(self, graph_name, graph_attributes):
        print("Creating DGL graph...")
        g, labels = self.create_networkx_graph(graph_name, graph_attributes)
        print("done!")

        return g, labels
