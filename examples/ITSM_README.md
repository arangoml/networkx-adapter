# Graph Convolution Network Implementation with DGL using ArangoDB DGL Adapter


This document provides an overview of the implementation of Graph Convolution Networks with the ArangoDB DGL Adapter. The data represents the event log from an incident management application in an IT company. The data has been used for regression tasks pertaining to estimating the time for resolution of an incident. In this work, this data is used for a classification task. The classification task is to predict if an incident will be reassigned in the course of its resolution. The classification task is accomplished using a Graph Convolution Network. The steps involved are:

1. The characteristics of the data are identified using an exploratory data analysis notebook.

2. The data from the [UCI machine learning repository](https://archive.ics.uci.edu/ml/datasets/Incident+management+process+enriched+event+log) is processed to a form suitable for the learning task.

3. The pre-processed data is then loaded into ArangoDB. Oasis, ArangoDB's managed service offering is used for illustration. This eliminates the need for installation and configuration of ArangoDB for this exercise. See the note at the bottom of `ITSM_ArangoDB_Adapter.ipynb` for the details of doing this.

4. A database dump of the loaded data can be created using the _arangodump_ utility.

5. The _ArangoDB DGL Adapter_ is used to create a __dgl heterograph__ representation of the __ArangoDB__ graph using _Networkx_ to specify the heterograph.

6. The notebook, ITSM_ArangoDB_Adapter.ipynb, provides the details of implementing a GCN to predict if a incident will be reassigned in the course of its resolution. Please see the notebook for details.


 