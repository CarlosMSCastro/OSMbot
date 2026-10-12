"""Readable texts for the daily rewards on the board (owner, 2026-10-12). Pure: no network, no I/O.

The missions come as the game words them (English, ``progressTypeTranslation`` in the ``missions`` catalogue);
in Portuguese they are rewritten from their few shapes ("Buy any Defender rated 85+", "Train any GK"...). A prize
is told from its type and value in the game's reward catalogue (``v1.1/rewards``; the names there are templates
like "%@ Pack"). A text with no rule stays as the game gives it.
"""
from __future__ import annotations

import re

POSITIONS = {"player": "jogador", "attacker": "avançado", "defender": "defesa", "midfielder": "médio",
             "goalkeeper": "guarda-redes", "gk": "GR"}  # CB, CDM, ST... stay as the game writes them
FIXED = {
    "add a player to the transfer list": "Pôr um jogador na lista de transferências",
    "analyse your opponent": "Analisar o adversário",
    "start analysing your opponent": "Enviar o analista",
    "expand your stadium": "Melhorar o estádio",
    "start upgrading your stadium": "Começar a melhorar o estádio",
    "play friendly": "Jogar um amigável",
    "reduce training timer": "Encurtar um treino",
    "score goals": "Marcar golos",
    "spend club funds": "Gastar fundos do clube",
    "watch rewarded video": "Ver um vídeo com prémio",
}
_BUY = re.compile(r"buy any (\S+)( via the scout)?(?: for (\d+)M\+| rated (\d+)\+)?", re.I)
_OTHER = ((re.compile(r"sell any (\S+)", re.I), "Vender um {}"),
          (re.compile(r"start training any (\S+)", re.I), "Pôr a treinar um {}"),
          (re.compile(r"train any (\S+)", re.I), "Treinar um {}"))
# reward type -> (Portuguese, English); {v} the value, {m} the value in millions
PRIZES = {1: ("{v} boss coins", "{v} boss coins"), 15: ("{v} de energia", "{v} energy"),
          8: ("pacote de {m} de fundos", "{m} club funds pack"), 9: ("+{v}% de progressão de treino", "+{v}% training progression"),
          11: ("pacote de jogador", "player pack"), 13: ("saco de prémios", "reward bag"), 7: ("troca de posição", "position switch")}


def clean(text: str) -> str:
    """The game's text with odd spaces (some come as a broken character) made plain."""
    return " ".join((text or "").replace("�", " ").replace("\xa0", " ").split())


def _position(word: str) -> str:
    return POSITIONS.get(word.lower(), word)


def mission_text(text: str, lang: str = "pt") -> str:
    """A daily mission in the window's language."""
    text = clean(text)
    if lang != "pt":
        return text
    if text.lower() in FIXED:
        return FIXED[text.lower()]
    found = _BUY.fullmatch(text)
    if found:
        return (f"Comprar um {_position(found[1])}" + (" pelo olheiro" if found[2] else "")
                + (f" por {found[3]} M+" if found[3] else "") + (f" com rating {found[4]}+" if found[4] else ""))
    for pattern, words in _OTHER:
        found = pattern.fullmatch(text)
        if found:
            return words.format(_position(found[1]))
    return text


def millions(value: int) -> str:
    """3 000 000 -> "3 M", 2 500 000 -> "2,5 M" (one decimal at most, as the bot's log writes money)."""
    return f"{value / 1e6:.1f}".rstrip("0").rstrip(".").replace(".", ",") + " M"


def prize_text(prize: dict | None, lang: str = "pt") -> str:
    """{"type", "value", "action"} as words: "5 boss coins", "pacote de 3 M de fundos"... The action id when the
    type is not known."""
    if not prize:
        return "—"
    words = PRIZES.get(prize.get("type"))
    value = prize.get("value") or 0
    if words:
        return words[lang != "pt"].format(v=value, m=millions(value))
    action = prize.get("action") or "?"
    return re.sub(r"^(DailyMissionsReward(Missions_)?|DailyLogin)", "", action)


def amount(value: int, goal: int) -> str:
    """A mission's progress: "2/3", or in millions for money ("5 M/5 M")."""
    if goal >= 100_000:
        return f"{millions(min(value, goal))}/{millions(goal)}"
    return f"{min(value, goal)}/{goal}"
