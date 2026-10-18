"""Точка входа в консольную программу."""

from primitive_db.engine import run


def main() -> None:
    """Запустить командный интерфейс базы данных."""
    run()


if __name__ == "__main__":
    main()
