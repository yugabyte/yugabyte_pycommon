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

import logging

from .base import TestCase

from yugabyte_pycommon import init_logging


class FileSystemUtilTestCase(TestCase):
    def test_mkdir_p(self):
        for log_level in [logging.INFO, logging.WARN, logging.DEBUG, logging.ERROR, logging.FATAL]:
            init_logging(log_level=log_level)