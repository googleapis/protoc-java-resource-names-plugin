#!/usr/bin/env python

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
import sys
import pystache

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from plugin.templates import resource_name, insertion_points
from plugin.utils import proto_utils, gapic_utils


TEMPLATE_LOCATION = os.path.join('plugin', 'templates')

def render_new_file(renderer, response, resource):
  f = response.file.add()
  f.name = resource.filename()
  f.content = renderer.render(resource)


def generate_resource_name_types(response, gapic_config, java_package):
  renderer = pystache.Renderer(search_dirs=TEMPLATE_LOCATION)
  for collection_config in gapic_config.collection_configs.values():
    resource = resource_name.ResourceName(collection_config, java_package)
    resource_type = resource_name.ResourceNameType(resource.className(), java_package)
    render_new_file(renderer, response, resource)
    render_new_file(renderer, response, resource_type)

  for fixed_config in gapic_config.fixed_collections.values():
    resource = resource_name.ResourceNameFixed(fixed_config, java_package)
    resource_type = resource_name.ResourceNameType(resource.className(), java_package)
    render_new_file(renderer, response, resource)
    render_new_file(renderer, response, resource_type)

  for oneof_config in gapic_config.collection_oneofs.values():
    resource_oneof = resource_name.ResourceNameOneof(oneof_config, java_package)
    render_new_file(renderer, response, resource_oneof)


def generate_get_set_injection(response, gapic_config, request, java_package):
  renderer = pystache.Renderer(search_dirs=TEMPLATE_LOCATION)
  for pf in get_protos_to_generate_for(request):
    for item, package in proto_utils.traverse(pf):
      filename = os.path.join(java_package.replace('.', os.path.sep), item.name + '.java')
      for field in item.field:
        entity_name = gapic_config.get_entity_name_for_message_field(
            item.name, field.name)
        if entity_name:
          concrete_resource = None
          if entity_name == gapic_utils.GAPIC_CONFIG_ANY:
            resource = resource_name.ResourceNameAny()
            concrete_resource = resource_name.ResourceNameUntyped()
          elif entity_name in gapic_config.collection_configs:
            collection = gapic_config.collection_configs.get(entity_name)
            resource = resource_name.ResourceName(collection, java_package)
          elif entity_name in gapic_config.collection_oneofs:
            collection = gapic_config.collection_oneofs.get(entity_name)
            resource = resource_name.ResourceNameOneof(collection, java_package)
          else:
            raise ValueError('entity name not found: ' + entity_name)

          f = response.file.add()
          f.name = filename
          f.insertion_point = 'builder_scope:' + package + '.' + item.name
          f.content = renderer.render(get_builder_view(field)(resource, field, concrete_resource))

          f = response.file.add()
          f.name = filename
          f.insertion_point = 'class_scope:' + package + '.' + item.name
          f.content = renderer.render(get_class_view(field)(resource, field, concrete_resource))


def get_builder_view(field):
  if field.label == FieldDescriptorProto.LABEL_REPEATED:
    return insertion_points.InsertBuilderList
  else:
    return insertion_points.InsertBuilder


def get_class_view(field):
  if field.label == FieldDescriptorProto.LABEL_REPEATED:
    return insertion_points.InsertClassList
  else:
    return insertion_points.InsertClass


def get_protos_to_generate_for(request):
  proto_files = dict((pf.name, pf) for pf in request.proto_file)
  for pf_name in request.file_to_generate:
    if pf_name in proto_files:
      yield proto_files[pf_name]


def resolve_java_package_name(request):
  java_package = None
  for pf in get_protos_to_generate_for(request):
    for item, package in proto_utils.traverse(pf):
      for opt in proto_utils.get_named_options(pf, 'java_package'):
        if java_package is not None and java_package != opt[1]:
          raise ValueError('got conflicting java packages: '
                           + str(java_package) + ' and '
                           + str(opt[1]))
        java_package = opt[1]
        break
  if java_package is None:
    raise ValueError('java package not defined')
  return java_package


def main(data):
  # Parse request
  request = plugin.CodeGeneratorRequest()
  request.ParseFromString(data)

  java_package = resolve_java_package_name(request)
  gapic_config = gapic_utils.read_from_gapic_yaml(request.parameter)

  # Generate output
  response = plugin.CodeGeneratorResponse()

  generate_resource_name_types(response, gapic_config, java_package)
  generate_get_set_injection(response, gapic_config, request, java_package)

  # Serialise response message
  output = response.SerializeToString()

  return output

if __name__ == '__main__':
  try:
    source = sys.stdin.buffer
    dest = sys.stdout.buffer
  except AttributeError:
    source = sys.stdin
    dest = sys.stdout

  # Read request message from stdin
  data = source.read()

  output = main(data)

  # Write to stdout
  dest.write(output)
