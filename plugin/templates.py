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

from google.gax import path_template
from plugin.utils import protoutils


def get_lower(s):
  return s[:1].lower() + s[1:]


def lower_underscore_to_lower_camel(snake_str):
  components = snake_str.split('_')
  return components[0] + "".join(x.title() for x in components[1:])


def lower_underscore_to_upper_camel(snake_str):
  components = snake_str.split('_')
  return "".join(x.title() for x in components)


class ResourceName(object):

  def __init__(self, fmt_data):
    name, fmt_str, proto_file = fmt_data
    pt = [seg.literal for seg in path_template.PathTemplate(fmt_str).segments
          if seg.kind == path_template._BINDING]
    self.format_name_upper = name
    self.format_name_lower = get_lower(name)
    self.parameter_list = [
        {
            'parameter': lower_underscore_to_lower_camel(lit),
            'parameter_name': lower_underscore_to_lower_camel(lit),
            'not_last': True,
        } for lit in pt]
    self.parameter_list[-1]['not_last'] = False
    self.format_fields = [
        {
            'upper': f['parameter'],
            'lower': f['parameter']
        } for f in self.parameter_list]
    self.format_string = fmt_str
    self.package_name = proto_file.package
    for ext, ext_value in protoutils.get_named_options(proto_file, 'java_package'):
      self.package_name = ext_value
      break

  def formatNameUpper(self):
    return self.format_name_upper

  def formatNameLower(self):
    return self.format_name_lower

  def formatFields(self):
    return self.format_fields

  def parameterList(self):
    return self.parameter_list

  def packageName(self):
    return self.package_name;

  def formatString(self):
    return self.format_string


class InsertBuilder(object):

  def __init__(self, formatted_field_data):
    _, _, field, fmt, _ = formatted_field_data
    self.format_name_upper = fmt[0]
    self.format_name_lower = get_lower(fmt[0])
    self.original_name_upper = lower_underscore_to_upper_camel(field.name)

  def formatNameUpper(self):
    return self.format_name_upper

  def formatNameLower(self):
    return self.format_name_lower

  def originalNameUpper(self):
    return self.original_name_upper


class InsertBuilderList(InsertBuilder):
  pass


class InsertClass(InsertBuilder):
  pass


class InsertClassList(InsertBuilder):
  pass

