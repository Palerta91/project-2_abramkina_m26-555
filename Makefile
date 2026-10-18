.PHONY: install run lint format test build

install:
	uv sync

run:
	uv run database

lint:
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

build:
	uv build
