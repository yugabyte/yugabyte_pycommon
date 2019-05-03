# This file is part of yugabyte_pycommon.
# https://github.com/yugabyte/yugabyte_pycommon
SHELL:=bash

# Licensed under the Apache 2.0 license:
# http://www.opensource.org/licenses/Apache 2.0-license
#  Copyright (c) YugaByte, Inc.

.PHONY: docs list release setup test tox coverage-html unit venv

# lists all available targets
list:
	@sh -c "$(MAKE) -p no_targets__ | awk -F':' '/^[a-zA-Z0-9][^\$$#\/\\t=]*:([^=]|$$)/ {split(\$$1,A,/ /);for(i in A)print A[i]}' | grep -v '__\$$' | grep -v 'make\[1\]' | grep -v 'Makefile' | sort"
# required for list
no_targets__:

# install all dependencies (do not forget to create a virtualenv first)
setup:
	@pip install -U -e .\[tests\]
	@pip install -U -e .\[docs\]

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

release: tox
	rm -f dist/*
	python setup.py sdist
	ls dist/*
	exit 1
	pip install --user twine
	twine upload dist/yugabyte_pycommon*.tar.gz

docs: venv
	@. venv/bin/activate && cd docs && make html

venv:
	if [[ ! -d venv ]]; then \
		python3 -m virtualenv venv; \
		. venv/bin/activate && pip install -e .[core] .[docs]; \
	fi
