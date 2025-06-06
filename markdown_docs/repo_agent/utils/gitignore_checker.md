## ClassDef GitignoreChecker
**GitignoreChecker**: класс GitignoreChecker предназначен для проверки файлов и папок в указанной директории на соответствие шаблонам из файла .gitignore.

**Attributes**:
* параметр 1: `directory` (str) — директория, в которой будет производиться проверка.
* параметр 2: `gitignore_path` (str) — путь к файлу .gitignore.
* `folder_patterns` (list) — список шаблонов для папок, извлечённых из файла .gitignore.
* `file_patterns` (list) — список шаблонов для файлов, извлечённых из файла .gitignore.

**Описание кода**:

Класс GitignoreChecker инициализируется с указанием директории и пути к файлу .gitignore. В методе `_load_gitignore_patterns` происходит чтение и парсинг содержимого файла .gitignore, извлечение шаблонов для папок и файлов. Метод `_parse_gitignore` разделяет содержимое файла на отдельные шаблоны, а `_split_gitignore_patterns` разделяет шаблоны на списки для папок и файлов.

Метод `check_files_and_folders` выполняет проверку всех файлов и папок в указанной директории на соответствие шаблонам из файла .gitignore. Он возвращает список путей к файлам с расширением .py, которые не соответствуют шаблонам и, следовательно, не игнорируются.

Метод `_is_ignored` проверяет, соответствует ли указанный путь какому-либо шаблону из списка шаблонов. Он возвращает `True`, если путь соответствует шаблону, и `False` в противном случае.

**Примечание**:
При использовании класса GitignoreChecker необходимо убедиться, что файл .gitignore существует по указанному пути или указать альтернативный путь к файлу .gitignore.

**Пример вывода**:
Список путей к файлам с расширением .py, которые не игнорируются согласно шаблонам из файла .gitignore.
### FunctionDef __init__(self)
**__init__**: Функция __init__ инициализирует объект класса GitignoreChecker, задавая директорию для проверки и путь к файлу .gitignore.

**parameters**:
* параметр 1: directory (str): директория, которую нужно проверить.
* параметр 2: gitignore_path (str): путь к файлу .gitignore.

**Описание кода**:
Функция __init__ принимает два аргумента: directory и gitignore_path. Она сохраняет их в атрибуты экземпляра класса self.directory и self.gitignore_path соответственно. Затем она вызывает функцию _load_gitignore_patterns, которая загружает и анализирует содержимое файла .gitignore, разделяя шаблоны на папки и файлы. Результаты этого анализа сохраняются в атрибутах экземпляра self.folder_patterns и self.file_patterns.

**Примечание**:
При использовании функции __init__ необходимо убедиться, что путь к директории directory и файлу .gitignore gitignore_path указаны корректно. В противном случае могут возникнуть проблемы с загрузкой шаблонов из файла .gitignore.
***
### FunctionDef _load_gitignore_patterns(self)
**_load_gitignore_patterns**: Функция _load_gitignore_patterns загружает и анализирует содержимое файла .gitignore, затем разделяет шаблоны на шаблоны папок и шаблоны файлов.

**parameters**:
* параметр 1: self (экземпляр класса GitignoreChecker)

**Описание кода**:
Функция _load_gitignore_patterns пытается открыть и прочитать файл .gitignore, указанный в атрибуте self.gitignore_path. Если файл не найден, используется путь по умолчанию, который определяется относительно расположения файла с этой функцией. Содержимое файла анализируется, а затем шаблоны разделяются на папки и файлы.

Функция обрабатывает ситуацию, когда файл .gitignore не найден, используя конструкцию try-except для обработки исключения FileNotFoundError. В случае ошибки она открывает файл по пути по умолчанию и читает его содержимое.

Возвращает кортеж, содержащий два списка: один для шаблонов папок и один для шаблонов файлов.

**Примечание**:
При использовании функции _load_gitignore_patterns необходимо убедиться, что путь к файлу .gitignore указан корректно, иначе будет использован путь по умолчанию, который может не соответствовать требуемому расположению.

**Пример вызова**:
Функция _load_gitignore_patterns вызывается в конструкторе класса GitignoreChecker, который инициализируется с указанием директории и пути к файлу .gitignore.
***
### FunctionDef _parse_gitignore
**_parse_gitignore_**: Функция _parse_gitignore предназначена для анализа содержимого файла .gitignore и возврата извлечённых шаблонов в виде списка.

**parameters**:
- параметр 1: `gitignore_content` (str) — содержимое файла .gitignore.

**Описание кода**:
Функция _parse_gitignore принимает строку `gitignore_content`, которая содержит текст из файла .gitignore. Затем содержимое строки разбивается на отдельные строки с помощью метода `splitlines()`. Каждая строка очищается от начальных и конечных пробелов с помощью метода `strip()`. Если строка не пуста и не начинается с символа `#`, она добавляется в список `patterns`. В результате функция возвращает список `patterns`, содержащий извлечённые шаблоны из файла .gitignore.

**Примечание**:
При использовании функции важно убедиться, что передаваемый параметр `gitignore_content` содержит корректное содержимое файла .gitignore без ошибок форматирования. Комментарии, начинающиеся с символа `#`, будут игнорироваться.

**Пример вывода**:
```
["pattern1", "pattern2", "pattern3"]
```
***
### FunctionDef _split_gitignore_patterns
**_split_gitignore_patterns**: Функция _split_gitignore_patterns разделяет список шаблонов из файла .gitignore на шаблоны папок и шаблоны файлов.

**parameters**:
- параметр 1: `gitignore_patterns (list)` — список шаблонов из файла .gitignore.

**Описание кода**:
Функция _split_gitignore_patterns принимает на вход список `gitignore_patterns`, содержащий шаблоны из файла .gitignore. Затем она перебирает каждый шаблон в списке и проверяет, заканчивается ли он на символ `/`. Если шаблон заканчивается на `/`, функция добавляет его (без символа `/` в конце) в список `folder_patterns`. Если шаблон не заканчивается на `/`, функция добавляет его в список `file_patterns`. В результате функция возвращает кортеж, содержащий два списка: `folder_patterns` и `file_patterns`.

**Примечание**:
При использовании функции важно убедиться, что входной список `gitignore_patterns` корректно сформирован и содержит только допустимые шаблоны. Шаблоны, которые должны быть добавлены в список `folder_patterns`, должны явно указывать на папки, заканчиваясь на `/`.

**Пример вывода**:
```
(
    ['folder1', 'folder2/'],
    ['file1', 'file2.txt']
)
```
***
### FunctionDef _is_ignored
**_is_ignored_**: Функция _is_ignored проверяет, соответствует ли заданный путь любому из указанных шаблонов.

**parameters**:
* параметр 1: `path (str)` — путь, который нужно проверить.
* параметр 2: `patterns (list)` — список шаблонов для проверки.
* параметр 3: `is_dir (bool = False)` — указывает, является ли путь директорией (по умолчанию False).

**Описание кода**:
Функция _is_ignored принимает путь и список шаблонов, а также опциональный параметр is_dir, который указывает на то, что проверяется директория. Затем она последовательно применяет каждый шаблон к пути с помощью функции fnmatch.fnmatch. Если путь соответствует какому-либо шаблону, функция возвращает True. Если путь является директорией и шаблон заканчивается на "/", а путь соответствует шаблону без последнего символа "/", функция также возвращает True. В противном случае функция возвращает False.

**Примечание**:
При использовании функции _is_ignored важно правильно указать путь и шаблоны, чтобы проверка была корректной. Обратите внимание, что параметр is_dir влияет на обработку шаблонов, заканчивающихся на "/".

**Пример вывода**:
```
_is_ignored("example.txt", ["*.txt"])  # Вернёт False
_is_ignored("example.txt", ["*.txt", "*.py"])  # Вернёт False
_is_ignored("example.py", ["*.py"])  # Вернёт True
_is_ignored("directory/", ["*/*"])  # Вернёт True
```
***
### FunctionDef check_files_and_folders(self)
**check_files_and_folders**: Функция `check_files_and_folders` осуществляет проверку всех файлов и папок в указанной директории на соответствие паттернам, указанным в файле .gitignore, и возвращает список файлов с расширением .py, которые не игнорируются.

**parameters**:
- параметр не указан явно, все необходимые данные берутся из атрибутов объекта.

**Описание кода**:
Функция `check_files_and_folders` использует метод `os.walk` для обхода всех папок и файлов в указанной директории (`self.directory`). Для каждой папки она проверяет, не игнорируется ли она, используя метод `_is_ignored` и паттерны для папок (`self.folder_patterns`).

Затем функция проверяет каждый файл в папке. Если файл не игнорируется согласно паттернам для файлов (`self.file_patterns`) и имеет одно из указанных расширений (.py, .java, .go, .kt, .kts), то путь к файлу добавляется в список `not_ignored_files`. Путь к файлу представлен относительно директории `self.directory`.

**Примечание**:
При использовании функции `check_files_and_folders` необходимо убедиться, что атрибут `self.directory` установлен корректно, чтобы функция могла корректно работать с файлами и папками.

**Пример вывода**:
`["./path/to/file1.py", "./path/to/file2.py"]`
***
