#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

import setuptools

setuptools.setup(
    name="btc",
    version="0.1.0",
    author="Nicolas Vetsch",
    author_email="vetschnicolas@gmail.com",
    description="Python module for interfacing with Büchi Temperature Controllers via their RS232 port.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/vetschn/btc",
    project_urls={"Bug Tracker": "https://github.com/vetschn/btc/issues"},
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Chemistry",
    ],
    keywords=["Büchi", "Temperature Controller", "btc01", "btc02"],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    entry_points={"console_scripts": ["btc_logger=btc:logger"]},
    install_requires=["pyserial"],
    python_requires=">=3.9",
)
