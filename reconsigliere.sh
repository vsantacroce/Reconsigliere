#!/usr/bin/env bash
# Ouvre la fenêtre de Reconsigliere sous Ubuntu : ./reconsigliere.sh
set -e
cd "$(dirname "$0")"
if ! python3 -c "import tkinter, venv" 2>/dev/null; then
  echo "Il manque des paquets système. Installe-les une fois avec :"
  echo "  sudo apt install python3-tk python3-venv"
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "Première installation, une minute…"
  python3 -m venv --system-site-packages .venv
fi
if ! cmp -s requirements.txt .venv/.installe; then
  .venv/bin/python -m pip install -q -r requirements.txt
  cp requirements.txt .venv/.installe
fi
PYTHONPATH="$PWD/src" exec .venv/bin/python -m reconsigliere.fenetre
