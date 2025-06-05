from tree_sitter import Parser, Language  # type: ignore
import tree_sitter_python as tspython  # type: ignore
import tree_sitter_java as tsjava  # type: ignore
import tree_sitter_go as tsgo  # type: ignore
import tree_sitter_kotlin as tskotlin  # type: ignore

import os
import json
import git
from collections import Counter
from colorama import Fore, Style
from tqdm import tqdm

from repo_agent.log import logger
from repo_agent.settings import SettingsManager
from repo_agent.utils.gitignore_checker import GitignoreChecker
from repo_agent.utils.meta_info_utils import is_latest_version_file_regex

LANGUAGE_MAPPING = {
    "python": Language(tspython.language()),
    "java": Language(tsjava.language()),
    "go": Language(tsgo.language()),
    "kotlin": Language(tskotlin.language()),
}

NODE_TYPES = {
    "python": {
        "function": ["function_definition", "decorated_definition"],
        "class": ["class_definition"],
    },
    "java": {
        "function": ["method_declaration", "constructor_declaration"],
        "class": ["class_declaration"],
    },
    "go": {
        "function": ["function_declaration", "method_declaration"],
        "class": [],
    },  # Go doesn't have classes per se
    "kotlin": {
        "function": ["function_declaration"],
        "class": ["class_declaration", "object_declaration"],
    },
}

# File extension to language mapping
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".java": "java",
    ".go": "go",
    ".kt": "kotlin",
    ".kts": "kotlin",
}


class FileHandler:
    def __init__(self, repo_path, file_path):
        self.file_path = file_path
        self.repo_path = repo_path

        setting = SettingsManager.get_setting()
        self.project_hierarchy = (
            setting.project.target_repo / setting.project.hierarchy_name  # type: ignore
        )

        # Determine language from file extension or detect most popular language
        if file_path is not None:
            self.language_name = self._detect_language(file_path)
        else:
            self.language_name = self._detect_most_popular_language()

        if self.language_name and self.language_name in LANGUAGE_MAPPING:
            self.ts_language = LANGUAGE_MAPPING[self.language_name]
            self.parser = Parser(self.ts_language)
        else:
            self.ts_language = None
            self.parser = None

        self.code = None
        self.root = None

    def _detect_language(self, file_path):
        """Detect programming language from file extension"""
        _, ext = os.path.splitext(file_path)
        return EXTENSION_TO_LANGUAGE.get(ext.lower())

    def _detect_most_popular_language(self):
        """Detect the most popular language in the repository"""
        try:
            gitignore_checker = GitignoreChecker(
                directory=self.repo_path,
                gitignore_path=os.path.join(self.repo_path, ".gitignore"),
            )

            language_counter = Counter()

            # Count files by language
            for file_path in gitignore_checker.check_files_and_folders():
                language = self._detect_language(file_path)
                if language:
                    language_counter[language] += 1

            if language_counter:
                # Return the most common language
                most_popular = language_counter.most_common(1)[0][0]
                logger.info(
                    f"Detected most popular language in repository: {most_popular}"
                )
                return most_popular
            else:
                # Default to Python if no supported languages found
                logger.warning(
                    "No supported languages found in repository, defaulting to Python"
                )
                return "python"

        except Exception as e:
            logger.error(f"Error detecting most popular language: {e}")
            # Default to Python in case of error
            return "python"

    def read_file(self, file_path=None):
        """Read file content"""
        target_file_path = file_path if file_path is not None else self.file_path

        if target_file_path is None:
            raise ValueError(
                "No file path specified and no default file path available"
            )

        abs_file_path = os.path.join(self.repo_path, target_file_path)
        with open(abs_file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content

    def write_file(self, file_path, content):
        """Write content to file"""
        if file_path.startswith("/"):
            file_path = file_path[1:]

        abs_file_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        with open(abs_file_path, "w", encoding="utf-8") as file:
            file.write(content)

    def get_modified_file_versions(self, file_path=None):
        """Get current and previous versions of the file from git"""
        target_file_path = file_path if file_path is not None else self.file_path

        if target_file_path is None:
            raise ValueError(
                "No file path specified and no default file path available"
            )

        repo = git.Repo(self.repo_path)

        # Read the file in the current working directory (current version)
        current_version_path = os.path.join(self.repo_path, target_file_path)
        with open(current_version_path, "r", encoding="utf-8") as file:
            current_version = file.read()

        # Get the file version from the last commit (previous version)
        commits = list(repo.iter_commits(paths=target_file_path, max_count=1))
        previous_version = None
        if commits:
            commit = commits[0]
            try:
                previous_version = (
                    (commit.tree / target_file_path).data_stream.read().decode("utf-8")
                )
            except KeyError:
                previous_version = None  # The file may be newly added and not present in previous commits

        return current_version, previous_version

    def parse_code(self, code: str):
        """Parse code using tree-sitter"""
        if not self.parser:
            return None
        self.code = code
        tree = self.parser.parse(code.encode("utf8"))
        self.root = tree.root_node
        return self.root

    def parse_file(self, filename: str):
        """Parse file using tree-sitter"""
        with open(os.path.join(self.repo_path, filename), "r", encoding="utf-8") as f:
            code = f.read()
        return self.parse_code(code)

    def get_node_text(self, node):
        """Get text content of a node"""
        if not self.code:
            return ""
        start_byte = node.start_byte
        end_byte = node.end_byte
        return self.code.encode("utf8")[start_byte:end_byte].decode("utf8")

    def extract_name(self, node):
        """Extract name from a node, handling decorated functions properly"""
        # For decorated definitions in Python, we need to find the function_definition inside
        if node.type == "decorated_definition":
            for child in node.children:
                if child.type == "function_definition":
                    return self._extract_name_from_function_definition(child)
        elif node.type == "function_definition":
            return self._extract_name_from_function_definition(node)
        else:
            # For other node types (classes, methods in other languages)
            return self._extract_name_generic(node)

    def _extract_name_from_function_definition(self, node):
        """Extract name specifically from function_definition node"""
        for child in node.children:
            if child.type == "identifier":
                return self.get_node_text(child)
        return "unknown"

    def _extract_name_generic(self, node):
        """Generic name extraction for non-function nodes"""
        # Special handling for Go methods with receivers
        if self.language_name == "go" and node.type in [
            "method_declaration",
            "function_declaration",
        ]:
            return self._extract_go_function_name(node)

        for child in node.children:
            if child.type == "identifier" or child.type == "name":
                return self.get_node_text(child)
        return "unknown"

    def _extract_go_function_name(self, node):
        """Extract function/method name specifically for Go"""
        # For Go methods: func (receiver) name(params)
        # For Go functions: func name(params)

        # Look for field_identifier (for methods) or identifier (for functions)
        for child in node.children:
            if child.type == "field_identifier":
                # This is the method name
                return self.get_node_text(child)
            elif child.type == "identifier":
                # Check if this identifier is the function name (not part of receiver)
                # Function name should come after any parameter_list (receiver)
                receiver_found = False
                for prev_child in node.children:
                    if prev_child == child:
                        break
                    if prev_child.type == "parameter_list":
                        receiver_found = True

                # If no receiver found, or this identifier comes after receiver,
                # it's likely the function name
                if not receiver_found:
                    # For regular functions: func name(params)
                    return self.get_node_text(child)

        return "unknown"

    def extract_parameters(self, node):
        """Extract parameters from function/method node"""
        if self.language_name == "python":
            return self._extract_python_parameters(node)
        elif self.language_name == "java":
            return self._extract_java_parameters(node)
        elif self.language_name == "go":
            return self._extract_go_parameters(node)
        elif self.language_name == "kotlin":
            return self._extract_kotlin_parameters(node)
        return []

    def _extract_python_parameters(self, node):
        """Extract parameters for Python functions"""
        # Handle decorated definitions
        if node.type == "decorated_definition":
            for child in node.children:
                if child.type == "function_definition":
                    return self._extract_python_parameters(child)

        # Handle regular function definitions
        for child in node.children:
            if child.type == "parameters":
                params = []
                for param_child in child.children:
                    if param_child.type == "identifier":
                        params.append(self.get_node_text(param_child))
                    elif param_child.type == "default_parameter":
                        # Get the parameter name from default parameter
                        for subchild in param_child.children:
                            if subchild.type == "identifier":
                                params.append(self.get_node_text(subchild))
                                break
                return params
        return []

    def _extract_java_parameters(self, node):
        """Extract parameters for Java methods"""
        for child in node.children:
            if child.type == "formal_parameters":
                params = []
                for param_child in child.children:
                    if param_child.type == "formal_parameter":
                        # Get parameter name (last identifier in formal_parameter)
                        identifiers = [
                            c for c in param_child.children if c.type == "identifier"
                        ]
                        if identifiers:
                            params.append(self.get_node_text(identifiers[-1]))
                return params
        return []

    def _extract_go_parameters(self, node):
        """Extract parameters for Go functions"""
        for child in node.children:
            if child.type == "parameter_list":
                params = []
                for param_child in child.children:
                    if param_child.type == "parameter_declaration":
                        # Get parameter names
                        for subchild in param_child.children:
                            if subchild.type == "identifier":
                                params.append(self.get_node_text(subchild))
                return params
        return []

    def _extract_kotlin_parameters(self, node):
        """Extract parameters for Kotlin functions"""
        for child in node.children:
            if child.type == "function_value_parameters":
                params = []
                for param_child in child.children:
                    if param_child.type == "function_value_parameter":
                        # Get parameter name
                        for subchild in param_child.children:
                            if subchild.type == "simple_identifier":
                                params.append(self.get_node_text(subchild))
                                break
                return params
        return []

    def get_functions_and_classes(self):
        """Extract functions and classes from parsed code"""
        if not self.root or not self.language_name:
            return []

        result = []

        def walk(node, parent_name=None):
            for child in node.children:
                node_type = child.type
                type_map = NODE_TYPES[self.language_name]  # type: ignore

                if node_type in type_map["function"]:
                    name = self.extract_name(child)
                    params = self.extract_parameters(child)
                    code_content = self.get_node_text(child)
                    result.append(
                        (
                            (
                                "FunctionDef"
                                if self.language_name == "python"
                                else "Function"
                            ),
                            name,
                            child.start_point[0] + 1,  # 1-based
                            child.end_point[0] + 1,
                            params,
                            parent_name,
                            code_content,
                        )
                    )

                elif node_type in type_map["class"]:
                    name = self.extract_name(child)
                    code_content = self.get_node_text(child)
                    result.append(
                        (
                            "ClassDef" if self.language_name == "python" else "Class",
                            name,
                            child.start_point[0] + 1,
                            child.end_point[0] + 1,
                            [],
                            None,
                            code_content,
                        )
                    )
                    walk(child, name)
                else:
                    walk(child, parent_name)

        walk(self.root)
        return result

    def get_obj_code_info(
        self, code_type, code_name, start_line, end_line, params, file_path=None
    ):
        """Get detailed information about a code object"""
        code_info = {}
        code_info["type"] = code_type
        code_info["name"] = code_name
        code_info["md_content"] = []
        code_info["code_start_line"] = start_line
        code_info["code_end_line"] = end_line
        code_info["params"] = params

        target_file_path = file_path if file_path is not None else self.file_path

        if target_file_path is None:
            raise ValueError(
                "No file path specified and no default file path available"
            )

        with open(
            os.path.join(self.repo_path, target_file_path),
            "r",
            encoding="utf-8",
        ) as code_file:
            lines = code_file.readlines()
            code_content = "".join(lines[start_line - 1 : end_line])
            name_column = lines[start_line - 1].find(code_name) if lines else 0

            # Check for return statement
            have_return = "return" in code_content

            code_info["have_return"] = have_return
            code_info["code_content"] = code_content
            code_info["name_column"] = name_column

        return code_info

    def generate_file_structure(self, file_path):
        """Generate structure for a single file"""
        if file_path is None:
            raise ValueError("File path cannot be None for generate_file_structure")

        # Detect language for this specific file
        language = self._detect_language(file_path)

        if not language or language not in LANGUAGE_MAPPING:
            # Fallback to basic parsing for unsupported files
            return self._fallback_file_structure(file_path)

        # Temporarily switch language if different from current
        original_language = self.language_name
        original_parser = self.parser

        if language != self.language_name:
            self.language_name = language
            self.ts_language = LANGUAGE_MAPPING[language]
            self.parser = Parser(self.ts_language)

        try:
            self.parse_file(file_path)
            structures = self.get_functions_and_classes()
            file_objects = []

            for struct in structures:
                (
                    structure_type,
                    name,
                    start_line,
                    end_line,
                    params,
                    parent,
                    code_content,
                ) = struct
                code_info = self.get_obj_code_info(
                    structure_type, name, start_line, end_line, params, file_path
                )
                # Add parent information
                code_info["parent"] = parent
                file_objects.append(code_info)

            return file_objects

        finally:
            # Restore original language settings
            self.language_name = original_language
            self.parser = original_parser

    def _fallback_file_structure(self, file_path):
        """Fallback parsing for unsupported file types"""
        # For unsupported files, return empty structure
        return []

    def generate_overall_structure(self, file_path_reflections, jump_files) -> dict:
        """Generate structure for entire repository"""
        repo_structure = {}
        gitignore_checker = GitignoreChecker(
            directory=self.repo_path,
            gitignore_path=os.path.join(self.repo_path, ".gitignore"),
        )

        bar = tqdm(gitignore_checker.check_files_and_folders())
        for not_ignored_files in bar:
            normal_file_names = not_ignored_files
            if not_ignored_files in jump_files:
                print(
                    f"{Fore.LIGHTYELLOW_EX}[TreeSitter-Parser] Unstaged AddFile, ignore this file: {Style.RESET_ALL}{normal_file_names}"
                )
                continue
            elif is_latest_version_file_regex(not_ignored_files):
                print(
                    f"{Fore.LIGHTYELLOW_EX}[TreeSitter-Parser] Skip Latest Version, Using Git-Status Version]: {Style.RESET_ALL}{normal_file_names}"
                )
                continue
            try:
                repo_structure[normal_file_names] = self.generate_file_structure(
                    not_ignored_files
                )
            except Exception as e:
                logger.error(
                    f"Alert: An error occurred while generating file structure for {not_ignored_files}: {e}"
                )
                continue
            bar.set_description(f"generating repo structure: {not_ignored_files}")
        return repo_structure

    def convert_to_markdown_file(self, file_path=None):
        """Convert file structure to markdown format"""
        with open(self.project_hierarchy, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        if file_path is None:
            file_path = self.file_path

        if file_path is None:
            raise ValueError(
                "No file path specified and no default file path available"
            )

        # Handle both dict and list formats
        if isinstance(json_data.get(file_path), list):
            file_objects = json_data.get(file_path, [])
            # Convert list to dict format for compatibility
            file_dict = {}
            for obj in file_objects:
                file_dict[obj["name"]] = obj
        else:
            file_dict = json_data.get(file_path, {})

        if not file_dict:
            raise ValueError(
                f"No file object found for {file_path} in project_hierarchy.json"
            )

        markdown = ""
        parent_dict = {}

        # Handle both dict values and list of objects
        if hasattr(file_dict, "values"):
            objects = sorted(file_dict.values(), key=lambda obj: obj["code_start_line"])
        else:
            objects = sorted(file_dict, key=lambda obj: obj["code_start_line"])

        for obj in objects:
            if obj.get("parent") is not None:
                parent_dict[obj["name"]] = obj["parent"]

        current_parent = None
        for obj in objects:
            level = 1
            parent = obj.get("parent")
            while parent is not None:
                level += 1
                parent = parent_dict.get(parent)
            if level == 1 and current_parent is not None:
                markdown += "***\n"
            current_parent = obj["name"]
            params_str = ""
            if obj["type"] in ["FunctionDef", "AsyncFunctionDef", "Function"]:
                params_str = "()"
                if obj.get("params"):
                    params_str = f"({', '.join(obj['params'])})"
            markdown += f"{'#' * level} {obj['type']} {obj['name']}{params_str}:\n"
            md_content = obj.get("md_content", [])
            markdown += f"{md_content[-1] if len(md_content) > 0 else ''}\n"
        markdown += "***\n"

        return markdown
