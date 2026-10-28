"""The game's prediction of a real match (owner, 2026-10-25: "melhor que perder as coins sempre") and the end of
season prize (owner: "se eu me esquecer o bot levanta"). THEORY.md section 17.

Predictions (DISCOVERY.md section 3, the site's ``matchPrediction.js`` v32583): every ~2 days one real match,
``GET matchpredictions`` (start, end, prize in ``actionId``, result once known). One prediction at a time:
``GET user/usermatchprediction`` (404 when none), ``POST user/usermatchpredictions`` {matchPredictionId, homeGoals,
awayGoals}. Only the exact score wins (``isResultCorrect``). Once the match is over and its result is in, the
site takes the prediction away with ``DELETE user/usermatchpredictions/{id}``, right or wrong (right: the answer
lists the prizes); only then is the next match open to predict.

End of season: ``GET user/history`` lists every season with ``claimed`` and ``reward`` (boss coins);
``PUT user/history/{id}/claim`` collects one (the site's career page).
"""
from __future__ import annotations

import time

PREDICTION = (1, 1)  # [S] the commonest exact score in football; the bot knows nothing of the real teams


def step(mine: dict | None, matches: list[dict], now: float) -> tuple[str, dict] | None:
    """What to do now (pure): ("claim", the prediction) once its match is over with a result; ("predict", the
    match) when there is no prediction and a match is open; None otherwise."""
    if mine:
        match = next((m for m in matches if m.get("id") == mine.get("matchPredictionId")), None)
        over = match is not None and match["endTimestamp"] < now
        if over and match.get("homeGoalsResult") is not None and match.get("awayGoalsResult") is not None:
            return "claim", mine
        if match is not None or not matches:
            return None
        return "claim", mine  # its match is no longer listed: clear it, as the site does, so the next one opens
    open_ = [m for m in matches if m["startTimestamp"] <= now < m["endTimestamp"]]
    return ("predict", min(open_, key=lambda m: m["endTimestamp"])) if open_ else None


def to_collect(history: list[dict]) -> list[dict]:
    """The seasons whose prize is still to collect (pure)."""
    return [s for s in history if not s.get("claimed") and (s.get("reward") or 0) > 0]


def run_prediction(client, confirm: bool, log=print, now: float | None = None) -> int:
    """Predict the open match, or collect the last prediction. Returns failures."""
    now = now or time.time()
    status, matches = client.get("matchpredictions")
    if status != 200 or not isinstance(matches, list):
        return 0
    status, mine = client.get("user/usermatchprediction")
    mine = mine if status == 200 and isinstance(mine, dict) and mine.get("id") else None
    todo = step(mine, matches, now)
    if todo is None:
        return 0
    kind, item = todo
    if kind == "predict":
        label = f"{item['homeTeamName']} {PREDICTION[0]}-{PREDICTION[1]} {item['awayTeamName']} (prémio {item.get('actionId')})"
        if not confirm:
            log(f"Simulação: previa {label}")
            return 0
        status, _ = client.post("user/usermatchpredictions", {"matchPredictionId": item["id"],
                                                              "homeGoals": PREDICTION[0], "awayGoals": PREDICTION[1]})
        log(f"Previsão: {label}" if status == 200 else f"Previsão: {label} recusada ({status})")
        return 0 if status == 200 else 1
    match = next((m for m in matches if m.get("id") == item.get("matchPredictionId")), {})
    result = (f"{match.get('homeTeamName')} {match.get('homeGoalsResult')}-{match.get('awayGoalsResult')} "
              f"{match.get('awayTeamName')}, previsto {item.get('homeGoals')}-{item.get('awayGoals')}") if match else "jogo já fora da lista"
    if not confirm:
        log(f"Simulação: fechava a previsão ({result})")
        return 0
    status, prizes = client.request("DELETE", f"user/usermatchpredictions/{item['id']}")
    won = [p.get("reward") or {} for p in prizes] if status == 200 and isinstance(prizes, list) else []
    got = ", ".join(f"{r.get('name') or r.get('type')} {r.get('value')}" for r in won if r)
    log(f"Previsão: {result} · " + (f"certa, prémio: {got}" if got else "errada") if status == 200
        else f"Previsão: fechar falhou ({status})")
    return 0 if status == 200 else 1


def claim_seasons(client, confirm: bool, log=print) -> int:
    """Collect the prize of every finished season not yet collected. Returns failures."""
    status, body = client.get("user/history")
    if status != 200 or not isinstance(body, list) or not body:
        return 0
    failures = 0
    for season in to_collect(body[0].get("history") or []):
        label = f"{season.get('team')} ({season.get('leagueName')}, {season.get('ranking')}.º): {season.get('reward')} boss coins"
        if not confirm:
            log(f"Simulação: reclamaria o prémio de fim de época de {label}")
            continue
        status, _ = client.put(f"user/history/{season['id']}/claim")
        log(f"Fim de época: prémio de {label} reclamado" if status == 200 else f"Fim de época: {label} recusado ({status})")
        if status == 200:
            from osmbot.game import wallet as ledger

            ledger.note("recompensas", season.get("reward") or 0)
        failures += status != 200
    return failures
