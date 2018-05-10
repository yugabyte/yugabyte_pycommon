#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) YugaByte, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.  See the License for the specific language governing permissions and limitations
# under the License.
#

# This file is part of yugabyte_pycommon, used in build scripts for YugaByte Database.
# https://github.com/yugabyte/yugabyte_pycommon

# We will appreciate your GitHub stars at https://github.com/yugabyte/yugabyte-db!

from yugabyte_pycommon import trim_long_text

from tests.base import TestCase

from yugabyte_pycommon import run_program, quote_for_bash, ExternalProgramError


class ExternalCommandsTestCase(TestCase):
    def test_run_program_noerror(self):
        result = run_program("true")
        self.assertEquals(0, result.returncode)
        self.assertEquals('', result.stdout)
        self.assertEquals('', result.stderr)

    def test_exit_codes(self):
        for exit_code in [0, 1, 2, 3, 10, 20, 100, 150, 200, 250, 255]:
            result = run_program("exit %d" % exit_code, shell=True, error_ok=exit_code != 0)
            self.assertEquals(exit_code, result.returncode)

    def test_quote_for_bash(self):
        for s in [
            '',
            'a',
            'a b'
            '"foo"'
            'foo"bar',
            'foo " bar',
            "foo'bar",
            '$foo $bar',
            "\\",
            "\\\\",
            "\\\\\\",
            '"' + "'",
            '"' + "'" + '"' + "'",
            r"""'\''"""
        ]:
            result = run_program('echo ' + quote_for_bash(s), shell=True)
            self.assertEquals(s, result.stdout)

    def test_error_reporing(self):
        with self.assertRaises(ExternalProgramError):
            run_program('false')
