import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).resolve().parents[1]

with open("../README.md", "r") as f:
    long_description = f.read()

# This call to setup() does all the work
setup(
    name="adbnx_adapter",
    author="ArangoDB",
    author_email="rajiv@arangodb.com",
    version="1.0.1",
    description="Convert ArangoDB graphs to NetworkX & vice-versa.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arangoml/networkx-adapter",
    packages=["adbnx_adapter"],
    include_package_data=True,
    python_requires=">=3.6",
    license="Apache Software License",
    install_requires=["python-arango==7.2.0", "networkx>=2.5.1,<=2.6.3"],
    tests_require=["pytest", "pytest-cov"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
