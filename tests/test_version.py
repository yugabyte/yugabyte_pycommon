#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of yugabyte_pycommon.
# https://github.com/yugabyte/yugabyte_pycommon

# Licensed under the Apache 2.0 license:
# http://www.opensource.org/licenses/Apache 2.0-license
# Copyright (c) 2018, Mikhail Bautin <mbautin@users.noreply.github.com>

from preggy import expect

from yugabyte_pycommon import __version__
from tests.base import TestCase


class VersionTestCase(TestCase):
    def test_has_proper_version(self):
        expect(__version__).to_equal('1.0.0')
