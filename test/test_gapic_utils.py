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
from plugin.templates import resource_name

import yaml

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


def test_update_collections_multi_pattern():
    res = resource_pb2.ResourceDescriptor()
    res.type = 'test/Book'
    res.pattern.append("shelves/{shelf}/books/{book}")
    res.pattern.append("archives/{archive}/books/{book}")

    collections = {}
    collection_oneofs = {}
    gapic_utils.update_collections(res, collections, collection_oneofs)
    assert collections == {}
    assert collection_oneofs == {
        'book_oneof': {
            'collection_names': [],
            'oneof_name': 'book_oneof'
        }
    }


def test_update_collections_single_pattern():
    res = resource_pb2.ResourceDescriptor()
    res.type = 'test/Book'
    res.pattern.append("shelves/{shelf}/books/{book}")

    collections = {}
    collection_oneofs = {}
    gapic_utils.update_collections(res, collections, collection_oneofs)
    assert collections == {
        'book': {
            'entity_name': 'book',
            'name_pattern': 'shelves/{shelf}/books/{book}'
        }
    }
    assert collection_oneofs == {}


def test_get_parent_resources_single_pattern():
    book = resource_pb2.ResourceDescriptor()
    book.type = 'test/Book'
    book.pattern.append("shelves/{shelf}/books/{book}")

    shelf = resource_pb2.ResourceDescriptor()
    shelf.type = 'test/Shelf'
    shelf.pattern.append("shelves/{shelf}")

    pattern_map = {
        "shelves/{shelf}/books/{book}": [book],
        "shelves/{shelf}": [shelf]
    }
    assert shelf == gapic_utils.get_parent_resource(book, pattern_map)


def test_get_parent_resources_multi_pattern():
    book = resource_pb2.ResourceDescriptor()
    book.type = 'test/Book'
    book.pattern.append("shelves/{shelf}/books/{book}")
    book.pattern.append("projects/{project}/books/{book}")

    shelf = resource_pb2.ResourceDescriptor()
    shelf.type = 'test/Shelf'
    shelf.pattern.append("shelves/{shelf}/books/{book}")

    parent = resource_pb2.ResourceDescriptor()
    parent.type = 'test/Parent'
    parent.pattern.append("shelves/{shelf}")
    parent.pattern.append("projects/{project}")

    pattern_map = {
        "shelves/{shelf}/books/{book}": [book],
        "projects/{project}/books/{book}": [book],
        "shelves/{shelf}": [parent],
        "projects/{project}": [parent]
    }
    assert parent == gapic_utils.get_parent_resource(book, pattern_map)


def test_get_parent_resources_multi_pattern_fail():
    book = resource_pb2.ResourceDescriptor()
    book.type = 'test/Book'
    book.pattern.append("shelves/{shelf}/books/{book}")
    book.pattern.append("projects/{project}/books/{book}")

    parent = resource_pb2.ResourceDescriptor()
    parent.type = 'test/Parent'
    parent.pattern.append("shelves/{shelf}")

    book_parent = resource_pb2.ResourceDescriptor()
    book_parent.type = 'test/BookParent'
    book_parent.pattern.append("shelves/{shelf}")
    book_parent.pattern.append("projects/{project}")
    book_parent.pattern.append("projects/{project}/locations/{location}")

    pattern_map = {
        "shelves/{shelf}/books/{book}": [book],
        "projects/{project}/books/{book}": [book],
        "shelves/{shelf}": [parent],
    }
    assert gapic_utils.get_parent_resource(book, pattern_map) is None


def test_update_collections_with_deprecated_collections():
    book = resource_pb2.ResourceDescriptor()
    book.type = 'test/Book'
    book.pattern.append("shelves/{shelf}/books/{book}")
    book.pattern.append("archives/{archive}/books/{book}")

    gapic_v2 = {
        'interfaces': [{
            'deprecated_collections': [
                {
                    'entity_name': 'some_archive_book',
                    'name_pattern': "archives/{archive}/books/{book}"
                },
                {
                    'entity_name': 'my_shelf_book',
                    'name_pattern': "shelves/{shelf}/books/{book}",
                    'language_overrides': [
                        {'language': 'java',
                         'entity_name': 'shelf_book'}]
                }
            ]}
        ]
    }

    collection_oneofs = {
        'book_oneof': {
            'oneof_name': 'book_oneof',
            'collection_names': []
        }
    }
    collections = {}
    pattern_map = {
        "archives/{archive}/books/{book}": [book],
        "shelves/{shelf}/books/{book}": [book]
    }

    gapic_utils.update_collections_with_deprecated_resources(
        gapic_v2, pattern_map, collections, collection_oneofs)

    assert collection_oneofs == {
        'book_oneof': {
            'oneof_name': 'book_oneof',
            'collection_names': [
                'some_archive_book', 'my_shelf_book']
        }
    }
    assert collections == {
        'some_archive_book': {
            'entity_name': 'some_archive_book',
            'name_pattern': "archives/{archive}/books/{book}"
        },
        'my_shelf_book': {
            'entity_name': 'my_shelf_book',
            'name_pattern': "shelves/{shelf}/books/{book}",
            'language_overrides': [
                {'language': 'java',
                 'entity_name': 'shelf_book'}]
        }
    }


def test_library_gapic_v1():

    request = plugin_pb2.CodeGeneratorRequest()
    proto_files = ["library_simple.proto", "archive.proto"]
    request.file_to_generate.extend(proto_files)
    request.parameter = "test/testdata/library_gapic_v1.yaml"

    with open(request.parameter) as f:
        gapic_yaml = yaml.load(f, Loader=yaml.SafeLoader)

    file_descriptor_set_file = "test/testdata/test_output/library.desc"
    subprocess.check_call(
        ['protoc',
         '-o',
         file_descriptor_set_file,
         '--include_imports',
         '--proto_path=test/testdata',
         '--proto_path=.',
         '--proto_path=./googleapis'] +
        proto_files)
    with open(file_descriptor_set_file, 'rb') as f:
        file_descriptor_set = descriptor_pb2.FileDescriptorSet.FromString(
            f.read())

    request.proto_file.extend(file_descriptor_set.file)

    gapic_config = gapic_utils.create_gapic_config(gapic_yaml)
    resource_name_artifacts = gapic_utils.collect_resource_name_types(
        gapic_config, "com.google.example.library.v1")
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceName
            and r.format_string == 'archives/{archive_id}/books/{book_id=**}'
            and r.format_name_lower == 'archivedBookName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceName
            and r.format_string == 'book/{book_id}'
            and r.format_name_lower == 'shelfBookName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceNameFixed
            and r.fixed_value == '_deleted-book_'
            and r.class_name == 'DeletedBook']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ParentResourceName
            and r.class_name == 'BookName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceNameFactory
            and r.class_name == 'BookNames']


def test_library_gapic_v2():

    request = plugin_pb2.CodeGeneratorRequest()
    proto_files = ["test/testdata/library_simple.proto",
                   "test/testdata/archive.proto",
                   "test/testdata/common_resources.proto"]
    request.file_to_generate.extend(proto_files)
    request.parameter = "test/testdata/library_gapic_v2.yaml"

    with open(request.parameter) as f:
        gapic_yaml = yaml.load(f, Loader=yaml.SafeLoader)

    file_descriptor_set_file = "test/testdata/test_output/library.desc"
    subprocess.check_call(
        ['protoc',
         '-o',
         file_descriptor_set_file,
         '--include_imports',
         '--proto_path=.',
         '--proto_path=../googleapis'] +
        proto_files)
    with open(file_descriptor_set_file, 'rb') as f:
        file_descriptor_set = descriptor_pb2.FileDescriptorSet.FromString(
            f.read())

    request.proto_file.extend(file_descriptor_set.file)

    reconstructed_gapic_config = gapic_utils.reconstruct_gapic_yaml(
        gapic_yaml, request)
    assert [c for c in [
        {
            'name_pattern': 'projects/{project}/shelves/{shelf}/books/{book}',
            'language_overrides': [
                {'language': 'java',
                 'entity_name': 'shelf_book'}
            ],
            'entity_name': 'book',
        },
        {
            'entity_name': 'deleted_book',
            'name_pattern': '_deleted-book_'
        },
        {
            'entity_name': 'archive_book',
            'name_pattern': 'archives/{archive}/books/{book}',
            'language_overrides': [{
                'language': 'java',
                'entity_name': 'archived_book'
            }]
        },
        {
            'name_pattern': 'projects/{project}/shelves/{shelf}',
            'entity_name': 'shelf',
        },
        {
            'name_pattern': 'projects/{project}',
            'entity_name': 'project',
        },
        {
            'name_pattern':
                'projects/{project}/locations/{location}/'
                'publishers/{publisher}',
            'entity_name': 'publisher',
        },
        {
            'entity_name': 'location',
            'name_pattern': 'projects/{project}/locations/{location}'
        },
        {
            'entity_name': 'folder',
            'name_pattern': 'folders/{folder}'
        },
    ] if c in reconstructed_gapic_config['collections']]
    assert reconstructed_gapic_config['collection_oneofs'] == [
        {
            'collection_names': ['book', 'archive_book', 'deleted_book'],
            'oneof_name': 'book_oneof'
        }
    ]

    gapic_config = gapic_utils.create_gapic_config(reconstructed_gapic_config)
    resource_name_artifacts \
        = gapic_utils.collect_resource_name_types(
            gapic_config, "com.google.example.library.v1")
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceName
            and r.format_string ==
            'projects/{project}/shelves/{shelf}/books/{book}'
            and r.format_name_lower == 'shelfBookName'
            and r.parent_interface == 'BookName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceName
            and r.format_string == 'archives/{archive}/books/{book}'
            and r.format_name_lower == 'archivedBookName'
            and r.parent_interface == 'BookName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceName
            and r.format_string == 'projects/{project}/shelves/{shelf}'
            and r.format_name_lower == 'shelfName'
            and r.parent_interface == 'ResourceName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceNameFixed
            and r.fixed_value == '_deleted-book_'
            and r.class_name == 'DeletedBook'
            and r.parent_interface == 'BookName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ParentResourceName
            and r.class_name == 'BookName']
    assert [r for r in resource_name_artifacts if
            type(r) is resource_name.ResourceNameFactory
            and r.class_name == 'BookNames']
