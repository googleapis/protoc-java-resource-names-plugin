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

import mock
import os
import pytest
import subprocess
import shutil

TEST_DIR = os.path.join('test', 'testdata')
TEST_OUTPUT_DIR = os.path.join(TEST_DIR, 'test_output')

def read_baseline(baseline):
  filename = os.path.join(TEST_DIR, baseline + '.baseline')
  with open(filename) as f:
    return f.readlines()


def check_output(actual_output_file, baseline):
  with open(actual_output_file) as f:
    actual_output = f.readlines()
  expected_output = read_baseline(baseline)
  assert expected_output == actual_output, "Baseline error.\nExpected: " \
      + str(expected_output) \
      + "\nActual: " \
      + str(actual_output)


def run_protoc_gapic_plugin(output_dir, include_dirs, proto, lang_out=None):
  def format_output_arg(name, output_dir):
    return '--{}_out={}'.format(name, output_dir)

  args = ['protoc']
  if lang_out is not None:
    args.append(format_output_arg(lang_out, output_dir))
  args += [format_output_arg('gapic', output_dir),
           '--plugin=protoc-gen-gapic=gapic_plugin.py']
  args += ['-I' + path for path in include_dirs]
  args.append(proto)
  subprocess.check_call(args)


def clean_test_output():
  shutil.rmtree(TEST_OUTPUT_DIR, True)
  os.mkdir(TEST_OUTPUT_DIR)


def test_resource_name_generation():
  clean_test_output()
  include_dirs = ['.', '../googleapis']
  run_protoc_gapic_plugin(TEST_OUTPUT_DIR,
                          include_dirs,
                          os.path.join(TEST_DIR, 'library_simple.proto'),
                          'java')
  generated_output_dir = os.path.join(TEST_OUTPUT_DIR,
                                      'com',
                                      'google',
                                      'example',
                                      'library',
                                      'v1')
  check_output(os.path.join(generated_output_dir, 'BookName.java'), 'java_standard_book_name')
