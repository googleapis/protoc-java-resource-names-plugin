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
import subprocess

from plugin.pb2 import resource_pb2
from plugin.utils import gapic_utils
from google.protobuf.compiler import plugin_pb2
from google.protobuf import descriptor_pb2

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
    assert gapic_utils.reversed_variable_segments(
        "_deleted-topic_") == ["topic", "deleted"]


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
    assert gapic_utils.build_entity_names([
        "projects/{project}/topics/{topic}",
        "_deleted-topic_",
    ], "topic") == \
           {"projects/{project}/topics/{topic}": "topic",
            "_deleted-topic_": "deleted_topic"}


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


def test_vision_product_set():
    res = resource_pb2.ResourceDescriptor()
    res.type = 'vision.googleapis.com/ProductSet'
    res.pattern.append("projects/{project}/locations/{location}/productSets/{product_set}")

    collections = {}
    collection_oneofs = {}
    gapic_utils.update_collections(res, {}, collections, collection_oneofs)
    assert collections == {
        'product_set': {
            'entity_name': 'product_set',
            'name_pattern': 'projects/{project}/locations/{location}/productSets/{product_set}'
        },
    }


def test_pubsub():
    gapic_config = {}
    request = plugin_pb2.CodeGeneratorRequest()
    request.file_to_generate.append("google/pubsub/v1/pubsub.proto")

    file_descriptor_set_file = "test/testdata/test_output/pubsub.desc"
    subprocess.check_call(['protoc', '-o', file_descriptor_set_file, '--include_imports', '--proto_path=.',
                           '--proto_path=../googleapis',
                           'google/pubsub/v1/pubsub.proto'])
    with open(file_descriptor_set_file, 'rb') as f:
        file_descriptor_set = descriptor_pb2.FileDescriptorSet.FromString(
            f.read())

    request.proto_file.extend(file_descriptor_set.file)

    reconstructed_gapic_config = gapic_utils.reconstruct_gapic_yaml(gapic_config, request)
    assert reconstructed_gapic_config['collections'] == [
        {
            'entity_name': 'topic',
            'name_pattern': 'projects/{project}/topics/{topic}'
        },
        {
            'entity_name': 'deleted_topic',
            'name_pattern': '_deleted-topic_'
        },
        {
            'entity_name': 'subscription',
            'name_pattern': 'projects/{project}/subscriptions/{subscription}'
        },
    ]
    assert reconstructed_gapic_config['collection_oneofs'] == [
        {
            'collection_names': ['topic', 'deleted_topic'],
            'oneof_name': 'topic_oneof'
        }
    ]


#
# def test_vision():
#     gapic_config = {}
#     api_protofile = "google/cloud/vision/v1/product_search_service.proto"
#     request = plugin_pb2.CodeGeneratorRequest()
#     request.file_to_generate.append(api_protofile)
#
#     file_descriptor_set_file = "testdata/test_output/vision.desc"
#     subprocess.check_call(
#         ['protoc', '-o', file_descriptor_set_file, '--include_imports', '--proto_path=.', '--proto_path=../googleapis',
#          api_protofile])
#     with open(file_descriptor_set_file, 'rb') as f:
#         file_descriptor_set = descriptor_pb2.FileDescriptorSet.FromString(
#             f.read())
#
#     request.proto_file.extend(file_descriptor_set.file)
#
#     reconstructed_gapic_config = gapic_utils.reconstruct_gapic_yaml(gapic_config, request)
#     assert reconstructed_gapic_config['collections'] == [
#         {
#             'entity_name': 'product',
#             'name_pattern': 'projects/{project}/locations/{location}/products/{product}'
#         },
#         {
#             'entity_name': 'location',
#             'name_pattern': 'projects/{project}/locations/{location}'
#         },
#         {
#             'entity_name': 'product_set',
#             'name_pattern': 'projects/{project}/locations/{location}/productSets/{product_set}'
#         },
#         {
#             'entity_name': 'reference_image',
#             'name_pattern': 'projects/{project}/locations/{location}/products/{product}/referenceImages/{reference_image}'
#         }
#     ]
#     assert reconstructed_gapic_config['collection_oneofs'] == []
