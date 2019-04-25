# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from plugin.pb2 import resource_pb2
from plugin.utils import gapic_utils


def test_build_parent_patterns():
    patterns = [
        "foos/{foo}/bars/{bar}",
        "foos/{foo}/busy/bars/{bar}",
        "foos/{foo}/bars/{bar}/bang",
        "foos/{foo}",
    ]
    expected_parents = [
        "foos/{foo}",
        "foos/{foo}",
        "foos/{foo}/bars/{bar}",
        "",
    ]
    assert gapic_utils.build_parent_patterns(patterns) == expected_parents


def test_reversed_variable_segments():
    assert gapic_utils.reversed_variable_segments(
        "foos/{foo}/bars/{bar}") == ["bar", "foo"]
    assert gapic_utils.reversed_variable_segments(
        "foos/{foo}/busy/bars/{bar}") == ["bar", "foo"]


def test_build_trie_from_segments_list():
    segments_list = [
        ["bar", "foo"],
        ["bar", "baz", "foo"]
    ]
    expected_trie = {
        "bar": {
            "foo": {},
            "baz": {"foo": {}}
        }
    }
    assert gapic_utils.build_trie_from_segments_list(
        segments_list) == expected_trie


def test_build_entity_names():
    assert gapic_utils.build_entity_names([
        "foos/{foo}/bars/{bar}"], "") == \
        {"foos/{foo}/bars/{bar}": "bar"}
    assert gapic_utils.build_entity_names([
        "foos/{foo}/bars/{bar}"], "fuzz") == \
        {"foos/{foo}/bars/{bar}": "fuzz"}
    assert gapic_utils.build_entity_names([
        "foos/{foo}/bars/{bar}",
        "foos/{foo}/bazs/{baz}/bars/{bar}"], "") == \
        {"foos/{foo}/bars/{bar}": "foo",
         "foos/{foo}/bazs/{baz}/bars/{bar}": "baz"}
    assert gapic_utils.build_entity_names([
        "foos/{foo}/bars/{bar}",
        "foos/{foo}/bazs/{baz}/bars/{bar}"], "bar") == \
        {"foos/{foo}/bars/{bar}": "foo_bar",
         "foos/{foo}/bazs/{baz}/bars/{bar}": "baz_bar"}
    assert gapic_utils.build_entity_names([
        "foos/{foo}/bars/{bar}",
        "foos/{foo}/bazs/{baz}/bars/{bar}",
        "foos/{foo}/wizzs/{wizz}/bazs/{baz}/bars/{bar}"
    ], "bar") == \
        {"foos/{foo}/bars/{bar}": "foo_bar",
         "foos/{foo}/bazs/{baz}/bars/{bar}": "foo_baz_bar",
            "foos/{foo}/wizzs/{wizz}/bazs/{baz}/bars/{bar}": "wizz_baz_bar"}


def test_update_collections():
    res = resource_pb2.ResourceDescriptor()
    res.type = 'test/Book'
    res.pattern.append("shelves/{shelf}/books/{book}")
    res.pattern.append("archives/{archive}/books/{book}")
    res.history = resource_pb2.ResourceDescriptor.ORIGINALLY_SINGLE_PATTERN

    collections = {}
    collection_oneofs = {}
    gapic_utils.update_collections(res, {}, collections, collection_oneofs)
    assert collections == {
        'book': {
            'entity_name': 'book',
            'name_pattern': 'shelves/{shelf}/books/{book}'
        },
        'archive_book': {
            'entity_name': 'archive_book',
            'name_pattern': 'archives/{archive}/books/{book}'
        }
    }
    assert collection_oneofs == {
        'book_oneof': {
            'collection_names': ['book', 'archive_book'],
            'oneof_name': 'book_oneof'
        }
    }
