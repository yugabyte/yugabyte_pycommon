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
import os
import tempfile
import subprocess

from yugabyte_pycommon import trim_long_text, run_program, quote_for_bash

from .base import TestCase


class TextManipulationsTestCase(TestCase):
    def test_trim_long_text(self):
        long_text = "\n".join([str(i) for i in range(1, 11)])
        self.assertEquals(long_text, trim_long_text(long_text, 20))
        self.assertEquals(long_text, trim_long_text(long_text, 10))
        self.assertEquals(
            "1\n2\n3\n4\n(2 lines skipped)\n7\n8\n9\n10", trim_long_text(long_text, 9))
        self.assertEquals(
            """1
2
(6 lines skipped)
9
10""", trim_long_text(long_text, 5))

        self.assertEquals('1\n2\n(6 lines skipped)\n9\n10', trim_long_text(long_text, 5))
        self.assertEquals("1\n(8 lines skipped)\n10", trim_long_text(long_text, 4))
        self.assertEquals("1\n(8 lines skipped)\n10", trim_long_text(long_text, 3))
        self.assertEquals("1\n(8 lines skipped)\n10", trim_long_text(long_text, 2))
        self.assertEquals("1\n(8 lines skipped)\n10", trim_long_text(long_text, 1))

    def test_quote_for_bash(self):
        for s in [
            "\\" * 1,
            "\\" * 2,
            "\\" * 3,
            "\\" * 4,
            "\\" * 5,
            "\\" * 6,
            '',
            'a',
            'a b'
            '"foo"'
            'foo"bar',
            'foo " bar',
            "foo'bar",
            '$foo $bar',
            '"' + "'",
            '"' + "'" + '"' + "'",
            r"""'\''""",
            'foo bar',
            ' ',
            'foo ',
            ' foo',
            ' foo bar '
            ';',
            ' ;',
            '; ',
            ' ; '
            '.',
            '*',
            ' .',
            '. ',
            '* ',
            ' *'
        ]:
            quoted_s = quote_for_bash(s)
            tmp_file_path = None

            try:
                with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as tmp_file:
                    cmd = 'echo -n ' + quoted_s
                    tmp_file.write(cmd.encode('utf-8'))
                    tmp_file_path = tmp_file.name

                result = subprocess.check_output(
                        ['bash', tmp_file_path]).decode('utf-8')
                self.assertEqual(s, result,
                                 "For input string: [[ {} ]], quote_for_bash produced [[ {} ]], "
                                 "but echo -n with that argument returned: [[ {} ]]".format(
                                     s, quoted_s, result
                                 ))
            finally:
                if False and tmp_file_path and os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
