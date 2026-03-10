#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[ERROR] python3 not found"
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
assert sys.version_info >= (3,8), f"Python >=3.8 required, got {sys.version}"
print("Python version OK:", sys.version.split()[0])
PY

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

python run_local.py
