.PHONY: install run debug clean fclean lint lint-strict

.venv/.installed: pyproject.toml
	POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --extras rendering
	touch .venv/.installed

install: .venv/.installed

run:
	poetry run python a_maze_ing.py config.txt

debug:
	poetry run python -m pdb a_maze_ing.py config.txt

build-mazegen:
	poetry build
	cp dist/mazegen-1.0.0-py3-none-any.whl .


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

fclean: clean
	rm -rf .venv
	rm -f poetry.lock
	rm -rf dist

lint:
	poetry run flake8 . --exclude .venv
	poetry run mypy --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs \
		--exclude .venv .

lint-strict:
	poetry run flake8 . --exclude .venv
	poetry run mypy --strict . --exclude .venv