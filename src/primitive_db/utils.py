"""Функции чтения и записи метаданных и данных таблиц."""

import json
import os

from primitive_db.constants import DATA_DIR


def load_metadata(filepath: str) -> dict:
    """Загрузить метаданные; если файла пока нет, вернуть пустой словарь."""
    try:
        with open(filepath, encoding="utf-8") as metadata_file:
            return json.load(metadata_file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str, data: dict) -> None:
    """Сохранить метаданные в JSON-файл."""
    directory = os.path.dirname(filepath) or "."
    os.makedirs(directory, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as metadata_file:
        json.dump(data, metadata_file, ensure_ascii=False, indent=4)


def load_table_data(table_name: str) -> list[dict]:
    """Загрузить записи таблицы или вернуть пустой список для новой таблицы."""
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")

    try:
        with open(filepath, encoding="utf-8") as data_file:
            return json.load(data_file)
    except FileNotFoundError:
        return []


def save_table_data(table_name: str, data: list[dict]) -> None:
    """Сохранить записи таблицы в отдельный JSON-файл."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")

    with open(filepath, "w", encoding="utf-8") as data_file:
        json.dump(data, data_file, ensure_ascii=False, indent=4)


def delete_table_data(table_name: str) -> None:
    """Удалить файл с записями таблицы, если он существует."""
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
