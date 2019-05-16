#!/usr/bin/env python
# Copyright 2019, Google LLC
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
#     * Neither the name of Google LLC nor the names of its
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

import re
import sys

import yaml

from google.protobuf.compiler import plugin_pb2

from plugin.utils import gapic_utils


def entrypoint():
    try:
        source = sys.stdin.buffer
        dest = sys.stdout.buffer
    except AttributeError:
        source = sys.stdin
        dest = sys.stdout

    # Read request message from stdin
    r = plugin_pb2.CodeGeneratorRequest.FromString(source.read())
    output_filename = 'gapic.v1.yaml'
    if r.parameter:
        with open(r.parameter, 'r') as f:
            gapic_v2 = yaml.load(f)
        output_filename = re.sub(r'[._]v[\d]', '.v1', r.parameter)
        if '.v1' not in output_filename:
            output_filename = re.sub(r'\.ya?ml$', '.v1.yaml', output_filename)
    else:
        gapic_v2 = {}

    # Create a GAPIC v1 YAML.
    gapic_v1 = gapic_utils.reconstruct_gapic_yaml(gapic_v2, r)

    # Write to stdout
    F = plugin_pb2.CodeGeneratorResponse.File
    dest.write(plugin_pb2.CodeGeneratorResponse(file=[
        F(name=output_filename, content=yaml.dump(
            gapic_v1,
            default_flow_style=False,
        ))
    ]).SerializeToString())
