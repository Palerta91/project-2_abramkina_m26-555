"""Автоматические проверки функций и команд примитивной базы данных."""

from primitive_db import core, decorators, engine, parser, utils


def make_metadata() -> dict:
    """Создать схему users для проверок операций с данными."""
    return {
        "users": {
            "columns": [
                {"name": "ID", "type": "int"},
                {"name": "name", "type": "str"},
                {"name": "age", "type": "int"},
                {"name": "is_active", "type": "bool"},
            ]
        }
    }


def make_records() -> list[dict]:
    """Создать две записи для проверок выборки и изменения данных."""
    return [
        {"ID": 1, "name": "Sergei", "age": 28, "is_active": True},
        {"ID": 2, "name": "Anna", "age": 31, "is_active": False},
    ]


def test_load_metadata_returns_empty_dict_for_missing_file(tmp_path) -> None:
    """Отсутствующий файл метаданных означает пустую базу."""
    assert utils.load_metadata(str(tmp_path / "db_meta.json")) == {}


def test_metadata_and_table_data_are_saved_as_json(tmp_path, monkeypatch) -> None:
    """Метаданные и записи можно загрузить после сохранения."""
    monkeypatch.chdir(tmp_path)
    metadata = make_metadata()
    records = make_records()

    utils.save_metadata("db_meta.json", metadata)
    utils.save_table_data("users", records)

    assert utils.load_metadata("db_meta.json") == metadata
    assert utils.load_table_data("users") == records


def test_create_table_adds_id_column() -> None:
    """Новый столбец ID:int ставится перед пользовательскими столбцами."""
    metadata = {}

    result = core.create_table(metadata, "users", [("name", "str"), ("age", "int")])

    assert result is metadata
    assert metadata["users"]["columns"] == [
        {"name": "ID", "type": "int"},
        {"name": "name", "type": "str"},
        {"name": "age", "type": "int"},
    ]


def test_create_table_reports_duplicate_and_unknown_types(capsys) -> None:
    """Повторное имя и тип вне схемы int/str/bool отклоняются."""
    metadata = {}
    core.create_table(metadata, "users", [("name", "str")])

    assert core.create_table(metadata, "users", [("name", "str")]) is None
    assert 'Таблица "users" уже существует.' in capsys.readouterr().out

    assert core.create_table({}, "products", [("price", "float")]) is None
    assert "float" in capsys.readouterr().out


def test_insert_generates_next_id_and_converts_values(capsys) -> None:
    """Вставка приводит значения по схеме и увеличивает ID."""
    metadata = make_metadata()
    records = make_records()

    result = core.insert(metadata, "users", ["Lena", "32", "true"], records)

    assert result is records
    assert records[-1] == {
        "ID": 3,
        "name": "Lena",
        "age": 32,
        "is_active": True,
    }
    assert "Функция insert выполнилась за" in capsys.readouterr().out


def test_insert_rejects_wrong_number_of_values(capsys) -> None:
    """Вставка требует значение для каждого пользовательского столбца."""
    result = core.insert(make_metadata(), "users", ["Lena", "32"], [])

    assert result is None
    assert "нужно передать 3 значений" in capsys.readouterr().out


def test_insert_rejects_invalid_value_without_changing_records(capsys) -> None:
    """Неверное значение не добавляется в таблицу."""
    records = make_records()

    result = core.insert(
        make_metadata(), "users", ["Lena", "тридцать", "true"], records
    )

    assert result is None
    assert len(records) == 2
    assert "должно быть типа int" in capsys.readouterr().out


def test_select_returns_all_rows_or_matching_rows(capsys) -> None:
    """Выборка работает с условием и без него."""
    records = make_records()

    assert core.select(records) == records
    assert core.select(records, {"age": 31}) == [records[1]]
    assert capsys.readouterr().out.count("Функция select выполнилась за") == 2


def test_update_changes_matching_rows() -> None:
    """Обновление меняет только запись, совпавшую с where."""
    records = make_records()

    result = core.update(
        records,
        {"age": 29},
        {"name": "Sergei"},
    )

    assert result is records
    assert records[0]["age"] == 29
    assert records[1]["age"] == 31


def test_delete_requires_confirmation(monkeypatch, capsys) -> None:
    """Удаление отменяется без y и сохраняет записи."""
    records = make_records()
    monkeypatch.setattr(decorators, "prompt", lambda _: "n")

    result = core.delete(records, {"ID": 1})

    assert result is None
    assert len(records) == 2
    assert "Операция отменена." in capsys.readouterr().out


def test_delete_removes_matching_rows_after_confirmation(monkeypatch) -> None:
    """Подтверждение y удаляет только запись по условию."""
    records = make_records()
    monkeypatch.setattr(decorators, "prompt", lambda _: "y")

    result = core.delete(records, {"ID": 1})

    assert result == [records[1]]


def test_drop_table_removes_metadata_and_data_file(tmp_path, monkeypatch) -> None:
    """Подтвержденное удаление убирает таблицу и ее JSON-файл."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(decorators, "prompt", lambda _: "y")
    metadata = make_metadata()
    utils.save_table_data("users", make_records())

    result = core.drop_table(metadata, "users")

    assert result == {}
    assert "users" not in metadata
    assert utils.load_table_data("users") == []


def test_parser_handles_quoted_values_and_clauses() -> None:
    """Парсер сохраняет строку с пробелом и извлекает условия команд."""
    tokens = parser.tokenize_command(
        'insert into users values ("Sergei Petrov", 28, true)'
    )

    assert parser.parse_values(tokens[4:]) == ["Sergei Petrov", "28", "true"]
    assert parser.parse_where_clause(["where", "age", "=", "28"]) == {"age": "28"}
    assert parser.parse_set_clause(["set", "age", "=", "29"]) == {"age": "29"}


def test_cache_runs_value_function_once() -> None:
    """Повторный запрос с тем же ключом возвращает сохраненный результат."""
    cache_result = decorators.create_cacher()
    calls = {"count": 0}

    def get_value() -> str:
        calls["count"] += 1
        return "cached"

    assert cache_result("users", get_value) == "cached"
    assert cache_result("users", get_value) == "cached"
    assert calls["count"] == 1


def test_cli_commands_save_and_display_records(tmp_path, monkeypatch, capsys) -> None:
    """CLI создает таблицу, сохраняет запись и печатает ее через PrettyTable."""
    monkeypatch.chdir(tmp_path)
    metadata = utils.load_metadata("db_meta.json")

    engine.handle_command(
        parser.tokenize_command("create_table users name:str age:int"), metadata
    )
    engine.handle_command(
        parser.tokenize_command('insert into users values ("Lena", 30)'),
        utils.load_metadata("db_meta.json"),
    )
    engine.handle_command(
        parser.tokenize_command("select from users where age = 30"),
        utils.load_metadata("db_meta.json"),
    )

    output = capsys.readouterr().out
    assert 'Таблица "users" успешно создана' in output
    assert "Запись с ID=1 успешно добавлена" in output
    assert "Lena" in output
    assert utils.load_table_data("users") == [{"ID": 1, "name": "Lena", "age": 30}]


def test_cli_update_and_delete_save_changes(tmp_path, monkeypatch, capsys) -> None:
    """CLI обновляет и удаляет запись, сохраняя изменения в JSON."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(decorators, "prompt", lambda _: "y")
    metadata = utils.load_metadata("db_meta.json")
    engine.handle_command(
        parser.tokenize_command("create_table users name:str age:int"), metadata
    )
    engine.handle_command(
        parser.tokenize_command('insert into users values ("Lena", 30)'),
        utils.load_metadata("db_meta.json"),
    )

    engine.handle_command(
        parser.tokenize_command("update users set age = 31 where name = Lena"),
        utils.load_metadata("db_meta.json"),
    )
    assert utils.load_table_data("users")[0]["age"] == 31

    engine.handle_command(
        parser.tokenize_command("delete from users where ID = 1"),
        utils.load_metadata("db_meta.json"),
    )
    assert utils.load_table_data("users") == []
    assert "успешно обновлены" in capsys.readouterr().out
