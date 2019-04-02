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
GAPIC_CONFIG_V1_PATH = os.path.join(TEST_DIR, 'testdata/library_gapic_v1.yaml')


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

    def test_identify_single_and_fixed_entities(self):
        project = {'name_pattern': 'projects/*', 'entity_name': 'project'}
        deleted_book = {'name_pattern': '_deleted-book_',
                        'entity_name': 'deleted_book'}
        shelf = {'name_pattern': 'shelves/*/books/*',
                 'entity_name': 'shelf'}
        book = {'name_pattern': 'book/{book_id}',
                'entity_name': 'book'}
        all_resource_names = [project, deleted_book, shelf, book]
        (singles, fixies) = gapic_utils.find_single_and_fixed_entities(
            all_resource_names)

        self.assertIn(project, singles)
        self.assertIn(deleted_book, fixies)
        self.assertIn(shelf, singles)
        self.assertIn(book, singles)

    def test_explicit_fixed_name_config_parsing(self):
        gapic_config = gapic_utils.read_from_gapic_yaml(GAPIC_CONFIG_V1_PATH)
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

        self.assertEqual(2, len(gapic_config.collection_configs))
        # Project name won't be included because it is a common resource name.
        self.assertIn(
            "book",
            gapic_config.collection_configs)
        self.assertIn(
            "archived_book",
            gapic_config.collection_configs)
