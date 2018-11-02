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
Utilities for running external commands.
"""

import os
import sys
import logging
import subprocess
import tempfile
import threading

from yugabyte_pycommon.text_manipulation import cmd_line_args_to_str, decode_utf8, trim_long_text, \
    quote_for_bash
from yugabyte_pycommon.logging_util import is_verbose_mode


# Default number of lines to shorten long stdout/stderr to.
DEFAULT_MAX_LINES_TO_SHOW = 1000

DEFAULT_UNIX_SHELL = 'bash'


class ProgramResult:
    """
    This represents the result of executing an external program.
    """
    def __init__(self, cmd_line, cmd_line_str, returncode, stdout, stdout_path, stderr,
                 stderr_path, program_path, invocation_details_str, max_lines_to_show,
                 output_captured):
        self.cmd_line = cmd_line
        self.cmd_line_str = cmd_line_str
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.program_path = program_path
        self.invocation_details_str = invocation_details_str
        self.max_lines_to_show = max_lines_to_show
        self.output_captured = output_captured

        self._set_error_msg()

    def success(self):
        """
        :return: whether the external program exited with a success
        """
        return self.returncode == 0

    def failure(self):
        """
        :return: whether the external program exited with a failure
        """
        return self.returncode != 0

    def get_stdout_and_stderr_together(self):
        """
        :return: a string with user-friendly versions of stdout and stderr of the external program,
                 concatenated together.
        """
        stdout_and_stderr = (
            self.get_user_friendly_stdout_msg() + self.get_user_friendly_stderr_msg())
        if not stdout_and_stderr:
            stdout_and_stderr = "No stdout or stderr from command: " + self.invocation_details_str
        return stdout_and_stderr

    def print_output_to_stdout(self):
        """
        Print both stdout and stderr of the external program to the stdout.
        """
        sys.stdout.write(self.get_stdout_and_stderr_together())
        sys.stdout.flush()

    def _set_error_msg(self):
        if self.returncode == 0:
            self.error_msg = None
            return

        self.error_msg = "Non-zero exit code {} from {}.".format(
            self.returncode,
            self.invocation_details_str,
            self.returncode, cmd_line_args_to_str)

        self.error_msg += self.get_user_friendly_stdout_msg()
        self.error_msg += self.get_user_friendly_stderr_msg()
        self.error_msg = self.error_msg.rstrip()

    def get_stdout(self):
        if self.stdout is not None:
            return self.stdout
        if self.stdout_path is not None:
            from yugabyte_pycommon import read_file
            return read_file(self.stdout_path)

    def get_stderr(self):
        if self.stderr is not None:
            return self.stderr
        if self.stderr_path is not None:
            from yugabyte_pycommon import read_file
            return read_file(self.stderr_path)

    def _wrap_for_error_msg(self, stream_type):
        assert stream_type in ['output', 'error']
        if stream_type == 'output':
            value = self.get_stdout()
        else:
            value = self.get_stderr()
        if value is None or not value.strip():
            return ""
        value = value.rstrip()
        return "\nStandard {} from {}:\n{}\n(end of standard {})\n".format(
            stream_type, self.invocation_details_str,
            trim_long_text(value, self.max_lines_to_show),
            stream_type)

    def get_user_friendly_stdout_msg(self):
        """
        :return: a user-friendly version of the external program's standard output
        """
        return self._wrap_for_error_msg("output")

    def get_user_friendly_stderr_msg(self):
        """
        :return: a user-friendly version of the external program's standard error
        """
        return self._wrap_for_error_msg("error")

    def raise_error_if_failed(self):
        """
        This is useful for delayed handling of external program errors. Raises an error if the
        external program failed. Otherwise does nothing.
        """
        if self.failure():
            raise ExternalProgramError(self.error_msg, self)

    def print_output_and_raise_error_if_failed(self):
        if self.failure():
            # TODO: maybe print stdout to stdout, stderr to stderr?
            # TODO: avoid loading large output into memory.
            self.print_output_to_stdout()
            self.raise_error_if_failed()


class ExternalProgramError(Exception):
    def __init__(self, message, result):
        self.message = message
        self.result = result


class WorkDirContext:
    """
    Allows setting a working directory context for running external programs. The directory will
    be changed to the given directory on entering the block, and will be restored to the old
    directory on exit.

    .. code-block:: python

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
                max_lines_to_show=DEFAULT_MAX_LINES_TO_SHOW, cwd=None, shell=None,
                stdout_path=None, stderr_path=None, stdout_stderr_prefix=None, **kwargs):
    """
    Run the given program identified by its argument list, and return a :py:class:`ProgramResult`
    object.

    :param args: This could be a single string, or a tuple/list of elements where each element is
        either a string or an integer. If a single string is given as ``args``, and the ``shell``
        parameter is not specified, it is automatically set to true.
    :param report_errors: whether errors during execution (as identified by exit code) should be
        reported in the log.
    :param capture_output: whether standard output and standard error of the program need to be
        captured in variables inside of the resulting :py:class:`ProgramResult` object.
    :param error_ok: if this is true, we won't raise an exception in case the external program
                     fails.
    :param stdout_path: instead of trying to capture all standard output in memory, save it
        to this file. Both `stdout_file_path` and `stderr_file_path` have to be specified or
        unspecified at the same time. Also `shell` has to be true in this mode as we are using
        shell redirections to implement this.
    :param stderr_path: similar to ``stdout_file_path`` but for standard error.
    :param stdout_stderr_prefix: allows setting both `stdout_path` and `stderr_path` quickly.
        Those variables are set to the value of this parameter with `.out` and `.err` appended.
    """
    if isinstance(args, str) and shell is None:
        # If we are given a single string, assume it is a command line to be executed in a shell.
        shell = True

    if isinstance(args, str):
        # This is a special case, but very common.
        cmd_line_str = args
        args = [args]
    else:
        if isinstance(args, tuple):
            args = list(args)

        if isinstance(args, str):
            args = [args]

        def normalize_arg(arg):
            if isinstance(arg, int):
                return str(arg)
            return arg

        args = [normalize_arg(arg) for arg in args]

        cmd_line_str = cmd_line_args_to_str(args)

    if (stdout_path is None) != (stderr_path is None):
        raise ValueError(
            "stdout_file_path and stderr_file_path have to specified or unspecified at the same "
            "time. Got: stdout_file_path={}, stderr_file_path={}", stdout_path,
            stderr_path)

    output_to_files = stdout_path is not None
    if stdout_stderr_prefix is not None:
        if output_to_files:
            raise ValueError(
                "stdout_stderr_prefix cannot be specified at the same time with stdout_path "
                "or stderr_path")
        stdout_path = stdout_stderr_prefix + '.out'
        stderr_path = stdout_stderr_prefix + '.err'
        output_to_files = True

    if output_to_files and not shell:
        raise ValueError("If {stdout,stderr}_to_file are specified, shell must be True")

    invocation_details_str = "external program {{ %s }} running in '%s'" % (
            cmd_line_str, cwd or os.getcwd())

    if output_to_files:
        cmd_line_str = '( %s ) >%s 2>%s' % (
            cmd_line_str,
            quote_for_bash(stdout_path),
            quote_for_bash(stderr_path)
        )
        invocation_details_str += ", saving stdout to {{ %s }}, stderr to {{ %s }}" % (
            # For the ease of copying and pasting, convert to absolute paths.
            os.path.abspath(stdout_path),
            os.path.abspath(stderr_path)
        )

    if is_verbose_mode():
        logging.info("Running %s", invocation_details_str)

    tmp_script_path = None
    try:
        output_redirection = subprocess.PIPE if (capture_output and not output_to_files) else None
        args_to_run = args
        if shell:
            # Save the script to a temporary file to avoid anomalies with backslash un-escaping
            # described at http://bit.ly/2SFoMpN (on Ubuntu 18.04).
            with tempfile.NamedTemporaryFile(suffix='.sh', delete=False) as tmp_script_file:
                tmp_script_file.write(cmd_line_str.encode('utf-8'))
                tmp_script_path = tmp_script_file.name
                args_to_run = os.getenv('SHELL', DEFAULT_UNIX_SHELL) + ' ' + quote_for_bash(
                    tmp_script_path)

        program_subprocess = subprocess.Popen(
            args_to_run,
            stdout=output_redirection,
            stderr=output_redirection,
            shell=shell,
            cwd=cwd,
            **kwargs)

        program_stdout, program_stderr = program_subprocess.communicate()
        if output_to_files:
            def report_unexpected_output(stream_name, output):
                if output is not None and output.strip():
                    logging.warn(
                        "Unexpected standard %s from %s (should have been redirected):\n%s",
                        stream_name, invocation_details_str, output)

            report_unexpected_output('output', program_stdout)
            report_unexpected_output('error', program_stderr)
            program_stdout = None
            program_stderr = None

    except OSError:
        logging.error("Failed to run %s", invocation_details_str)
        raise

    finally:
        if tmp_script_path and os.path.exists(tmp_script_path):
            os.remove(tmp_script_path)

    def cleanup_output(out_str):
        if out_str is None:
            return None
        return decode_utf8(out_str)

    clean_stdout = cleanup_output(program_stdout)
    clean_stderr = cleanup_output(program_stderr)

    result = ProgramResult(
        cmd_line=args,
        cmd_line_str=cmd_line_str,
        program_path=os.path.realpath(args[0]),
        returncode=program_subprocess.returncode,
        stdout=clean_stdout,
        stdout_path=stdout_path,
        stderr=clean_stderr,
        stderr_path=stderr_path,
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
    :return: ``True`` if the program succeeded
    """
    return run_program(args, error_ok=True, report_errors=False, **kwargs).failure()


def program_succeeds_no_log(args, **kwargs):
    """
    Run the given program, and returns True if it succeeded. Does not log anything in case of
    success or failure.

    :param args: command line arguments or a single string to run as a shell command
    :param kwargs: additional keyword arguments for subprocess.Popen
    :return: ``True`` if the program failed
    """
    return run_program(args, error_ok=True, report_errors=False, **kwargs).success()


def program_succeeds_empty_output(args, **kwargs):
    """
    Runs a program that is not expected to produce any output.

    :param args: command line arguments or a single string to run as a shell command
    :param kwargs: additional keyword arguments for subprocess.Popen
    :raises ExternalProgramError: if the program succeeds but produces extra output
    :return: ``True`` if the program succeeds and does not produce any output
    """
    result = run_program(args, error_ok=True, report_errors=False, **kwargs)
    if result.failure():
        return False

    if result.stdout.strip():
        error_msg = "Unexpected output in case of success. " + result.get_user_friendly_stdout_msg()
        logging.error(error_msg)
        raise ExternalProgramError(error_msg, result)

    return True
