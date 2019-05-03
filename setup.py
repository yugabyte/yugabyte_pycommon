#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (c) 2019 YugaByte, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.  See the License for the specific language governing permissions and limitations under
# the License.

from setuptools import setup, find_packages
from yugabyte_pycommon import version
import subprocess

tests_require = [
    'mock',
    'nose',
    'coverage',
    'yanc',
    'preggy',
    'tox',
    'ipdb',
    'coveralls',
    'sphinx',
    'testfixtures',
    'semver'
]

docs_require = [
    'sphinx',
    'sphinx_rtd_theme'
]

setup(
    name='yugabyte_pycommon',
    version=yugabyte_pycommon_version.compute_version(),
    description='Common utilities used in YugaByte Database\'s build infrastructure but could '
                'also be useful for anyone. E.g. convenient utilities for running external '
                'programs, logging, etc. Please give YugaByte DB a star at '
                'https://github.com/yugabyte/yugabyte-db -- much appreciated!',
    long_description=
        'Common utilities used in YugaByte Database\'s build infrastructure but could also be '
        'useful for anyone. E.g. convenient utilities for running external programs, logging, etc.',
    keywords='tool tools utility utilities yugabyte run command external process group_by',
    author='YugaByte, Inc.',
    author_email='mbautin@users.noreply.github.com',
    url='https://github.com/yugabyte/yugabyte_pycommon',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),

    # If set to True, this tells setuptools to automatically include any data files it finds inside
    # your package directories that are specified by your MANIFEST.in file. For more information,
    # see the section below on Including Data Files.
    include_package_data=True,

    # A string or list of strings specifying what other distributions need to be installed when this
    # one is. See the section below on Declaring Dependencies for details and examples of the format
    # of this argument.
    install_requires=[
        # add your dependencies here
        # remember to use 'package-name>=x.y.z,<x.y+1.0' notation (this way you get bugfixes)
    ],

    # A dictionary mapping names of "extras" (optional features of your project) to strings or lists
    # of strings specifying what other distributions must be installed to support those features.
    # See the section below on Declaring Dependencies for details and examples of the format of this
    # argument.
    extras_require={
        'tests': tests_require,
        'docs': docs_require
    },

    # A dictionary mapping entry point group names to strings or lists of strings defining the entry
    # points. Entry points are used to support dynamic discovery of services or plugins provided by
    # a project. See Dynamic Discovery of Services and Plugins for details and examples of the
    # format of  this argument. In addition, this keyword is used to support Automatic Script
    # Creation.
    entry_points={
        'console_scripts': [
            # add cli scripts here in this form:
            # 'yugabyte_pycommon=yugabyte_pycommon.cli:main',
        ],
    },
)
