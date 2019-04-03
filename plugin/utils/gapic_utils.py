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

from collections import OrderedDict
import copy

import yaml

from google.api import resource_pb2

from .casing_utils import to_snake


GAPIC_CONFIG_ANY = '*'


def read_from_gapic_yaml(request):
    """Read the GAPIC YAML from disk and process it.

    Args:
        request (~.plugins_pb2.CodeGeneratorRequest): A code generator
            request received from protoc. The name of the YAML file
            is in ``request.parameter``.
    """
    # Load the YAML file from disk.
    yaml_file = request.parameter
    if yaml_file:
        with open(yaml_file) as f:
            gapic_yaml = yaml.load(f)
    else:
        gapic_yaml = {}

    # It is possible we got a "GAPIC v2", or no GAPIC YAML at all.
    # GAPIC v2 is a stripped down GAPIC config that moves most of the relevant
    # configuration, including resource names, over to annotations.
    # No GAPIC YAML at all means all config is in annotations.
    #
    # If either of these situations apply, "build back" what the GAPIC v1
    # would have looked like, allowing the rest of the logic to stay the
    # same.
    #
    # Prop 65 Warning: The GAPIC config is known to the state of California
    # to cause cancer and reproductive harm. The reason we do not refactor
    # away from it here is because this tool is supposed to have a short
    # shelf life, and it is safer to be backwards-looking than
    # forward-looking in this case.
    if not gapic_yaml or gapic_yaml['config_schema_version'] != '1.0.0':
        gapic_yaml = reconstruct_gapic_yaml(gapic_yaml, request)

    collections = {}
    all_entities = []
    if 'collections' in gapic_yaml:
        all_entities.extend(gapic_yaml['collections'])
    for interface in gapic_yaml.get('interfaces', []):
        if 'collections' in interface:
            all_entities.extend(interface['collections'])

    single_resource_names, fixed_resource_names = \
        find_single_and_fixed_entities(all_entities)

    collections = load_collection_configs(single_resource_names, collections)

    fixed_collections = {}
    # TODO(andrealin): Remove the fixed_resource_name_values
    # parsing once they no longer exist in GAPIC configs.
    if 'fixed_resource_name_values' in gapic_yaml:
        fixed_collections = load_fixed_configs(
            gapic_yaml['fixed_resource_name_values'],
            fixed_collections,
            collections,
            "fixed_value")
    # Add the fixed resource names that are defined in the collections.
    fixed_collections = load_fixed_configs(
        fixed_resource_names,
        fixed_collections,
        collections,
        "name_pattern")

    oneofs = {}
    if 'collection_oneofs' in gapic_yaml:
        oneofs = load_collection_oneofs(gapic_yaml['collection_oneofs'],
                                        collections, fixed_collections)

    return GapicConfig(collections, fixed_collections, oneofs)


def reconstruct_gapic_yaml(gapic_config, request):
    """Reconstruct a full GAPIC v1 config based on proto annotations.

    Args:
        gapic_config (dict): A dictionary representing the GAPIC config
            read from disk. This is must be a GAPIC config with a schema
            version other than 1.0.0. It may be an empty dictionary
            if no GAPIC config was present.
        request (~.plugin_pb2.CodeGeneratorRequest): A code generator
            request received from protoc.

    Returns:
        dict: A reconstructed GAPIC v1 config (at least as far as resource
            names are concerned).
    """
    # Make a shallow copy of the GAPIC config, so that we are not
    # modifying the passed dictionary in-place.
    gapic_config = copy.copy(gapic_config)

    # For debugability, set the schema version to something new and exciting.
    gapic_config.setdefault('config_schema_version', 'missing')
    gapic_config['config_schema_version'] += 'reconstructed'

    # Sort existing collections in a dictionary so we can look up by
    # entity names. (This makes it easier to avoid plowing over stuff that
    # is explicitly defined in YAML.)
    collections = OrderedDict([(i['entity_name'], i) for i in
                              gapic_config.get('collections', ())])
    for interface in gapic_config.get('interfaces', ()):
        collections.update([(i['entity_name'], i) for i in
                           interface.get('collections', ())])

    # Do the same thing for collection oneofs.
    collection_oneofs = OrderedDict([(i['oneof_name'], i) for i in
                                    gapic_config.get('collection_oneofs', ())])
    for interface in gapic_config.get('interfaces', ()):
        collection_oneofs.update([(i['oneof_name'], i) for i in
                                 interface.get('collection_oneofs', ())])

    # Iterate over the files to be generated looking for messages that have
    # a google.api.resource annotation.
    # This annotation corresponds to a collection in the GAPIC v1 config.
    for proto_file in request.proto_file:
        # We only want to do stuff with files we were explicitly asked to
        # generate. Ignore the rest.
        if proto_file.name not in request.file_to_generate:
            continue

        # Iterate over all of the messages in the file.
        for message in proto_file.message:
            for field in message.field:
                # If this is a single resource, build a collection.
                res = field.options.Extensions[resource_pb2.resource]
                if res:
                    name = to_snake(res.symbol if res.symbol else message.name)
                    collections.setdefault(name, {
                        'entity_name': name,
                        'name_pattern': res.pattern,
                    })
                    continue

                # If this is a resource set, build that collection.
                res_set = field.options.Extensions[resource_pb2.resource_set]
                if res_set:
                    collection_names = []

                    # Any resources declared as part of this resource set
                    # correspond to an explicitly declared collection in the
                    # GAPIC config.
                    for res in res_set.resources:
                        name = to_snake(
                            res.symbol if res.symbol else message.name)
                        collections.set_default(name, {
                            'entity_name': name,
                            'name_pattern': res.pattern,
                        })
                        collection_names.append(name)

                    # Any resources that are referenced in the resource set
                    # correspond to a resource which should have been declared
                    # separately.
                    #
                    # In this case, we just blindly assume that the collection
                    # will have been declared and hope for the best.
                    for ref in res_set.resource_references:
                        collection_names.append(to_snake(ref.split('.')[-1]))

                    # Add the resource set to "collection_oneofs".
                    name = res_set.symbol if res_set.symbol else message.name
                    collection_oneofs.setdefault(name, {
                        'oneof_name': name,
                        'collection_names': collection_names,
                    })

        # Resource references are fundamentally applied to RPCs in the GAPIC
        # config, so we need to place them into that structure.
        # In order to do that, we need to get the interfaces and methods into
        # a dictionary structure rather than a list structure.
        interfaces = OrderedDict([(i['name'], i) for i in
                                 gapic_config.get('interfaces', ())])
        for interface in interfaces:
            interface['methods'] = OrderedDict([(i['name'], i) for i in
                                                interface.get('methods', ())])

        # At this point, all collections that are declared in any of our
        # messages should be in place, so now we take resource references
        # and add them.
        #
        # These become "field_name_patterns" in the GAPIC config, with
        # the field name being the key and the name of the collection or
        # collection_oneof being the value.
        for message in proto_file.message:
            for field in message.field:
                # Get the resource reference for this field, if any.
                ref_annotation = resource_pb2.resource_reference
                ref = message.options.Extensions[ref_annotation]
                if not ref:
                    continue

                # Find the method for which this message is the input,
                # and get the GAPIC YAML portion for it.
                # -------------------------
                # TODO: populate `service` -- need to figure out the RPC(s)
                # where this is used by iterating over them and then get to
                # the service name from that.
                # -------------------------
                method_yaml = interfaces.get(service, {}).get('methods', {})

                # Apply this field name pattern.
                method_yaml.setdefault('field_name_patterns', {})
                method_yaml['field_name_patterns'].setdefault(
                    field.name,
                    to_snake(ref.split('.')[-1]),
                )

    # Take the collections and collection_oneofs, convert them back to lists,
    # and drop them on the GAPIC YAML.
    gapic_yaml['collections'] = list(collections.values())
    gapic_yaml['collection_oneofs'] = list(collection_oneofs.values())

    # Done; Return the modified GAPIC YAML.
    return gapic_yaml


def find_single_and_fixed_entities(all_resource_names):
    single_entities = []
    fixed_entities = []

    for collection in all_resource_names:
        name_pattern = collection['name_pattern']
        if '{' in name_pattern or '*' in name_pattern:
            single_entities.append(collection)
        else:
            fixed_entities.append(collection)
    return single_entities, fixed_entities


def load_collection_configs(config_list, existing_configs):
    for config in config_list:
        entity_name = config['entity_name']
        name_pattern = config['name_pattern']
        java_entity_name = entity_name

        overrides = config.get('language_overrides', [])
        overrides = [ov for ov in overrides if ov['language'] == 'java']
        if len(overrides) > 1:
            raise ValueError('expected only one java override')
        if len(overrides) == 1:
            override = overrides[0]
            if 'common_resource_name' in override:
                continue
            java_entity_name = override['entity_name']

        if entity_name in existing_configs:
            existing_name_pattern = existing_configs[entity_name].name_pattern
            if existing_name_pattern != name_pattern:
                raise ValueError(
                    'Found collection configs with same entity name '
                    'but different patterns. Name: ' + entity_name)
        else:
            existing_configs[entity_name] = CollectionConfig(entity_name,
                                                             name_pattern,
                                                             java_entity_name)
    return existing_configs


def load_fixed_configs(config_list,
                       existing_configs,
                       existing_collections,
                       pattern_key_name):
    for config in config_list:
        entity_name = config['entity_name']
        fixed_value = config[pattern_key_name]
        java_entity_name = entity_name
        # TODO implement override support (only if necessary before this
        # plugin is deprecated...)
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
            existing_configs[entity_name] = FixedCollectionConfig(
                entity_name, fixed_value, java_entity_name)
    return existing_configs


def load_collection_oneofs(config_list, existing_collections,
                           fixed_collections):
    existing_oneofs = {}
    for config in config_list:
        root_type_name = config['oneof_name']
        collection_names = config['collection_names']
        resources = []
        fixed_resources = []
        for collection in collection_names:
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
            root_type_name, resources, fixed_resources, collection_names)
    return existing_oneofs


def create_field_name(message_name, field):
    return message_name + '.' + field


class CollectionConfig(object):

    def __init__(self, entity_name, name_pattern, java_entity_name):
        self.entity_name = entity_name
        self.name_pattern = name_pattern
        self.java_entity_name = java_entity_name


class FixedCollectionConfig(object):

    def __init__(self, entity_name, fixed_value, java_entity_name):
        self.entity_name = entity_name
        self.fixed_value = fixed_value
        self.java_entity_name = java_entity_name


class CollectionOneof(object):

    def __init__(self, oneof_name, resources, fixed_resources,
                 collection_names):
        self.oneof_name = oneof_name
        self.resource_list = resources
        self.fixed_resource_list = fixed_resources
        self.collection_names = collection_names


class GapicConfig(object):

    def __init__(self,
                 collection_configs={},
                 fixed_collections={},
                 collection_oneofs={},
                 **kwargs):
        self.collection_configs = collection_configs
        self.fixed_collections = fixed_collections
        self.collection_oneofs = collection_oneofs
