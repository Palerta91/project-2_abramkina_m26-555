"""Обработка ошибок, подтверждение операций, замер времени и кэш."""

import time

from prompt_toolkit import prompt


def handle_db_errors(function):
    """Вывести сообщение об ошибке базы данных."""

    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            message = str(error)
            if message.startswith("Таблица "):
                print(f"Ошибка: {message}")
            else:
                print(f"Ошибка валидации: {message}")

        return None

    return wrapper


def confirm_action(action_name: str):
    """Запросить подтверждение перед операцией."""

    def decorator(function):
        def wrapper(*args, **kwargs):
            answer = prompt(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            )
            if answer.lower() != "y":
                print("Операция отменена.")
                return None
            return function(*args, **kwargs)

        return wrapper

    return decorator


def log_time(function):
    """Показать время выполнения функции в секундах."""

    def wrapper(*args, **kwargs):
        started_at = time.monotonic()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started_at
            print(f"Функция {function.__name__} выполнилась за {elapsed:.3f} секунд")

    return wrapper


def create_cacher():
    """Создать кэш в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        """Вернуть сохраненный результат или вычислить его один раз."""
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    return cache_result
