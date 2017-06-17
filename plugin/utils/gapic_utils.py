# Copyright 2016, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#         * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#         * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#         * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import yaml

GAPIC_CONFIG_ANY = '*'


def read_from_gapic_yaml(yaml_file):
    with open(yaml_file) as f:
        gapic_yaml = yaml.load(f)

    collections = {}
    if 'collections' in gapic_yaml:
        collections = load_collection_configs(gapic_yaml['collections'],
                                              collections)
    for interface in gapic_yaml.get('interfaces', []):
        if 'collections' in interface:
            collections = load_collection_configs(interface['collections'],
                                                  collections)
    fixed_collections = {}
    if 'fixed_resource_name_values' in gapic_yaml:
        fixed_collections = load_fixed_configs(
            gapic_yaml['fixed_resource_name_values'], collections)

    oneofs = {}
    if 'collection_oneofs' in gapic_yaml:
        oneofs = load_collection_oneofs(gapic_yaml['collection_oneofs'],
                                        collections, fixed_collections)

    field_resource_name_map = {}
    if 'resource_name_generation' in gapic_yaml:
        field_resource_name_map = load_resource_name_map(
            gapic_yaml['resource_name_generation'], oneofs, collections)

    return GapicConfig(collections, fixed_collections, oneofs,
                       field_resource_name_map)


def load_collection_configs(config_list, existing_configs):
    for config in config_list:
        entity_name = config['entity_name']
        name_pattern = config['name_pattern']
        if entity_name in existing_configs:
            existing_name_pattern = existing_configs[entity_name].name_pattern
            if existing_name_pattern != name_pattern:
                raise ValueError(
                    'Found collection configs with same entity name '
                    'but different patterns. Name: ' + entity_name)
        else:
            existing_configs[entity_name] = CollectionConfig(entity_name,
                                                             name_pattern)
    return existing_configs


def load_fixed_configs(config_list, existing_collections):
    existing_configs = {}
    for config in config_list:
        entity_name = config['entity_name']
        fixed_value = config['fixed_value']
        if entity_name in existing_collections:
            raise ValueError(
                'Found different collection configs with same entity '
                'name but of different types. Name: ' + entity_name)
        if entity_name in existing_configs:
            existing_fixed_value = existing_configs[entity_name].fixed_value
            if existing_fixed_value != fixed_value:
                raise ValueError(
                    'Found fixed collection configs with same entity '
                    'name but different values. Name: ' + entity_name)
        else:
            existing_configs[entity_name] = FixedCollectionConfig(entity_name,
                                                                  fixed_value)
    return existing_configs


def load_collection_oneofs(config_list, existing_collections,
                           fixed_collections):
    existing_oneofs = {}
    for config in config_list:
        root_type_name = config['oneof_name']
        collection_list = config['collection_names']
        resources = []
        fixed_resources = []
        for collection in collection_list:
            if (collection not in existing_collections and
                    collection not in fixed_collections):
                raise ValueError(
                    'Collection specified in collection '
                    'oneof, but no matching collection '
                    'was found. Oneof: ' +
                    root_type_name + ', Collection: ' + collection)
            if collection in existing_collections:
                resources.append(existing_collections[collection])
            else:
                fixed_resources.append(fixed_collections[collection])

        if (root_type_name in existing_oneofs or
            root_type_name in existing_collections or
                root_type_name in fixed_collections):
            raise ValueError('Found two collection oneofs with same name: ' +
                             root_type_name)
        existing_oneofs[root_type_name] = CollectionOneof(
            root_type_name, resources, fixed_resources)
    return existing_oneofs


def load_resource_name_map(resource_name_generation, oneofs, collections):
    field_resource_name_map = {}
    for message_config in resource_name_generation:
        message_name = message_config['message_name']
        for field, coll in message_config['field_entity_map'].items():
            full_field_name = create_field_name(message_name, field)
            if full_field_name in field_resource_name_map:
                raise ValueError(
                    'Found multiple specifications for '
                    'same field in '
                    'resource_name_generation config. Use'
                    ' fully qualified message name to '
                    'avoid conflicts. Name: ' + full_field_name)
            if (coll not in oneofs and coll not in collections
                    and coll != GAPIC_CONFIG_ANY):
                raise ValueError('Unknown collection specified for field ' +
                                 full_field_name + ': ' + coll)
            field_resource_name_map[full_field_name] = coll
    return field_resource_name_map


def create_field_name(message_name, field):
    return message_name + '.' + field


class CollectionConfig(object):

    def __init__(self, entity_name, name_pattern):
        self.entity_name = entity_name
        self.name_pattern = name_pattern


class FixedCollectionConfig(object):

    def __init__(self, entity_name, fixed_value):
        self.entity_name = entity_name
        self.fixed_value = fixed_value


class CollectionOneof(object):

    def __init__(self, oneof_name, resources, fixed_resources):
        self.oneof_name = oneof_name
        self.resource_list = resources
        self.fixed_resource_list = fixed_resources


class GapicConfig(object):

    def __init__(self,
                 collection_configs={},
                 fixed_collections={},
                 collection_oneofs={},
                 field_resource_name_map={},
                 **kwargs):
        self.collection_configs = collection_configs
        self.fixed_collections = fixed_collections
        self.collection_oneofs = collection_oneofs
        self.field_resource_name_map = field_resource_name_map

    def get_entity_name_for_message_field(self, message_name, field_name):
        return self.field_resource_name_map.get(
            create_field_name(message_name, field_name))
