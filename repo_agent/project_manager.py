import os
from collections import defaultdict
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path

from repo_agent.parsers.file_parser import TreeSitterParser
from repo_agent.references_finder import ReferenceFinder
from repo_agent.log import logger


class ProjectHandler:
    """Multi-language project handler to replace jedi.Project"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.reference_finder = ReferenceFinder(str(self.repo_path))
        
        self.language_extensions = {
            ".py": "python",
            ".java": "java", 
            ".go": "go",
            ".kt": "kotlin",
            ".kts": "kotlin"
        }
        
        self._file_cache = {}
        self._structure_cache = {}
        
    def get_supported_files(self) -> List[str]:
        """Get all supported source files in the project"""
        supported_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in {'node_modules', 'target', 'build', 'dist', '__pycache__'}]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.language_extensions.keys()):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo_path)
                    supported_files.append(rel_path)
                    
        return sorted(supported_files)
    
    def get_file_language(self, file_path: str) -> Optional[str]:
        """Determine the programming language of a file"""
        _, ext = os.path.splitext(file_path)
        return self.language_extensions.get(ext.lower())
    
    def parse_file(self, file_path: str) -> Optional[Dict]:
        """Parse a file and return its structure"""
        if file_path in self._file_cache:
            return self._file_cache[file_path]
            
        language = self.get_file_language(file_path)
        if not language:
            return None
            
        try:
            abs_path = os.path.join(self.repo_path, file_path)
            parser = TreeSitterParser(str(self.repo_path), file_path)
            structure = parser.generate_file_structure(file_path)
            
            self._file_cache[file_path] = {
                "language": language,
                "structure": structure,
                "path": file_path
            }
            
            return self._file_cache[file_path]
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None
    
    def get_all_functions(self) -> Dict[str, List[Dict]]:
        """Get all functions/methods across the project, grouped by file"""
        functions_by_file = {}
        
        for file_path in self.get_supported_files():
            file_info = self.parse_file(file_path)
            if not file_info:
                continue
                
            functions = []
            for item in file_info["structure"]:
                if item["type"] in ["FunctionDef", "AsyncFunctionDef", "Function", "method_declaration"]:
                    functions.append({
                        "name": item["name"],
                        "start_line": item["code_start_line"],
                        "end_line": item["code_end_line"],
                        "params": item.get("params", []),
                        "parent": item.get("parent")
                    })
            
            if functions:
                functions_by_file[file_path] = functions
                
        return functions_by_file
    
    def get_all_classes(self) -> Dict[str, List[Dict]]:
        """Get all classes across the project, grouped by file"""
        classes_by_file = {}
        
        for file_path in self.get_supported_files():
            file_info = self.parse_file(file_path)
            if not file_info:
                continue
                
            classes = []
            for item in file_info["structure"]:
                if item["type"] in ["ClassDef", "Class", "class_declaration"]:
                    classes.append({
                        "name": item["name"],
                        "start_line": item["code_start_line"],
                        "end_line": item["code_end_line"],
                        "methods": self._get_class_methods(file_info["structure"], item["name"])
                    })
            
            if classes:
                classes_by_file[file_path] = classes
                
        return classes_by_file
    
    def _get_class_methods(self, structure: List[Dict], class_name: str) -> List[Dict]:
        """Get all methods belonging to a specific class"""
        methods = []
        for item in structure:
            if (item.get("parent") == class_name and 
                item["type"] in ["FunctionDef", "AsyncFunctionDef", "Function", "method_declaration"]):
                methods.append({
                    "name": item["name"],
                    "start_line": item["code_start_line"],
                    "end_line": item["code_end_line"],
                    "params": item.get("params", [])
                })
        return methods
    
    def find_definition(self, file_path: str, line: int, column: int) -> Optional[Tuple[str, int, int]]:
        """Find definition of symbol at given position"""
        # This is a simplified implementation
        # For full definition finding, we'd need more sophisticated analysis
        try:
            references = self.reference_finder.get_references(file_path, line, column, scope="project")
            
            # For now, return the first reference as a potential definition
            # In a full implementation, we'd analyze the context to determine actual definitions
            if references:
                return references[0]
                
        except Exception as e:
            logger.error(f"Error finding definition: {e}")
            
        return None
    
    def get_references(self, file_path: str, line: int, column: int, scope: str = "project") -> List[Tuple[str, int, int]]:
        """Get all references to symbol at given position"""
        return self.reference_finder.get_references(file_path, line, column, scope)
    
    def get_project_stats(self) -> Dict[str, int]:
        """Get statistics about the project"""
        stats = {
            "total_files": 0,
            "python_files": 0,
            "java_files": 0,
            "go_files": 0,
            "kotlin_files": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_lines": 0
        }
        
        for file_path in self.get_supported_files():
            language = self.get_file_language(file_path)
            stats["total_files"] += 1
            stats[f"{language}_files"] += 1
            
            # Count functions and classes
            file_info = self.parse_file(file_path)
            if file_info:
                for item in file_info["structure"]:
                    if item["type"] in ["FunctionDef", "AsyncFunctionDef", "Function", "method_declaration"]:
                        stats["total_functions"] += 1
                    elif item["type"] in ["ClassDef", "Class", "class_declaration"]:
                        stats["total_classes"] += 1
            
            try:
                abs_path = os.path.join(self.repo_path, file_path)
                with open(abs_path, 'r', encoding='utf-8') as f:
                    stats["total_lines"] += len(f.readlines())
            except:
                pass
                
        return stats


class ProjectManager:
    """Enhanced ProjectManager using ProjectHandler instead of jedi.Project"""
    
    def __init__(self, repo_path, project_hierarchy):
        self.repo_path = repo_path
        self.project = ProjectHandler(self.repo_path)  # Replace jedi.Project
        self.project_hierarchy = os.path.join(
            self.repo_path, project_hierarchy, "project_hierarchy.json"
        )

    def get_project_structure(self):
        """
        Returns the structure of the project by recursively walking through the directory tree.
        Enhanced to support multiple languages.

        Returns:
            str: The project structure as a string.
        """

        def walk_dir(root, prefix=""):
            structure.append(prefix + os.path.basename(root))
            new_prefix = prefix + "  "
            for name in sorted(os.listdir(root)):
                if name.startswith("."):
                    continue
                path = os.path.join(root, name)
                if os.path.isdir(path):
                    walk_dir(path, new_prefix)
                elif os.path.isfile(path):
                    supported_extensions = {".py", ".java", ".go", ".kt", ".kts"}
                    if any(name.endswith(ext) for ext in supported_extensions):
                        lang_indicator = ""
                        if name.endswith(".py"):
                            lang_indicator = " [Python]"
                        elif name.endswith(".java"):
                            lang_indicator = " [Java]"
                        elif name.endswith(".go"):
                            lang_indicator = " [Go]"
                        elif name.endswith((".kt", ".kts")):
                            lang_indicator = " [Kotlin]"
                        
                        structure.append(new_prefix + name + lang_indicator)

        structure = []
        walk_dir(self.repo_path)
        return "\n".join(structure)

    def build_path_tree(self, who_reference_me, reference_who, doc_item_path):
        """Build a tree structure showing file relationships"""
        def tree():
            return defaultdict(tree)

        path_tree = tree()

        for path_list in [who_reference_me, reference_who]:
            for path in path_list:
                parts = path.split(os.sep)
                node = path_tree
                for part in parts:
                    node = node[part]

        parts = doc_item_path.split(os.sep)
        parts[-1] = "✳️" + parts[-1]
        node = path_tree
        for part in parts:
            node = node[part]

        def tree_to_string(tree, indent=0):
            s = ""
            for key, value in sorted(tree.items()):
                s += "    " * indent + key + "\n"
                if isinstance(value, dict):
                    s += tree_to_string(value, indent + 1)
            return s

        return tree_to_string(path_tree)
    
    def get_project_summary(self):
        """Get a comprehensive summary of the project"""
        stats = self.project.get_project_stats()
        functions_by_file = self.project.get_all_functions()
        classes_by_file = self.project.get_all_classes()
        
        summary = f"""
Project Summary:
===============
Total Files: {stats['total_files']}
- Python: {stats['python_files']}
- Java: {stats['java_files']}
- Go: {stats['go_files']}
- Kotlin: {stats['kotlin_files']}

Total Functions: {stats['total_functions']}
Total Classes: {stats['total_classes']}
Total Lines of Code: {stats['total_lines']}

Files with Functions: {len(functions_by_file)}
Files with Classes: {len(classes_by_file)}
"""
        return summary
    
    def find_symbol_references(self, file_path: str, line: int, column: int, 
                             in_file_only: bool = False) -> List[Tuple[str, int, int]]:
        """Find all references to a symbol - replacement for jedi functionality"""
        scope = "file" if in_file_only else "project"
        return self.project.get_references(file_path, line, column, scope)
    
    def get_supported_languages(self) -> Set[str]:
        """Get all programming languages found in the project"""
        languages = set()
        for file_path in self.project.get_supported_files():
            lang = self.project.get_file_language(file_path)
            if lang:
                languages.add(lang)
        return languages


if __name__ == "__main__":
    project_manager = ProjectManager(repo_path="", project_hierarchy="")
    print(project_manager.get_project_structure())
    print(project_manager.get_project_summary())