from repo_agent.doc_meta_info import DocItem
from repo_agent.log import logger
from repo_agent.prompt import chat_template
from repo_agent.settings import SettingsManager
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llama_index.llms.openai_like import OpenAILike
from llm.yagpt import yandex_gpt

# from llm.gpt import ask_gpt  - возьмем нормальный GPT из OpenAILike
from llm.gigachat import gigachat_gpt


class ChatEngine:
    def __init__(self, project_manager, model_name="openai", temperature=0.6):
        self.model_name = model_name.lower()
        self.temperature = temperature
        self.project_manager = project_manager
        logger.info(f'Model name set to {self.model_name}')
        if self.model_name == "openai":
            from llama_index.llms.openai_like import OpenAILike

            setting = SettingsManager.get_setting()
            self.llm = OpenAILike(
                api_key=setting.chat_completion.openai_api_key,
                api_base=setting.chat_completion.openai_base_url,
                timeout=setting.chat_completion.request_timeout,
                model=setting.chat_completion.model,
                temperature=self.temperature,
                max_retries=1,
                is_chat_model=True,
            )
        elif self.model_name not in {"yagpt", "gigachat"}:
            raise ValueError(f"Unsupported model: {self.model_name}")

    def build_prompt(self, doc_item: DocItem):
        setting = SettingsManager.get_setting()

        code_info = doc_item.content
        referenced = len(doc_item.who_reference_me) > 0
        code_type = code_info["type"]
        code_name = code_info["name"]
        code_content = code_info["code_content"]
        have_return = code_info["have_return"]
        file_path = doc_item.get_full_name()

        def get_referenced_prompt(doc_item: DocItem) -> str:
            if not doc_item.reference_who:
                return ""
            prompt = ["As you can see, the code calls the following objects:"]
            for reference_item in doc_item.reference_who:
                prompt.append(
                    f"""obj: {reference_item.get_full_name()}
Document:\n{reference_item.md_content[-1] if reference_item.md_content else 'None'}
Raw code:\n{reference_item.content.get("code_content", "")}\n{"=" * 10}"""
                )
            return "\n".join(prompt)

        def get_referencer_prompt(doc_item: DocItem) -> str:
            if not doc_item.who_reference_me:
                return ""
            prompt = ["Also, the code has been called by the following objects:"]
            for referencer_item in doc_item.who_reference_me:
                prompt.append(
                    f"""obj: {referencer_item.get_full_name()}
Document:\n{referencer_item.md_content[-1] if referencer_item.md_content else 'None'}
Raw code:\n{referencer_item.content.get("code_content", "None")}\n{"=" * 10}"""
                )
            return "\n".join(prompt)

        def get_relationship_description(referencer, reference):
            if referencer and reference:
                return "And please include the reference relationship with its callers and callees..."
            elif referencer:
                return "And please include the relationship with its callers..."
            elif reference:
                return "And please include the relationship with its callees..."
            return ""

        code_type_tell = "Class" if code_type == "ClassDef" else "Function"
        parameters_or_attribute = (
            "attributes" if code_type == "ClassDef" else "parameters"
        )
        have_return_tell = (
            "**Output Example**: Mock up a possible appearance..."
            if have_return
            else ""
        )
        combine_ref_situation = (
            "and combine it with its calling situation," if referenced else ""
        )

        referencer_content = get_referencer_prompt(doc_item)
        reference_letter = get_referenced_prompt(doc_item)
        has_relationship = get_relationship_description(
            referencer_content, reference_letter
        )

        project_structure_prefix = ", and the related hierarchical structure of this project is as follows (The current object is marked with an *):"

        return chat_template.format_messages(
            combine_ref_situation=combine_ref_situation,
            file_path=file_path,
            project_structure_prefix=project_structure_prefix,
            code_type_tell=code_type_tell,
            code_name=code_name,
            code_content=code_content,
            have_return_tell=have_return_tell,
            has_relationship=has_relationship,
            reference_letter=reference_letter,
            referencer_content=referencer_content,
            parameters_or_attribute=parameters_or_attribute,
            language=setting.project.language,
        )

    def generate_doc(self, doc_item: DocItem):
        messages = self.build_prompt(doc_item)
        user_prompt = messages[-1].content
        logger.info(f'Used model {self.model_name}')
        logger.info(user_prompt)
        try:
            if self.model_name == "openai":
                response = self.llm.chat(messages)
                logger.debug(f"OpenAI Tokens: {response.raw.usage.total_tokens}")
                return response.message.content

            elif self.model_name == "yagpt":
                return yandex_gpt(user_prompt, model="4", temperature=self.temperature)

            elif self.model_name == "gigachat":
                return gigachat_gpt(user_prompt, temperature=self.temperature)

        except Exception as e:
            logger.error(f"Error in model call: {e}")
            raise
