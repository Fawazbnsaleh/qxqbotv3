.PHONY: help install run monitor format test clean

PWD := $(shell pwd)
VENV_PATH = $(PWD)/al_rased/venv
PYTHON = $(VENV_PATH)/bin/python
PIP = $(VENV_PATH)/bin/pip

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PIP) install -r al_rased/requirements.txt
	$(PIP) install -r al_rased/requirements-dev.txt
	@echo "Dependencies installed."

run: ## Run the Telegram bot
	export PYTHONPATH=$(PWD) && cd al_rased && $(PYTHON) main.py

monitor: ## Run the Telethon monitor
	cd al_rased && ./start_monitor.sh

format: ## Format code using black and ruff
	$(PYTHON) -m black al_rased scripts
	$(PYTHON) -m ruff check al_rased scripts --fix

lint: ## Run static type checking
	$(PYTHON) -m mypy al_rased

test: ## Run tests
	$(PYTHON) -m pytest

clean: ## Remove temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
