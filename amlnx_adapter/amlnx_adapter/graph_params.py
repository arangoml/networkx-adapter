#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 08:03:58 2020

@author: Rajiv Sambasivan
"""

class GraphParams:
    @property
    def DB_SECTION(self):
        return "arangodb"
    @property
    def DATA_SECTION(self):
        return "queries"
    @property
    def DB_SERVICE_HOST(self):
        return "DB_service_host"

    @property
    def DB_DATA_QUERY(self):
        return "load_data"

    @property
    def DB_SERVICE_PORT(self):
        return "DB_service_port"

    @property
    def DB_NAME(self):
        return "dbName"

    @property
    def DB_REPLICATION_FACTOR(self):
        return "arangodb_replication_factor"

    @property
    def DB_USER_NAME(self):
        return "username"

    @property
    def DB_PASSWORD(self):
        return "password"
    @property
    def DB_CONN_PROTOCOL(self):
        return "conn_protocol"
    
    @property
    def DB_VERTICES(self):
        return "vertices"
    @property
    def DB_VERTEX_COL(self):
        return "vertexCollections"
    @property
    def DB_EDGE_COL(self):
        return "edgeCollections"

    @property
    def DB_EDGES(self):
        return "edges"

    @property
    def DB_EDGE_COL_NAME(self):
        return "edge_col_name"
    
    @property
    def DB_EDGE_FROM(self):
        return "from"
    
    @property
    def DB_EDGE_TO(self):
        return "to"