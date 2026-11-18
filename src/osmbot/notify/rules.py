"""Which messages the owner wants (D-110) and their text. Pure: the board's club snapshot in, alerts out.

An ``Alert`` has a ``kind`` (the switch that turns it off), a ``key`` (the same fact never goes out twice) and the
``text``. The messages carry no spoilers: a match is announced as played, never with its result (owner, 2026-11-18).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape

# kind -> on unless the config says otherwise (events off: owner, 2026-11-18)
DEFAULTS = {"jogo": True, "pre_jogo": True, "adversario": True, "venda": True, "erro": True, "evento": False}
KINDS = {
    "jogo": "O jogo já passou (sem resultado)",
    "pre_jogo": "Pré-jogo com coisas laranjas ou por marcar",
    "adversario": "O adversário fez estágio ou treino secreto",
    "venda": "Vendi alguém",
    "erro": "O bot não conseguiu fazer algo",
    "evento": "Fim de treinos e eventos",
}
HOURS_BEFORE = 1.0  # the pre-match warning goes out when the match is this close (owner, 2026-11-18)
ANALYSIS = "Análise"  # only ready near the hour: never a warning of its own
TRAININGS = "4 treinos"  # ticks by itself when the sessions end and the bot collects them: not the owner's to fix
SKIPPED = (ANALYSIS, TRAININGS)
RULE = "fora da regra"  # a step the game ticks but the owner's rule does not (orange on the card)
SECRET = "treino secreto"  # the card's note on the analysis when the opponent is on a secret training


@dataclass(frozen=True)
class Alert:
    kind: str
    key: str
    text: str  # plain, one line per fact
    club: str | None = None  # whose logo goes with it
    html: str | None = None  # the same, dressed for Telegram (bold names, a symbol per kind)


def enabled(config: dict | None, kind: str) -> bool:
    """Whether the owner wants this kind (``config``: the ``notificacoes`` block; missing keys use ``DEFAULTS``)."""
    return bool((config or {}).get(kind, DEFAULTS.get(kind, False)))


def pregame(club: dict, now: float, hours: float = HOURS_BEFORE) -> Alert | None:
    """The card's orange or unticked steps (not the analysis nor the 4 trainings), once, when the match is within ``hours``."""
    match = club.get("match")
    if not match or not 0 < match - now <= hours * 3600:
        return None
    prep = club.get("prep") or {}
    why = prep.get("why") or {}
    lines, dressed = [], []
    for name, done, extra in prep.get("steps") or []:
        if name in SKIPPED:
            continue
        if extra == RULE:
            reasons = why.get(name) or []
            lines.append(f"🟠 {name}: {reasons[0]}" if reasons else f"🟠 {name}")
            dressed.append(f"🟠 <b>{escape(name)}</b>: {escape(reasons[0])}" if reasons else f"🟠 <b>{escape(name)}</b>")
        elif not done:
            lines.append(f"⚪ {name}: por marcar")
            dressed.append(f"⚪ <b>{escape(name)}</b>: por marcar")
    if not lines:
        return None
    wait = max(1, round((match - now) / 60))
    name = str(club.get("name"))
    return Alert("pre_jogo", f"pre:{club.get('key')}:{int(match)}", f"{name}: jogo em {wait} min\n" + "\n".join(lines), name,
                 f"⏰ <b>{escape(name)}</b> · jogo em {wait} min\n" + "\n".join(dressed))


def opponent(club: dict) -> Alert | None:
    """The opponent is on a training camp and/or a secret training (known after the analysis; owner: "importante")."""
    upcoming = club.get("next") or {}
    steps = (club.get("prep") or {}).get("steps") or []
    secret = any(name == ANALYSIS and extra == SECRET for name, _, extra in steps)
    camp = bool(upcoming.get("camp"))
    if not (secret or camp):
        return None
    what = "estágio e treino secreto" if secret and camp else "treino secreto" if secret else "estágio"
    note = "" if camp or not secret else " (com treino secreto o jogo não deixa ver o resto)"
    name, rival = str(club.get("name")), str(upcoming.get("opponent", "o adversário"))
    return Alert("adversario", f"adv:{club.get('key')}:{int(club.get('match') or 0)}:{what}",
                 f"{name}: {rival} fez {what}{note}", name,
                 f"🚨 <b>{escape(name)}</b>\n{escape(rival)} fez <b>{what}</b>{escape(note)}")


def played(club: str, game: str) -> Alert:
    """"The match is over", with no result (``game``: any id that tells this match from the next)."""
    return Alert("jogo", f"jogo:{game}", f"{club}: o jogo já passou", club, f"⚽ <b>{escape(club)}</b>\nO jogo já passou")


def sale(club: str, player: str, price: str, game: str) -> Alert:
    """Someone of the owner's was sold (``price`` already written, "2,25 M")."""
    return Alert("venda", f"venda:{game}", f"{club}: {player} vendido por {price}", club,
                 f"💰 <b>{escape(club)}</b>\n{escape(player)} vendido por <b>{escape(price)}</b>")


def error(what: str, key: str) -> Alert:
    return Alert("erro", f"erro:{key}", f"⚠️ {what}", None, f"🔴 <b>Erro</b>\n<code>{escape(what)}</code>")


# Errors worth a message (owner, 2026-11-18): what stops the bot or writes nothing. The rest ("... volto a tentar", the
# videos, the network) the bot handles by itself: it only reaches the phone when it keeps failing (``repeated``).
CRITICAL = re.compile(r"^(Parou|Início de sessão|Sessão|Treinos: \d+ falha)", re.IGNORECASE)
REPEAT_COUNT, REPEAT_WINDOW, REPEAT_COOLDOWN = 5, 3 * 3600, 6 * 3600  # 5 times in 3 h, then silence for 6 h


def category(text: str) -> str:
    """What failed, for counting: the line up to the first colon ("Vídeos", "Rede")."""
    return text.split(":", 1)[0].strip()[:40] or "erro"


def is_critical(text: str) -> bool:
    return bool(CRITICAL.match(text.lstrip("! ").strip()))


def repeated(what: str, count: int, last: str, at: float) -> Alert:
    hours = REPEAT_WINDOW // 3600
    return Alert("erro", f"repetido:{what}:{int(at)}", f"⚠️ {what} falhou {count} vezes em {hours} h: {last}", None,
                 f"🔴 <b>{escape(what)}</b> falhou {count} vezes em {hours} h\n<code>{escape(last)}</code>")


_SALE = re.compile(r"^Venda: (.+?) \((.+?)\) vendido por (.+?)(?: \(|;)")
_PLAYED = re.compile(r"^Jogo: (.+?) \d+-\d+ (.+?) \((?:casa|fora)\)")


def from_log_line(message: str, is_error: bool = False) -> Alert | None:
    """The alert a line of the bot's log makes, if any: a sale, an official match played (no result in the text) or
    an error. The line itself is the key, so the same line never goes out twice."""
    text = message.lstrip(chr(7)).lstrip("! ").strip()
    if sold := _SALE.match(text):
        return sale(sold[2], sold[1], sold[3], text)
    if played_ := _PLAYED.match(text):
        return Alert("jogo", f"jogo:{text}", f"{played_[1]}: o jogo contra {played_[2]} já passou", played_[1],
                     f"⚽ <b>{escape(played_[1])}</b>\nO jogo contra {escape(played_[2])} já passou")
    if is_error and is_critical(text):
        return error(text, text[:120])
    return None


def due(alerts: list[Alert | None], config: dict | None, sent: set[str]) -> list[Alert]:
    """What goes out now: the kinds that are on, never the same key twice (``sent`` is updated)."""
    out = []
    for alert in alerts:
        if alert and enabled(config, alert.kind) and alert.key not in sent:
            sent.add(alert.key)
            out.append(alert)
    return out
