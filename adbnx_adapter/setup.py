from setuptools import setup
import pathlib


# The directory containing this file
HERE = pathlib.Path(__file__).resolve().parents[1]


with open(HERE/"README.md", "r") as fh:
    long_description = fh.read()

# This call to setup() does all the work
setup(
    name="adbnx_adapter",
    version="0.0.0.1",
    description="package for creating networkx adapters for arangodb",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arangoml/networkx-adapter",
    author="ArangoDB",
    author_email="rajiv@arangodb.com",
    license="Apache",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7"],
    packages=["adbnx_adapter", "adbnx_adapter.dgl", "adbnx_adapter.node2vec"],
    include_package_data=True )
