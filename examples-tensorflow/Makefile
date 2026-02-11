SHELL := /bin/bash

help: ## Print help for each target
	$(info Available commands:)
	$(info ==========================================================================================)
	@grep '^[[:alnum:]_-]*:.* ##' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS=":.* ## "}; {printf "%-30s %s\n", $$1, $$2};'

setup: ## Sets up the Python environment with uv
	@echo "Setting up TensorFlow/ML examples environment..."
	uv sync
	@echo "✓ Environment ready! Activate with: source .venv/bin/activate"

shell: ## Opens a Python shell in the virtual environment
	uv run python

jupyter: ## Starts Jupyter notebook server
	uv run jupyter notebook

clean: ## Removes virtual environment and cache files
	@echo "Cleaning up..."
	rm -rf .venv
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} \;
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "✓ Cleaned!"
