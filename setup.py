#!/usr/bin/env python
# coding=utf-8
from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

short_description = '{}'.format(
    'Automated JSON API based communication with Samsung SyncThru Web Service')

setup(
    name='PySyncThru',
    version='0.5.2',
    description=short_description,
    author='nielstron',
    author_email='n.muendler@web.de',
    url='https://github.com/nielstron/pysyncthru/',
    py_modules=['pysyncthru'],
    packages=find_packages(),
    package_data={'pysyncthru.tests.test_structure': ['sws/app/information/home/home.json', '*.html']},
    install_requires=[
        'demjson',
        'aiohttp',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Object Brokering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='python syncthru json api samsung printer',
    python_requires='>=3',
    test_suite='pysyncthru.tests',
)
