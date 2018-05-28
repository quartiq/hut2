#!/usr/bin/env python3

import sys
from setuptools import setup
from setuptools import find_packages


setup(
    name="hut2",
    version="0.1",
    description="Python/ARTIQ driver for Anel HUT2",
    long_description=open("README.rst").read(),
    author="Robert Jördens",
    author_email="rj@quartiq.de",
    url="https://github.com/quartiq/hut2",
    download_url="https://github.com/quartiq/hut2",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            # "aqctl_hut2 = hut2.aqctl_hut2:main",
        ],
    },
    test_suite="hut2.test",
    license="LGPLv3+",
)
