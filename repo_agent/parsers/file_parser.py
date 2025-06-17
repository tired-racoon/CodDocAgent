import os
import json
import git
import hashlib
from functools import lru_cache
from tree_sitter import Parser, Language  # type: ignore
import tree_sitter_python as tspython  # type: ignore
import tree_sitter_java as tsjava  # type: ignore
import tree_sitter_go as tsgo  # type: ignore
import tree_sitter_kotlin as tskotlin  # type: ignore

from tqdm import tqdm
from colorama import Fore, Style
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

EXTENSION_TO_LANGUAGE = {'.py': 'python', '.java': 'java', '.go': 'go', '.kt': 'kotlin', '.kts': 'kotlin'}
NODE_TYPES = {...}

class TreeSitterParser:
    def __init__(self, repo_path, file_path=None):
        self.repo_path = repo_path
        setting = SettingsManager.get_setting()
        self.project_hierarchy = setting.project.target_repo / setting.project.hierarchy_name

    def _detect_language(self, file_path):
        _, ext = os.path.splitext(file_path)
        return EXTENSION_TO_LANGUAGE.get(ext.lower())

    @lru_cache(maxsize=None)
    def _read_file(self, abs_path):
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()

    def read_file(self, file_path):
        abs_path = os.path.join(self.repo_path, file_path)
        return self._read_file(abs_path)

    @lru_cache(maxsize=None)
    def parse_code(self, code: str, language_name: str):
        parser = Parser()
        parser.set_language(LANGUAGE_MAPPING[language_name])
        tree = parser.parse(code.encode('utf8'))
        return tree.root_node

    @lru_cache(maxsize=None)
    def generate_file_structure(self, file_path):
        language = self._detect_language(file_path)
        if not language or language not in LANGUAGE_MAPPING:
            return []
        code = self.read_file(file_path)
        root = self.parse_code(code, language)
        result = []

        # Однопроходный обход дерева (O(n))
        stack = [(root, None)]
        while stack:
            node, parent = stack.pop()
            type_map = NODE_TYPES[language]
            if node.type in type_map['function']:
                name = self.extract_name(node)
                params = self.extract_parameters(node)
                start, end = node.start_point[0]+1, node.end_point[0]+1
                snippet = code.splitlines()[start-1:end]
                result.append((language, 'func', name, start, end, params, parent, '\n'.join(snippet)))
            elif node.type in type_map['class']:
                name = self.extract_name(node)
                start, end = node.start_point[0]+1, node.end_point[0]+1
                snippet = code.splitlines()[start-1:end]
                result.append((language, 'class', name, start, end, [], None, '\n'.join(snippet)))
                parent = name
            for child in reversed(node.children):
                stack.append((child, parent))
        return result

    def generate_overall_structure(self, jump_files=None):
        jump_files = set(jump_files or [])
        cache = {}
        gitignore_checker = GitignoreChecker(self.repo_path, os.path.join(self.repo_path, '.gitignore'))
        structure = {}
        for path in tqdm(gitignore_checker.check_files_and_folders()):
            if path in jump_files or is_latest_version_file_regex(path):
                continue
            # Хеш-контроль, чтобы не парсить заново
            content = self.read_file(path)
            h = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if cache.get(path) == h:
                continue
            objs = self.generate_file_structure(path)
            structure[path] = objs
            cache[path] = h
        return structure