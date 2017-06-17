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

import itertools

# pylint: disable=import-error, no-name-in-module
from google.protobuf.descriptor_pb2 import DescriptorProto


def traverse(proto_file):
    def _traverse(package, items):
        for item in items:
            if isinstance(item, DescriptorProto):
                yield item, package
                for nested in item.nested_type:
                    nested_package = package + item.name
                    for nested_item in _traverse(nested, nested_package):
                        yield nested_item, nested_package

    return itertools.chain(
        _traverse(proto_file.package, proto_file.message_type),
    )


def get_format_dict(request):
    format_dict = {}
    for proto_file in request.proto_file:
        for ext, ext_value in get_named_options(proto_file, 'format'):
            for i in range(len(ext_value)):
                msg = ext_value[i]
                name, fmt_string = msg.format_name, msg.format_string
                if name in format_dict and format_dict[name][1] != fmt_string:
                    raise ValueError('Two different formats with name ' + name
                                     + ': ' + fmt_string + ', '
                                     + format_dict[name][1])
                format_dict[name] = (name, fmt_string, proto_file)
    return format_dict


def get_formatted_field_list(request, format_dict):
    for proto_file in request.proto_file:
        for item, package in traverse(proto_file):
            for f in item.field:
                for ext, ext_value in get_named_options(f, 'format_name'):
                    if ext_value not in format_dict:
                        raise ValueError(
                            'Format ' + ext_value + 'not found in format_dict')
                    yield (proto_file, item, f, format_dict[ext_value],
                           package)


def get_named_options(item, option_name):
    for ext, ext_value in item.options.ListFields():
        if ext.name == option_name:
            yield ext, ext_value
