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

from plugin.utils import casing_utils


class InsertBuilder(object):

    def __init__(self, resource, field, concrete_resource):
        if concrete_resource is None:
            concrete_resource = resource
        self.resource_class_name = resource.className()
        self.resource_var_name = resource.varName()
        self.resource_full_class_name = resource.fullClassName()
        self.concrete_resource_full_name = concrete_resource.fullClassName()
        self.field_name_upper = casing_utils.lower_underscore_to_upper_camel(
            field.name)

    def resourceTypeClassName(self):
        return self.resource_class_name

    def resourceTypeVarName(self):
        return self.resource_var_name

    def resourceTypeFullClassName(self):
        return self.resource_full_class_name

    def concreteResourceTypeFullClassName(self):
        return self.concrete_resource_full_name

    def fieldNameUpper(self):
        return self.field_name_upper


class InsertBuilderList(InsertBuilder):
    pass


class InsertClass(InsertBuilder):
    pass


class InsertClassList(InsertBuilder):
    pass
