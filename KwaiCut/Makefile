.PHONY: install install-all lint format typecheck test serve desktop initdb docker clean

# Editable install with dev tooling only (fast; what CI uses).
install:
	pip install -e ".[dev]"

# Full install including desktop (PyQt6) and AI (torch/whisper) extras.
install-all:
	pip install -e ".[dev,desktop,ai,postgres]"

lint:
	ruff check src tests

format:
	ruff check --fix src tests
	ruff format src tests

typecheck:
	mypy

test:
	pytest

serve:
	kwaicut serve --reload

desktop:
	kwaicut-desktop

initdb:
	kwaicut initdb

docker:
	docker compose -f deploy/docker-compose.yml up --build

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info var *.db
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
