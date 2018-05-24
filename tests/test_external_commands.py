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

from .base import TestCase

import os

from yugabyte_pycommon import run_program, quote_for_bash, ExternalProgramError, WorkDirContext, \
    program_fails_no_log, program_succeeds_no_log, program_succeeds_empty_output, check_run_program
import logging
from testfixtures import LogCapture

class ExternalCommandsTestCase(TestCase):
    def test_run_program_noerror(self):
        result = run_program("true")
        self.assertEquals(0, result.returncode)
        self.assertEquals('', result.stdout)
        self.assertEquals('', result.stderr)

    def test_exit_codes(self):
        for exit_code in [0, 1, 2, 3, 10, 20, 100, 150, 200, 250, 255]:
            result = run_program("exit %d" % exit_code, shell=True, error_ok=exit_code != 0)
            self.assertEquals(exit_code, result.returncode)

    def test_error_reporing(self):
        with self.assertRaises(ExternalProgramError):
            run_program('false')

    def test_work_dir_context(self):
        old_work_dir = os.getcwd()
        for d in ['/tmp', os.path.expanduser('~')]:
            with WorkDirContext(d):
                self.assertEquals(d, os.getcwd())
                self.assertEquals(d, run_program('pwd').stdout.strip())

        self.assertEquals(old_work_dir, os.getcwd())

    def _capture_error_log_from_cmd(self, cmd):
        with LogCapture(level=logging.ERROR) as captured_logs:
            run_program(cmd, error_ok=True, report_errors=True)
        return str(captured_logs).strip()

    def test_log_error(self):
        self.assertRegexpMatches(
            self._capture_error_log_from_cmd("echo Output!; exit 1"), r"""
Non-zero exit code 1 from external program {{ echo Output!; exit 1 }} running in '.*'.
Standard output from external program {{ echo Output!; exit 1 }} running in '.*':
Output!
\(end of standard output\)""".strip())

        self.assertRegexpMatches(
            self._capture_error_log_from_cmd("echo Output!; echo Error! >&2; exit 1"), r"""
Non-zero exit code 1 from external program {{ echo Output!; echo Error! >&2; exit 1 }} running in '.*'.
Standard output from external program {{ echo Output!; echo Error! >&2; exit 1 }} running in '.*':
Output!
\(end of standard output\)
.*
Standard error from external program {{ echo Output!; echo Error! >&2; exit 1 }} running in '.*':
Error!
\(end of standard error\)""".strip())

    def test_shortcut_functions(self):
        self.assertTrue(program_fails_no_log('false'))
        self.assertFalse(program_fails_no_log('true'))
        self.assertFalse(program_succeeds_no_log('false'))
        self.assertTrue(program_succeeds_no_log('true'))
        self.assertTrue(program_succeeds_empty_output('true'))
        self.assertFalse(program_succeeds_empty_output('false'))
        with self.assertRaises(ExternalProgramError):
            self.assertTrue(program_succeeds_empty_output('echo foo'))

    def test_check_run_program(self):
        self.assertEquals(0, check_run_program('true'))
        with self.assertRaises(ExternalProgramError):
            check_run_program('false')

    def test_no_output_capture(self):
        result = run_program(
            'echo "This is expected to show up in the test output"',
            capture_output=False)
        self.assertIsNone(result.stdout)
        self.assertIsNone(result.stderr)
        self.assertFalse(result.output_captured)

    def test_error_msg(self):
        # No error message if exit code is 0.
        self.assertIsNone(run_program('true').error_msg)

        result = run_program(
            'echo " This is stdout! "; echo " This is stderr! " >&2; exit 1', error_ok=True)
        self.assertRegexpMatches(
            result.error_msg.strip(),
"""
Non-zero exit code 1 from external program {{ echo " This is stdout! "; echo " This is stderr! " >&2; exit 1 }} running in '.*'.
Standard output from external program {{ echo " This is stdout! "; echo " This is stderr! " >&2; exit 1 }} running in '.*':
 This is stdout!
\(end of standard output\)

Standard error from external program {{ echo " This is stdout! "; echo " This is stderr! " >&2; exit 1 }} running in '.*':
 This is stderr!
\(end of standard error\)
""".strip())

    def test_stdout_and_stderr_together(self):
        self.assertRegexpMatches(
            run_program('echo foo').get_stdout_and_stderr_together().strip(), r"""
Standard output from external program {{ echo foo }} running in '.*':
foo
\(end of standard output\)
            """.strip())
        self.assertRegexpMatches(
            run_program('echo bar >&2').get_stdout_and_stderr_together().strip(), r"""
Standard error from external program {{ echo bar >&2 }} running in '.*':
bar
\(end of standard error\)
            """.strip())
        self.assertRegexpMatches(
            run_program('echo foo; echo bar >&2').get_stdout_and_stderr_together().strip(), r"""
Standard output from external program {{ echo foo; echo bar >&2 }} running in '.*':
foo
\(end of standard output\)

Standard error from external program {{ echo foo; echo bar >&2 }} running in '.*':
bar
\(end of standard error\)
            """.strip())

