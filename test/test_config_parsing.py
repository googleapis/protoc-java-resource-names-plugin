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
from plugin.utils import gapic_utils
from unittest import TestCase
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
GAPIC_CONFIG_PATH = os.path.join(TEST_DIR, 'testdata/library_gapic.yaml')


class TestConfigParsing(TestCase):
    def test_config_parsing(self):
        gapic_config = gapic_utils.read_from_gapic_yaml(GAPIC_CONFIG_PATH)
        self.assertEqual(1, len(gapic_config.fixed_collections))
        self.assertEqual(
            "deleted_book",
            gapic_config.fixed_collections['deleted_book'].entity_name)
        self.assertEqual(
            "_deleted-book_",
            gapic_config.fixed_collections['deleted_book'].fixed_value)
        self.assertEqual(
            "deleted_book",
            gapic_config.fixed_collections['deleted_book'].java_entity_name)
