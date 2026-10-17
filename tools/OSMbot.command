#!/bin/bash
# Mac: duplo clique abre a janela do OSMbot a partir do código deste repo (README, "Mac").
cd "$(dirname "$0")/.." || exit 1
if [ ! -x .venv/bin/osmbot ]; then
  python3 -m venv .venv && .venv/bin/pip install -e . && .venv/bin/python -m playwright install firefox || exit 1
fi
exec .venv/bin/osmbot
