from setuptools import find_packages, setup

with open("./README.md") as fp:
    long_description = fp.read()

setup(
    name="adbnx_adapter",
    author="ArangoDB",
    author_email="rajiv@arangodb.com",
    description="Convert ArangoDB graphs to NetworkX & vice-versa.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arangoml/networkx-adapter",
    keywords=["arangodb", "networkx", "adapter"],
    packages=find_packages(exclude=["tests", "examples"]),
    include_package_data=True,
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    python_requires=">=3.6",
    license="Apache Software License",
    install_requires=[
        "python-arango==7.3.0",
        "networkx>=2.5.1",
        "setuptools>=42",
        "setuptools_scm[toml]>=3.4",
    ],
    extras_require={
        "dev": [
            "black",
            "flake8>=3.8.0",
            "isort>=5.0.0",
            "mypy>=0.790",
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "coveralls>=3.3.1",
            "types-setuptools",
            "types-requests",
        ],
    },
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
