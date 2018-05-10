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

import logging


from yugabyte_pycommon.text_manipulation import get_bool_env_var


def is_verbose_mode():
    return get_bool_env_var('YB_VERBOSE')


def get_default_log_level():
    if is_verbose_mode():
        return logging.DEBUG
    return logging.INFO


def init_logging(log_level=None):
    if log_level is None:
        log_level = get_default_log_level()
    logging.basicConfig(
        level=log_level,
        format="[%(filename)s:%(lineno)d] %(asctime)s %(levelname)s: %(message)s"
    )
