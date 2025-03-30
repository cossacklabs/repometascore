# Makefile

# Check if .env exists and include it
ifneq (,$(wildcard .env))
include .env
# Extract variable names from .env and export them
export $(shell sed 's/=.*//' .env)
endif

define check_command
@command -v "$(1)" > /dev/null || (echo "missing command '$(1)'" && exit 1)
endef

update:
	$(call check_command,uv)
	@echo "Installing dependencies..."
	@uv venv
	@bash -c "source .venv/bin/activate"
	uv sync

setup:
	$(MAKE) setup_uv
	$(MAKE) setup_python

setup_uv:
	@echo "Setting up the environment..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "'uv' is already installed."; \
	else \
		echo "'uv' is not installed. Installing..."; \
		bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"; \
	fi

setup_python:
	$(call check_command,uv)
	uv python install python3.13
	uv venv
	@bash -c "source .venv/bin/activate"
	uv sync
