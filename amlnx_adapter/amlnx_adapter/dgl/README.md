# DGL Arango DB Networkx Adapter

To create the ArangoDB Networkx adapter we need an implementation of the `Networkx_Arango_Adapter` for DGL. We will be implementing the  `create_networkx_graph()` method for DGL. Please see the `dgl_networkx_arango_adapter.py` for details.

The details of the implementation are as follows. The adapter can obtain data to create the Networkx representation using one of the following:

1. A database dump
2. Connecting to the database and fetching the data by executing a query.

You can specify the particular mode to use in an application by specifying the `load_from_db` parameter in the adapter. When a database dump is used to load the data, you will need to specify the details of the graph representation in a graph descriptor file (see `graph_descriptor.yaml`). Each facet of the graph is described in a section of the descriptor file. The details of the sections are as follows:

1. `edge_data`: Use this section to provide the details of the edge data for the graph. For each edge provide an edge name and the data file location for that data. For example, the line:

    `incident-support_org: ../data/incident_support_org.json`

    indicates that the data for the edge `incident-support_org` is found in the file ../data/incident_support_org.json. Relative paths are used in this example, but you could use an absolute path if you prefer.
    
2. `vertex_data: Use this section to provide the details of the vertex data for the graph. For each vertex, provide the vertex name and the data file location for that vertex. For example, the line:

    `incident: ../data/incident.json `  

    indicates that the data for the vertex `incident` is found in the file ../data/incident.json

3. exclude_attributes: The data for vertices and nodes store system generated attributes like keys and version numbers associated with the vertex and the node. You can indicate that the attributes you want to be excluded from the vertex properties by specifying them here. For example:

    `exclude_attributes:

            all: ['bipartite', '_key', '_rev', 'node_id', '_id']
   
            incident: ['reassigned']`

    indicates that the attributes `_key`, `_rev` etc., should not be included in the networkx representation
        of the vertex properties. The `all` property indicates that this rule
     applies to all vertex representations. If we have specific additional attributes for particular nodes, then we need to specify them independently. For example the rule for the `incident` node specifies that the `reassigned` property should not be included.


4. arangodb: The keys specified under this section are applicable when data is obtained by connecting to a database. Connection string, host names etc. are specified here.

5. queries: The keys specified in this section are applicable when data is obtained by connecting to a database.

Plese see `dgl_networkx_arango_adapter.py` for the details of how data is loaded using the options specified in the




