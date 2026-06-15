#!/bin/sh

PYTHON="./.venv/bin/python"

PYTHON -u -m src.scraper.main --pdf-path "$1"
PYTHON -u -m src.scraper.codegen
