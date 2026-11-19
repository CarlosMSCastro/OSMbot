"""Ver → Vídeos (owner, 2026-11-19): which videos the bot tried on a day and which went through. Pure: it takes the
lines of ``logs/*/videos`` (each with "pc", the folder it came from) and gives the rows and the totals."""
from __future__ import annotations

from datetime import date, datetime

KINDS = ("loja", "treino", "dinheiro")
FILTERS = ("Todos", "Passaram", "Falharam")


def day_of(record: dict) -> date:
    return datetime.fromtimestamp(record["t"]).date()


def days(records: list[dict]) -> list[date]:
    """The days with videos, newest first."""
    return sorted({day_of(r) for r in records if "t" in r}, reverse=True)


def totals(records: list[dict], day: date) -> dict[str, tuple[int, int]]:
    """Per kind of video on ``day``: (went through, tried)."""
    out = {}
    for kind in KINDS:
        tried = [r for r in records if r.get("tipo") == kind and day_of(r) == day]
        out[kind] = (sum(1 for r in tried if r.get("ok")), len(tried))
    return out


def summary(records: list[dict], day: date) -> str:
    """ "Loja 3 de 12 · Treino 2 de 5 · Dinheiro 0 de 4" (kinds not tried that day are left out)."""
    parts = [f"{kind.capitalize()} {ok} de {tried}" for kind, (ok, tried) in totals(records, day).items() if tried]
    return " · ".join(parts) if parts else "Nenhum vídeo tentado neste dia"


def rows(records: list[dict], day: date, which: str = "Todos", kind: str | None = None) -> list[dict]:
    """The day's videos, newest first, as the window's table shows them."""
    keep = [r for r in records if "t" in r and day_of(r) == day and (kind is None or r.get("tipo") == kind)
            and (which == "Todos" or bool(r.get("ok")) == (which == "Passaram"))]
    out = []
    for r in sorted(keep, key=lambda r: r["t"], reverse=True):
        result = "passou" + (f" (+{r['coins']} coins)" if r.get("coins") else "") if r.get("ok") else "falhou"
        out.append({"hora": f"{datetime.fromtimestamp(r['t']):%H:%M}", "tipo": r.get("tipo", "?"), "clube": r.get("clube") or "",
                    "jogador": r.get("jogador") or "", "resultado": result, "ok": bool(r.get("ok")),
                    "motivo": r.get("erro") or "", "pc": r.get("pc") or ""})
    return out
