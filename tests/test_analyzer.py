[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "hta-analytics"
version = "0.1.0"
authors = [
    { name="Vaše Jméno", email="vas.email@domena.cz" }
]
description = "Pokročilý nástroj pro Health Technology Assessment (MCDA, citlivostní analýza)"
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.20.0",
    "matplotlib>=3.5.0",
    "scipy>=1.7.0"
]
