from tree_sitter import Parser
from tree_sitter_language_pack import get_language

PY_LANGUAGE = get_language("python")

parser = Parser(PY_LANGUAGE)

code = b"""
def hello():
    print("world")
"""

tree = parser.parse(code)

print("Root node:", tree.root_node)