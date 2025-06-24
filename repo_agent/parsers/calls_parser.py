import os
from functools import lru_cache
from collections import defaultdict
from tree_sitter import Node  # type: ignore

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
                if language in {"java", "kotlin"}:
                    call_name = self._extract_function_name(node, code)
                else:
                    func_node = node.child_by_field_name("function")
                    call_name = self._extract_function_name(func_node, code)

                if parent_func and call_name:
                    calls.append((parent_func, call_name))

            for child in node.children:
                walk(child, parent_func)

        walk(root)

        rel_path = os.path.relpath(file_path, self.repo_path)
        return [(name, start, end, rel_path) for name, start, end in functions], calls

    def _extract_function_name(self, node: Node, code: bytes) -> str | None:
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
            for child in node.children:
                if child.type == "identifier":
                    return self._get_node_text(child, code)
            return None

        elif node.type == "identifier":
            return self._get_node_text(node, code)

        else:
            return self._get_node_text(node, code)

    def _get_node_text(self, node: Node, code: bytes) -> str | None:
        if not node:
            return None
        return code[node.start_byte:node.end_byte].decode("utf-8")

    @lru_cache(maxsize=256)
    def _load_ast_and_code(self, file_path: str, language: str) -> tuple[Node, bytes]:
        parser = TreeSitterParser(language)
        root = parser.parse_file(file_path)
        with open(file_path, "rb") as f:
            code = f.read()
        return root, code

    def process_file(self, file_path: str, language: str):
        try:
            root, code = self._load_ast_and_code(file_path, language)
            functions, calls = self.extract_functions_and_calls(
                root, language, code, file_path
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

        except Exception as e:
            print(f"[!] Failed to process {file_path}: {e}")

    def build_from_repo(self):
        for root_dir, _, files in os.walk(self.repo_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                lang = {
                    ".py": "python",
                    ".go": "go",
                    ".java": "java",
                    ".kt": "kotlin"
                }.get(ext)
                if not lang:
                    continue

                path = os.path.join(root_dir, file)
                self.process_file(path, lang)

    def get_call_graph(self):
        return self.call_graph
