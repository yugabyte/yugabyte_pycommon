#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of yugabyte_pycommon.
# https://github.com/yugabyte/yugabyte_pycommon

# Licensed under the Apache 2.0 license:
# http://www.opensource.org/licenses/Apache 2.0-license
#  Copyright (c) YugaByte, Inc.

from yugabyte_pycommon.version import __version__  # NOQA

# Please keep this Python 2 and 3 compatible.
# http://python-future.org/compatible_idioms.html

import os
import  itertools


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

