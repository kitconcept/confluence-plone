### Defensive settings for make:
#     https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
.SHELLFLAGS:=-xeu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

# Python checks
UV?=uv

# installed?
ifeq (, $(shell which $(UV) ))
  $(error "UV=$(UV) not found in $(PATH)")
endif

BACKEND_FOLDER=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

VENV_FOLDER=$(BACKEND_FOLDER)/.venv
BIN_FOLDER=$(VENV_FOLDER)/bin


all: install

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


############################################
# Installation
############################################

$(BIN_FOLDER)/pytest: ## Install dependencies
	@echo "$(GREEN)==> Install environment$(RESET)"
	@uv sync

.PHONY: install
install: $(BIN_FOLDER)/pytest ## Install package

.PHONY: sync
sync: ## Sync project dependencies
	@echo "$(GREEN)==> Sync project dependencies$(RESET)"
	@uv sync

.PHONY: clean
clean: ## Clean environment
	@echo "$(RED)==> Cleaning environment and build$(RESET)"
	@rm -rf $(VENV_FOLDER) .python-version .ruff_cache .pytest_cache .mypy_cache .coverage .coverage.* htmlcov dist

############################################
# Linting
############################################
.PHONY: lint-mypy
lint-mypy: $(BIN_FOLDER)/pytest ## Check type hints
	@echo "$(GREEN)==> Check type hints$(RESET)"
	@uv run mypy src

.PHONY: lint
lint: $(BIN_FOLDER)/pytest ## Check code base according to Plone standards
	@echo "$(GREEN)==> Lint codebase$(RESET)"
	@uvx ruff@latest check --fix
	@uvx ruff@latest format --check
	@uvx pyroma@latest -d .
	@uvx check-python-versions@latest .
	@$(MAKE) lint-mypy

############################################
# Formatting
############################################
.PHONY: format
format: $(BIN_FOLDER)/pytest ## Check and fix code base according to Plone standards
	@echo "$(GREEN)==> Format codebase$(RESET)"
	@uvx ruff@latest check --select I --fix
	@uvx ruff@latest format

.PHONY: check
check: format lint ## Format and lint the code base

############################################
# Tests
############################################
.PHONY: test
test: $(BIN_FOLDER)/pytest ## Run tests
	@uv run pytest

.PHONY: test-coverage
test-coverage: $(BIN_FOLDER)/pytest ## Run tests and check the coverage (100% required)
	@echo "$(GREEN)==> Run tests with coverage$(RESET)"
	@rm -f .coverage .coverage.*
	@uv run coverage run -m pytest
	@uv run coverage combine
	@uv run coverage report

############################################
# Documentation
############################################
.PHONY: docs-install
docs-install: ## Install the documentation environment
	@$(MAKE) -C ./docs install

.PHONY: docs-html
docs-html: ## Build HTML documentation
	@$(MAKE) -C ./docs html

.PHONY: docs-livehtml
docs-livehtml: ## Build documentation and serve it
	@$(MAKE) -C ./docs livehtml

.PHONY: docs-vale
docs-vale: ## Run vale on the documentation
	@$(MAKE) -C ./docs vale

.PHONY: docs-linkcheckbroken
docs-linkcheckbroken: ## Run checks for broken links
	@$(MAKE) -C ./docs linkcheckbroken

.PHONY: docs-test
docs-test: ## Run vale, check for broken links, and run the doctests of the documentation
	@$(MAKE) -C ./docs test

############################################
# Release
############################################
.PHONY: changelog
changelog: ## Display the draft for the changelog
	@echo "🚀 Display the draft for the changelog"
	@uv run towncrier --draft

.PHONY: release
release: ## Release the package to pypi.org
	@echo "🚀 Release package"
	@uv run prerelease
	@uv run release
	@rm -Rf dist
	@uv build
	@uv publish
	@uv run postrelease
