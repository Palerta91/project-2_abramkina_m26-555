"""Ввод команд и вызов операций базы данных."""

import json

from prettytable import PrettyTable
from prompt_toolkit import prompt

from primitive_db import core, parser
from primitive_db.constants import META_FILE
from primitive_db.decorators import create_cacher
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

cache_result = create_cacher()


def print_help() -> None:
    """Показать доступные команды."""
    print("\n*** Примитивная база данных ***")
    print("create_table <таблица> <столбец:тип> ... - создать таблицу")
    print("list_tables - показать список таблиц")
    print("drop_table <таблица> - удалить таблицу")
    print("insert into <таблица> values (<значения>) - добавить запись")
    print("select from <таблица> [where <столбец> = <значение>] - прочитать записи")
    print("update <таблица> set <столбец> = <значение> where <условие> - обновить")
    print("delete from <таблица> where <условие> - удалить записи")
    print("info <таблица> - показать схему и число записей")
    print("help - справка; exit - выход\n")


def convert_clause_values(metadata: dict, table_name: str, clause: dict) -> dict:
    """Привести значения из where или set к типам столбцов."""
    columns = core.get_columns(metadata, table_name)
    column_types = {column["name"]: column["type"] for column in columns}
    converted_values = {}

    for column_name, value in clause.items():
        column_type = column_types[column_name]
        converted_values[column_name] = core.convert_value(value, column_type)

    return converted_values


def print_records(metadata: dict, table_name: str, records: list[dict]) -> None:
    """Показать записи в виде таблицы."""
    columns = core.get_columns(metadata, table_name)
    column_names = [column["name"] for column in columns]
    table = PrettyTable()
    table.field_names = column_names

    for record in records:
        table.add_row([record[column_name] for column_name in column_names])

    print(table)


def handle_create_table(tokens: list[str], metadata: dict) -> None:
    """Создать таблицу и сохранить её описание."""
    if len(tokens) < 3:
        raise ValueError("используйте create_table <таблица> <столбец:тип> ...")

    table_name = tokens[1]
    columns = parser.parse_column_definitions(tokens[2:])
    result = core.create_table(metadata, table_name, columns)
    if result is None:
        return

    save_metadata(META_FILE, result)
    save_table_data(table_name, [])
    column_names = ", ".join(
        f"{column['name']}:{column['type']}" for column in result[table_name]["columns"]
    )
    print(f'Таблица "{table_name}" успешно создана со столбцами: {column_names}')


def handle_drop_table(tokens: list[str], metadata: dict) -> None:
    """Удалить таблицу и сохранить метаданные."""
    if len(tokens) != 2:
        raise ValueError("используйте drop_table <таблица>")

    table_name = tokens[1]
    result = core.drop_table(metadata, table_name)
    if result is None:
        return

    save_metadata(META_FILE, result)
    print(f'Таблица "{table_name}" успешно удалена.')


def handle_insert(tokens: list[str], metadata: dict) -> None:
    """Добавить запись и сохранить таблицу."""
    if len(tokens) < 6 or tokens[1].lower() != "into" or tokens[3].lower() != "values":
        raise ValueError("используйте insert into <таблица> values (<значения>)")

    table_name = tokens[2]
    values = parser.parse_values(tokens[4:])
    records = load_table_data(table_name)
    result = core.insert(metadata, table_name, values, records)
    if result is None:
        return

    save_table_data(table_name, result)
    print(f'Запись с ID={result[-1]["ID"]} успешно добавлена в таблицу "{table_name}".')


def handle_select(tokens: list[str], metadata: dict) -> None:
    """Найти записи и вывести их таблицей."""
    if len(tokens) < 3 or tokens[1].lower() != "from":
        raise ValueError("используйте select from <таблица> [where столбец = значение]")

    table_name = tokens[2]
    core.get_columns(metadata, table_name)
    records = load_table_data(table_name)
    condition = None
    if len(tokens) > 3:
        condition = parser.parse_where_clause(tokens[3:])
        condition = convert_clause_values(metadata, table_name, condition)

    # После изменения данных ключ меняется, и выборка вычисляется заново.
    cache_key = json.dumps([table_name, records, condition], sort_keys=True)
    result = cache_result(cache_key, lambda: core.select(records, condition))
    if result is not None:
        print_records(metadata, table_name, result)


def handle_update(tokens: list[str], metadata: dict) -> None:
    """Изменить подходящие записи и сохранить таблицу."""
    if len(tokens) < 7:
        raise ValueError(
            "используйте update <таблица> set <присваивание> where <условие>"
        )

    table_name = tokens[1]
    # Последние четыре части команды: where столбец = значение.
    set_tokens = tokens[2:-4]
    where_tokens = tokens[-4:]

    new_values = parser.parse_set_clause(set_tokens)
    new_values = convert_clause_values(metadata, table_name, new_values)
    condition = parser.parse_where_clause(where_tokens)
    condition = convert_clause_values(metadata, table_name, condition)

    records = load_table_data(table_name)
    result = core.update(records, new_values, condition)
    if result is None:
        return

    save_table_data(table_name, result)
    print(f'Записи в таблице "{table_name}" успешно обновлены.')


def handle_delete(tokens: list[str], metadata: dict) -> None:
    """Удалить подходящие записи и сохранить таблицу."""
    if len(tokens) < 6 or tokens[1].lower() != "from":
        raise ValueError("используйте delete from <таблица> where столбец = значение")

    table_name = tokens[2]
    condition = parser.parse_where_clause(tokens[3:])
    condition = convert_clause_values(metadata, table_name, condition)
    records = load_table_data(table_name)
    result = core.delete(records, condition)
    if result is None:
        return

    save_table_data(table_name, result)
    print(f'Записи из таблицы "{table_name}" успешно удалены.')


def handle_info(tokens: list[str], metadata: dict) -> None:
    """Показать столбцы таблицы и число записей."""
    if len(tokens) != 2:
        raise ValueError("используйте info <таблица>")

    table_name = tokens[1]
    records = load_table_data(table_name)
    details = core.info(metadata, table_name, records)
    if details is None:
        return

    column_names = ", ".join(
        f"{column['name']}:{column['type']}" for column in details["columns"]
    )
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {column_names}")
    print(f"Количество записей: {details['row_count']}")


def handle_command(tokens: list[str], metadata: dict) -> bool:
    """Выбрать обработчик команды. Для exit вернуть False."""
    command = tokens[0].lower()

    if command in ("help", "exit", "list_tables") and len(tokens) != 1:
        raise ValueError(f"команда {command} не принимает аргументы")

    if command == "help":
        print_help()
    elif command == "exit":
        return False
    elif command == "list_tables":
        tables = core.list_tables(metadata)
        if not tables:
            print("Таблиц нет.")
        for table_name in tables:
            print(f"- {table_name}")
    elif command == "create_table":
        handle_create_table(tokens, metadata)
    elif command == "drop_table":
        handle_drop_table(tokens, metadata)
    elif command == "insert":
        handle_insert(tokens, metadata)
    elif command == "select":
        handle_select(tokens, metadata)
    elif command == "update":
        handle_update(tokens, metadata)
    elif command == "delete":
        handle_delete(tokens, metadata)
    elif command == "info":
        handle_info(tokens, metadata)
    else:
        print(f"Функции {tokens[0]} нет. Попробуйте снова.")

    return True


def run() -> None:
    """Читать и выполнять команды до выхода."""
    print_help()

    while True:
        try:
            user_input = prompt("Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        try:
            tokens = parser.tokenize_command(user_input)
            if not tokens:
                continue
            metadata = load_metadata(META_FILE)
            if not handle_command(tokens, metadata):
                break
        except ValueError as error:
            print(f"Некорректное значение: {error}. Попробуйте снова.")
        except KeyError as error:
            print(f"Некорректное значение: {error.args[0]}. Попробуйте снова.")
