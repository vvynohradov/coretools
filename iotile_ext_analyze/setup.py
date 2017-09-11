from setuptools import setup, find_packages

import version

setup(
    name="iotile-ext-analyze",
    packages=find_packages(exclude=("test",)),
    version=version.version,
    license="LGPLv3",
    install_requires=[
        "iotile-core>=3.15.2",
        "iotile-ext-cloud>=0.3.1",
        "numpy>=1.13.1",
        "pandas>=0.20.3"
    ],
    description="Advanced Data Visualization and Analysis Tools for IOTile.cloud Data",
    author="Arch",
    author_email="info@arch-iot.com",
    url="http://github.com/iotile/coretools",
    keywords=["iotile", "arch", "embedded", "hardware", "firmware"],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    long_description="""\
IOTile Data Analsysis Extensions
--------------------------------

A set of extensions to IOTile CoreTools that allow you to easily analyze and visualize
IOTile.cloud data using standard tools like Pandas and Numpy.
"""
)
