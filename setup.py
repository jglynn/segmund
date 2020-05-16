"""
A service for aggregating segment data from Strava
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='segmund-toolchain',
    version='1.0.0',
    description='A service for aggregating segment data from Strava',
    long_description='A service for aggregating segment data from Strava',
    url='https://github.com/jglynn/segmund-toolchain',
    license='Apache-2.0'
)
