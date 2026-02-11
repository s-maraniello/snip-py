SHELL := /bin/bash
# UV_CLI is used to check if uv is installed
UV_CLI := $(shell which uv)

# Define all example directories
EXAMPLE_DIRS := examples-core-python examples-datascience examples-hpc examples-tensorflow

help: ## Print help for each target
	$(info Available commands:)
	$(info ==========================================================================================)
	@grep '^[[:alnum:]_-]*:.* ##' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS=":.* ## "}; {printf "%-30s %s\n", $$1, $$2};'


#################################################################################
# SETUP COMMANDS ################################################################

uv-install: ## Installs UV package manager
	@if [ -z "$(UV_CLI)" ]; then \
		echo "Installing uv via Homebrew..."; \
		brew install uv; \
	else \
		echo "uv is already installed at $(UV_CLI)"; \
	fi

setup: ## Sets up all Python environments for all example folders
	@echo "Setting up all example environments..."
	@for dir in $(EXAMPLE_DIRS); do \
		echo ""; \
		echo "Setting up $$dir..."; \
		$(MAKE) -C $$dir setup; \
	done
	@echo ""
	@echo "✓ All environments set up successfully!"

setup-%: ## Sets up a specific example folder (e.g., make setup-datascience)
	@echo "Setting up examples-$*..."
	@$(MAKE) -C examples-$* setup


#################################################################################
# UTILITIES #####################################################################

clean: ## Cleans up cache files and .venv in all example folders
	@echo "Cleaning up cache files and virtual environments..."
	@for dir in $(EXAMPLE_DIRS); do \
		echo "Cleaning $$dir..."; \
		$(MAKE) -C $$dir clean; \
	done
	@echo "Cleaning root directory..."
	@find . -name __pycache__ -type d -prune -exec rm -rf {} \;
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@echo "✓ Cleanup complete!"

clean-%: ## Cleans a specific example folder (e.g., make clean-datascience)
	@echo "Cleaning examples-$*..."
	@$(MAKE) -C examples-$* clean

