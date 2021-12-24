# ArangoDB-Networkx Adapter
[![build](https://github.com/arangoml/networkx-adapter/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/arangoml/networkx-adapter/actions/workflows/build.yml)
[![CodeQL](https://github.com/arangoml/networkx-adapter/actions/workflows/analyze.yml/badge.svg?branch=master)](https://github.com/arangoml/networkx-adapter/actions/workflows/analyze.yml)
[![Coverage Status](https://coveralls.io/repos/github/arangoml/networkx-adapter/badge.svg?branch=master)](https://coveralls.io/github/arangoml/networkx-adapter)
[![Last commit](https://img.shields.io/github/last-commit/arangoml/networkx-adapter)](https://github.com/arangoml/networkx-adapter/commits/master)

[![PyPI version badge](https://img.shields.io/pypi/v/adbnx-adapter?color=3775A9&style=for-the-badge&logo=pypi&logoColor=FFD43B)](https://pypi.org/project/adbnx-adapter/)
[![Python versions badge](https://img.shields.io/pypi/pyversions/adbnx-adapter?color=3776AB&style=for-the-badge&logo=python&logoColor=FFD43B)](https://pypi.org/project/adbnx-adapter/)

[![License](https://img.shields.io/github/license/arangoml/networkx-adapter?color=9E2165&style=for-the-badge)](https://github.com/arangoml/networkx-adapter/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/static/v1?style=for-the-badge&label=code%20style&message=black&color=black)](https://github.com/psf/black)
[![Downloads](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=282661&label=Downloads&query=total_downloads&url=https://api.pepy.tech/api/projects/adbnx-adapter)](https://pepy.tech/project/adbnx-adapter)

![](https://raw.githubusercontent.com/arangoml/networkx-adapter/1.0.0/examples/assets/logos/ArangoDB_logo.png)

![](https://raw.githubusercontent.com/arangoml/networkx-adapter/1.0.0/examples/assets/logos/networkx_logo.svg)

The ArangoDB-Networkx Adapter exports Graphs from ArangoDB, a multi-model Graph Database, into NetworkX, the swiss army knife for graph analysis with python, and vice-versa.



## About NetworkX

Networkx is a commonly used tool for analysis of network-data. If your analytics use cases require the use of all your graph data, for example, to summarize graph structure, or answer global path traversal queries, then using the ArangoDB Pregel API is recommended. If your analysis pertains to a subgraph, then you may be interested in getting the Networkx representation of the subgraph for one of the following reasons:

    1. An algorithm for your use case is available in Networkx.
    2. A library that you want to use for your use case works with Networkx Graphs as input.

##  Quickstart

Get Started on Colab: <a href="https://colab.research.google.com/github/arangoml/networkx-adapter/blob/master/examples/ArangoDB_NetworkX_Adapter.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

##  Development & Testing

Prerequisite: `arangorestore` must be installed

1. `git clone https://github.com/arangoml/networkx-adapter.git`
2. `cd networkx-adapter`
3. `python -m venv .venv`
4. `source .venv/bin/activate` (MacOS) or `.venv/scripts/activate` (Windows)
5. `pip install -e .[dev]`
6. `pytest`