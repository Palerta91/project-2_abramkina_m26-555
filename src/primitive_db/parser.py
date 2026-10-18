"""Разбор поддерживаемого набора команд базы данных."""

import shlex


def tokenize_command(command: str) -> list[str]:
    """Разбить команду на слова, сохраняя строки в кавычках единым значением."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars="(),")
    lexer.whitespace_split = True
    return list(lexer)


def parse_column_definitions(tokens: list[str]) -> list[tuple[str, str]]:
    """Преобразовать аргументы вида name:str в пары имя-тип."""
    columns = []

    for token in tokens:
        column_name, separator, column_type = token.partition(":")
        if not separator or not column_name or not column_type:
            raise ValueError(f"некорректное описание столбца {token!r}")
        columns.append((column_name, column_type))

    return columns


def parse_values(tokens: list[str]) -> list[str]:
    """Разобрать значения из формы values (..., ...)."""
    if len(tokens) < 2 or tokens[0] != "(" or tokens[-1] != ")":
        raise ValueError("после values укажите значения в круглых скобках")

    values = []
    expect_value = True

    for token in tokens[1:-1]:
        if token == ",":
            if expect_value:
                raise ValueError("между значениями не должно быть пустых полей")
            expect_value = True
            continue

        if not expect_value:
            raise ValueError("разделяйте значения запятыми")
        values.append(token)
        expect_value = False

    if expect_value and values:
        raise ValueError("после последнего значения не нужна запятая")
    if not values:
        raise ValueError("передайте хотя бы одно значение")

    return values


def parse_where_clause(tokens: list[str]) -> dict[str, str]:
    """Разобрать простое условие where column = value."""
    if len(tokens) != 4 or tokens[0].lower() != "where" or tokens[2] != "=":
        raise ValueError("условие должно иметь вид where столбец = значение")
    return {tokens[1]: tokens[3]}


def parse_set_clause(tokens: list[str]) -> dict[str, str]:
    """Разобрать присваивание set column = value."""
    if len(tokens) != 4 or tokens[0].lower() != "set" or tokens[2] != "=":
        raise ValueError("присваивание должно иметь вид set столбец = значение")
    return {tokens[1]: tokens[3]}
