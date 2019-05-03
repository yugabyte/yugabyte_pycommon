# Copyright (c) 2019 YugaByte, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
# in compliance with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.  See the License for the specific language governing permissions and limitations under
# the License.

import subprocess
import os
import sys
import semver


ALLOW_LOCAL_CHANGES = False

LICENSE_HEADER = """
# Copyright (c) YugaByte, Inc.

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


if __name__ == '__main__':
    local_changes = subprocess.check_output(
            ['git', 'diff-index', '--name-only', 'HEAD', '--']).strip()
    if not ALLOW_LOCAL_CHANGES and local_changes:
        raise RuntimeError('Local changes found!')
    subprocess.check_output(['git', 'fetch'])
    changes_vs_master = subprocess.check_output(
            ['git', 'diff', '--name-only', 'HEAD', 'origin/master']).strip()
    if not ALLOW_LOCAL_CHANGES and changes_vs_master:
        raise RuntimeError("Local changes not pushed to origin/master")

    tags_str = subprocess.check_output(['git', 'tag']).decode('utf-8')
    tags = [tag.strip() for tag in tags_str.split("\n") if tag.strip()]
    max_version = None
    for tag in tags:
        if tag.startswith('v'):
            version = tag[1:]
            if max_version is None or semver.compare(version, max_version) > 0:
                max_version = version
    if max_version is None:
        max_version = '0.1.0'

    diff_vs_max_version_tag = subprocess.check_output(
            ['git', 'diff', '--name-only', 'v%s' % max_version, 'HEAD']).strip()
    if not diff_vs_max_version_tag:
        from yugabyte_pycommon import version
        if version.__version__  == max_version:
            print("HEAD is already tagged as %s, no need to create a new tag" % max_version)
            sys.exit(0)
        else:
            print("The version.py file has version %s but the max version from tags is %s" %
                  (version.__version__, max_version))
    else:
        print("Found differences between max version from tag %s and HEAD:\n%s" % (
            max_version, diff_vs_max_version_tag))

    new_version = semver.bump_patch(max_version)
    version_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.py')
    with open(version_file_path, 'w') as version_file:
        version_file.write('%s\nversion = "%s"\n' % (LICENSE_HEADER, new_version))
    subprocess.check_call(['git', 'add', version_file_path])
    changes_needed = subprocess.check_output(
            ['git', 'diff', '--name-only', 'HEAD', version_file_path])
    if changes_needed:
        subprocess.check_call(
                ['git', 'commit', version_file_path, '-m', "Updating version to " + new_version])
    else:
        print("Version file is already up-to-date")
    subprocess.check_call(['git', 'push', 'origin', 'HEAD:master'])
    new_tag = 'v' + new_version
    subprocess.check_call(['git', 'tag', new_tag])
    subprocess.check_call(['git', 'push', 'origin', new_tag])
