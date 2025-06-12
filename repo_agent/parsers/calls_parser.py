import os
from collections import defaultdict
from functools import lru_cache

from repo_agent.parsers.file_parser import TreeSitterParser
from tree_sitter import Node  # type: ignore


class CallGraphBuilder:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.call_graph = defaultdict(lambda: {"calls": set(), "called_by": set()})
        self.ignore_libs = {
            "python": {"numpy", "pandas", "collections", "os", "sys", "logging", "re", "datetime", "json",
                       "itertools"},
            "go": {"fmt", "io", "net", "http", "os", "sync", "context", "time", "bytes", "errors"},
            "java": {"java", "javax", "org.slf4j", "com.google", "com.fasterxml", "junit", "org.apache",
                     "javax.servlet", "org.w3c", "org.xml"},
            "kotlin": {"kotlin", "java", "org.jetbrains", "android", "com.google", "io.reactivex",
                       "com.squareup", "org.json", "org.w3c", "javax"}
        }
        self.scc = []
        self.component_of = {}
        self.compressed_graph = {}

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

                root_name = call_name.split('.')[0]
                if parent_func and call_name and root_name not in self.ignore_libs.get(language, ()):
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

        # После построения raw-графа вычисляем SCC и сжимаем граф
        self._compute_scc_and_compress()

    def get_call_graph(self):
        return self.call_graph

    def get_compressed_graph(self):
        return self.compressed_graph

    def _compute_scc_and_compress(self):
        index_counter = 0
        stack = []
        index = {}
        lowlink = {}
        on_stack = {}
        sccs = []

        for node in list(self.call_graph.keys()):
            if node not in index:
                dfs_stack = [(node, 0)]
                while dfs_stack:
                    current, stage = dfs_stack.pop()
                    if stage == 0:
                        index[current] = index_counter
                        lowlink[current] = index_counter
                        index_counter += 1
                        stack.append(current)
                        on_stack[current] = True
                        dfs_stack.append((current, 1))
                        for neighbor in self.call_graph[current]["calls"]:
                            if neighbor not in self.call_graph:
                                continue
                            if neighbor not in index:
                                dfs_stack.append((neighbor, 0))
                            elif on_stack.get(neighbor, False):
                                lowlink[current] = min(lowlink[current], index[neighbor])
                    else:
                        for neighbor in self.call_graph[current]["calls"]:
                            if neighbor not in self.call_graph:
                                continue
                            if on_stack.get(neighbor, False):
                                lowlink[current] = min(lowlink[current], lowlink[neighbor])
                        if lowlink[current] == index[current]:
                            scc = []
                            while True:
                                w = stack.pop()
                                on_stack[w] = False
                                scc.append(w)
                                if w == current:
                                    break
                            sccs.append(scc)

        self.scc = sccs
        self.component_of = {node: cid for cid, comp in enumerate(sccs) for node in comp}
        compressed = {}
        for cid, comp in enumerate(sccs):
            outgoing = set()
            for node in comp:
                for nbr in self.call_graph[node]["calls"]:
                    if nbr in self.component_of and self.component_of[nbr] != cid:
                        outgoing.add(self.component_of[nbr])
            compressed[cid] = {"nodes": comp, "calls": outgoing}
        self.compressed_graph = compressed
