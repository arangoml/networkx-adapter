#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May  5 14:49:38 2020

@author: admin2
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:33:12 2020

@author: Rajiv Sambasivan
"""

from amlnx_adapter.graph_params import GraphParams
from amlnx_adapter.node2vec.imdb_networkx_arango_adapter import IMDB_Networkx_Adapter

def test_conn():
    gp = GraphParams()
    cfg = {}
    cfg[gp.DB_USER_NAME] = "TUT9ygmsja2ydixfj1tphagho"
    cfg[gp.DB_NAME] = "TUT1q291acnwc5d3z8mvb2r7"
    cfg[gp.DB_CONN_PROTOCOL] = 'https'
    cfg[gp.DB_PASSWORD] = 'TUT3b7d6xeb37rtdujx5hodl'
    cfg[gp.DB_SERVICE_HOST] = '5904e8d8a65f.arangodb.cloud'
    cfg[gp.DB_SERVICE_HOST]
    cfg[gp.DB_DATA_QUERY] = 'FOR ratings in Ratings  return {''user'': ratings._from,\
        ''movie'': ratings._to, ''rating'': ratings.ratings}'
    
    ma = IMDB_Networkx_Adapter(graph_config = cfg)
    #g = ma.create_networkx_graph()
    
    return ma