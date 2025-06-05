import json
import sys

from repo_agent.log import logger


class JsonFileProcessor:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_json_file(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            logger.exception(f"File not found: {self.file_path}")
            sys.exit(1)

    def extract_data(self):
        json_data = self.read_json_file()
        md_contents = []
        extracted_contents = []
        for file, items in json_data.items():
            if isinstance(items, list):
                for item in items:
                    if "md_content" in item and item["md_content"]:
                        md_contents.append(item["md_content"][0])
                        item_dict = {
                            "type": item.get("type", "UnknownType"),
                            "name": item.get("name", "Unnamed"),
                            "code_start_line": item.get("code_start_line", -1),
                            "code_end_line": item.get("code_end_line", -1),
                            "have_return": item.get("have_return", False),
                            "code_content": item.get("code_content", "NoContent"),
                            "name_column": item.get("name_column", 0),
                            "item_status": item.get("item_status", "UnknownStatus"),
                        }
                        extracted_contents.append(item_dict)
        return md_contents, extracted_contents

    def recursive_search(self, data_item, search_text, code_results, md_results):
        if isinstance(data_item, dict):
            for key, value in data_item.items():
                if isinstance(value, (dict, list)):
                    self.recursive_search(value, search_text, code_results, md_results)
        elif isinstance(data_item, list):
            for item in data_item:
                if isinstance(item, dict) and item.get("name") == search_text:
                    if "code_content" in item:
                        code_results.append(item["code_content"])
                        md_results.append(item["md_content"])
                self.recursive_search(item, search_text, code_results, md_results)

    def search_code_contents_by_name(self, file_path, search_text):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                code_results = []
                md_results = (
                    []
                )  # List to store matching items' code_content and md_content
                self.recursive_search(data, search_text, code_results, md_results)
                if code_results or md_results:
                    return code_results, md_results
                else:
                    return ["No matching item found."], ["No matching item found."]
        except FileNotFoundError:
            return "File not found."
        except json.JSONDecodeError:
            return "Invalid JSON file."
        except Exception as e:
            return f"An error occurred: {e}"


if __name__ == "__main__":
    processor = JsonFileProcessor("database.json")
    md_contents, extracted_contents = processor.extract_data()
