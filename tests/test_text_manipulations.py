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

from yugabyte_pycommon import trim_long_text

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
