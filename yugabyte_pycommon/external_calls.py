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
import threading

from yugabyte_pycommon.text_manipulation import cmd_line_args_to_str, decode_utf8, trim_long_text
from yugabyte_pycommon.logging_util import is_verbose_mode


# Default number of lines to shorten long stdout/stderr to.
DEFAULT_MAX_LINES_TO_SHOW = 1000


class ProgramResult:
    """
    This represents the result of executing an external program.
    """
    def __init__(self, cmd_line, returncode, stdout, stderr, error_msg, program_path,
                 invocation_details_str, max_lines_to_show, output_captured):
        self.cmd_line = cmd_line
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.error_msg = error_msg
        self.program_path = program_path
        self.invocation_details_str = invocation_details_str
        self.max_lines_to_show = max_lines_to_show
        self.output_captured = output_captured

    def success(self):
        return self.returncode == 0

    def failure(self):
        return self.returncode != 0

    def _wrap_for_error_msg(self, stream_type):
        assert stream_type in ['output', 'error']
        if stream_type == 'output':
            value = self.stdout
        else:
            value = self.stderr
        if value is None or not value.strip():
            return ""
        return "\nStandard {} from {}:\n{}\n(end of standard {})\n".format(
            stream_type, self.invocation_details_str,
            trim_long_text(value, self.max_lines_to_show),
            stream_type)

    def stdout_for_error_msg(self):
        return self._wrap_for_error_msg("output")

    def stderr_for_error_msg(self):
        return self._wrap_for_error_msg("error")


class ExternalProgramError(Exception):
    def __init__(self, message, result):
        self.message = message
        self.result = result


class WorkDirContext:
    """
    Allows setting a context for running external programs.

    Example:

    with WorkDirContext('/tmp'):
        run_program('ls')
    """
    def __init__(self, work_dir):
        self.thread_local = threading.local()
        self.work_dir = work_dir

    def __enter__(self):
        self.thread_local.old_dir = os.getcwd()
        os.chdir(self.work_dir)

    def __exit__(self, exception_type, exception_value, traceback):
        os.chdir(self.thread_local.old_dir)


def run_program(args, error_ok=False, report_errors=None, capture_output=True,
                max_lines_to_show=DEFAULT_MAX_LINES_TO_SHOW, cwd=None, shell=None, **kwargs):
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
        output_redirection = subprocess.PIPE if capture_output else None
        program_subprocess = subprocess.Popen(
            args,
            stdout=output_redirection,
            stderr=output_redirection,
            shell=shell,
            cwd=cwd,
            **kwargs)
        program_stdout, program_stderr = program_subprocess.communicate()

    except OSError:
        logging.error("Failed to run %s", invocation_details_str)
        raise

    error_msg = None

    def cleanup_output(out_str):
        if out_str is None:
            return None
        return decode_utf8(out_str.rstrip())

    clean_stdout = cleanup_output(program_stdout)
    clean_stderr = cleanup_output(program_stderr)

    result = ProgramResult(
        cmd_line=args,
        program_path=os.path.realpath(args[0]),
        returncode=program_subprocess.returncode,
        stdout=clean_stdout,
        stderr=clean_stderr,
        error_msg=error_msg,
        invocation_details_str=invocation_details_str,
        max_lines_to_show=max_lines_to_show,
        output_captured=capture_output)

    if program_subprocess.returncode != 0:
        error_msg = "Non-zero exit code {} from {}.".format(
                program_subprocess.returncode,
                invocation_details_str,
                program_subprocess.returncode, cmd_line_str)

        error_msg += result.stdout_for_error_msg()
        error_msg += result.stderr_for_error_msg()
        error_msg = error_msg.rstrip()

        if report_errors is None:
            report_errors = not error_ok
        if report_errors:
            logging.error(error_msg)
        # TODO: optionally write raw stdout/stderr to files for better debugging.

        if not error_ok:
            raise ExternalProgramError(error_msg, result)

    return result


def program_fails_no_log(args, **kwargs):
    """
    Run the given program, and returns if it failed. Does not log anything in case of success
    or failure.
    :param args: command line arguments or a single string to run as a shell command
    :param kwargs: additional keyword arguments for subprocess.Popen
    :return: True if the program succeeded
    """
    return run_program(args, error_ok=True, report_errors=False, **kwargs).failure()


def program_succeeds_no_log(args, **kwargs):
    """
    Run the given program, and returns True if it succeeded. Does not log anything in case of
    success or failure.
    :param args: command line arguments or a single string to run as a shell command
    :param kwargs: additional keyword arguments for subprocess.Popen
    :return: True if the program failed
    """
    return run_program(args, error_ok=True, report_errors=False, **kwargs).success()


def program_succeeds_empty_output(args, **kwargs):
    """
    Runs a program that is not expected to produce any output.
    :param args: command line arguments or a single string to run as a shell command
    :param kwargs: additional keyword arguments for subprocess.Popen
    :raises ExternalProgramError: if the program succeeds but produces extra output
    :return: True if the program succeeds and does not produce any output
    """
    result = run_program(args, error_ok=True, report_errors=False, **kwargs)
    if result.failure():
        return False

    if result.stdout.strip():
        error_msg = "Unexpected output in case of success. " + result.stdout_for_error_msg()
        logging.error(error_msg)
        raise ExternalProgramError(error_msg, result)

    return True
