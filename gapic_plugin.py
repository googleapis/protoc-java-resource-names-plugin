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
from plugin.utils import protoutils, gapicutils


TEMPLATE_LOCATION = os.path.join('plugin', 'templates')

def render_new_file(renderer, response, resource):
  f = response.file.add()
  f.name = resource.filename()
  f.content = renderer.render(resource)


def generate_resource_name_types(response, gapic_config, proto_file):
  renderer = pystache.Renderer(search_dirs=TEMPLATE_LOCATION)
  for collection_config in gapic_config.collection_configs.values():
    resource = resource_name.ResourceName(collection_config)
    resource_type = resource_name.ResourceNameType(collection_config)
    render_new_file(renderer, response, resource)
    render_new_file(renderer, response, resource_type)

  for oneof_config in gapic_config.collection_oneofs.values():
    resource_oneof = resource_name.ResourceNameOneof(oneof_config, proto_file)
    render_new_file(renderer, response, resource_oneof)


def generate_get_set_injection(response, gapic_config, request):
  renderer = pystache.Renderer(search_dirs=TEMPLATE_LOCATION)
  #print 'generate_get_set_injection'
  for proto_file in request.proto_file:
    #print 'protofile:', proto_file.name
    for item, package in protoutils.traverse(proto_file):
      java_package = package
      for opt in protoutils.get_named_options(proto_file, 'java_package'):
        java_package = opt[1]
        break
      filename = os.path.join(java_package.replace('.', os.path.sep), item.name + '.java')
      for field in item.field:
        entity_name = gapic_config.get_entity_name_for_message_field(
            item.name, field.name)
        if entity_name:
          f = response.file.add()
          f.name = filename
          f.insertion_point = 'builder_scope:' + package + '.' + item.name
          f.content = renderer.render(construct_builder_view(gapic_config, entity_name, field))

          f = response.file.add()
          f.name = filename
          f.insertion_point = 'class_scope:' + package + '.' + item.name
          f.content = renderer.render(construct_class_view(gapic_config, entity_name, field))
        #else:
        #  print 'miss:', item.name, field.name


def construct_builder_view(gapic_config, entity_name, field):
  if entity_name in gapic_config.collection_configs:
    collection_config = gapic_config.collection_configs.get(entity_name)
    resource = resource_name.ResourceName(collection_config)
    if field.label == FieldDescriptorProto.LABEL_REPEATED:
      return insertion_points.InsertBuilderList(resource, field)
    else:
      return insertion_points.InsertBuilder(resource, field)
  elif entity_name in gapic_config.collection_oneofs:
    # NOT SUPPORTED
    #if field.label == FieldDescriptorProto.LABEL_REPEATED:
    #  return templates.InsertBuilderList(formatted_field_data)
    #else:
    #  return templates.InsertBuilder(formatted_field_data)
    pass


def construct_class_view(gapic_config, entity_name, field):
  if entity_name in gapic_config.collection_configs:
    collection_config = gapic_config.collection_configs.get(entity_name)
    resource = resource_name.ResourceName(collection_config)
    if field.label == FieldDescriptorProto.LABEL_REPEATED:
      return insertion_points.InsertClassList(resource, field)
    else:
      return insertion_points.InsertClass(resource, field)
  elif entity_name in gapic_config.collection_oneofs:
    # NOT SUPPORTED
    #if field.label == FieldDescriptorProto.LABEL_REPEATED:
    #  return templates.InsertBuilderList(formatted_field_data)
    #else:
    #  return templates.InsertBuilder(formatted_field_data)
    pass


if __name__ == '__main__':
  # Read request message from stdin
  data = sys.stdin.read()

  # Parse request
  request = plugin.CodeGeneratorRequest()
  request.ParseFromString(data)

  # Expect only one proto on the command line
  if len(request.file_to_generate) != 1:
    raise ValueError('expected 1 proto file on the command line, got:' + str(request.file_to_generate))
  proto_file_name = request.file_to_generate[0]
  for pf in request.proto_file:
    if pf.name == proto_file_name:
      proto_file = pf
      break

  gapic_config = gapicutils.read_from_gapic_yaml(request.parameter)

  # Generate output
  response = plugin.CodeGeneratorResponse()

  generate_resource_name_types(response, gapic_config, proto_file)
  generate_get_set_injection(response, gapic_config, request)

  # Serialise response message
  output = response.SerializeToString()

  # Write to stdout
  sys.stdout.write(output)
