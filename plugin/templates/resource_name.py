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

import os
from google.gax import path_template
from plugin.utils import casing_utils

RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA = 'com.google.api.resourcenames'
RESOURCE_NAMES_TYPE_PACKAGE_JAVA = 'com.google.api.resourcenames.types'


class ResourceNameBase(object):

    def resourceNameTypePackageName(self):
        return RESOURCE_NAMES_TYPE_PACKAGE_JAVA

    def resourceNameGlobalPackageName(self):
        return RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA

    def filename(self):
        class_dir = self.package().replace('.', os.path.sep)
        return os.path.join(class_dir, self.className() + '.java')

    def fullClassName(self):
        return self.package() + '.' + self.className()

    def className(self):
        raise NotImplementedError('className must be implemented by child')

    def varName(self):
        return casing_utils.get_lower(self.className())

    def package(self):
        raise NotImplementedError('package must be implemented by child')


class ResourceName(ResourceNameBase):

    def __init__(self, collection_config, java_package):

        entity_name = collection_config.entity_name
        name_template = path_template.PathTemplate(
            collection_config.name_pattern)
        id_segments = [
            seg.literal for seg in name_template.segments
            if seg.kind == path_template._BINDING
        ]

        self.format_name_upper = casing_utils.get_resource_type_class_name(
            entity_name)
        self.format_name_lower = casing_utils.get_resource_type_var_name(
            entity_name)
        self.type_name_upper = casing_utils.get_resource_type_from_class_name(
            self.format_name_upper)
        self.parameter_list = [{
            'parameter': casing_utils.lower_underscore_to_lower_camel(lit),
            'parameter_name': lit,
            'not_first': True,
            'not_last': True,
        } for lit in id_segments]
        self.parameter_list[0]['not_first'] = False
        self.parameter_list[-1]['not_last'] = False
        self.format_fields = [{
            'upper': casing_utils.lower_camel_to_upper_camel(f['parameter']),
            'lower': f['parameter'],
        } for f in self.parameter_list]
        self.format_string = collection_config.name_pattern
        self.package_name = java_package

    def className(self):
        return self.format_name_upper

    def typeNameUpper(self):
        return self.type_name_upper

    def formatFields(self):
        return self.format_fields

    def parameterList(self):
        return self.parameter_list

    def formatString(self):
        return self.format_string

    def package(self):
        return self.package_name


class ResourceNameOneof(ResourceNameBase):

    def __init__(self, oneof, java_package):
        entity_name = oneof.oneof_name
        self.oneof_class_name = casing_utils.get_oneof_class_name(entity_name)
        self.single_resource_types = [{
            'resourceTypeClassName': resource.className(),
            'resourceTypeVarName': resource.varName(),
            'resourcePackage': resource.package(),
        } for resource in (ResourceName(x, java_package)
                           for x in oneof.resource_list)]
        self.fixed_resource_types = [{
            'resourceTypeClassName': resource.className(),
            'resourceTypeVarName': resource.varName(),
            'resourcePackage': resource.package(),
        } for resource in (ResourceNameFixed(x, java_package)
                           for x in oneof.fixed_resource_list)]
        self.resource_types = (self.single_resource_types
                               + self.fixed_resource_types)

        self.oneof_package_name = java_package

    def className(self):
        return self.oneof_class_name

    def resourceTypes(self):
        return self.resource_types

    def singleResourceTypes(self):
        return self.single_resource_types

    def fixedResourceTypes(self):
        return self.fixed_resource_types

    def package(self):
        return self.oneof_package_name


class ResourceNameType(ResourceNameBase):

    def __init__(self, class_name, java_package):
        self.type_name_upper = casing_utils.get_resource_type_from_class_name(
            class_name)
        self.package_name = java_package

    def className(self):
        return self.type_name_upper

    def package(self):
        return self.package_name


class ResourceNameFixed(ResourceNameBase):

    def __init__(self, fixed_config, java_package):
        self.format_name_upper = \
            casing_utils.get_fixed_resource_type_class_name(
                fixed_config.entity_name)
        self.fixed_value = fixed_config.fixed_value
        self.package_name = java_package

    def className(self):
        return self.format_name_upper

    def fixedValue(self):
        return self.fixed_value

    def package(self):
        return self.package_name


class ResourceNameAny(ResourceNameBase):

    def className(self):
        return 'ResourceName'

    def package(self):
        return RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA


class ResourceNameUntyped(ResourceNameBase):

    def className(self):
        return 'UntypedResourceName'

    def package(self):
        return RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA
