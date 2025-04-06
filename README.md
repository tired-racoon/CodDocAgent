<h1 align="center">
  <img src="https://github.com/OpenBMB/RepoAgent/assets/138990495/06bc2449-c82d-4b9e-8c83-27640e541451" width="50" alt="RepoAgent logo"/> <em>RepoAgent: An LLM-Powered Framework for Repository-level Code Documentation Generation.</em>
</h1>

<p align="center">
  <img src="https://img.shields.io/pypi/dm/repoagent" alt="PyPI - Downloads"/>
  <a href="https://pypi.org/project/repoagent/">
    <img src="https://img.shields.io/pypi/v/repoagent" alt="PyPI - Version"/>
  </a>
  <a href="Pypi">
    <img src="https://img.shields.io/pypi/pyversions/repoagent" alt="PyPI - Python Version"/>
  </a>
  <img alt="GitHub License" src="https://img.shields.io/github/license/LOGIC-10/RepoAgent">
  <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/LOGIC-10/RepoAgent?style=social">
  <img alt="GitHub issues" src="https://img.shields.io/github/issues/LOGIC-10/RepoAgent">
  <a href="https://arxiv.org/abs/2402.16667v1">
    <img src="https://img.shields.io/badge/cs.CL-2402.16667-b31b1b?logo=arxiv&logoColor=red" alt="arXiv"/>
  </a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/OpenBMB/RepoAgent/main/assets/images/RepoAgent.png" alt="RepoAgent"/>
</p>

<p align="center">
  <a href="https://github.com/LOGIC-10/RepoAgent/blob/main/README.md">English readme</a>
   • 
  <a href="https://github.com/LOGIC-10/RepoAgent/blob/main/README_CN.md">简体中文 readme</a>
</p>

## :tv: Demo

[![Watch the video](https://img.youtube.com/vi/YPPJBVOP71M/hqdefault.jpg)](https://youtu.be/YPPJBVOP71M)

## 👾 Background

В области компьютерного программирования значение комплексной проектной документации, включающей подробные пояснения к каждому файлу на Python, трудно переоценить. Такая документация служит краеугольным камнем для понимания, поддержки и совершенствования кодовой базы. Он обеспечивает необходимый контекст и обоснование кода, облегчая нынешним и будущим разработчикам понимание назначения, функциональности и структуры программного обеспечения. Это не только помогает нынешним и будущим разработчикам понять цель и структуру проекта, но и гарантирует, что проект остается доступным и изменяемым с течением времени, что значительно облегчает процесс обучения для новых членов команды.

Традиционно создание и поддержка документации по программному обеспечению требовали значительных человеческих усилий и опыта, что было сложной задачей для небольших команд без специального персонала. Внедрение больших языковых моделей (LLM), таких как GPT, изменило ситуацию, позволив ИИ выполнять большую часть процесса документирования. Этот сдвиг позволяет разработчикам-специалистам сосредоточиться на проверке и тонкой настройке, что значительно сокращает ручную работу с документацией.

**🏆 Наша цель - создать интеллектуальный помощник по работе с документами, который помогает людям читать и понимать репозитории и создавать документы, что в конечном итоге помогает повысить эффективность работы и сэкономить время.**

## ✨ Функции

- **🤖 Автоматически обнаруживает изменения в репозиториях Git, отслеживая добавления, удаления и модификации файлов.**
- **📝 Самостоятельно анализирует структуру кода с помощью AST, генерируя документы для отдельных объектов.**
- **🔍 Точная идентификация связей двунаправленного вызова между объектами, расширяющая глобальную перспективу содержимого документа.**
- **📚 Легко заменяет содержимое Markdown на основе изменений, сохраняя согласованность документации.**
- **🕙 Выполняет многопоточные параллельные операции, повышая эффективность создания документов.**
- **👭 Предлагает надежный автоматизированный метод обновления документации для совместной работы в команде.**
- **😍 Отображайте документацию по коду удивительным образом. (с помощью книги документов для каждого проекта на базе Gitbook)**


## 🚀 Начало работы

### Способ установки

#### Использование GitHub Actions

Этот репозиторий поддерживает GitHub Actions для автоматизации рабочих процессов, таких как создание, тестирование и развертывание. Подробные инструкции по настройке и использованию GitHub Actions в этом репозитории приведены в [actions/run-repoagent](https://github.com/marketplace/actions/run-repoagent).


#### Для разработчиков

Чтобы развивать проект:

- **Install PDM**: If you haven't already, [install PDM](https://pdm-project.org/latest/#installation).
- **Use CodeSpace, or Clone the Repository**:

    - **Use CodeSpace**
    The easiest way to get RepoAgent enviornment. Click below to use the GitHub Codespace, then go to the next step.
  
    [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/LOGIC-10/RepoAgent?quickstart=1)
  
    - **Clone the Repository**
  
    ```bash
    git clone https://github.com/LOGIC-10/RepoAgent.git
    cd RepoAgent
    ```

- **Setup with PDM**

    - Initialize the Python virtual environment. Make sure to run the below cmd in `/RepoAgent` directory:
    
      ```bash
      pdm venv create --name repoagent
      ```
    
    - [Activate virtual environment](https://pdm-project.org/latest/usage/venv/#activate-a-virtualenv)
    
    - Install dependencies using PDM
    
      ```bash
       pdm install
      ```

### Configuring RepoAgent

Прежде чем настраивать конкретные параметры для агента репозитория, пожалуйста, убедитесь, что Openal API настроен как переменная среды в командной строке:

```sh
export OPENAI_API_KEY=YOUR_API_KEY # on Linux/Mac
set OPENAI_API_KEY=YOUR_API_KEY # on Windows
$Env:OPENAI_API_KEY = "YOUR_API_KEY" # on Windows (PowerShell)
```

## Run RepoAgent

Enter the root directory of RepoAgent and try the following command in the terminal:
```sh
repoagent run #this command will generate doc, or update docs(pre-commit-hook will automatically call this)
repoagent run --print-hierarchy # Print how repo-agent parse the target repo
```

The run command supports the following optional flags (if set, will override config defaults):

- `-m`, `--model` TEXT: Указывает модель, которая будет использоваться для завершения. 
- `-t`, `--temperature` FLOAT: Задает температуру генерации для модели. Более низкие значения делают модель более детерминированной. Default: `0.2`
- `-r`, `--request-timeout` INTEGER: Определяет время ожидания в секундах для запроса API. По умолчанию: `60`
- `-b`, `--base-url` TEXT: Базовый URL-адрес для вызовов API. 
- `-tp`, `--target-repo-path` PATH: Путь файловой системы к целевому репозиторию. Используется в качестве корневого каталога для создания документации. По умолчанию: `path/to/your/target/repository`
- `-hp`, `--hierarchy-path` TEXT: Имя или путь к файлу иерархии проекта, используемому для организации структуры документации. По умолчанию: `.project_doc_record`
- `-mdp`, `--markdown-docs-path` TEXT: Путь к папке, в которой будет храниться или генерироваться документация Markdown. По умолчанию: `markdown_docs`
- `-i`, `--ignore-list` TEXT: Список файлов или каталогов, которые следует игнорировать при создании документации, разделенный запятыми.
- `-l`, `--language` TEXT: Код ISO 639 или название языка для документации. По умолчанию: `Russian`
- `-ll`, `--log-level` [DEBUG|INFO|WARNING|ERROR|CRITICAL]: Устанавливает уровень ведения журнала для приложения. По умолчанию: `INFO`

Вы также можете воспользоваться следующей функцией

```sh
repoagent clean # Remove repoagent-related cache
repoagent diff # Check what docs will be updated/generated based on current code change
```

Если вы впервые создаете документацию для целевого репозитория, RepoAgent автоматически создаст файл JSON, содержащий информацию о глобальной структуре, и папку с именем Markdown_Docs в корневом каталоге целевого репозитория для хранения документов.

После того, как вы изначально сгенерировали глобальную документацию для целевого репозитория, или если проект, который вы клонировали, уже содержит информацию о глобальной документации, вы можете легко и автоматически поддерживать внутреннюю документацию проекта со своей командой, настроив  **pre-commit hook** в целевом репозитории! 

### Use `pre-commit` 

В настоящее время Repo Agent поддерживает создание документации для проектов, что требует некоторой настройки в целевом репозитории.

Во-первых, убедитесь, что целевой репозиторий является репозиторием git и был инициализирован.

```sh
git init
```
Установите pre-commit в целевом репозитории, чтобы обнаружить изменения в репозитории git.

```sh
pip install pre-commit
```
Create a file named `.pre-commit-config.yaml` in the root directory of the target repository. An example is as follows:

```yml
repos:
  - repo: local
    hooks:
    - id: repo-agent
      name: RepoAgent
      entry: repoagent
      language: system
      pass_filenames: false # prevent from passing filenames to the hook
      # You can specify the file types that trigger the hook, but currently only python is supported.
      types: [python]
```

Для получения информации о конкретных методах настройки крючков, пожалуйста, обратитесь к [pre-commit](https://pre-commit.com/#plugins).
После настройки файла yaml выполните следующую команду для установки перехватчика.

```sh
pre-commit install
```

Таким образом, каждый git-коммит запускает функцию агента репозитория, автоматически обнаруживающую изменения в целевом репозитории и генерирующую соответствующие документы.
Далее вы можете внести некоторые изменения в целевой репозиторий, например, добавить новый файл в целевой репозиторий или изменить существующий файл.
Вам просто нужно следовать обычному рабочему процессу git: git add, git commit -m "your commit message", git push
Программа Repo Agent автоматически запустится при фиксации git, обнаружит файлы, которые вы добавили на предыдущем шаге, и сгенерирует соответствующие документы.

После выполнения Repo Agent автоматически изменит промежуточные файлы в целевом репозитории и официально отправит фиксацию. После завершения выполнения будет выведен зеленый индикатор "Пройдено", как показано на рисунке ниже:
![Execution Result](https://raw.githubusercontent.com/OpenBMB/RepoAgent/main/assets/images/ExecutionResult.png)

Сгенерированный документ будет сохранен в указанной папке в корневом каталоге целевого хранилища. Отображение сгенерированного документа выглядит так, как показано ниже:
![Documentation](https://raw.githubusercontent.com/OpenBMB/RepoAgent/main/assets/images/Doc_example.png)
![Documentation](https://raw.githubusercontent.com/OpenBMB/RepoAgent/main/assets/images/8_documents.png)

Мы использовали стандартную модель **gpt-3.5-turbo** для создания документации для проекта [**XAgent**](https://github.com/OpenBMB/XAgent), который содержит приблизительно **270 000 строк** кода. Вы можете просмотреть результаты этой генерации в каталоге Markdown_Docs проекта Agent на GitHub. Для повышения качества документации мы предлагаем рассмотреть более продвинутые модели, такие как **gpt-4-1106** или **gpt-4-0125-preview**.

** В конце концов, вы можете гибко настраивать формат вывода, шаблон и другие аспекты документа, настраивая подсказку. Мы рады вашему изучению более научного подхода к автоматизированному написанию технических текстов и вашему вкладу в сообщество.** 

### ### Изучаем общение с журналистами

Мы концептуализируем ** Чат с Repo** как единый шлюз для этих нижестоящих приложений, выступающий в качестве соединителя, который связывает RepoAgent с пользователями-людьми и другими агентами искусственного интеллекта. Наши будущие исследования будут направлены на адаптацию интерфейса к различным приложениям и настройку его в соответствии с их уникальными характеристиками и требованиями к реализации.

Здесь мы демонстрируем предварительный прототип одной из наших задач: Автоматические вопросы и ответы по проблемам и объяснение кода. Вы можете запустить сервер, выполнив следующий код.

```sh
pip install repoagent[chat-with-repo]
repoagent chat-with-repo
```
