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

"""
Utilities for manipulating files.
"""


import tempfile
import atexit


def get_tmp_file_path(*args, **kwargs):
    """
    Generates a temporary file name. Arguments are exactly like those of
    `tempfile.NamedTemporaryFile`. The file is immediately closed and scheduled to be deleted at
    exit, unless the `delete_at_exit` parameter value says otherwise.
    """
    kwargs['delete'] = False
    delete_at_exit = False
    if 'delete_at_exit' in kwargs:
        delete_at_exit = kwargs.pop('delete_at_exit')

    named_tmp_file = tempfile.NamedTemporaryFile(*args, **kwargs)
    named_tmp_file.close()
    file_path = named_tmp_file.name
    if delete_at_exit:
        def delete_file():
            if os.path.exists(file_path):
                os.remove(file_path)
        atexit.register(delete_file)
    return file_path


def read_file(file_path):
    """
    Reads the contents of the given file.
    :param file_path: the file path to read
    :return: the contents of the file
    """
    with open(file_path) as f:
        return f.read()
