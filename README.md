# ArangoDB-Networkx Adapter

<center>
<img src="assets/logos/ArangoDB_logo.png" width=95% >
</center>


Networkx is commonly used for analysis of network-data. If your analytics use cases require the use of all your graph data, for example, to summarize graph structure, or answer global path traversal queries, then using the ArangoDB Pregel API is recommended. If your analysis pertains to a subgraph, then you may be interested in getting the Networkx representation of the subgraph for one of the following reasons:

    1. An algorithm for your use case is available in Networkx.
    2. A library that you want to use for your use case works with Networkx Graphs as input.


Check the DGL folder for an implementation of a Networkx-Adapter for the Deep Graph Library.
