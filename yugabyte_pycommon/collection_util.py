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

import itertools


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
