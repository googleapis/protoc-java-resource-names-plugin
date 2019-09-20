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

        name_template = path_template.PathTemplate(
            collection_config.name_pattern)
        id_segments = [
            seg.literal for seg in name_template.segments
            if seg.kind == path_template._BINDING
        ]
        self.format_name_lower = casing_utils.get_resource_type_var_name(
            collection_config.java_entity_name)
        self.type_name_upper = casing_utils.get_resource_type_from_class_name(
            self.class_name)
        if oneof:
            self.parent_interface = \
                casing_utils.get_parent_resource_name_class_name(
                    oneof.oneof_name)
            self.extension_keyword = 'extends'
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

    def __init__(self, oneof, java_package):
        super(ParentResourceName, self).__init__(
            casing_utils.get_parent_resource_name_class_name(
                oneof.oneof_name),
            java_package)

    def template_name(self):
        return "parent_resource_name.mustache"


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
                           for x in oneof.resource_list)]
        self.fixed_resource_types = [{
            'resource_type_class_name': resource.class_name,
            'resource_type_var_name': resource.var_name,
            'resource_package': resource.package,
        } for resource in (ResourceNameFixed(x, java_package, oneof)
                           for x in oneof.fixed_resource_list)]
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
