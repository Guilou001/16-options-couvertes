# Prérequis : uv
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 12 tests fermés, sans réseau
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests

all:              ## fetch + lab (réseau requis)
	$(UV) run ovc fetch
	$(UV) run ovc lab
