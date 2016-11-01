# Copyright 2016, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
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
from plugin.utils import protoutils, casingutils


RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA = 'com.google.api.resourcenames'
RESOURCE_NAMES_TYPE_PACKAGE_JAVA = 'com.google.api.resourcenames.types'


class ResourceNameBase(object):

  def resourceNameTypePackageName(self):
    return RESOURCE_NAMES_TYPE_PACKAGE_JAVA

  def resourceNameGlobalPackageName(self):
    return RESOURCE_NAMES_GLOBAL_PACKAGE_JAVA


class ResourceName(ResourceNameBase):

  def __init__(self, collection_config):

    entity_name = collection_config.entity_name
    name_template = path_template.PathTemplate(collection_config.name_pattern)
    id_segments = [seg.literal for seg in name_template.segments
          if seg.kind == path_template._BINDING]

    self.format_name_upper = casingutils.get_resource_type_class_name(
        entity_name)
    self.format_name_lower = casingutils.get_resource_type_var_name(
        entity_name)
    self.type_name_upper = casingutils.get_resource_type_type_name(
        entity_name)
    self.parameter_list = [
        {
            'parameter': casingutils.lower_underscore_to_lower_camel(lit),
            'parameter_name': lit,
            'not_first': True,
            'not_last': True,
        } for lit in id_segments]
    self.parameter_list[0]['not_first'] = False
    self.parameter_list[-1]['not_last'] = False
    self.format_fields = [
        {
            'upper': casingutils.lower_camel_to_upper_camel(f['parameter']),
            'lower': f['parameter'],
        } for f in self.parameter_list]
    self.format_string = collection_config.name_pattern

  def formatNameUpper(self):
    return self.format_name_upper

  def formatNameLower(self):
    return self.format_name_lower

  def typeNameUpper(self):
    return self.type_name_upper

  def formatFields(self):
    return self.format_fields

  def parameterList(self):
    return self.parameter_list

  def formatString(self):
    return self.format_string

  def filename(self):
    class_dir = RESOURCE_NAMES_TYPE_PACKAGE_JAVA.replace('.', os.path.sep)
    return os.path.join(class_dir, self.format_name_upper + '.java')


class ResourceNameOneof(ResourceNameBase):

  def __init__(self, oneof, proto_file):
    entity_name = oneof.entity_name
    self.oneof_class_name = casingutils.get_oneof_class_name(entity_name)
    self.resource_types = [
        {
            'resourceTypeClassName': casingutils.get_resource_type_class_name(
                entity_name),
            'resourceTypeVarName': casingutils.get_resource_type_var_name(
                entity_name),
        } for resource_type in oneof.resource_type_list]

  def oneofClassName(self):
    return self.oneof_class_name

  def resourceTypes(self):
    return self.resource_types

  def resourceNameOneofPackageName(self):
    return self.oneof_package_name


class ResourceNameType(ResourceNameBase):

  def __init__(self, collection_config):
    entity_name = collection_config.entity_name
    self.type_name_upper = casingutils.get_resource_type_type_class_name(
        entity_name)

  def typeNameUpper(self):
    return self.type_name_upper


class ResourceNameInvalid(ResourceNameBase):

  def __init__(self, invalid_config):
    self.format_name_upper = casingutils.get_resource_type_class_name(
        invalid_config.entity_name)
    self.invalid_value = invalid_config.invalid_value

  def formatNameUpper(self):
    return self.format_name_upper

  def invalidValue(self):
    return self.invalid_value
