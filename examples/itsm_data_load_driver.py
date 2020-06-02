#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  6 15:43:03 2020

@author: admin2
"""

from ITSM_data_loader import ITSM_Dataloader
import oasis

def load_ITSM_data_to_ArangoDB():
    conn = oasis.getTempCredentials()
    itsmdl = ITSM_Dataloader(conn)
   
    
    return itsmdl