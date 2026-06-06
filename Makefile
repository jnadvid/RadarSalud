# RadarSalud - Makefile de conveniencia (sin Docker)
.PHONY: help install dev init-db ingest analyze serve simulate clear-sim map test lint clean

PY ?= python
VENV ?= .venv
BIN = $(VENV)/bin

help:
	@echo "RadarSalud - comandos disponibles:"
	@echo "  make install      Crear venv e instalar el paquete (modo editable)"
	@echo "  make dev          Instalar con dependencias de desarrollo"
	@echo "  make init-db      Crear la base SQLite y sembrar el catálogo de fuentes"
	@echo "  make ingest       Ejecutar ingesta de todas las fuentes reales operativas"
	@echo "  make analyze      Detectar anomalías sobre datos reales"
	@echo "  make simulate     Lanzar preset de simulación (gripe_madrid)"
	@echo "  make clear-sim    Limpiar todas las simulaciones"
	@echo "  make map          Generar mapa (modo all) en data/processed/"
	@echo "  make serve        Arrancar el servidor FastAPI local"
	@echo "  make test         Ejecutar la batería de tests"
	@echo "  make lint         Ejecutar ruff"
	@echo "  make clean        Borrar artefactos generados (no toca .env)"

install:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e .

dev:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

init-db:
	$(BIN)/radarsalud init-db

ingest:
	$(BIN)/radarsalud ingest-all

analyze:
	$(BIN)/radarsalud analyze --mode real

simulate:
	$(BIN)/radarsalud simulate --preset gripe_madrid

clear-sim:
	$(BIN)/radarsalud clear-simulations

map:
	$(BIN)/radarsalud map --mode all

serve:
	$(BIN)/radarsalud serve

test:
	$(BIN)/pytest

lint:
	$(BIN)/ruff check radarsalud tests

clean:
	rm -f data/radarsalud.sqlite
	rm -f data/processed/*.html data/processed/*.geojson
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
