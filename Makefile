# This file is part of yugabyte_pycommon.
# https://github.com/yugabyte/yugabyte_pycommon

# Licensed under the Apache 2.0 license:
# http://www.opensource.org/licenses/Apache 2.0-license
#  Copyright (c) YugaByte, Inc.

# lists all available targets
list:
	@sh -c "$(MAKE) -p no_targets__ | awk -F':' '/^[a-zA-Z0-9][^\$$#\/\\t=]*:([^=]|$$)/ {split(\$$1,A,/ /);for(i in A)print A[i]}' | grep -v '__\$$' | grep -v 'make\[1\]' | grep -v 'Makefile' | sort"
# required for list
no_targets__:

# install all dependencies (do not forget to create a virtualenv first)
setup:
	@pip install -U -e .\[tests\]

# test your application (tests in the tests/ directory)
test: unit

unit:
	@coverage run --branch `which nosetests` -vv -s tests/ -s yugabyte_pycommon/ --with-doctest
	# TODO: increase the coverage threshold here when appropriate.
	@coverage report -m --fail-under=10

# show coverage in html format
coverage-html: unit
	@coverage html

# run tests against all supported python versions
tox:
	pip install --user tox
	@tox

#docs:
	#@cd yugabyte_pycommon/docs && make html && open _build/html/index.html
