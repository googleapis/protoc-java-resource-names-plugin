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
import chevron

from google.protobuf.compiler import plugin_pb2 as plugin

from plugin.utils import proto_utils, gapic_utils


def render_new_file(response, resource):
    f = response.file.add()
    f.name = resource.filename()
    templ_path = resource.template_path()
    with open(templ_path, 'r') as templ:
        f.content = chevron.render(templ, resource)


def generate_resource_name_types(response, gapic_config, java_package):
    resources = gapic_utils.collect_resource_name_types(
        gapic_config, java_package)
    for resource in resources:
        render_new_file(response, resource)


def get_protos_to_generate_for(request):
    proto_files = dict((pf.name, pf) for pf in request.proto_file)
    for pf_name in request.file_to_generate:
        if pf_name in proto_files:
            yield proto_files[pf_name]


def resolve_java_package_names(request):
    java_packages = set()
    for pf in get_protos_to_generate_for(request):
        for opt in proto_utils.get_named_options(pf, 'java_package'):
            if opt[1]:
                java_packages.add(opt[1])
                break
    if not java_packages:
        raise ValueError('java package not defined')
    return java_packages


def main(data):
    # Parse request
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    java_packages = resolve_java_package_names(request)
    gapic_config = gapic_utils.read_from_gapic_yaml(request)
    # Generate output
    response = plugin.CodeGeneratorResponse()

    for java_package in java_packages:
        generate_resource_name_types(response, gapic_config, java_package)

    # Serialise response message
    output = response.SerializeToString()

    return output


def entrypoint():
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


if __name__ == '__main__':
    entrypoint()
