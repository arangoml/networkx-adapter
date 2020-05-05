from setuptools import setup

# The directory containing this file
#HERE = pathlib.Path(__file__).resolve().parents[1]


with open("README.md", "r") as fh:
    long_description = fh.read()

# This call to setup() does all the work
setup(
    name="amlnx_adapter",
    version="0.0.0.4.8",
    description="package for creating networkx adapters for arangodb",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arangoml/arangopipe",
    author="ArangoDB",
    author_email="rajiv@arangodb.com",
    license="Apache",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7"],
    packages=["amlnx_adapter", "amlnx_adapter.dgl", "amlnx_adapter.node2vec"],
    package_data={'amlnx_adapter.dgl': ['*.crt'], 'amlnx_adapter':['*.crt'], "amlnx_adapter.node2vec":["*.yaml"]},
    include_package_data=True )


