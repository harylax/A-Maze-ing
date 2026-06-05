.PHONY: install run build-mazegen clean fclean lint lint-strict

venv/.installed: requirements.txt
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install mlx-2.2-py3-none-any.whl
	venv/bin/pip install -r requirements.txt
	touch venv/.installed

install: venv/.installed

run:
	venv/bin/python3 a_maze_ing.py config.txt

debug:
	venv/bin/python3 -m pdb a_maze_ing.py config.txt

dist/mazegen-1.0.0-py3-none-any.whl:
	venv/bin/python3 -m build
	cp dist/mazegen-1.0.0-py3-none-any.whl .

build-mazegen: dist/mazegen-1.0.0-py3-none-any.whl

clean:
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +

fclean: clean
	rm -rf venv
	rm -rf dist

lint:
	venv/bin/flake8 . --exclude venv
	venv/bin/mypy . --warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs \
		--exclude venv

lint-strict:
	venv/bin/flake8 . --exclude venv
	venv/bin/mypy . --strict --exclude venv
