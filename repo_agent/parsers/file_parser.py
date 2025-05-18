from tree_sitter import Parser, Language

import tree_sitter_python as tspython
import tree_sitter_java as tsjava
import tree_sitter_go as tsgo
import tree_sitter_kotlin as tskotlin

LANGUAGE_MAPPING = {
    'python': Language(tspython.language()),
    'java': Language(tsjava.language()),
    'go': Language(tsgo.language()),
    'kotlin': Language(tskotlin.language()),
}


class TreeSitterParser:
    def __init__(self, language_name: str):
        if language_name not in LANGUAGE_MAPPING:
            raise ValueError(f"Unsupported language: {language_name}")
        self.ts_language = LANGUAGE_MAPPING[language_name]
        self.parser = Parser(self.ts_language)

    def parse_code(self, code: str):
        tree = self.parser.parse(code.encode('utf8'))
        return tree.root_node

    def parse_file(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        return self.parse_code(code)

    def walk_tree(self, node, indent=0):
        print("  " * indent + f"{node.type} [{node.start_point} - {node.end_point}]")
        for child in node.children:
            self.walk_tree(child, indent + 1)
