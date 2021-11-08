from setuptools import setup
import pathlib


# The directory containing this file
HERE = pathlib.Path(__file__).resolve().parents[1]


# This call to setup() does all the work
setup(
    name="adbnx_adapter",
    version="0.0.0.2.5.3-1",
    description="package for creating networkx adapters for arangodb",
    long_description="package for creating networkx adapters for arangodb",
    long_description_content_type="text/markdown",
    url="https://github.com/arangoml/networkx-adapter",
    author="ArangoDB",
    author_email="rajiv@arangodb.com",
    license="Apache",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7"],
    packages=["adbnx_adapter"],
    include_package_data=True)
