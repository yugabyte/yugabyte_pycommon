#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of yugabyte_pycommon.
# https://github.com/yugabyte/yugabyte_pycommon

# Licensed under the Apache 2.0 license:
# http://www.opensource.org/licenses/Apache 2.0-license
#  Copyright (c) YugaByte, Inc.

from setuptools import setup, find_packages
from yugabyte_pycommon import __version__

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
    'testfixtures'
]

setup(
    name='yugabyte_pycommon',
    version=__version__,
    description='Common utilities used in YugaByte Database\'s build infrastructure but could '
                'also be useful for anyone. E.g. convenient utilities for running external '
                'programs, logging, etc. Please give YugaByte DB a star at '
                'https://github.com/yugabyte/yugabyte-db -- much appreciated!',
    long_description=
        'Common utilities used in YugaByte Database\'s build infrastructure but could also be '
        'useful for anyone. E.g. convenient utilities for running external programs, logging, etc.',
    keywords='tool tools utility utilities yugabyte run command external process group_by',
    author='Mikhail Bautin',
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
    include_package_data=True,
    install_requires=[
        # add your dependencies here
        # remember to use 'package-name>=x.y.z,<x.y+1.0' notation (this way you get bugfixes)
    ],
    extras_require={
        'tests': tests_require,
    },
    entry_points={
        'console_scripts': [
            # add cli scripts here in this form:
            # 'yugabyte_pycommon=yugabyte_pycommon.cli:main',
        ],
    },
)
