TARGETS = rail/ scripts/ tests/

install:
	uv sync

install-dev:
	uv sync --extra dev

install-all:
	uv sync --all-extras

mcp:
	uv run rail-mcp

mcp-http:
	uv run rail-mcp-http

format:
	uv run --extra dev ruff format $(TARGETS)

lint:
	uv run --extra dev ruff check $(TARGETS)

lint-fix:
	uv run --extra dev ruff check --fix $(TARGETS)

test:
	uv run --extra dev pytest -vv

test-all:
	uv run --extra dev pytest -vv --all

stations:
	uv run python scripts/generate_station_enum.py

requirements:
	uv export --format requirements-txt --no-hashes > requirements.txt

.DEFAULT_GOAL := help
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make install-all  - Install all dependencies including dev"
	@echo "  make mcp          - Run MCP server on STDIO"
	@echo "  make mcp-http     - Run MCP server over HTTP"
	@echo "  make format       - Format code with ruff"
	@echo "  make lint         - Lint code with ruff"
	@echo "  make lint-fix     - Lint and auto-fix with ruff"
	@echo "  make test         - Run test suite"
	@echo "  make test-all     - Run all tests"
	@echo "  make stations     - Regenerate station enum from data/stations.csv"
	@echo "  make requirements - Export requirements.txt"

.PHONY: help install install-dev install-all mcp mcp-http format lint lint-fix test test-all stations requirements
