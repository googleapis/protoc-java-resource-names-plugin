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

import re


def get_lower(s):
    return s[:1].lower() + s[1:]


def to_snake(s):
    """Convert any string to snake case.

    Args:
        s (str): The input string, provided in any sane case system.

    Returns:
        str: The string in snake case (and all lower-cased).
    """
    # Replace all capital letters that are preceded by a lower-case letter.
    s = re.sub(r'(?<=[a-z])([A-Z])', r'_\1', str(s))

    # Find all capital letters that are followed by a lower-case letter,
    # and are preceded by any character other than underscore.
    # (Note: This also excludes beginning-of-string.)
    s = re.sub(r'(?<=[^_])([A-Z])(?=[a-z])', r'_\1', s)

    # Numbers are a weird case; the goal is to spot when they _start_
    # some kind of name or acronym (e.g. 2FA, 3M).
    #
    # Find cases of a number preceded by a lower-case letter _and_
    # followed by at least two capital letters or a single capital and
    # end of string.
    s = re.sub(r'(?<=[a-z])(\d)(?=[A-Z]{2})', r'_\1', s)
    s = re.sub(r'(?<=[a-z])(\d)(?=[A-Z]$)', r'_\1', s)

    # Done; return the camel-cased string.
    return s.lower()


def lower_underscore_to_lower_camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def lower_underscore_to_upper_camel(snake_str):
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)


def lower_camel_to_upper_camel(lower_camel_str):
    return lower_camel_str[0].upper() + lower_camel_str[1:]


def remove_suffix(original, suffix):
    if original.endswith(suffix):
        return original[:-len(suffix)]
    return original


def get_resource_type_class_name(entity_name):
    name = '_'.join([entity_name, 'name'])
    return lower_underscore_to_upper_camel(name)


def get_fixed_resource_type_class_name(entity_name):
    return lower_underscore_to_upper_camel(entity_name)


def get_resource_type_var_name(entity_name):
    name = '_'.join([entity_name, 'name'])
    return lower_underscore_to_lower_camel(name)


def get_resource_type_from_class_name(class_name):
    return class_name + 'Type'


def get_oneof_lower_underscore(entity_name):
    entity_name = remove_suffix(entity_name, '_oneof')
    return '_'.join([entity_name, 'name_oneof'])


def get_oneof_class_name(entity_name):
    name = get_oneof_lower_underscore(entity_name)
    return lower_underscore_to_upper_camel(name)


def get_parent_resource_name_lower_underscore(entity_name):
    entity_name = remove_suffix(entity_name, '_oneof')
    return '_'.join([entity_name, 'name'])


def get_parent_resource_name_class_name(entity_name):
    name = get_parent_resource_name_lower_underscore(entity_name)
    return lower_underscore_to_upper_camel(name)


def get_resource_name_factory_lower_underscore(entity_name):
    entity_name = remove_suffix(entity_name, '_oneof')
    return '_'.join([entity_name, 'names'])


def get_resource_name_factory_class_name(entity_name):
    name = get_resource_name_factory_lower_underscore(entity_name)
    return lower_underscore_to_upper_camel(name)


def get_untyped_resource_name_lower_underscore(entity_name):
    entity_name = remove_suffix(entity_name, '_oneof')
    return '_'.join(['untyped', entity_name, 'name'])


def get_untyped_resource_name_class_name(entity_name):
    name = get_untyped_resource_name_lower_underscore(entity_name)
    return lower_underscore_to_upper_camel(name)
