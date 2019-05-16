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
import re
import yaml

from plugin.pb2 import resource_pb2
from plugin.utils.casing_utils import to_snake
from plugin.templates import resource_name

GAPIC_CONFIG_ANY = '*'


def create_gapic_config(gapic_yaml):
    """ Create a GapicConfig object from a gapic yaml.
    Args:
        gapic_yaml: Serialized GAPIC yaml.
    """
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


def read_from_gapic_yaml(request):
    """Read the GAPIC YAML from disk and process it.

    Args:
        request (~.plugins_pb2.CodeGeneratorRequest): A code generator
            request received from protoc. The name of the YAML file
            is in ``request.parameter``.
    Returns:
        A final GapicConfig object containing all resource information.
    """
    # Load the YAML file from disk.
    yaml_file = request.parameter
    if yaml_file:
        with open(yaml_file) as f:
            gapic_yaml = yaml.load(f, Loader=yaml.SafeLoader)
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
    if not gapic_yaml or gapic_yaml.get(
            'config_schema_version', '1.0.0') != '1.0.0':
        gapic_yaml = reconstruct_gapic_yaml(gapic_yaml, request)

    return create_gapic_config(gapic_yaml)


def reconstruct_gapic_yaml(gapic_config, request):  # noqa: C901
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
    gapic_config.setdefault('config_schema_version', 'unspecified')
    gapic_config['config_schema_version'] += '-reconstructed'

    # Sort existing collections in a dictionary so we can look up by
    # name patterns. (This makes it easier to avoid plowing over stuff that
    # is explicitly defined in YAML.)
    collections = OrderedDict([(i['name_pattern'], i) for i in
                               gapic_config.get('collections', ())])
    for interface in gapic_config.get('interfaces', ()):
        collections.update([(i['name_pattern'], i) for i in
                            interface.get('collections', ())])

    # Do the same thing for collection oneofs, but order by entity names.
    collection_oneofs = OrderedDict(
        [(i['oneof_name'], i) for i in gapic_config.get(
            'collection_oneofs', ())])
    for interface in gapic_config.get('interfaces', ()):
        collection_oneofs.update([(i['oneof_name'], i) for i in
                                  interface.get('collection_oneofs', ())])

    # Find all unified resource types that have child references. For these
    # resources, we need to generate collection configs for their parents
    # patterns.
    types_with_child_references = set()
    for proto_file in request.proto_file:
        # We only want to do stuff with files we were explicitly asked to
        # generate. Ignore the rest.
        if proto_file.name not in request.file_to_generate:
            continue

        for message in proto_file.message_type:
            for field in message.field:
                # Get the resource reference for this field, if any.
                ref_annotation = resource_pb2.resource_reference
                ref = field.options.Extensions[ref_annotation]
                if ref.child_type:
                    types_with_child_references.add(ref.child_type)

    # Iterate over the files to be generated looking for messages that have
    # a google.api.resource annotation.
    # This annotation corresponds to a collection in the GAPIC v1 config.
    for proto_file in request.proto_file:
        # We only want to do stuff with files we were explicitly asked to
        # generate. Ignore the rest.
        if proto_file.name not in request.file_to_generate:
            continue

        # Iterate over all of the messages in the file.
        for message in proto_file.message_type:
            # If this is not a resource, move on.
            res = message.options.Extensions[resource_pb2.resource]
            if not res.pattern:
                continue

            update_collections(res, types_with_child_references,
                               collections, collection_oneofs)

    # Take the collections and collection_oneofs, convert them back to lists,
    # and drop them on the GAPIC YAML.
    gapic_config['collections'] = list(collections.values())
    gapic_config['collection_oneofs'] = list(collection_oneofs.values())

    # Done; Return the modified GAPIC YAML.
    return gapic_config


def update_collections(
        res, types_with_child_references, collections, collection_oneofs):
    # Determine the name.
    name = to_snake(res.type.split('/')[-1])

    # pylint: disable=no-member
    has_oneof = len(res.pattern) > 1 or res.history == \
        resource_pb2.ResourceDescriptor.FUTURE_MULTI_PATTERN

    # If ORIGINALLY_SINGLE_PATTERN is set or there is only one pattern
    # and FUTURE_MULTI_PATTERN is NOT set, then we need special naming
    # for that pattern.
    single_pattern_naming = \
        res.history == \
        resource_pb2.ResourceDescriptor.ORIGINALLY_SINGLE_PATTERN or (
            len(res.pattern) == 1 and res.history !=
            resource_pb2.ResourceDescriptor.FUTURE_MULTI_PATTERN
        )
    # pylint: enable=no-member

    # Build a map from patterns to names. These need to be built
    # together to resolve conflicts
    entity_names = build_entity_names(res.pattern, name)

    if single_pattern_naming:
        entity_names[res.pattern[0]] = name

    collection_names = []
    # Build collections for all of the patterns in the descriptor
    for pattern in res.pattern:
        collection_name = entity_names[pattern]
        collections.setdefault(pattern, {}).update({
            'entity_name': collection_name,
            'name_pattern': pattern,
        })
        collection_names.append(entity_names[pattern])

    if has_oneof:
        # Add the resource collection to "collection_oneofs".
        oneof_name = name + '_oneof'
        collection_oneofs.setdefault(oneof_name, {}).update({
            'oneof_name': oneof_name,
            'collection_names': collection_names,
        })

    if res.type in types_with_child_references:
        # Derive patterns for the parent resources
        parent_patterns = build_parent_patterns(res.pattern)

        # Build a map from patterns to names. These need to be built
        # together to resolve conflicts
        parent_entity_names = build_entity_names(parent_patterns, '')

        parent_collection_names = []
        for pattern in parent_patterns:
            collections.update({
                parent_entity_names[pattern]: {
                    'entity_name': parent_entity_names[pattern],
                    'name_pattern': pattern,
                }
            })
            parent_collection_names.append(parent_entity_names[pattern])


# Build a map from patterns to entity names. We use a trie structure to resolve
# the entity name in a unique fashion, by looking to see which keys in the
# trie have multiple entries, meaning that that entry distinguishes a pattern
# from another pattern (i.e. the trie branches at that node).
def build_entity_names(patterns, suffix):
    segments_list = [reversed_variable_segments(p) for p in patterns]
    trie = build_trie_from_segments_list(segments_list)
    name_map = {}
    for pattern, segments in zip(patterns, segments_list):
        node = trie
        name_components = []
        if suffix:
            name_components.append(suffix)
        for segment in segments:
            if len(node) > 1:
                name_components.append(segment)
            node = node[segment]
        if not name_components:
            # This can occur for a single pattern and empty suffix
            if segments:
                name_components.append(segments[0])
        name_map[pattern] = '_'.join(name_components[::-1])
    return name_map


def build_trie_from_segments_list(segments_list):
    trie = {}
    for segments in segments_list:
        node = trie
        for segment in segments:
            node.setdefault(segment, {})
            node = node[segment]
    return trie


def reversed_variable_segments(ptn):
    if isFixedPattern(ptn):
        start_index = next(i for (i, c) in enumerate(list(ptn)) if c.isalpha())
        end_index = len(ptn) - next(
            i for (i, c) in enumerate(list(ptn)[::-1]) if c.isalpha())
        name_parts = re.split(r'[^a-zA-Z]', ptn[start_index:end_index])
        name_parts.reverse()
        return name_parts
    else:
        segs = []
        for seg in ptn.split('/')[::-1]:
            if _is_variable_segment(seg):
                segs.append(seg[1:-1])
        return segs


def build_parent_patterns(patterns):
    def _parent_pattern(pattern):
        segs = pattern.split('/')
        last_index = len(segs) - 2
        while last_index >= 0 and not _is_variable_segment(segs[last_index]):
            last_index -= 1
        last_index += 1
        return '/'.join(segs[:last_index])
    return [_parent_pattern(p) for p in patterns if not(isFixedPattern(p))]


def _is_variable_segment(segment):
    return len(segment) > 0 and segment[0] == '{' and segment[-1] == '}'


def find_single_and_fixed_entities(all_resource_names):
    single_entities = []
    fixed_entities = []

    for collection in all_resource_names:
        name_pattern = collection['name_pattern']
        if isFixedPattern(name_pattern):
            fixed_entities.append(collection)
        else:
            single_entities.append(collection)
    return single_entities, fixed_entities


def isFixedPattern(pattern):
    return not('{' in pattern or '*' in pattern)


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


def collect_resource_name_types(gapic_config, java_package):
    resources = []

    for collection_config in gapic_config.collection_configs.values():
        oneof = get_oneof_for_resource(collection_config, gapic_config)
        resource = resource_name.ResourceName(
            collection_config, java_package, oneof)
        resources.append(resource)

    for fixed_config in gapic_config.fixed_collections.values():
        oneof = get_oneof_for_resource(fixed_config, gapic_config)
        resource = resource_name.ResourceNameFixed(
            fixed_config, java_package, oneof)
        resources.append(resource)

    for oneof_config in gapic_config.collection_oneofs.values():
        parent_resource = resource_name.ParentResourceName(
            oneof_config, java_package)
        untyped_resource = resource_name.UntypedResourceName(
            oneof_config, java_package)
        resource_factory = resource_name.ResourceNameFactory(
            oneof_config, java_package)
        resources.append(parent_resource)
        resources.append(untyped_resource)
        resources.append(resource_factory)

    return resources


def get_oneof_for_resource(collection_config, gapic_config):
    oneof = None
    for oneof_config in gapic_config.collection_oneofs.values():
        for collection_name in oneof_config.collection_names:
            if collection_name == collection_config.entity_name:
                if oneof:
                    raise ValueError(
                        "A collection cannot be part of multiple oneofs")
                oneof = oneof_config
    return oneof


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
