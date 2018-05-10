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

from yugabyte_pycommon.version import __version__  # NOQA

# Please keep this Python 2 and 3 compatible.
# http://python-future.org/compatible_idioms.html

import os
import itertools
import subprocess
import logging
import re

from collections import namedtuple


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


def group_by_to_list(arr, key_fn):
    """
    Group the given list-like collection by the key computed using the given function. The
    collection does not have to be sorted in advance.

    @return a list of (key, list_of_values) tuples where keys are sorted

    >>> group_by_to_list([100, 201, 300, 301, 400], lambda x: x % 2)
    [(0, [100, 300, 400]), (1, [201, 301])]
    >>> group_by_to_list([100, 201, 300, 301, 400, 401, 402], lambda x: x % 3)
    [(0, [201, 300, 402]), (1, [100, 301, 400]), (2, [401])]

    """
    return [(k, list(v)) for (k, v) in itertools.groupby(sorted(arr, key=key_fn), key_fn)]


def group_by_to_dict(arr, key_fn):
    """
    Given a list-like collection and a function that computes a key, returns a map from keys to all
    values with that key.

    >>> group_by_to_dict([100, 201, 300, 301, 400], lambda x: x % 2)
    {0: [100, 300, 400], 1: [201, 301]}
    >>> group_by_to_dict([100, 201, 300, 301, 400, 401, 402], lambda x: x % 3)
    {0: [201, 300, 402], 1: [100, 301, 400], 2: [401]}
    """
    return dict(group_by_to_list(arr, key_fn))


def make_list(obj):
    """
    Convert the given object to a list. Strings get converted to a list of one string, not to a
    list of their characters. Sets are sorted.

    >>> make_list('asdf')
    ['asdf']
    >>> make_list(['a', 'b', 'c'])
    ['a', 'b', 'c']
    >>> make_list(set(['z', 'a', 'b']))
    ['a', 'b', 'z']
    >>> make_list(set(['z', 'a', 10, 20]))
    [10, 20, 'a', 'z']
    >>> make_list(set([10, 20, None, 'a', 'z']))
    [10, 20, None, 'a', 'z']
    """
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, set):
        # Sort by string representation because objects of different types are not comparable in
        # Python 3.
        return sorted(obj, key=lambda item: str(item))
    return list(obj)


def make_set(obj):
    if isinstance(obj, set):
        return obj
    return set(make_list(obj))


# ------------------------------------------------------------------------------------------------
# Filesystem utilities
# ------------------------------------------------------------------------------------------------


def mkdir_p(d):
    """
    Similar to the "mkdir -p ..." shell command. Creates the given directory and all enclosing
    directories. No-op if the directory already exists.

    """

    if os.path.isdir(d):
        return
    try:
        os.makedirs(d)
    except OSError:
        if os.path.isdir(d):
            return
        raise


def decode_utf8(bytes):
    if isinstance(bytes, str):
        return bytes
    return bytes.decode('utf-8')


# ------------------------------------------------------------------------------------------------
# Utilities for running external commands
# ------------------------------------------------------------------------------------------------

class ProgramResult:
    """
    This represents the result of executing an external program.
    """
    def __init__(self, cmd_line, returncode, stdout, stderr, error_msg, program_path):
        self.cmd_line = cmd_line
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.error_msg = error_msg
        self.program_path = program_path


class ExternalProgramError(Exception):
    def __init__(self, message, result):
        self.message = message
        self.result = result


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


def quote_for_bash(s):
    if s == '':
        return "''"
    if re.search(r"""['"${}()\\]""", s):
        return "'" + s.replace("'", r"'\''") + "'"
    return s


def cmd_line_args_to_str(args):
    """
    Converts a list of command-line arguments, including an executable program in the beginning,
    to a single command-line string suitable for pasing into Bash.

    :param args: an array with a program path and command-line arguments
    :return: a string suitable for pasing into Bash
    """
    return ' '.join([quote_for_bash(arg) for arg in args])


def run_program(args, error_ok=False, max_error_lines=10000, **kwargs):
    """
    Run the given program identified by its argument list, and return a ProgramResult object.
    :param error_ok: False to raise an exception on errors, True not to raise it.
    """
    if not isinstance(args, list):
        args = [args]

    def normalize_arg(arg):
        if isinstance(arg, int):
            return str(arg)
        return arg
    args = [normalize_arg(arg) for arg in args]

    try:
        program_subprocess = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **kwargs)

    except OSError:
        logging.error("Failed to run program {}".format(args))
        raise

    program_stdout, program_stderr = program_subprocess.communicate()
    error_msg = None

    def cleanup_output(out_str):
        return decode_utf8(out_str.strip())
    clean_stdout = cleanup_output(program_stdout)
    clean_stderr = cleanup_output(program_stderr)

    result = ProgramResult(
        cmd_line=args,
        program_path=os.path.realpath(args[0]),
        returncode=program_subprocess.returncode,
        stdout=clean_stdout,
        stderr=clean_stderr,
        error_msg=error_msg)

    if program_subprocess.returncode != 0:
        error_msg = "Non-zero exit code {} from: {} ; stdout: '{}' stderr: '{}'".format(
                program_subprocess.returncode, cmd_line_args_to_str(args),
                trim_long_text(clean_stdout, max_error_lines),
                trim_long_text(clean_stderr, max_error_lines))
        if not error_ok:
            raise ExternalProgramError(error_msg, result)

    return result

