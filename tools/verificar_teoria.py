"""Check the theory against the bot's records in logs/ (docs/VERIFICACAO.md). Read-only: never talks to the game.

    python tools/verificar_teoria.py

Prints a table, one row per check: the rule, what the records say, how many matches, and the verdict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from osmbot.checks.theory import run  # noqa: E402


def records() -> list[dict]:
    found = []
    for path in sorted((ROOT / "logs").glob("*/jogos/*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                found.append(json.loads(line))
            except ValueError:
                pass
    return found


def main() -> None:
    results = run(records())
    print("| Verificação | Regra | Registos | Jogos | Veredicto |")
    print("|---|---|---|---|---|")
    for r in results:
        print(f"| {r.key} | {r.rule} | {r.measured} | {r.sample} | **{r.verdict}** |")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
