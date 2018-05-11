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

"""Utilities for running external commands"""

import os
import logging
import subprocess

from yugabyte_pycommon.text_manipulation import cmd_line_args_to_str, decode_utf8, trim_long_text
from yugabyte_pycommon.logging_util import is_verbose_mode


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

    def success(self):
        return self.returncode != 0


class ExternalProgramError(Exception):
    def __init__(self, message, result):
        self.message = message
        self.result = result


work_dir_context_stack = []


class WorkDirContext:
    """
    Allows setting a context for running external programs. Does not actually change the working
    directory.

    Example:

    with WorkDirContext('/tmp'):
        run_program('ls')
    """
    def __init__(self, work_dir):
        self.work_dir = work_dir

    def __enter__(self):
        work_dir_context_stack.append(self)

    def __exit__(self, exception_type, exception_value, traceback):
        assert self is work_dir_context_stack[-1]
        work_dir_context_stack.pop()


def run_program(args, error_ok=False, max_error_lines=10000, cwd=None, shell=None, **kwargs):
    """
    Run the given program identified by its argument list, and return a ProgramResult object.
    :param error_ok: False to raise an exception on errors, True not to raise it.
    """
    if isinstance(args, tuple):
        args = list(args)

    if isinstance(args, str):
        args = [args]
        if shell is None:
            shell = True

    if cwd is None and work_dir_context_stack:
        cwd = work_dir_context_stack[-1].work_dir

    def normalize_arg(arg):
        if isinstance(arg, int):
            return str(arg)
        return arg

    args = [normalize_arg(arg) for arg in args]

    cmd_line_str = cmd_line_args_to_str(args)
    invocation_details_str = "external program in directory %s: %s" % (
        cwd or os.getcwd(), cmd_line_str)

    if is_verbose_mode():
        logging.info("Running %s", invocation_details_str)

    try:
        program_subprocess = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            cwd=cwd,
            **kwargs)

    except OSError:
        logging.error("Failed to run %s", invocation_details_str)
        raise

    program_stdout, program_stderr = program_subprocess.communicate()
    error_msg = None

    def cleanup_output(out_str):
        return decode_utf8(out_str.rstrip())

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
                program_subprocess.returncode, cmd_line_str,
                trim_long_text(clean_stdout, max_error_lines),
                trim_long_text(clean_stderr, max_error_lines))
        if not error_ok:
            raise ExternalProgramError(error_msg, result)

    return result
