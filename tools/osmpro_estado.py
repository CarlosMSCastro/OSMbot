"""Estado do estudo dos vídeos do OSMPro (D-063): OSMPro/_kb/ESTADO.md, gerado a partir das pastas.

- transcrito = existe ``_kb/legendas/<id>.json`` (sem ``erro``); "sem legendas" = existe com ``erro``
- analisado  = existe ``_kb/notas/<id>.md`` (as conclusões desse vídeo, 1 a 1)

Nunca se edita o ESTADO.md à mão: corre-se isto outra vez.

    python tools/osmpro_estado.py
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "OSMPro"
KB = ROOT / "_kb"


def videos() -> list[dict]:
    rows = []
    for name in ("osmproworld.csv", "andresantana.csv"):
        for row in csv.DictReader((ROOT / name).open(encoding="utf-8")):
            found = re.search(r"(?:v=|shorts/)([\w-]{11})", row["link"])
            if found:
                rows.append({**row, "id": found.group(1), "canal": name[:-4],
                             "categoria": row.get("categoria") or "OSMPROworld"})
    return rows


def transcript(video_id: str) -> str:
    path = KB / "legendas" / f"{video_id}.json"
    if not path.exists():
        return "por fazer"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return "por fazer"
    if data.get("erro"):
        return "sem legendas"
    return f"{data.get('lingua')} {'auto' if data.get('automatica') else 'autor'}"


def note(video_id: str) -> tuple[str, int]:
    """(data da análise, nº de conclusões) da nota do vídeo, ou ("", 0)."""
    path = KB / "notas" / f"{video_id}.md"
    if not path.exists():
        return "", 0
    text = path.read_text(encoding="utf-8")
    when = re.search(r"^- \*\*Analisado:\*\* (\S+)", text, re.M)
    part = text.split("## Conclusões", 1)[1].split("\n## ", 1)[0] if "## Conclusões" in text else ""
    return (when.group(1) if when else "?"), len(re.findall(r"^\d+\. ", part, re.M))


def main() -> None:
    rows = videos()
    lines, totals = [], Counter()
    by_category: dict[str, Counter] = {}
    for row in rows:
        state = transcript(row["id"])
        when, count = note(row["id"])
        group = by_category.setdefault(row["categoria"], Counter())
        group["videos"] += 1
        group["transcritos"] += state not in ("por fazer", "sem legendas")
        group["sem legendas"] += state == "sem legendas"
        group["analisados"] += bool(when)
        group["conclusoes"] += count
        link = f"[nota](notas/{row['id']}.md)" if when else ""
        title = row["titulo"].replace("|", "/")
        lines.append(f"| {row['data']} | {row['categoria']} | [{title}]({row['link']}) | {row['duracao']} | {state} "
                     f"| {when} | {count or ''} | {link} |")
    for group in by_category.values():
        totals.update(group)
    out = ["# Estado do estudo dos vídeos", "",
           "Gerado por `tools/osmpro_estado.py`; não editar à mão. Transcrito = legendas em `legendas/`; "
           "analisado = nota em `notas/` (D-063).", "",
           f"**Total:** {totals['videos']} vídeos · {totals['transcritos']} transcritos · {totals['sem legendas']} sem "
           f"legendas · {totals['analisados']} analisados · {totals['conclusoes']} conclusões", "",
           "| Categoria | Vídeos | Transcritos | Sem legendas | Analisados | Conclusões |", "|---|---|---|---|---|---|"]
    out += [f"| {name} | {g['videos']} | {g['transcritos']} | {g['sem legendas']} | {g['analisados']} | {g['conclusoes']} |"
            for name, g in by_category.items()]
    out += ["", "## Vídeo a vídeo", "", "| Data | Categoria | Título | Duração | Legendas | Analisado | Conclusões | Nota |",
            "|---|---|---|---|---|---|---|---|"] + lines
    KB.mkdir(parents=True, exist_ok=True)
    (KB / "ESTADO.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{totals['transcritos']} transcritos, {totals['sem legendas']} sem legendas, {totals['analisados']} analisados "
          f"de {totals['videos']}")


if __name__ == "__main__":
    main()
