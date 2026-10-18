# project#2_abramkina_m26-555

Учебный проект «Примитивная база данных» на Python. Приложение будет запускаться
в терминале, хранить структуру таблиц и записи в JSON-файлах и поддерживать
основные операции с таблицами и данными.

## Среда разработки

- Python 3.12.13.
- UV 0.13.1 для окружения, зависимостей и сборки пакета.
- Ruff для проверки стиля кода.
- PrettyTable для вывода записей и prompt-toolkit для ввода команд.

## Установка и команды

Из корня проекта:

```bash
make install
make run
make lint
make test
make build
```

Прямые команды UV:

```bash
uv sync
uv run database
uv run ruff check .
uv run pytest
uv build
```

## Структура приложения

```text
src/primitive_db/
├── __init__.py
├── main.py         # точка входа
├── engine.py       # цикл CLI и вызов операций
├── core.py         # таблицы и CRUD-логика
├── utils.py        # JSON-файлы метаданных и записей
├── parser.py       # разбор условий команд
├── decorators.py   # обработка ошибок, подтверждение, время, кэш
└── constants.py    # имена файлов и поддерживаемые типы

data/               # отдельный JSON-файл для каждой таблицы
db_meta.json        # метаданные таблиц
```

Файлы `db_meta.json` и `data/` с локальными данными исключены из Git.

## Управление таблицами

```text
create_table users name:str age:int is_active:bool
list_tables
drop_table users
```

При создании `ID:int` добавляется автоматически. Разрешены типы `int`, `str` и
`bool`. Удаление таблицы просит подтверждение.

## CRUD-операции

```text
insert into users values ("Sergei", 28, true)
select from users
select from users where age = 28
update users set age = 29 where name = "Sergei"
delete from users where ID = 1
info users
```

Строковые значения передаются в кавычках, `bool` — как `true` или `false`.
Вставка автоматически создает следующий ID. Удаление записи также просит
подтверждение. Табличный вывод выполняется через PrettyTable.

## Демонстрация

Полный сценарий: создать таблицу, добавить запись, выполнить выборку, обновить и
удалить запись, удалить таблицу и завершить программу.

[![Демонстрация проекта в asciinema](https://asciinema.org/a/J1SmqSXaI2ZPDR1B.svg)](https://asciinema.org/a/J1SmqSXaI2ZPDR1B)

[Локальный файл записи](demo.cast).
