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

from plugin import templates
from plugin.utils import protoutils
from plugin.generated import resource_name_format_pb2


TEMPLATE_LOCATION = os.path.join('plugin', 'templates')

def generate_resource_name_types(response, format_dict):
  renderer = pystache.Renderer(search_dirs=TEMPLATE_LOCATION)
  for fmt_data in format_dict.values():
    name, _, proto_file = fmt_data
    filename = name + '.java'
    for ext, ext_value in protoutils.get_named_options(proto_file, 'java_package'):
      filename = os.path.join(ext_value.replace('.', os.sep), filename)
      break
    f = response.file.add()
    f.name = filename
    f.content = renderer.render(templates.ResourceName(fmt_data))


def generate_get_set_injection(response, formatted_field_list):
  renderer = pystache.Renderer(search_dirs=TEMPLATE_LOCATION)
  for formatted_field_data in formatted_field_list:
    proto_file, item, _, _, package = formatted_field_data
    filename = item.name + '.java'
    for ext, ext_value in protoutils.get_named_options(proto_file, 'java_package'):
      filename = os.path.join(ext_value.replace('.', os.sep), filename)
      break
    f = response.file.add()
    f.name = filename
    f.insertion_point = 'builder_scope:' + package + '.' + item.name
    f.content = renderer.render(construct_builder_view(formatted_field_data))

    f = response.file.add()
    f.name = filename
    f.insertion_point = 'class_scope:' + package + '.' + item.name
    f.content = renderer.render(construct_class_view(formatted_field_data))


def construct_builder_view(formatted_field_data):
  _, _, f, _, _ = formatted_field_data
  if f.label == FieldDescriptorProto.LABEL_REPEATED:
    return templates.InsertBuilderList(formatted_field_data)
  else:
    return templates.InsertBuilder(formatted_field_data)

def construct_class_view(formatted_field_data):
  _, _, f, _, _ = formatted_field_data
  if f.label == FieldDescriptorProto.LABEL_REPEATED:
    return templates.InsertClassList(formatted_field_data)
  else:
    return templates.InsertClass(formatted_field_data)


if __name__ == '__main__':
  # Read request message from stdin
  data = sys.stdin.read()

  # Parse request
  request = plugin.CodeGeneratorRequest()
  request.ParseFromString(data)

  format_dict = protoutils.get_format_dict(request)
  formatted_field_list = list(protoutils.get_formatted_field_list(request, format_dict))

  # Generate output
  response = plugin.CodeGeneratorResponse()

  generate_resource_name_types(response, format_dict)
  generate_get_set_injection(response, formatted_field_list)

  # Serialise response message
  output = response.SerializeToString()

  # Write to stdout
  sys.stdout.write(output)
