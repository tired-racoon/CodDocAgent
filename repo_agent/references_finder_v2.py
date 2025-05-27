import os
from collections import defaultdict
from tree_sitter import Node
from typing import List, Tuple, Set, Optional, Dict

from repo_agent.parsers.file_parser import TreeSitterParser
from repo_agent.log import logger


class ReferenceObject:
    """Mimics jedi reference object with name, line, column, and module_path attributes"""
    
    def __init__(self, name: str, line: int, column: int, module_path: str):
        self.name = name
        self.line = line
        self.column = column
        self.module_path = module_path
    
    def __repr__(self):
        return f"<ReferenceObject: {self.name} at {self.module_path}:{self.line}:{self.column}>"


class ReferenceFinder:
    def __init__(self, repo_path: str, file_path: str = None):
        self.repo_path = repo_path
        self.file_path = file_path  # Current file path (like jedi.Script)
        self.parsers = {}  # Cache parsers for different languages
        
        self.identifier_types = {
            "python": {"identifier", "name"},
            "java": {"identifier"},
            "go": {"identifier", "field_identifier", "package_identifier"},
            "kotlin": {"simple_identifier", "identifier"}
        }
        
        self.scope_types = {
            "python": {
                "function_definition", "class_definition", "method_definition",
                "lambda", "comprehension", "for_statement", "with_statement"
            },
            "java": {
                "class_declaration", "method_declaration", "constructor_declaration",
                "block", "for_statement", "enhanced_for_statement", "while_statement"
            },
            "go": {
                "function_declaration", "method_declaration", "func_literal",
                "block", "for_statement", "range_clause", "if_statement"
            },
            "kotlin": {
                "class_declaration", "function_declaration", "anonymous_function",
                "lambda_literal", "for_statement", "while_statement", "if_expression"
            }
        }
        
        # Define variable definition contexts for better filtering
        self.definition_types = {
            "python": {
                "assignment", "augmented_assignment", "parameter",
                "function_definition", "class_definition", "import_statement",
                "import_from_statement", "for_statement", "with_statement"
            },
            "java": {
                "variable_declarator", "formal_parameter", "catch_formal_parameter",
                "enhanced_for_statement", "local_variable_declaration"
            },
            "go": {
                "var_declaration", "short_var_declaration", "parameter_declaration",
                "function_declaration", "method_declaration", "range_clause"
            },
            "kotlin": {
                "variable_declaration", "parameter", "function_declaration",
                "class_declaration", "for_statement"
            }
        }

    def _get_parser(self, language: str) -> TreeSitterParser:
        """Get or create parser for specific language"""
        if language not in self.parsers:
            dummy_path = f"dummy.{self._get_extension(language)}"
            self.parsers[language] = TreeSitterParser(self.repo_path, dummy_path)
        return self.parsers[language]

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            "python": "py",
            "java": "java", 
            "go": "go",
            "kotlin": "kt"
        }
        return extensions.get(language, "txt")

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension"""
        ext_to_lang = {
            ".py": "python",
            ".java": "java",
            ".go": "go", 
            ".kt": "kotlin",
            ".kts": "kotlin"
        }
        _, ext = os.path.splitext(file_path)
        return ext_to_lang.get(ext.lower())

    def _get_node_text(self, node: Node, code: bytes) -> str:
        """Extract text from tree-sitter node"""
        if not node:
            return ""
        return code[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")

    def _find_node_at_position(self, root: Node, line: int, column: int) -> Optional[Node]:
        """Find the most specific node at given line and column (1-based line, 0-based column)"""
        def find_deepest(node: Node) -> Optional[Node]:
            # Convert to 0-based for tree-sitter
            target_line = line - 1
            target_col = column
            
            # Check if position is within this node bounds
            if not (node.start_point[0] <= target_line <= node.end_point[0]):
                return None
            
            # If on start/end line, check column bounds more carefully
            if node.start_point[0] == target_line and node.start_point[1] > target_col:
                return None
            if node.end_point[0] == target_line and node.end_point[1] <= target_col:
                return None
                
            # Look for deeper matches in children first
            for child in node.children:
                deeper = find_deepest(child)
                if deeper:
                    return deeper
            
            return node
        
        return find_deepest(root)

    def _get_identifier_at_position(self, root: Node, code: bytes, language: str, 
                                  line: int, column: int) -> Optional[str]:
        """Get identifier name at specific position"""
        node = self._find_node_at_position(root, line, column)
        if not node:
            return None
        
        identifier_types = self.identifier_types.get(language, {"identifier"})
        
        # First check if current node is an identifier
        if node.type in identifier_types:
            return self._get_node_text(node, code)
        
        # Walk up to find identifier node
        current = node.parent
        while current:
            if current.type in identifier_types:
                # Check if the identifier contains our position
                if (current.start_point[0] <= line - 1 <= current.end_point[0] and
                    current.start_point[1] <= column <= current.end_point[1]):
                    return self._get_node_text(current, code)
            current = current.parent
        
        # Walk down to find identifier in children
        def find_identifier_in_subtree(node: Node) -> Optional[str]:
            if node.type in identifier_types:
                return self._get_node_text(node, code)
            for child in node.children:
                result = find_identifier_in_subtree(child)
                if result:
                    return result
            return None
        
        if node:
            return find_identifier_in_subtree(node)
        
        return None

    def _find_all_identifiers(self, root: Node, code: bytes, language: str, 
                            target_name: str) -> List[Tuple[int, int, str]]:
        """Find all occurrences of an identifier in the syntax tree"""
        matches = []
        identifier_types = self.identifier_types.get(language, {"identifier"})
        
        def walk(node: Node):
            if node.type in identifier_types:
                text = self._get_node_text(node, code)
                if text == target_name:
                    # Convert to 1-based line numbers, keep 0-based columns
                    context = self._get_reference_context(node, language)
                    matches.append((node.start_point[0] + 1, node.start_point[1], context))
            
            for child in node.children:
                walk(child)
        
        walk(root)
        return matches

    def _get_reference_context(self, node: Node, language: str) -> str:
        """Determine the context of a reference (definition, usage, etc.)"""
        if not node.parent:
            return "usage"
        
        definition_types = self.definition_types.get(language, set())
        
        # Walk up the tree to find definition context
        current = node.parent
        while current:
            if current.type in definition_types:
                return "definition"
            # Check for specific patterns that indicate definitions
            if language == "python":
                # Check for assignment targets
                if (current.type == "assignment" and 
                    current.child_by_field_name("left") and
                    self._node_contains_position(current.child_by_field_name("left"), node)):
                    return "definition"
                # Check for function/class definitions
                if (current.type in ("function_definition", "class_definition") and
                    current.child_by_field_name("name") == node):
                    return "definition"
            elif language == "java":
                if (current.type == "variable_declarator" and
                    current.child_by_field_name("name") == node):
                    return "definition"
            current = current.parent
        
        return "usage"

    def _node_contains_position(self, container: Node, target: Node) -> bool:
        """Check if container node contains target node"""
        if not container or not target:
            return False
        
        def check_children(node: Node) -> bool:
            if node == target:
                return True
            for child in node.children:
                if check_children(child):
                    return True
            return False
        
        return check_children(container)

    def _is_same_scope(self, root: Node, language: str, pos1: Tuple[int, int], 
                      pos2: Tuple[int, int]) -> bool:
        """Check if two positions are in the same scope"""
        scope_types = self.scope_types.get(language, set())
        
        def find_enclosing_scope(line: int, col: int) -> Optional[Node]:
            node = self._find_node_at_position(root, line, col)
            if not node:
                return None
            
            current = node
            while current:
                if current.type in scope_types:
                    return current
                current = current.parent
            return root  # Global scope
        
        scope1 = find_enclosing_scope(pos1[0], pos1[1])
        scope2 = find_enclosing_scope(pos2[0], pos2[1])
        
        return scope1 == scope2

    def _filter_references_by_scope(self, references: List[Tuple[int, int, str]], 
                                  origin_pos: Tuple[int, int], root: Node, 
                                  language: str) -> List[Tuple[int, int, str]]:
        """Filter references based on scoping rules"""
        filtered = []
        
        for ref_line, ref_col, context in references:
            # Always include definitions
            if context == "definition":
                filtered.append((ref_line, ref_col, context))
                continue
            
            # For usages, check if they're in the same scope as a definition
            # This is a simplified check - a full implementation would need
            # proper scope analysis
            if self._is_same_scope(root, language, origin_pos, (ref_line, ref_col)):
                filtered.append((ref_line, ref_col, context))
        
        return filtered

    def find_references_in_file(self, file_path: str, variable_name: str, 
                              origin_line: int, origin_column: int, 
                              filter_scope: bool = True) -> List[Tuple[str, int, int, str]]:
        """Find all references to a variable in a single file"""
        language = self._detect_language(file_path)
        if not language:
            return []
        
        try:
            parser = self._get_parser(language)
            root = parser.parse_file(file_path)
            
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            code_bytes = code.encode("utf-8")
            
            # Find all occurrences of the identifier
            matches = self._find_all_identifiers(root, code_bytes, language, variable_name)
            
            # Apply scope filtering if requested
            if filter_scope:
                matches = self._filter_references_by_scope(
                    matches, (origin_line, origin_column), root, language
                )
            
            # Convert to result format and filter out origin position
            references = []
            rel_path = os.path.relpath(file_path, self.repo_path)
            
            for line, col, context in matches:
                if not (line == origin_line and col == origin_column):
                    references.append((rel_path, line, col, variable_name))
            
            return references
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []

    def find_references_in_repo(self, variable_name: str, origin_file: str,
                              origin_line: int, origin_column: int) -> List[Tuple[str, int, int, str]]:
        """Find all references to a variable across the entire repository"""
        all_references = []
        origin_language = self._detect_language(origin_file)
        
        if not origin_language:
            return []
        
        # Get supported file extensions
        extensions = {".py", ".java", ".go", ".kt", ".kts"}
        
        # Process files in a more efficient order (same language first)
        files_to_process = []
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() not in extensions:
                    continue
                
                file_path = os.path.join(root, file)
                file_language = self._detect_language(file_path)
                
                if file_language:
                    # Prioritize same language files
                    priority = 0 if file_language == origin_language else 1
                    files_to_process.append((priority, file_path, file_language))
        
        # Sort by priority (same language first)
        files_to_process.sort(key=lambda x: x[0])
        
        for _, file_path, file_language in files_to_process:
            try:
                # For cross-language references, we might want different logic
                # For now, search in all supported files
                refs = self.find_references_in_file(
                    file_path, variable_name, origin_line, origin_column,
                    filter_scope=(file_language == origin_language)
                )
                all_references.extend(refs)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        return all_references

    def get_references(self, line: int, column: int, scope: str = "project") -> List[ReferenceObject]:
        """
        Main method to get references, mimicking jedi.Script.get_references()
        
        Args:
            line: Line number (1-based)
            column: Column number (0-based) 
            scope: "file" for file-only search, "project" for repository-wide
            
        Returns:
            List of ReferenceObject instances (mimics jedi reference objects)
        """
        if not self.file_path:
            logger.error("No file path specified in ReferenceFinder")
            return []
            
        abs_file_path = os.path.join(self.repo_path, self.file_path)
        
        if not os.path.exists(abs_file_path):
            logger.error(f"File not found: {abs_file_path}")
            return []
        
        language = self._detect_language(self.file_path)
        if not language:
            logger.error(f"Unsupported file type: {self.file_path}")
            return []
        
        try:
            # First, get the identifier at the specified position
            parser = self._get_parser(language)
            root = parser.parse_file(abs_file_path)
            
            with open(abs_file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            code_bytes = code.encode("utf-8")
            
            # Get the identifier name at the cursor position
            variable_name = self._get_identifier_at_position(
                root, code_bytes, language, line, column
            )
            
            if not variable_name:
                logger.warning(f"No identifier found at {self.file_path}:{line}:{column}")
                return []
            
            logger.debug(f"Found identifier '{variable_name}' at {self.file_path}:{line}:{column}")
            
            # Find references based on scope
            if scope == "file":
                raw_references = self.find_references_in_file(
                    abs_file_path, variable_name, line, column
                )
            else:
                raw_references = self.find_references_in_repo(
                    variable_name, abs_file_path, line, column
                )
            
            # Convert to ReferenceObject instances
            reference_objects = []
            for ref_file, ref_line, ref_col, ref_name in raw_references:
                # Convert relative path to absolute path for module_path
                abs_ref_path = os.path.join(self.repo_path, ref_file)
                ref_obj = ReferenceObject(
                    name=ref_name,
                    line=ref_line,
                    column=ref_col,
                    module_path=abs_ref_path
                )
                reference_objects.append(ref_obj)
                
            return reference_objects
                
        except Exception as e:
            logger.error(f"Error finding references: {e}")
            logger.error(
                f"Parameters: line={line}, column={column}, scope={scope}"
            )
            return []


def find_all_referencer(repo_path: str, variable_name: str, file_path: str, 
                       line_number: int, column_number: int, in_file_only: bool = False):
    """
    Drop-in replacement for the original jedi-based function
    
    Mimics the behavior:
    script = jedi.Script(path=os.path.join(repo_path, file_path))
    references = script.get_references(line=line_number, column=column_number, scope="file")
    
    Args:
        repo_path: Path to repository root
        variable_name: Name of variable to find references for (used for filtering)
        file_path: Path to file (relative to repo_path)
        line_number: Line number (1-based)
        column_number: Column number (0-based)
        in_file_only: If True, search only in current file
        
    Returns:
        List of (file_path, line, column) tuples
    """
    # Create ReferenceFinder with file_path (like jedi.Script with path parameter)
    finder = ReferenceFinder(repo_path, file_path)
    scope = "file" if in_file_only else "project"
    
    try:
        # Call get_references without file_path (like jedi.Script.get_references)
        references = finder.get_references(line_number, column_number, scope)
        
        # Additional filtering by variable name (safety check)
        # Also verify that we actually found the expected variable
        abs_file_path = os.path.join(repo_path, file_path)
        language = finder._detect_language(file_path)
        
        if language and os.path.exists(abs_file_path):
            parser = finder._get_parser(language)
            root = parser.parse_file(abs_file_path)
            
            with open(abs_file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            code_bytes = code.encode("utf-8")
            found_var = finder._get_identifier_at_position(
                root, code_bytes, language, line_number, column_number
            )
            
            # If the found variable doesn't match expected, log warning but continue
            if found_var != variable_name:
                logger.warning(
                    f"Variable name mismatch: expected '{variable_name}', "
                    f"found '{found_var}' at {file_path}:{line_number}:{column_number}"
                )
        
        # Filter out the original position
        filtered_refs = [
            (ref_file, ref_line, ref_col) 
            for ref_file, ref_line, ref_col in references
            if not (ref_file == file_path and ref_line == line_number and ref_col == column_number)
        ]
        
        logger.debug(f"Found {len(filtered_refs)} references for '{variable_name}'")
        return filtered_refs
        
    except Exception as e:
        logger.error(f"Error in find_all_referencer: {e}")
        return []