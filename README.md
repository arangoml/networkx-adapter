# ArangoDB-Networkx Adapter
[![build](https://github.com/arangoml/networkx-adapter/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/arangoml/networkx-adapter/actions/workflows/build.yml)
[![CodeQL](https://github.com/arangoml/networkx-adapter/actions/workflows/analyze.yml/badge.svg?branch=master)](https://github.com/arangoml/networkx-adapter/actions/workflows/analyze.yml)
[![Coverage Status](https://coveralls.io/repos/github/arangoml/networkx-adapter/badge.svg?branch=master)](https://coveralls.io/github/arangoml/networkx-adapter)
[![Last commit](https://img.shields.io/github/last-commit/arangoml/networkx-adapter)](https://github.com/arangoml/networkx-adapter/commits/master)

[![PyPI version badge](https://img.shields.io/pypi/v/adbnx-adapter?color=3775A9&style=for-the-badge&logo=pypi&logoColor=FFD43B)](https://pypi.org/project/adbnx-adapter/)
[![Python versions badge](https://img.shields.io/pypi/pyversions/adbnx-adapter?color=3776AB&style=for-the-badge&logo=python&logoColor=FFD43B)](https://pypi.org/project/adbnx-adapter/)

[![License](https://img.shields.io/github/license/arangoml/networkx-adapter?color=9E2165&style=for-the-badge)](https://github.com/arangoml/networkx-adapter/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/static/v1?style=for-the-badge&label=code%20style&message=black&color=black)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/pepy/dt/adbnx-adapter?style=for-the-badge&color=282661
)](https://pepy.tech/project/adbnx-adapter)

<a href="https://www.arangodb.com/" rel="arangodb.com">![](https://raw.githubusercontent.com/arangoml/networkx-adapter/master/examples/assets/logos/ArangoDB_logo.png)</a>
<a href="https://networkx.org/" rel="networkx.org">![](https://raw.githubusercontent.com/arangoml/networkx-adapter/master/examples/assets/logos/networkx_logo.svg)</a>

The ArangoDB-Networkx Adapter exports Graphs from ArangoDB, the multi-model database for graph & beyond, into NetworkX, the swiss army knife for graph analysis with python, and vice-versa.



## About NetworkX

Networkx is a commonly used tool for analysis of network-data. If your analytics use cases require the use of all your graph data, for example, to summarize graph structure, or answer global path traversal queries, then using the ArangoDB Pregel API is recommended. If your analysis pertains to a subgraph, then you may be interested in getting the Networkx representation of the subgraph for one of the following reasons:

    1. An algorithm for your use case is available in Networkx.
    2. A library that you want to use for your use case works with Networkx Graphs as input.


## Installation

#### Latest Release
```
pip install adbnx-adapter
```
#### Current State
```
pip install git+https://github.com/arangoml/networkx-adapter.git
```


##  Quickstart

[![Open In Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/arangoml/networkx-adapter/blob/master/examples/ArangoDB_NetworkX_Adapter.ipynb)

Also available as an ArangoDB Lunch & Learn session: [Graph & Beyond Course #2.9](https://www.arangodb.com/resources/lunch-sessions/graph-beyond-lunch-break-2-9-introducing-the-arangodb-networkx-adapter/)

```py
import networkx as nx

from arango import ArangoClient
from adbnx_adapter import ADBNX_Adapter, ADBNX_Controller

# Connect to ArangoDB
db = ArangoClient().db()

# Instantiate the adapter
adbnx_adapter = ADBNX_Adapter(db)
```

### ArangoDB to NetworkX
```py
#######################
# 1.1: via Graph name #
#######################

nx_g = adbnx_adapter.arangodb_graph_to_networkx("fraud-detection")

#############################
# 1.2: via Collection names #
#############################

nx_g = adbnx_adapter.arangodb_collections_to_networkx(
    "fraud-detection", 
    {"account", "bank", "branch", "Class", "customer"}, # Vertex collections
    {"accountHolder", "Relationship", "transaction"} # Edge collections
)

######################
# 1.3: via Metagraph #
######################

metagraph = {
    "vertexCollections": {
        "account": {"Balance", "account_type", "customer_id", "rank"},
        "customer": {"Name", "rank"},
    },
    "edgeCollections": {
        "transaction": {"transaction_amt", "sender_bank_id", "receiver_bank_id"},
        "accountHolder": {},
    },
}

nx_g = adbnx_adapter.arangodb_to_networkx("fraud-detection", metagraph)

#######################################
# 1.4: with a custom ADBNX Controller #
#######################################

class Custom_ADBNX_Controller(ADBNX_Controller):
    """ArangoDB-NetworkX controller.

    Responsible for controlling how nodes & edges are handled when
    transitioning from ArangoDB to NetworkX, and vice-versa.
    """

    def _prepare_arangodb_vertex(self, adb_vertex: dict, col: str) -> None:
        """Prepare an ArangoDB vertex before it gets inserted into the NetworkX
        graph.

        :param adb_vertex: The ArangoDB vertex object to (optionally) modify.
        :param col: The ArangoDB collection the vertex belongs to.
        """
        adb_vertex["foo"] = "bar"

    def _prepare_arangodb_edge(self, adb_edge: dict, col: str) -> None:
        """Prepare an ArangoDB edge before it gets inserted into the NetworkX
        graph.

        :param adb_edge: The ArangoDB edge object to (optionally) modify.
        :param col: The ArangoDB collection the edge belongs to.
        """
        adb_edge["bar"] = "foo"

nx_g = ADBNX_Adapter(db, Custom_ADBNX_Controller()).arangodb_graph_to_networkx("fraud-detection")
```

### NetworkX to ArangoDB
```py
#################################
# 2.1: with a Homogeneous Graph #
#################################

nx_g = nx.grid_2d_graph(5, 5)
edge_definitions = [
    {
        "edge_collection": "to",
        "from_vertex_collections": ["Grid_Node"],
        "to_vertex_collections": ["Grid_Node"],
    }
]

adb_g = adbnx_adapter.networkx_to_arangodb("Grid", nx_g, edge_definitions)

#############################################################
# 2.2: with a Homogeneous Graph & a custom ADBNX Controller #
#############################################################

class Custom_ADBNX_Controller(ADBNX_Controller):
    """ArangoDB-NetworkX controller.

    Responsible for controlling how nodes & edges are handled when
    transitioning from ArangoDB to NetworkX, and vice-versa.
    """

    def _prepare_networkx_node(self, nx_node: dict, col: str) -> None:
        """Prepare a NetworkX node before it gets inserted into the ArangoDB
        collection **col**.

        :param nx_node: The NetworkX node object to (optionally) modify.
        :param col: The ArangoDB collection the node belongs to.
        """
        nx_node["foo"] = "bar"

    def _prepare_networkx_edge(self, nx_edge: dict, col: str) -> None:
        """Prepare a NetworkX edge before it gets inserted into the ArangoDB
        collection **col**.

        :param nx_edge: The NetworkX edge object to (optionally) modify.
        :param col: The ArangoDB collection the edge belongs to.
        """
        nx_edge["bar"] = "foo"

adb_g = ADBNX_Adapter(db, Custom_ADBNX_Controller()).networkx_to_arangodb("Grid", nx_g, edge_definitions)

###################################
# 2.3: with a Heterogeneous Graph #
###################################

edges = [
   ('student:101', 'lecture:101'), 
   ('student:102', 'lecture:102'), 
   ('student:103', 'lecture:103'), 
   ('student:103', 'student:101'), 
   ('student:103', 'student:102'),
   ('teacher:101', 'lecture:101'),
   ('teacher:102', 'lecture:102'),
   ('teacher:103', 'lecture:103'),
   ('teacher:101', 'teacher:102'),
   ('teacher:102', 'teacher:103')
]
nx_g = nx.MultiDiGraph()
nx_g.add_edges_from(edges)

# ...

# Learn how this example is handled in Colab:
# https://colab.research.google.com/github/arangoml/networkx-adapter/blob/master/examples/ArangoDB_NetworkX_Adapter.ipynb#scrollTo=OuU0J7p1E9OM
```

##  Development & Testing

Prerequisite: `arangorestore`

1. `git clone https://github.com/arangoml/networkx-adapter.git`
2. `cd networkx-adapter`
3. (create virtual environment of choice)
4. `pip install -e .[dev]`
5. (create an ArangoDB instance with method of choice)
6. `pytest --url <> --dbName <> --username <> --password <>`

**Note**: A `pytest` parameter can be omitted if the endpoint is using its default value:
```python
def pytest_addoption(parser):
    parser.addoption("--url", action="store", default="http://localhost:8529")
    parser.addoption("--dbName", action="store", default="_system")
    parser.addoption("--username", action="store", default="root")
    parser.addoption("--password", action="store", default="")
```
