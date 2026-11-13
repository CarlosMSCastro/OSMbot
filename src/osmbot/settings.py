"""The client's switches, per club (D-104, owner 2026-11-13): which clubs the bot works on and which of its
automations run in each. Everything is on unless the config says otherwise, so nothing changes until a switch is
turned off. The pure part takes the ``clubes`` dict as it is kept in ``~/.osmbot/config.json``::

    "clubes": {"215028346_9": {"ativo": false, "automacoes": {"amigavel": false}}}

A club's key is ``<leagueId>_<teamId>`` (the same as a match's tactic id). The switches only stop what the bot
*writes*: the board still reads every club. They are read at the start of each pass, so a change counts from the
next cycle (owner, 2026-11-13).
"""
from __future__ import annotations

# key -> what it does (the board's "Definições" shows these)
AUTOMATIONS = {
    "treino": "Recolher e pôr a treinar",
    "amigavel": "Amigáveis antes do jogo",
    "analise": "Análise do adversário (2 h antes)",
    "analista_liga": "Analista pelos outros clubes da liga",
    "especialistas": "Especialistas pela regra (4 h antes)",
    "medico": "Médico e advogado",
    "poupanca": "Depósito na poupança antes do jogo",
    "estadio": "Subir o estádio",
    "patrocinadores": "Assinar patrocinadores",
    "relistar": "Relistar quem subiu de preço",
    "boost": "Boss coins nos treinos dos eventos",
}


# What belongs to the whole account, not to a club (key -> what it does); kept in the config's "conta" block
ACCOUNT = {
    "videos": "Ver vídeos (loja, treino e dinheiro)",
    "recompensas": "Início de sessão, missões e vídeos acumulados",
    "previsoes": "Previsões de jogos reais e prémio de fim de época",
    "inventario": "Usar os itens que vão expirar",
}
CAP = "teto_boss_coins_dia"  # in "conta": the most boss coins the bot spends a day (0 or missing: no ceiling)


def club_key(team: dict) -> str:
    return f"{team.get('leagueId')}_{team.get('id')}"


def load() -> dict:
    """The ``clubes`` block of this PC's config (empty when there is none)."""
    from osmbot.i18n import get_pref

    clubs = get_pref("clubes", {})
    return clubs if isinstance(clubs, dict) else {}


def active(clubs: dict, key: str) -> bool:
    return ((clubs.get(key) or {}).get("ativo", True)) is not False


def allowed(clubs: dict, key: str, automation: str | None = None) -> bool:
    """Whether the bot may write in the club: it is active and, for an automation, that one is on."""
    if not active(clubs, key):
        return False
    if automation is None:
        return True
    return ((clubs.get(key) or {}).get("automacoes") or {}).get(automation, True) is not False


def with_club(clubs: dict, key: str, *, active: bool | None = None, automation: str | None = None, on: bool | None = None) -> dict:
    """A copy of ``clubs`` with one switch changed (the club's, or one automation's)."""
    new = {k: {**v, "automacoes": dict(v.get("automacoes") or {})} for k, v in clubs.items()}
    club = new.setdefault(key, {"automacoes": {}})
    if active is not None:
        club["ativo"] = active
    if automation is not None and on is not None:
        club["automacoes"][automation] = on
    return new


def load_account() -> dict:
    """The ``conta`` block of this PC's config (empty when there is none)."""
    from osmbot.i18n import get_pref

    account = get_pref("conta", {})
    return account if isinstance(account, dict) else {}


def account_allowed(account: dict, automation: str) -> bool:
    """Whether the bot may do this account-wide automation (on unless the config says off)."""
    return account.get(automation, True) is not False


def spending_cap(account: dict | None = None) -> int | None:
    """The daily ceiling of boss coins the bot may spend (None: none set)."""
    value = (load_account() if account is None else account).get(CAP)
    return value if isinstance(value, int) and value > 0 else None
