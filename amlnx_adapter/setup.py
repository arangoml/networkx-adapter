import pathlib
from setuptools import setup

# The directory containing this file
#HERE = pathlib.Path(__file__).resolve().parents[1]


# The text of the README file
#README = (README.md).read_text()

# This call to setup() does all the work
setup(
    name="amlnx_adapter",
    version="0.0.0.1",
    description="package for creating networkx adapters for arangodb",
    long_description="placeholder for now",
    long_description_content_type="text/markdown",
    url="https://github.com/arangoml/arangopipe",
    author="ArangoDB",
    author_email="rajiv@arangodb.com",
    license="Apache",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7"],
    packages=["amlnx_adapter"],
    package_data={'config': ['dgl/graph_descriptor.yaml']},
    include_package_data=True
)
