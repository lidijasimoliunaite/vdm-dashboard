.PHONY: install build check test serve

install:
	pip install -e ".[dev]"

build:
	gits-dashboard build

check:
	gits-dashboard check

test:
	ruff check src tests && pytest -q

serve: build
	gits-dashboard serve
