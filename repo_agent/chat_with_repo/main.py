import time

from repo_agent.chat_with_repo.gradio_interface import GradioInterface
from repo_agent.chat_with_repo.rag import RepoAssistant
from repo_agent.log import logger
from repo_agent.settings import SettingsManager


def main():
    logger.info("Initializing the RepoAgent chat with doc module.")

    # Load settings
    setting = SettingsManager.get_setting()

    api_key = setting.chat_completion.openai_api_key  # type: ignore
    api_base = str(setting.chat_completion.openai_base_url)  # type: ignore
    db_path = (
        setting.project.target_repo  # type: ignore
        / setting.project.hierarchy_name  # type: ignore
        / "project_hierarchy.json"
    )

    assistant = RepoAssistant(api_key, api_base, db_path)

    md_contents, meta_data = assistant.json_data.extract_data()

    logger.info("Starting vector store creation...")
    start_time = time.time()
    assistant.vector_store_manager.create_vector_store(
        md_contents, meta_data, api_key, api_base
    )
    elapsed_time = time.time() - start_time
    logger.info(f"Vector store created successfully in {elapsed_time:.2f} seconds.")

    GradioInterface(assistant.respond)


if __name__ == "__main__":
    main()
