# Copyright 2016 Google LLC
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

import os
import re
from collections import OrderedDict
from plugin.utils import path_template
from plugin.utils import casing_utils
from plugin.utils.symbol_table import SymbolTable

RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA = 'com.google.api.resourcenames'


class ResourceNameBase(object):

    def __init__(self, class_name, package):
        self.class_name = class_name
        self.package = package
        self.resource_name_global_package_name = \
            RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA
        self.full_class_name = self.package + '.' + self.class_name
        self.var_name = casing_utils.get_lower(self.class_name)

    def filename(self):
        class_dir = self.package.replace('.', os.path.sep)
        return os.path.join(class_dir, self.class_name + '.java')

    def template_name(self):
        raise NotImplementedError(
            'template_name must be implemented by a child')

    def template_path(self):
        return os.path.join(os.path.dirname(__file__), self.template_name())


class ResourceName(ResourceNameBase):

    def __init__(self, collection_config, java_package, oneof):
        super(ResourceName, self).__init__(
            casing_utils.get_resource_type_class_name(
                collection_config.java_entity_name), java_package)
        symbol_table = SymbolTable()

        id_segments = get_id_segments(collection_config.name_pattern)
        self.format_name_lower = casing_utils.get_resource_type_var_name(
            collection_config.java_entity_name)
        self.type_name_upper = casing_utils.get_resource_type_from_class_name(
            self.class_name)
        self.builder_parent_class = ""
        if oneof:
            self.parent_interface = \
                casing_utils.get_parent_resource_name_class_name(
                    oneof.oneof_name)
            self.extension_keyword = 'extends'
            # TODO: Remove builder_parent_class after we delete the deprecated
            # per-pattern resource name subclasses
            if oneof.pattern_strings:
                self.builder_parent_class = self.parent_interface
        else:
            self.parent_interface = 'ResourceName'
            self.extension_keyword = 'implements'
        self.parameter_list = [{
            'parameter': symbol_table.getNewSymbol(
                casing_utils.lower_underscore_to_lower_camel(lit)),
            'parameter_name': lit,
            'not_first': True,
            'not_last': True,
        } for lit in id_segments]
        self.parameter_list[0]['not_first'] = False
        self.parameter_list[-1]['not_last'] = False
        self.format_fields = [{
            'upper': casing_utils.lower_underscore_to_upper_camel(
                f['parameter_name']),
            'lower': f['parameter'],
            'parameter_name_in_map':
                casing_utils.lower_underscore_to_lower_camel(
                    f['parameter_name']),
        } for f in self.parameter_list]
        self.format_string = collection_config.name_pattern

    def template_name(self):
        return "resource_name.mustache"


class ParentResourceName(ResourceNameBase):

    def __init__(self, oneof, java_package, pattern_strings):
        super(ParentResourceName, self).__init__(
            casing_utils.get_parent_resource_name_class_name(
                oneof.oneof_name),
            java_package)
        symbol_table = SymbolTable()

        pattern_to_id_segments = OrderedDict([
            (p, get_id_segments(p))
            for p in pattern_strings if not is_fixed_pattern(p)])

        self.has_fixed_patterns = \
            len(pattern_to_id_segments) < len(pattern_strings)
        self.has_formattable_patterns = len(pattern_to_id_segments) > 0

        segment_to_segment_symbols = OrderedDict()
        # Keep segment IDs to symbols in a dictionary, so that we
        # do not re-create a new symbol every time.
        for segments in pattern_to_id_segments.values():
            for seg in segments:
                if seg in segment_to_segment_symbols:
                    continue
                symbol = symbol_table.getNewSymbol(
                    casing_utils.lower_underscore_to_lower_camel(seg))
                segment_to_segment_symbols[seg] = symbol

        self.format_fields = [
            get_format_field(segment, segment_symbol)
            for segment, segment_symbol in segment_to_segment_symbols.items()
        ]
        if self.format_fields:
            self.format_fields[0]['not_first'] = False
            self.format_fields[-1]['not_last'] = False

        self.patterns = [
            ResourceNamePattern(pattern,
                                get_format_fields_for_pattern(
                                    pattern,
                                    pattern_to_id_segments,
                                    segment_to_segment_symbols))
            for pattern in pattern_strings]

        if len(self.patterns) > 0:
            self.first_pattern = self.patterns[0]
            self.patterns[0].set_first()
            self.patterns[0].set_short_builder_name()
            self.patterns[-1].set_last()

    def template_name(self):
        return "multi_pattern_resource_name.mustache" if self.patterns \
            else "deprecated_parent_resource_name.mustache"


class ResourceNamePattern:

    def __init__(self, pattern_string,
                 format_fields):
        self.is_fixed = len(format_fields) == 0
        self.is_formattable = not self.is_fixed
        self.pattern_string = pattern_string
        pattern_id = get_pattern_name(pattern_string)
        pattern_naming_styles = get_format_field(pattern_id, "")
        self.lower_camel = pattern_naming_styles['lower_camel']
        self.upper_camel = pattern_naming_styles['upper_camel']
        self.upper_underscore = pattern_naming_styles['upper_underscore']
        self.format_fields = format_fields
        self.builder_name = self.upper_camel + 'Builder'
        if format_fields:
            self.format_fields[0]['not_first'] = False
            self.format_fields[-1]['not_last'] = False
        for format_field in self.format_fields:
            format_field['pattern_builder_name'] = self.builder_name
        self.not_first = True
        self.is_first = False
        self.not_last = True

    def set_first(self):
        self.not_first = False
        self.is_first = True

    def set_last(self):
        self.not_last = False

    def set_short_builder_name(self):
        self.builder_name = 'Builder'
        for format_field in self.format_fields:
            format_field['pattern_builder_name'] = self.builder_name


class ResourceNameFactory(ResourceNameBase):

    def __init__(self, oneof, java_package):
        super(ResourceNameFactory, self).__init__(
            casing_utils.get_resource_name_factory_class_name(
                oneof.oneof_name),
            java_package)

        self.resource_class_name = \
            casing_utils.get_parent_resource_name_class_name(oneof.oneof_name)
        self.untyped_class_name = \
            casing_utils.get_untyped_resource_name_class_name(oneof.oneof_name)
        self.single_resource_types = [{
            'resource_type_class_name': resource.class_name,
            'resource_type_var_name': resource.var_name,
            'resource_package': resource.package,
        } for resource in (ResourceName(x, java_package, oneof)
                           for x in oneof.legacy_resource_list)]
        self.fixed_resource_types = [{
            'resource_type_class_name': resource.class_name,
            'resource_type_var_name': resource.var_name,
            'resource_package': resource.package,
        } for resource in (ResourceNameFixed(x, java_package, oneof)
                           for x in oneof.legacy_fixed_resource_list)]
        self.resource_types = (self.single_resource_types
                               + self.fixed_resource_types)

    def template_name(self):
        return "resource_name_factory.mustache"


class UntypedResourceName(ResourceNameBase):

    def __init__(self, oneof, java_package):
        super(UntypedResourceName, self).__init__(
            casing_utils.get_untyped_resource_name_class_name(
                oneof.oneof_name),
            java_package)

        self.parent_interface = \
            casing_utils.get_parent_resource_name_class_name(oneof.oneof_name)
        self.extension_keyword = 'extends'

    def template_name(self):
        return "untyped_resource_name.mustache"


class ResourceNameFixed(ResourceNameBase):

    def __init__(self, fixed_config, java_package, oneof):
        super(ResourceNameFixed, self).__init__(
            casing_utils.get_fixed_resource_type_class_name(
                fixed_config.java_entity_name), java_package)

        self.fixed_value = fixed_config.fixed_value
        if oneof:
            self.parent_interface = \
                casing_utils.get_parent_resource_name_class_name(
                    oneof.oneof_name)
            self.extension_keyword = 'extends'
        else:
            self.parent_interface = 'ResourceName'
            self.extension_keyword = 'implements'

    def template_name(self):
        return "resource_name_fixed.mustache"


def get_id_segments(pattern):
    name_template = path_template.PathTemplate(pattern)
    return [
        seg.literal for seg in name_template.segments
        if seg.kind == path_template._BINDING
    ]


def get_format_field(lower_underscore, symbol):
    return {
        'lower_underscore': lower_underscore,
        'lower_camel': casing_utils.lower_underscore_to_lower_camel(
                       lower_underscore),
        'lower_camel_symbol': symbol,
        'upper_underscore': casing_utils.lower_underscore_to_upper_underscore(
                            lower_underscore),
        'upper_camel': casing_utils.lower_underscore_to_upper_camel(
                       lower_underscore),
        'not_first': True,
        'not_last': True
    }


def get_format_fields_for_pattern(pattern,
                                  pattern_to_id_segments,
                                  segment_to_segment_symbols):
    if pattern not in pattern_to_id_segments:
        return []
    format_fields = [get_format_field(seg, segment_to_segment_symbols[seg])
                     for seg in pattern_to_id_segments[pattern]]
    format_fields[0]['not_first'] = False
    format_fields[-1]['not_last'] = False
    return format_fields


def is_fixed_pattern(pattern):
    return not('{' in pattern or '*' in pattern)


def get_pattern_name(pattern):
    if is_fixed_pattern(pattern):
        start_index = \
            next(i for (i, c) in enumerate(list(pattern)) if c.isalpha())
        end_index = len(pattern) - next(
            i for (i, c) in enumerate(list(pattern)[::-1]) if c.isalpha())
        name_parts = re.split(r'[^a-zA-Z]', pattern[start_index:end_index])
        return '_'.join(name_parts)
    else:
        return '_'.join(get_id_segments(pattern))
