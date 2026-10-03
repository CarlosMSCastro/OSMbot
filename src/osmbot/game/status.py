"""Read-only summary of the owner's active clubs, from ``GET user/accounts``.

Field names are the ones observed with ``osmbot probe user/accounts`` (2026-10-03).
What ``ranking`` means exactly (league position?) is still unconfirmed.
"""
from __future__ import annotations


def summarize(account: dict) -> list[str]:
    """One line per occupied team slot; empty slots are skipped."""
    lines = []
    for slot, content in sorted((account.get("teamSlots") or {}).items()):
        team = (content or {}).get("team")
        league = (content or {}).get("league") or {}
        if not team:
            continue
        lines.append(
            f"[{slot}] {team.get('name', '?')} | liga: {league.get('name', '?')} "
            f"(semana {league.get('weekNr', '?')}) | ranking: {team.get('ranking', '?')} "
            f"| orcamento: {team.get('budget', 0):,}".replace(",", ".")
        )
    return lines


def run_status() -> None:
    from osmbot.game.client import NeedsBrowserLogin, OsmClient

    try:
        client = OsmClient()
        status, account = client.get("user/accounts")
        wallet_status, wallet = client.get("user/bosscoinwallet")
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    if status != 200 or not isinstance(account, dict):
        raise SystemExit(f"Resposta inesperada do jogo (estado {status}).")
    coins = wallet.get("amount", "?") if wallet_status == 200 and isinstance(wallet, dict) else "?"
    print(f"Manager: {account.get('name', '?')} | boss coins: {coins}")
    lines = summarize(account)
    print("\n".join(lines) or "Nenhuma equipa ativa.")
