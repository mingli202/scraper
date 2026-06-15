#!/bin/sh

PYTHON="./.venv/bin/python"

PYTHON -m src.scraper.main --pdf-path "$1"
PYTHON -m src.scraper.codegen
