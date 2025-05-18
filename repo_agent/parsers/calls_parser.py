import os
from collections import defaultdict
from tree_sitter import Node

from repo_agent.parsers.file_parser import TreeSitterParser


class CallGraphBuilder:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.call_graph = defaultdict(lambda: {"calls": set(), "called_by": set()})

    def extract_functions_and_calls(
        self, root: Node, language: str, code: bytes, file_path: str
    ):
        functions = []
        calls = []

        def walk(node: Node, parent_func=None):
            if language == "python":
                if node.type in ("function_definition", "class_definition"):
                    name = self._get_node_text(node.child_by_field_name("name"), code)
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    functions.append((name, start_line, end_line))
                    parent_func = name

            elif language == "go":
                if node.type == "function_declaration":
                    name = self._get_node_text(node.child_by_field_name("name"), code)
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    functions.append((name, start_line, end_line))
                    parent_func = name

            elif language in ("java", "kotlin"):
                if node.type in (
                    "method_declaration",
                    "class_declaration",
                    "function_declaration",
                ):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = self._get_node_text(name_node, code)
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1
                        functions.append((name, start_line, end_line))
                        parent_func = name

            call_node_types = {
                "python": {"call", "function_call"},
                "java": {"method_invocation"},
                "kotlin": {"call_expression"},
                "go": {"call_expression"},
            }

            if node.type in call_node_types.get(language, set()):
                if language == "java":
                    call_name = self._extract_function_name(node, code)
                elif language == "kotlin":
                    call_name = self._extract_function_name(node, code)
                else:
                    function_name_node = node.child_by_field_name("function")
                    call_name = self._extract_function_name(function_name_node, code)

                if parent_func and call_name:
                    calls.append((parent_func, call_name))

            for child in node.children:
                walk(child, parent_func)

        walk(root)
        # Возвращаем список с функциями и вызовами + путь
        rel_path = os.path.relpath(file_path, self.repo_path)
        return [(name, start, end, rel_path) for name, start, end in functions], calls

    def _extract_function_name(self, node: Node, code: bytes) -> str:
        if node is None:
            return None
        if node.type in ("selector_expression", "member_expression"):
            left = self._extract_function_name(
                node.child_by_field_name("object")
                or node.child_by_field_name("operand"),
                code,
            )
            right = self._extract_function_name(
                node.child_by_field_name("name") or node.child_by_field_name("field"),
                code,
            )
            return f"{left}.{right}" if left and right else None
        elif node.type == "method_invocation":
            name_node = node.child_by_field_name("name")
            return self._get_node_text(name_node, code) if name_node else None
        elif node.type == "call_expression":
            # Специальная обработка Kotlin вызова функции
            for child in node.children:
                if child.type == "identifier":
                    return self._get_node_text(child, code)
            return None
        elif node.type == "identifier":
            return self._get_node_text(node, code)
        else:
            return self._get_node_text(node, code)

    def _get_node_text(self, node, code: bytes):
        if not node:
            return None
        # Берём срез из байтов и декодируем в строку
        return code[node.start_byte : node.end_byte].decode("utf8")

    def process_file(self, file_path: str, language: str):
        parser = TreeSitterParser(language)
        root = parser.parse_file(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        functions, calls = self.extract_functions_and_calls(
            root, language, code.encode("utf-8"), file_path
        )
        for func_name, start_line, end_line, rel_path in functions:
            self.call_graph[func_name]["location"] = {
                "file": rel_path,
                "start_line": start_line,
                "end_line": end_line,
            }
        for caller, callee in calls:
            self.call_graph[caller]["calls"].add(callee)
            self.call_graph[callee]["called_by"].add(caller)

    def build_from_repo(self):
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".py":
                    lang = "python"
                elif ext == ".go":
                    lang = "go"
                elif ext == ".java":
                    lang = "java"
                elif ext == ".kt":
                    lang = "kotlin"
                else:
                    continue

                path = os.path.join(root, file)
                try:
                    self.process_file(path, lang)
                except Exception as e:
                    print(f"Failed to process {path}: {e}")

    def get_call_graph(self):
        return self.call_graph
