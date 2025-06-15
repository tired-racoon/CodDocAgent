from __future__ import annotations
import requests
import json
import yaml
from repo_agent.log import logger


with open("config.yaml", "r", encoding="utf8") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


def getToken() -> str:
    """
    :return: data['iamToken'] (Возвращаем токен для взаимодействия с yagpt)
    Функция получения токена в yagpt
    """
    url = config["links"]["yandex_gpt_token_url"]
    myobj = {"yandexPassportOauthToken": config["auth"]["yandexPassportOauthToken"]}
    x = requests.post(url, json=myobj)
    data = json.loads(x.text)
    return data["iamToken"]


def yandex_gpt(prom: str, temperature=0.6, old_prompt="", old_response=""):
    """
    :param prom:
    :param model:
    :param old_prompt:
    :param old_response:
    :return: data['result']['alternatives'][0]['message']['text'] (возвращаем сгенерированные данные)
    Функция генерации кейсов через yagpt по переданному prompt - запросу (prom), параметру model, который отвечает
    за используемую версию yagpt
    параметры old_prompt и old_response используются для генерации дополнительных кейсов через функцию /getMoreCases
    """
    model_uri = ""
    model = config["models"]["yagpt"]
    if model == "lite4":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/yandexgpt-lite/latest"
    elif model == "pro4":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/yandexgpt/latest"
    elif model == "lite5":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/yandexgpt-lite/rc"
    elif model == "pro5":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/yandexgpt/rc"
    elif model == "llama8b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/llama-lite/rc"
    elif model == "llama70b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/llama/rc"
    # ниже идут пакетные модели
    elif model == "qwen2.5i-7b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/qwen2.5-7b-instruct"
    elif model == "qwen2.5i-72b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/qwen2.5-72b-instruct"
    elif model == "deepseek-r1-qwen32b":
        model_uri = (
            "gpt://" + config["auth"]["folder_id"] + "/deepseek-r1-distill-qwen-32b"
        )
    elif model == "gemma12b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/gemma-3-12b-it"
    elif model == "gemma27b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/gemma-3-27b-it"
    elif model == "qwen3-8b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/qwen3-8b"
    elif model == "qwen3-14b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/qwen3-14b"
    elif model == "qwen3-32b":
        model_uri = "gpt://" + config["auth"]["folder_id"] + "/qwen3-32b"
    else:
        raise ValueError("Model name in config is incorrect")
    if old_prompt == "" and old_response == "":
        messages = [{"role": "user", "text": prom}]
    else:
        messages = [
            {"role": "user", "text": old_prompt},
            {"role": "assistant", "text": old_response},
            {"role": "user", "text": prom},
        ]
    response = requests.post(
        config["links"]["yandex_gpt_api_url"],
        headers={
            "Authorization": f"Bearer {config['auth']['yandexgpt_key']}",
            "x-folder-id": config["auth"]["folder_id"],
        },
        json={
            "modelUri": model_uri,
            "completionOptions": {"stream": False, "temperature": temperature},
            "messages": messages,
        },
    )
    data = response.json()
    print(data)
    return data["result"]["alternatives"][0]["message"]["text"]
