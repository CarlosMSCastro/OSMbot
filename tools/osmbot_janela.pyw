"""Abre a janela do osmbot a partir do código (sem consola). Usado pelo atalho do ambiente de trabalho.

Corre-se com ``.venv\\Scripts\\pythonw.exe tools\\osmbot_janela.pyw``; o pythonw não tem consola, por isso a saída
de texto vai para o vazio (como no OSMbot.exe compilado).
"""
import os
import sys

if sys.stdout is None:
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")

from osmbot.cli import main  # noqa: E402

main([])
