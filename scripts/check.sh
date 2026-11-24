#!/usr/bin/env bash
# Reproduce every local gate used by CI. Does not contact GitHub or any customer system.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --disable-pip-version-check -q --upgrade pip setuptools
.venv/bin/python -m pip install --disable-pip-version-check -q -e '.[dev]'

.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/pytest
.venv/bin/pip-audit --skip-editable

echo "All local gates passed. GitHub Actions still verifies Python 3.11 and 3.12 independently."
