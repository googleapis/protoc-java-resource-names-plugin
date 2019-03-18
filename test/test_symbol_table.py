# Copyright 2019 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from plugin.utils.symbol_table import SymbolTable


def test_symbol_table():
    table = SymbolTable()

    # Escape a key word once
    keyword = "interface"
    escaped_keyword = table.getNewSymbol(keyword)
    assert escaped_keyword == "interface_"
    assert keyword == "interface"

    # Escape a key word twice
    assert table.getNewSymbol("interface") == "interface__"

    # Add a non-keyword
    assert table.getNewSymbol("bridge") == "bridge"
    # Escape the same non-keyword
    assert table.getNewSymbol("bridge") == "bridge_"

    # Escape a keyword that already has an underscore
    assert table.getNewSymbol("class_") == "class_"
    assert table.getNewSymbol("class") == "class__"
    assert table.getNewSymbol("class_") == "class___"

    # Make sure that a new instance of SymbolTable uses a different base set
    new_table = SymbolTable()
    assert new_table.getNewSymbol("interface") == "interface_"
