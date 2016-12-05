from setuptools import setup, find_packages

import os

version = "1.0.0"

setup(
    name="iotile-transport-bled112",
    packages=find_packages(exclude=("test",)),
    version=version,
    license="LGPLv3",
    install_requires=[
        "iotile-core>=3.0.0",
        "pyserial>=3.1.1"
    ],

    entry_points={'iotile.device_adapter': ['bled112 = iotile_transport_bled112.bled112:BLED112Adapter']},
    description="IOTile BLED112 Transport Plugin",
    author="Arch",
    author_email="info@arch-iot.com",
    url="http://github.com/iotile/lib_iotilecore",
    keywords=["iotile", "arch", "embedded", "hardware", "firmware"],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
        ],
    long_description="""\
IOTile BLED112 Transport Plugin
------

A python plugin for the IOTile framework that allows communication with IOTile devices over 
Bluetooth Smart using the BLED112 dongle.  See https://www.arch-iot.com.
"""
)
