#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 09:51:47 2020

@author: Rajiv Sambasivan
"""


import dgl
import numpy as np
import torch as th
import networkx as nx
from .arangoDB_networkx_adapter import ArangoDB_Networkx_Adapter


class DGLArangoDB_Networkx_Adapter(ArangoDB_Networkx_Adapter):
    def create_networkx_graph(
        self, graph_name: str, graph_attributes: dict, **query_options
    ):
        self.validate_attributes("graph", graph_attributes.keys(), self.GRAPH_ATRIBS)

        edge_names = []
        redge_names = []
        collection: str
        for collection, _ in graph_attributes["edgeCollections"].items():
            edge_names.append(collection)
            ens = collection.split("_", 1)
            redge = ens[1] + "_" + ens[0]
            redge_names.append(redge)

        sgdata = {ename: nx.DiGraph() for ename in edge_names}
        rsgdata = {ename: nx.DiGraph() for ename in redge_names}

        labels = []
        node_data = {}
        nxg = nx.DiGraph()

        print("Loading edge data...")
        for collection, attributes in graph_attributes["edgeCollections"].items():
            sgraph = sgdata[collection]
            ens = collection.split("_", 1)
            redge = ens[1] + "_" + ens[0]
            rsgraph = rsgdata[redge]

            for edge in self.fetch_docs(collection, attributes, True, query_options):
                nfrom = edge["_from"]
                nto = edge["_to"]
                sgraph.add_edge(nfrom, nto)
                sgraph.nodes[nfrom]["bipartite"] = 0
                sgraph.nodes[nto]["bipartite"] = 1
                rsgraph.add_edge(nto, nfrom)
                rsgraph.nodes[nfrom]["bipartite"] = 1
                rsgraph.nodes[nto]["bipartite"] = 0

        print("Loading vertex data...")

        vnames = []
        for collection, attributes in graph_attributes["vertexCollections"].items():
            vnames.append(collection)
            node_data[collection] = list()

            for vertex in self.fetch_docs(collection, attributes, True, query_options):
                exclude_attr = ["_id", "_key", "node_id"]
                if collection == "incident":
                    exclude_attr.append("reassigned")
                    labels.append(vertex["reassigned"])
                sdata = {k: v for k, v in vertex.items() if k not in exclude_attr}
                ndvalues = np.fromiter(sdata.values(), dtype=int)
                # rndata = np.asarray(ndvalues, dtype = int)
                # v_data = th.from_numpy(rndata)
                node_data[collection].append(ndvalues)

        print("Creating DGL Heterograph...")
        dict_desc = dict()
        for ename in edge_names:
            ens = ename.split("_", 1)
            redge = ens[1] + "_" + ens[0]
            fgk = (ens[0], ename, ens[1])
            dict_desc[fgk] = nxg
            rgk = (ens[1], redge, ens[0])
            dict_desc[fgk] = sgdata[ename]
            dict_desc[rgk] = rsgdata[redge]

        g = dgl.heterograph(dict_desc)

        for v in vnames:
            rndata = np.asarray(node_data[v], dtype=int)
            v_data = th.from_numpy(rndata)
            g.nodes[v].data["f"] = v_data

        print(f"Success: {graph_name} created")
        return g, labels

    def create_dgl_graph(self, graph_name, graph_attributes):
        print("Creating DGL graph...")
        g, labels = self.create_networkx_graph(graph_name, graph_attributes)
        print("done!")

        return g, labels
