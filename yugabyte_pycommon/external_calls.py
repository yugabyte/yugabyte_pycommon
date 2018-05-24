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
import sys
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
    def __init__(self, cmd_line, returncode, stdout, stderr, program_path,
                 invocation_details_str, max_lines_to_show, output_captured):
        self.cmd_line = cmd_line
        self.cmd_line_str = cmd_line_args_to_str(self.cmd_line)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.program_path = program_path
        self.invocation_details_str = invocation_details_str
        self.max_lines_to_show = max_lines_to_show
        self.output_captured = output_captured

        self._set_error_msg()

    def success(self):
        return self.returncode == 0

    def failure(self):
        return self.returncode != 0

    def print_output_to_stdout(self):
        """
        Print both stdout and stderr of the external program to the stdout.
        """
        stdout_and_stderr = self.stdout_for_error_msg() + self.stdout_for_log_msg()
        if not stdout_and_stderr:
            stdout_and_stderr = "No stdout or stderr from command: " + self.invocation_details_str
        sys.stdout.write(stdout_and_stderr)
        sys.stdout.flush()

    def _set_error_msg(self):
        if self.returncode == 0:
            self.error_msg = None
            return

        self.error_msg = "Non-zero exit code {} from {}.".format(
            self.returncode,
            self.invocation_details_str,
            self.returncode, cmd_line_args_to_str)

        self.error_msg += self.stdout_for_error_msg()
        self.error_msg += self.stderr_for_error_msg()
        self.error_msg = self.error_msg.rstrip()

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

    def raise_error_if_failed(self):
        if self.failure():
            raise ExternalProgramError(self.error_msg, self)


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
        invocation_details_str=invocation_details_str,
        max_lines_to_show=max_lines_to_show,
        output_captured=capture_output)

    if program_subprocess.returncode != 0:
        if report_errors is None:
            report_errors = not error_ok
        if report_errors:
            logging.error(result.error_msg)
        if not error_ok:
            result.raise_error_if_failed()

    return result


def check_run_program(*args, **kwargs):
    """
    Similar to subprocess.check_call but using our run_program facility.
    """
    kwargs['capture_output'] = False
    kwargs['report_errors'] = True
    run_program(*args, **kwargs)
    return 0


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
