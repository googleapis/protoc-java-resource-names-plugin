# Copyright 2020 Google Inc. All Rights Reserved.
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
import unittest
from unittest import TestCase

from plugin.utils.path_template import PathTemplate
"""
        "foos/{foo}/bars/{bar}~{car}~{cdr}",
        "foos/{foo}/bars/{bar}.{car}_{cdr}",
        "foos/{foo}/bars/{bar}-{car}.{cdr}~{zoo}",
"""


class PathTemplateTest(TestCase):

  def test_basic_patterns(self):
    path_template = PathTemplate("foos/{foo}/bars/{bar}")
    bindings = path_template.match("foos/foo1/bars/somebar")
    self.assertEqual(bindings["foo"], "foo1")
    self.assertEqual(bindings["bar"], "somebar")

    path_template = PathTemplate("foos/{name=*/bars}/{bar}")
    bindings = path_template.match("foos/foo1/bars/somebar")
    self.assertEqual(bindings["name"], "foo1")
    self.assertEqual(bindings["bar"], "somebar")

  def test_non_slash_resource_name_patterns(self):
    path_template = PathTemplate("foos/{foo}/bars/{bar}~{car}~{cdr}")
    bindings = path_template.match("foos/foo1/bars/abar~ferrari~iamlast")
    self.assertEqual(bindings["foo"], "foo1")
    self.assertEqual(bindings["bar"], "abar")
    self.assertEqual(bindings["car"], "ferrari")
    self.assertEqual(bindings["cdr"], "iamlast")

    path_template = PathTemplate("foos/{foo}/bars/{bar}_{car}.{cdr}")
    bindings = path_template.match("foos/foo1/bars/abar_ferrari.iamlast")
    self.assertEqual(bindings["foo"], "foo1")
    self.assertEqual(bindings["bar"], "abar")
    self.assertEqual(bindings["car"], "ferrari")
    self.assertEqual(bindings["cdr"], "iamlast")

    path_template = PathTemplate("foos/{foo}/bars/{bar_name}-{car-n}-{cdr_a}_{far-away}~{boo}")
    bindings = path_template.match("foos/foo1/bars/a-b-ar_away~ghost")
    self.assertEqual(bindings["foo"], "foo1")
    self.assertEqual(bindings["bar_name"], "a")
    self.assertEqual(bindings["car-n"], "b")
    self.assertEqual(bindings["cdr_a"], "ar")
    self.assertEqual(bindings["far-away"], "away")
    self.assertEqual(bindings["boo"], "ghost")


if __name__ == "__main__":
  unittest.main()
