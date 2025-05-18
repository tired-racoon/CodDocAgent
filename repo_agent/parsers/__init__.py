from repo_agent.parsers.file_parser import TreeSitterParser
from repo_agent.parsers.calls_parser import CallGraphBuilder

def get_file_parser(language: str) -> TreeSitterParser:
    if language.lower() in ['python', 'java', 'kotlin', 'go']:
        return TreeSitterParser(language)
    else:
        raise ValueError(f"File parser is not implemented for {language}")
    
def get_calls_parser(repo_path):
    return CallGraphBuilder(repo_path)