#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='palette-splunk-logger',

    version='1.0.0',
    license='Apache License 2.0',
    platforms='Linux',

    description=('The AsyncSplunkLogHandler class is a subclass of the logging.Handler'
                 ', supports sending logging messages to a Splunk server via'
                 'its HTTP Event Collector asynchronously.'),
    long_description=open('README.md', 'r').read(),
    author='Palette Developers',
    author_email='developers@palette-software.com',
    url='https://github.com/palette-software/palette-splunk-logger/',

    packages=find_packages(),
    include_package_data=True
)
