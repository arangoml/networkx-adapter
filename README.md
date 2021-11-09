# ArangoDB-Networkx Adapter
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

<center>
<img src="examples/assets/logos/networkx_logo.svg" width=50% >
</center>
<center>
<img src="examples/assets/logos/ArangoDB_logo.png" width=50% >
</center>

The ArangoDB-Networkx Adapter exports Graphs from ArangoDB, a multi-model Graph Database, into NetworkX, the swiss army knife for graph analysis with python, and vice-versa.

## About NetworkX

Networkx is a commonly used tool for analysis of network-data. If your analytics use cases require the use of all your graph data, for example, to summarize graph structure, or answer global path traversal queries, then using the ArangoDB Pregel API is recommended. If your analysis pertains to a subgraph, then you may be interested in getting the Networkx representation of the subgraph for one of the following reasons:

    1. An algorithm for your use case is available in Networkx.
    2. A library that you want to use for your use case works with Networkx Graphs as input.

##  Quickstart

Get Started on Colab: <a href="https://colab.research.google.com/github/arangoml/networkx-adapter/blob/master/examples/ArangoDB_NetworkxAdapter.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

##  Development & Testing

1. `git clone https://github.com/arangoml/networkx-adapter.git`
2. `cd networkx-adapter/adbnx_adapter`
3. `python -m venv .venv`
4. `source .venv/bin/activate` (MacOS) or `.venv/scripts/activate` (Windows)
5. `cd adbnx_adapter`
6. `pip install -e . pytest`
7. `pytest -s`
    * If you encounter `ModuleNotFoundError`, try closing & relaunching your virtual environment by running `deactivate` in your terminal & restarting from Step 4.
