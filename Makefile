.PHONY: help build test run

help:
	@printf "Available targets:\n"
	@printf "  build  Build source and wheel distributions\n"
	@printf "  test   Run the test suite\n"
	@printf "  run    Run the application entry point\n"

build:
	uv build

test:
	@status=0; uv run python -m unittest discover -s tests || status=$$?; \
	if [ "$$status" -eq 5 ]; then exit 0; fi; \
	exit "$$status"

run:
	uv run python -m src.main
