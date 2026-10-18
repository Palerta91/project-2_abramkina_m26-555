"""Операции с таблицами и записями."""

from primitive_db.constants import ID_COLUMN, ID_TYPE, VALID_TYPES
from primitive_db.decorators import confirm_action, handle_db_errors, log_time
from primitive_db.utils import delete_table_data, load_table_data


def convert_value(value: str, value_type: str):
    """Привести значение к типу столбца."""
    if value_type == "str":
        return str(value)
    if value_type == "int":
        try:
            return int(value)
        except ValueError as error:
            raise ValueError(f"значение {value!r} должно быть типа int") from error
    if value_type == "bool":
        normalized_value = str(value).lower()
        if normalized_value == "true":
            return True
        if normalized_value == "false":
            return False
        raise ValueError(f"значение {value!r} должно быть true или false")
    raise ValueError(f"неподдерживаемый тип данных {value_type!r}")


def get_columns(metadata: dict, table_name: str) -> list[dict[str, str]]:
    """Вернуть имена и типы столбцов."""
    return metadata[table_name]["columns"]


def matches_where(record: dict, where_clause: dict) -> bool:
    """Проверить, подходит ли запись под условия where."""
    return all(record[column] == value for column, value in where_clause.items())


@handle_db_errors
def create_table(
    metadata: dict, table_name: str, columns: list[tuple[str, str]]
) -> dict | None:
    """Создать таблицу со столбцом ID."""
    if not table_name.isidentifier():
        raise ValueError(f"имя таблицы {table_name!r} должно быть одним словом")
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    if not columns:
        raise ValueError("укажите хотя бы один пользовательский столбец")

    table_columns = [{"name": ID_COLUMN, "type": ID_TYPE}]
    used_names = {ID_COLUMN}

    for column_name, column_type in columns:
        if column_name in used_names:
            raise ValueError(f"столбец {column_name!r} уже задан")
        if column_type not in VALID_TYPES:
            raise ValueError(f"неподдерживаемый тип данных {column_type!r}")
        table_columns.append({"name": column_name, "type": column_type})
        used_names.add(column_name)

    metadata[table_name] = {"columns": table_columns}
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> dict | None:
    """Удалить таблицу вместе с её данными."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    del metadata[table_name]
    delete_table_data(table_name)
    return metadata


def list_tables(metadata: dict) -> list[str]:
    """Вернуть имена всех таблиц."""
    return list(metadata)


@handle_db_errors
@log_time
def insert(
    metadata: dict,
    table_name: str,
    values: list[str],
    table_data: list[dict] | None = None,
) -> list[dict] | None:
    """Добавить запись с новым ID."""
    user_columns = get_columns(metadata, table_name)[1:]
    if len(values) != len(user_columns):
        raise ValueError(
            f"для таблицы {table_name!r} нужно передать {len(user_columns)} значений"
        )

    if table_data is None:
        table_data = load_table_data(table_name)

    # В пустой таблице первый ID будет равен 1.
    next_id = max((row[ID_COLUMN] for row in table_data), default=0) + 1
    record = {ID_COLUMN: next_id}
    for column, value in zip(user_columns, values):
        record[column["name"]] = convert_value(value, column["type"])

    table_data.append(record)
    return table_data


@handle_db_errors
@log_time
def select(
    table_data: list[dict], where_clause: dict | None = None
) -> list[dict] | None:
    """Выбрать записи по условию, а без него — вернуть все."""
    if where_clause is None:
        return table_data
    return [row for row in table_data if matches_where(row, where_clause)]


@handle_db_errors
def update(
    table_data: list[dict],
    set_clause: dict,
    where_clause: dict,
    column_types: dict[str, str] | None = None,
) -> list[dict] | None:
    """Изменить записи, подходящие под условие where."""
    if column_types is not None:
        for column, value in set_clause.items():
            set_clause[column] = convert_value(value, column_types[column])

    for row in table_data:
        if matches_where(row, where_clause):
            row.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записи")
def delete(table_data: list[dict], where_clause: dict) -> list[dict] | None:
    """Удалить записи по условию where."""
    return [row for row in table_data if not matches_where(row, where_clause)]


@handle_db_errors
def info(metadata: dict, table_name: str, table_data: list[dict]) -> dict | None:
    """Вернуть столбцы таблицы и число записей."""
    columns = get_columns(metadata, table_name)
    return {"columns": columns, "row_count": len(table_data)}
