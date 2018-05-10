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


import os
import re


def quote_for_bash(s):
    if s == '':
        return "''"
    if re.search(r"""['"${}()\\]""", s):
        return "'" + s.replace("'", r"'\''") + "'"
    return s


def safe_path_join(*args):
    """
    Like os.path.join, but allows arguments to be None. If all arguments are None, returns None.
    A special case: if the first argument is None, always return None. That allows to set a number
    of constants as relative paths under a certain path which may itself be None.

    >>> safe_path_join()
    >>> safe_path_join(None)
    >>> safe_path_join(None, None)
    >>> safe_path_join('/a', None, 'b')
    '/a/b'
    >>> safe_path_join(None, '/a', None, 'b')  # special case: first arg is None
    """
    if not args or args[0] is None:
        return None
    args = [arg for arg in args if arg is not None]
    return os.path.join(*args)


def cmd_line_args_to_str(args):
    """
    Converts a list of command-line arguments, including an executable program in the beginning,
    to a single command-line string suitable for pasing into Bash.

    :param args: an array with a program path and command-line arguments
    :return: a string suitable for pasing into Bash
    """
    return ' '.join([quote_for_bash(arg) for arg in args])


def trim_long_text(text, max_lines):
    """
    Trim a potentially long multi-line message at the given number of lines.
    :param text: the input text
    :param max_lines: maximum number of lines
    :return: the trimmed message
    """
    max_lines = max(max_lines, 3)

    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text

    # Here is the math involved:
    # lines_at_each_end * 2 + 1 <= max_lines
    # lines_at_each_end <= (max_lines - 1) / 2
    lines_to_keep_at_each_end = int((max_lines - 1) / 2)

    num_lines_skipped = len(lines) - lines_to_keep_at_each_end * 2
    if num_lines_skipped <= 0:
        return text

    return "\n".join(
        lines[:lines_to_keep_at_each_end] +
        ['({} lines skipped)'.format(num_lines_skipped)] +
        lines[-lines_to_keep_at_each_end:]
    )


def decode_utf8(bytes):
    if isinstance(bytes, str):
        return bytes
    return bytes.decode('utf-8')


def get_bool_env_var(env_var_name):
    """
    >>> os.environ['YB_TEST_VAR'] = '  1 '
    >>> get_bool_env_var('YB_TEST_VAR')
    True
    >>> os.environ['YB_TEST_VAR'] = '  0 '
    >>> get_bool_env_var('YB_TEST_VAR')
    False
    >>> os.environ['YB_TEST_VAR'] = '  TrUe'
    >>> get_bool_env_var('YB_TEST_VAR')
    True
    >>> os.environ['YB_TEST_VAR'] = 'fAlSe '
    >>> get_bool_env_var('YB_TEST_VAR')
    False
    >>> os.environ['YB_TEST_VAR'] = '  YeS '
    >>> get_bool_env_var('YB_TEST_VAR')
    True
    >>> os.environ['YB_TEST_VAR'] = 'No'
    >>> get_bool_env_var('YB_TEST_VAR')
    False
    >>> os.environ['YB_TEST_VAR'] = ''
    >>> get_bool_env_var('YB_TEST_VAR')
    False
    """
    value = os.environ.get(env_var_name, None)
    if value is None:
        return False

    return value.strip().lower() in ['1', 't', 'true', 'y', 'yes']

