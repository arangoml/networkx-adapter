from setuptools import setup

# The directory containing this file
#HERE = pathlib.Path(__file__).resolve().parents[1]


with open("README.md", "r") as fh:
    long_description = fh.read()

# This call to setup() does all the work
setup(
    name="amlnx_adapter",
    version="0.0.0.3.6",
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
    packages=["amlnx_adapter", "amlnx_adapter.dgl"],
    package_data={'cert': ['amlnx_adapter/dgl/cert/ca-b9b556df.crt']},
    include_package_data=True )


