# Copyright 2016 Google Inc. All Rights Reserved.
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

import os
import pytest
import subprocess
import shutil
import difflib
from sys import stderr

from plugin.utils import casing_utils


TEST_DIR = os.path.join('test', 'testdata')
TEST_OUTPUT_DIR = os.path.join(TEST_DIR, 'test_output')


def check_output(output_class, output_path, baseline):
    baseline_file = os.path.join(TEST_DIR, baseline + '.baseline')
    with open(baseline_file) as f:
        expected_output = f.readlines()

    actual_output_file = os.path.join(TEST_OUTPUT_DIR,
                                      output_path,
                                      output_class + '.java')
    with open(actual_output_file) as f:
        actual_output = f.readlines()

    assert expected_output == actual_output, 'Baseline error. File "' \
        + baseline_file + '" did not match "' \
        + actual_output_file + '"\nDiff:\n' \
        + diff(expected_output,
               actual_output,
               baseline_file,
               actual_output_file)


def diff(expected_output, actual_output, fromfile, tofile):
    difflines = list(difflib.context_diff(expected_output,
                                          actual_output,
                                          fromfile=fromfile,
                                          tofile=tofile))
    if len(difflines) > 50:
        difflines = difflines[:50]
        difflines.append('*** diff too long, truncating ***\n')
    return "".join(difflines)


def run_protoc_gapic_plugin(output_dir, gapic_yaml, include_dirs, proto_files,
                            lang_out=None):
    def format_output_arg(name, output_dir, extra_arg=None):
        if extra_arg:
            return '--{}_out={}:{}'.format(name, extra_arg, output_dir)
        else:
            return '--{}_out={}'.format(name, output_dir)

    args = ['protoc']
    if lang_out is not None:
        args.append(format_output_arg(lang_out, output_dir))
    args += [format_output_arg('gapic', output_dir, gapic_yaml),
             '--plugin=protoc-gen-gapic=gapic_plugin.py']
    args += ['-I' + path for path in include_dirs]
    args += proto_files
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError as exc:
        stderr.write("Status : FAIL, message %s" % exc.output)


def clean_test_output():
    shutil.rmtree(TEST_OUTPUT_DIR, True)
    os.mkdir(TEST_OUTPUT_DIR)


@pytest.fixture(scope='class')
def run_protoc():
    clean_test_output()
    gapic_yaml = os.path.join(TEST_DIR, 'library_gapic.yaml')
    # TODO: make this path configurable
    include_dirs = ['.', './googleapis']
    proto_files = ['library_simple.proto', 'archive.proto']
    run_protoc_gapic_plugin(TEST_OUTPUT_DIR,
                            gapic_yaml,
                            include_dirs,
                            [os.path.join(TEST_DIR, x) for x in proto_files],
                            'java')


RESOURCE_NAMES_TO_GENERATE = ['shelf_book_name', 'shelf_name',
                              'archived_book_name', 'deleted_book']
ONEOFS_TO_GENERATE = ['book_oneof']
DONT_GENERATE = ['project_name']

PROTOC_OUTPUT_DIR = os.path.join('com', 'google', 'example', 'library', 'v1')


class TestProtocGapicPlugin(object):

    @pytest.mark.parametrize('resource', RESOURCE_NAMES_TO_GENERATE)
    def test_resource_name_generation(self, run_protoc, resource):
        generated_class = casing_utils.lower_underscore_to_upper_camel(
            resource)
        check_output(generated_class, PROTOC_OUTPUT_DIR, 'java_' + resource)

    @pytest.mark.parametrize('resource', DONT_GENERATE)
    def test_dont_generate(self, run_protoc, resource):
        generated_class = casing_utils.lower_underscore_to_upper_camel(
            resource)
        file_name = os.path.join(TEST_OUTPUT_DIR,
                                 PROTOC_OUTPUT_DIR,
                                 generated_class + '.java')
        assert not os.path.exists(file_name)

    @pytest.mark.parametrize('oneof', ONEOFS_TO_GENERATE)
    def test_parent_resource_name_generation(self, run_protoc, oneof):
        generated_parent = \
            casing_utils.get_parent_resource_name_class_name(oneof)
        parent_filename_fragment = \
            casing_utils.get_parent_resource_name_lower_underscore(oneof)
        check_output(generated_parent,
                     PROTOC_OUTPUT_DIR,
                     'java_' + parent_filename_fragment)

    @pytest.mark.parametrize('oneof', ONEOFS_TO_GENERATE)
    def test_untyped_resource_name_generation(self, run_protoc, oneof):
        generated_untyped = \
            casing_utils.get_untyped_resource_name_class_name(oneof)
        untyped_filename_fragment = \
            casing_utils.get_untyped_resource_name_lower_underscore(oneof)
        check_output(generated_untyped,
                     PROTOC_OUTPUT_DIR,
                     'java_' + untyped_filename_fragment)

    @pytest.mark.parametrize('oneof', ONEOFS_TO_GENERATE)
    def test_resource_name_factory_generation(self, run_protoc, oneof):
        generated_parent = \
            casing_utils.get_resource_name_factory_class_name(oneof)
        parent_filename_fragment = \
            casing_utils.get_resource_name_factory_lower_underscore(oneof)
        check_output(generated_parent,
                     PROTOC_OUTPUT_DIR,
                     'java_' + parent_filename_fragment)
