from setuptools import setup

with open("./README.md") as fp:
    long_description = fp.read()

setup(
    name="adbnx_adapter",
    author="Anthony Mahanna",
    author_email="anthony.mahanna@arangodb.com",
    description="Convert ArangoDB graphs to NetworkX & vice-versa.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arangoml/networkx-adapter",
    keywords=["arangodb", "networkx", "adapter"],
    packages=["adbnx_adapter"],
    include_package_data=True,
    python_requires=">=3.6",
    license="Apache Software License",
    install_requires=[
        "requests>=2.27.1",
        "python-arango>=7.4.1",
        "networkx>=2.5.1",
        "setuptools>=45",
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
        ],
    },
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
