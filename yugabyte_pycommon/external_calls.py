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


def run_program(args, error_ok=False, report_errors=None, max_error_lines=10000,
                cwd=None, shell=None, **kwargs):
    """
    Run the given program identified by its argument list, and return a ProgramResult object.
    :param error_ok: False to raise an exception on errors, True not to raise it.
    """
    ("Hello world!")
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
    invocation_details_str = "external program {{ %s }} running in '%s'" % (
            cmd_line_str, cwd or os.getcwd())

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

    logging.info("report_errors=%s", report_errors)
    if program_subprocess.returncode != 0:
        error_msg = "Non-zero exit code {} from {}.".format(
                program_subprocess.returncode,
                invocation_details_str,
                program_subprocess.returncode, cmd_line_str)

        def wrap_for_error_msg(output_or_error, value):
            if not value.strip():
                return ""
            return "\nStandard {} from {}:\n{}\n(end of standard {})\n".format(
                output_or_error, invocation_details_str, trim_long_text(value, max_error_lines),
                output_or_error)

        error_msg += wrap_for_error_msg("output", clean_stdout)
        error_msg += wrap_for_error_msg("error", clean_stderr)
        error_msg = error_msg.rstrip()

        if report_errors is None:
            report_errors = not error_ok
        if report_errors:
            logging.error(error_msg)
        # TODO: optionally write raw stdout/stderr to files for better debugging.

        if not error_ok:
            raise ExternalProgramError(error_msg, result)

    return result
