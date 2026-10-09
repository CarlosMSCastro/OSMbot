"""The console board of ``osmbot ativo`` (D-015): a fixed screen that redraws itself.

``collect`` reads the game (GET only); ``render`` is a pure function from that snapshot to text,
so the countdowns can be redrawn every second without touching the game.

Colours always mean the same thing:
  green  = done / good / progress made      yellow = needs attention (free slot, tired, incomplete)
  blue   = time still to run, work in progress, time saved by a video
  grey   = labels, empty bars, nothing going on   red = errors     (names and plain data have no colour)
"""
from __future__ import annotations

import os
import platform
import re
import sys
import time
from datetime import datetime

from osmbot.game.ads import SHOP_ACTION, TRAINING_ACTION, VIDEO_SAVES, money_state
from osmbot.game.slots import SlotStatus, count_listed
from osmbot.theory.fitness import YELLOW_BELOW, tired_starters

POSITIONS = {1: "ATA", 2: "MED", 3: "DEF", 4: "GR"}
NEXT_MATCH_TIMER = 14
BAR_SECONDS = 8 * 3600  # the bar is drawn against a normal 8h training
BAR_WIDTH = 20  # 2h (one video) = 5 cells
STADIUM_BAR_SECONDS = 18 * 3600  # a stadium upgrade takes 18h (gamesettings StadiumUpgrade, DISCOVERY.md)
WIDTH = 100  # the widest the board gets; it shrinks to the window
LABEL = 11  # width of the row labels ("dinheiro", "estádio"...)
GREEN, YELLOW, GREY, RESET = "\x1b[32m", "\x1b[33m", "\x1b[90m", "\x1b[0m"
RED, BLUE, BOLD = "\x1b[31m", "\x1b[36m", "\x1b[1m"  # the console's "cyan" is the blue we want
SPONSOR_SLOTS = 4
STADIUM_NAMES = {2: "Treinos", 1: "Campo", 0: "Capacidade"}
STADIUM_BAR_WIDTH = 14
VIDEOS_BAR_WIDTH = 10
SHOP_BAR_SECONDS = 3600  # the wait after the shop videos run out is 1h (confirmed by the owner, WORKLOG)
SHOP_BAR_WIDTH = 10
ANSI = re.compile(r"(\x1b\[[0-9;]*m)")


def span(seconds: float) -> str:
    minutes = int(max(0, seconds) // 60)
    return f"{minutes // 60}h{minutes % 60:02d}"


def money(amount: int) -> str:
    """12 345 678 -> "12,35 M"; 1 000 000 -> "1 M"; 450 000 -> "450 k" (999 600 also counts as 1 M)."""
    if abs(amount) >= 1_000_000 or round(abs(amount) / 1000) >= 1000:
        return f"{amount / 1_000_000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " M"
    return f"{amount / 1000:.0f} k"


def bar(left: float, total: float = BAR_SECONDS, width: int = BAR_WIDTH) -> str:
    done = 1 - min(max(left, 0), total) / total
    filled = round(done * width)
    return "█" * filled + "░" * (width - filled)


CLUBS_AT_ONCE, REQUESTS_PER_CLUB = 2, 3  # at most 6 requests at a time, like a browser


def get_many(client, paths: list[str]) -> list[tuple[int, object]]:
    """GET several paths at once (a few at a time); answers in the same order."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=REQUESTS_PER_CLUB) as pool:
        return list(pool.map(client.get, paths))


def collect(client) -> dict:
    """One snapshot of everything the board shows (GET requests only, several at a time)."""

    from osmbot.game.clubinfo import max_listed

    started = time.time()  # when the reading began: the board keeps the newest one (bot's or window's)
    (_, account), (_, wallet) = get_many(client, ["user/accounts", "user/bosscoinwallet"])
    leagues = {c["team"]["name"]: c.get("league") or {} for c in (account.get("teamSlots") or {}).values() if c and c.get("team")}

    def read_club(team: dict, base: str) -> dict:
        got = get_many(client, [f"{base}/{path}" for path in ("trainingsessions/ongoing", "timers", "players",
                                                               "finances/balanceandsavings", "stadium", "sponsors",
                                                               "transferplayers/0")])
        sessions, timers, players, funds, stadium, contracts, market = (body for _, body in got)
        match = next((t["finishedTimestamp"] for t in timers if t["type"] == NEXT_MATCH_TIMER), None)
        market = market if isinstance(market, list) else []
        slot = SlotStatus(team["name"], count_listed(players, market), max_listed(client, team["leagueId"]))
        running = [p["countdownTimer"]["finishedTimestamp"] for p in stadium["stadiumParts"]
                   if p.get("countdownTimer") and p["countdownTimer"]["finishedTimestamp"] > time.time()]
        live = [c for c in contracts if c.get("weeksLeft", 0) > 0]
        club = {
            "name": team["name"], "ranking": team.get("ranking"), "league": leagues.get(team["name"], {}).get("name", "?"),
            "tired": tired_starters(players), "match": match,
            "money": (funds["balance"], funds["savings"]),
            "stadium": {"parts": [(STADIUM_NAMES.get(p["stadiumPartType"], "?"), p["level"],
                                   max((lv["level"] for lv in p["stadiumPartLevels"]), default=0),
                                   (p.get("countdownTimer") or {}).get("finishedTimestamp"))
                                  for p in sorted(stadium["stadiumParts"], key=lambda p: -p["stadiumPartType"])],
                        "until": max(running) if running else None},
            "sponsors": {"slots": len(live), "revenue": sum(c["sponsorRevenueForTeam"] for c in live)}, "slots": (slot.listed, slot.maximum) if slot else None,
            "trainings": [
                {"id": s["id"], "name": s["player"]["name"], "pos": POSITIONS.get(s["player"]["position"], "?"),
                 "finish": s["countdownTimer"]["finishedTimestamp"], "claimed": s["countdownTimer"]["isClaimed"]}
                for s in sorted(sessions, key=lambda s: s["trainer"])
            ],
        }
        try:  # the card's extras (D-026): a problem here never hides the rest of the board
            from osmbot.game.clubinfo import club_extra

            club.update(club_extra(client, team, base, players, slot, market))
        except OSError:
            raise
        except Exception as error:
            club["extra_error"] = f"{type(error).__name__}: {error}"
        return club

    from concurrent.futures import ThreadPoolExecutor

    def read_account() -> tuple[dict, dict]:
        from osmbot.game.rewards import daily_state

        caps = get_many(client, [f"user/caps/actions/{action}/0" for action in (SHOP_ACTION, TRAINING_ACTION)])
        ads = {key: {"open": bool(cap.get("isClaimable")) and not cap.get("isCapReached"),
                     "reopen": cap.get("timestampUntilUnreached") if cap.get("isCapReached") else None}
               for key, (_, cap) in zip(("shop", "training"), caps)}
        ads["money"] = money_state(client)
        return ads, daily_state(client)

    teams = [(team, f"leagues/{team['leagueId']}/teams/{team['id']}") for team in
             (c["team"] for _, c in sorted((account.get("teamSlots") or {}).items()) if c and c.get("team"))]
    with ThreadPoolExecutor(max_workers=CLUBS_AT_ONCE + 1) as pool:  # clubs and account side by side: a few seconds
        account_part = pool.submit(read_account)
        clubs = list(pool.map(lambda item: read_club(*item), teams))
        ads, daily = account_part.result()
    return {"coins": wallet.get("amount"), "clubs": clubs, "ads": ads, "daily": daily, "read_at": started}


def wake_events(snapshot: dict | None, now: float) -> list[tuple[str, float]]:
    """What the bot is waiting for, soonest first: (label, timestamp)."""
    if not snapshot:
        return []
    events = []
    unclaimed = [t["finish"] for c in snapshot["clubs"] for t in c["trainings"] if not t["claimed"]]
    if any(finish <= now for finish in unclaimed):  # finished while the bot was busy (e.g. videos): collect it now
        events.append(("treino por recolher", now))
    finishes = [finish for finish in unclaimed if finish > now]
    if finishes:
        events.append(("treino acaba", min(finishes)))
    ends = [c["stadium"]["until"] for c in snapshot["clubs"] if (c.get("stadium") or {}).get("until")]
    if ends and min(ends) > now:
        events.append(("estádio acaba", min(ends)))
    for key, label in (("shop", "loja reabre"), ("training", "vídeo de treino reabre"), ("money", "dinheiro reabre")):
        reopen = (snapshot["ads"].get(key) or {}).get("reopen")
        if reopen and reopen > now:
            events.append((label, reopen))
    daily = snapshot.get("daily") or {}
    renews = (daily.get("login") or {}).get("renews")
    if renews and renews > now:
        events.append(("novo dia", renews))
    reopen = (daily.get("videos") or {}).get("reopen")
    if reopen and reopen > now:
        events.append(("vídeos acumulados reabrem", reopen))
    return sorted(events, key=lambda e: e[1])


def coin_jump(snapshot: dict | None, stats: dict | None) -> int | None:
    """Boss coins gained since the bot started (None while unknown)."""
    if snapshot and stats and stats.get("coins0") is not None:
        return snapshot["coins"] - stats["coins0"]
    return None


def summary_lines(snapshot: dict | None, stats: dict | None, now: float, full: bool = False) -> list[str]:
    """What the bot did since it started. The board shows one line (the videos); ``full`` (for the log)
    adds the coin jump, trainings, stadium and sponsors."""
    if not stats or stats.get("start") is None:
        return []
    head = f"Desde o arranque ({span(now - stats['start'])})"
    shortened = stats.get("training", 0) * VIDEO_SAVES // 3600
    videos = (f"vídeos: loja {stats.get('shop', 0)} · treino {stats.get('training', 0)} (encurtadas {shortened} h)"
              f" · dinheiro {stats.get('money', 0)}")
    if not full:
        return [f"{head} · {videos}"]
    jump = coin_jump(snapshot, stats)
    if jump is not None:
        head += f": salto {jump:+d} boss coins"
    return [head, f"  {videos} · treinos: {stats.get('claimed', 0)} recolhidos, {stats.get('started', 0)} postos"
                  f" · estádio {stats.get('upgrades', 0)} · patrocinadores {stats.get('signed', 0)}"
                  f" · recompensas: início {stats.get('r_login', 0)}, missões {stats.get('r_missions', 0)}, vídeos acumulados {stats.get('r_videos', 0)}"
                  f" · pré-jogo: amigáveis {stats.get('friendlies', 0)}, análises {stats.get('analyses', 0)}"]


def summary_text(snapshot: dict | None, stats: dict | None, now: float) -> str:
    return " · ".join(line.strip() for line in summary_lines(snapshot, stats, now, full=True))


def render(snapshot: dict | None, now: float, status: str, recent: list[str], machine: str, colour: bool = True,
           stats: dict | None = None, rows: int | None = None, cols: int | None = None) -> str:
    """The board as text. With ``rows``/``cols`` (the terminal size) it is shortened step by step until it fits:
    a board taller than the window would scroll and pile up copies of itself, a wider one would wrap."""
    width = max(40, min(WIDTH, cols - 1)) if cols else WIDTH
    for level in range(4):
        text = _render(snapshot, now, status, recent, machine, colour, stats, level, width)
        if rows is None or text.count("\n") + 1 <= rows - 1:
            return text
    return "\n".join(text.split("\n")[:max(1, rows - 1)])


def _clip(text: str, width: int) -> str:
    """Cut to the board width counting only what is visible (colour codes take no space)."""
    if len(ANSI.sub("", text)) <= width - 1:
        return text
    out, visible = [], 0
    for piece in ANSI.split(text):
        if ANSI.fullmatch(piece):
            out.append(piece)
            continue
        room = width - 2 - visible
        out.append(piece[:max(room, 0)])
        visible += min(len(piece), max(room, 0))
    return "".join(out) + (RESET if ANSI.search(text) else "") + "…"


def daily_lines(daily: dict | None, now: float, level: int, paint, painted_bar, width: int = WIDTH) -> list[str]:
    """The daily rewards (login, missions, day reward, accumulated videos): two lines, one shorter line when space is short."""
    if not daily:
        return []
    short = level >= 2
    done, todo, wait = (lambda text: paint(text, GREEN)), (lambda text: paint(text, YELLOW)), (lambda text: paint(text, GREY))
    parts = []
    login = daily.get("login")
    name = "início" if short else "início de sessão"
    if login:
        parts.append(todo(f"{name} por reclamar") if login["claimable"] else done(f"{name} √" + ("" if short else f" (dia {login['day']})")))
    missions = daily.get("missions")
    if missions and missions["total"]:
        finished = missions["claimed"] >= missions["total"]
        parts.append((done if finished else todo)(f"missões {missions['claimed']}/{missions['total']}" + (" √" if finished else "")))
        prize = "prémio" if short else "prémio do dia"
        parts.append(todo(f"{prize} por reclamar") if missions["day_pending"] else (done(f"{prize} √") if finished else wait(f"{prize} -")))
    renews = (login or {}).get("renews")
    new_day = paint(("novo dia " if short else "novo dia em ") + span(renews - now), BLUE) if renews and renews > now else ""
    videos = daily.get("videos")
    video = ""
    if videos:
        label = "posição" if short else "troca de posição"
        total = max(1, videos["threshold"])
        video = f"{label} " + painted_bar(total - videos["count"], total, VIDEOS_BAR_WIDTH) + f" {videos['count']}/{videos['threshold']}"
        if videos["claimable"]:
            video = todo(f"{label} por reclamar")
        elif videos.get("reopen") and videos["reopen"] > now and not short:
            video += " " + paint(f"reabre em {span(videos['reopen'] - now)}", BLUE)
    if short:
        joined = " · ".join(x for x in (" · ".join(parts), video, new_day) if x)
        return [_clip(" " + joined, width)] if joined else []
    rows = []
    if parts:
        rows.append(_clip(" " + paint("diárias".ljust(LABEL), GREY) + " · ".join(parts) + ("  " + new_day if new_day else ""), width))
    if video:
        rows.append(_clip(" " + paint("extra".ljust(LABEL), GREY) + video, width))
    return rows


def _render(snapshot: dict | None, now: float, status: str, recent: list[str], machine: str, colour: bool,
            stats: dict | None, level: int, width: int) -> str:
    """level 0 = everything; 1 = shorter log; 2 = also no blank lines before the totals;
    3 = no blank lines at all, shortest log, stadium time without its bar."""
    club_gap = [] if level >= 3 else [""]
    foot_gap = [] if level >= 2 else [""]

    def paint(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if colour and code else text

    def painted_bar(left: float, total: float, size: int, shortened: float = 0) -> str:
        """Green = time gone by, blue = the part of it a video skipped, grey = still to go."""
        filled = round((1 - min(max(left, 0), total) / total) * size)
        skipped = min(filled, round(max(shortened, 0) / total * size))
        return paint("█" * (filled - skipped), GREEN) + paint("█" * skipped, BLUE) + paint("░" * (size - filled), GREY)

    def row(label: str, text: str) -> str:
        return _clip("   " + paint(label.ljust(LABEL), GREY) + text, width)

    def timer(left: float, ready: bool) -> str:
        return paint("pronto", BOLD + GREEN) if ready else paint(span(left), BLUE)

    skipped = (stats or {}).get("shortened") or {}
    rule = "─" * (width - 2)
    base = f" OSMbot · {status} · {machine}"
    hint = "   Para parar: Ctrl+C"
    gap_to_clock = " " * max(1, width - 9 - len(base) - len(hint))
    lines = [base + paint(hint, GREY) + gap_to_clock + datetime.fromtimestamp(now).strftime("%H:%M:%S"), " " + rule]
    if snapshot is None:
        lines.append(" (a carregar…)")
    else:
        for club in snapshot["clubs"]:
            free = club["slots"][1] - club["slots"][0] if club["slots"] else 0
            head = " " + paint(f"{club['name'].upper()}   {club['ranking']}.º {club['league']}", BOLD + GREEN)
            if club["match"]:
                head += "   jogo em " + paint(span(club["match"] - now), BLUE)
            if club["slots"]:
                head += "   Lista de Transf. " + paint(f"{club['slots'][0]}/{club['slots'][1]}", BOLD + YELLOW if free else "")
            else:
                head += "   Lista de Transf. ?"
            lines += [*club_gap, _clip(head, width)]
            if club.get("money"):
                funds, savings = club["money"]
                lines.append(row("dinheiro", f"fundos {paint(money(funds), '' if funds else GREY)}"
                                             f" · poupança {paint(money(savings), '' if savings else GREY)}"))
            stadium = club.get("stadium")
            if stadium:
                bits = []
                for name, part_level, top, ends in stadium["parts"]:
                    text = f"{name} {part_level}/{top}"
                    if ends and ends > now:
                        left = ends - now
                        bits.append(paint(text, BLUE) + " " + (painted_bar(left, STADIUM_BAR_SECONDS, STADIUM_BAR_WIDTH) + " " if level < 3 else "» ")
                                    + paint(span(left), BLUE))
                    elif part_level >= top:
                        bits.append(paint(text + " √", GREEN))
                    else:
                        bits.append(text)
                lines.append(row("estádio", " · ".join(bits)))
            sponsors = club.get("sponsors")
            if sponsors:
                full = sponsors["slots"] >= SPONSOR_SLOTS
                lines.append(row("patroc.", paint(f"{sponsors['slots']}/{SPONSOR_SLOTS} escolhidos", GREEN if full else YELLOW)
                                 + f" · {money(sponsors['revenue'])}/ronda"))
            for t in club["trainings"]:
                left = t["finish"] - now
                ready = left <= 0 and not t["claimed"]
                state = timer(left, ready) + " " * (6 - len("pronto" if ready else span(left)))
                lines.append(f"   {t['name'][:14]:<14} {t['pos']:<4} {state} "
                             + painted_bar(left, BAR_SECONDS, BAR_WIDTH, skipped.get(t.get("id"), 0)))
            tired = club.get("tired") or []
            if tired:
                prefix, names = "   ! cansados: ", [f"{p['name'].split()[-1]} {p['fitness']}%" for p in tired]
                text = prefix + ", ".join(names)
                while len(text) > width - 1 and len(names) > 1:
                    names.pop()
                    text = prefix + ", ".join(names) + f" +{len(tired) - len(names)}"
                lines.append(paint(_clip(text, width), YELLOW))
        coins = " Boss coins " + paint(str(snapshot["coins"]), BOLD + YELLOW)
        jump = coin_jump(snapshot, stats)
        if jump is not None:
            coins += "  " + paint(f"{jump:+d}", BOLD + (GREEN if jump > 0 else RED if jump < 0 else GREY))
        shop = snapshot["ads"].get("shop") or {}
        reopen = shop.get("reopen")
        if not shop.get("open") and reopen and reopen > now:  # videos available: the bot is watching them, no bar
            coins += ("    " + paint("loja", GREY) + " " + painted_bar(reopen - now, SHOP_BAR_SECONDS, SHOP_BAR_WIDTH)
                      + " " + paint(span(reopen - now), BLUE))
        lines += [*foot_gap, coins, *daily_lines(snapshot.get("daily"), now, level, paint, painted_bar, width)]
    summary = summary_lines(snapshot, stats, now)
    if summary:
        lines += [*foot_gap, *[paint(_clip(" " + line, width), GREY) for line in summary]]
    if recent:  # the board only shows problems; everything else is in the log file
        def log_colour(line: str) -> str:
            body = line[9:].lstrip().lower()
            if "erro" in body or "falha" in body or body.startswith("parou"):
                return paint(line, RED)
            return paint(line, YELLOW if body.startswith(("!", "aviso")) else GREY)

        keep = {0: 5, 1: 3, 2: 3}.get(level, 2)
        lines += [" " + rule, *[_clip(" " + log_colour(line), width) for line in recent[-keep:]]]
    return "\n".join(lines)


class Screen:
    """Redraws the board in place (ANSI). Only used when the output is a real terminal."""

    def __init__(self) -> None:
        if platform.system() == "Windows":
            os.system("")  # switches on ANSI escape codes in the Windows console
        self._restore = _disable_quick_edit()
        self._out = sys.stdout  # the real terminal: stdout is redirected to the log while the bot works
        self._out.write("\x1b[?1049h\x1b[?25l")  # hide the cursor

    def draw(self, text: str) -> None:
        self._out.write("\x1b[H" + ("\x1b[K\n").join(text.split("\n")) + "\x1b[K\x1b[J")
        self._out.flush()

    def close(self) -> None:
        self._out.write("\x1b[?25h\x1b[?1049l")
        self._out.flush()
        if self._restore:
            self._restore()


def _disable_quick_edit():
    """Windows consoles freeze the program while text is selected with the mouse (the title says "Selecionar")
    and Ctrl+C then copies instead of stopping. Switch that off while the board runs; returns the undo."""
    if platform.system() != "Windows":
        return None
    try:
        import ctypes

        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-10)  # standard input
        mode = ctypes.c_uint32()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            return None
        old = mode.value
        kernel.SetConsoleMode(handle, (old | 0x80) & ~0x40)  # ENABLE_EXTENDED_FLAGS on, ENABLE_QUICK_EDIT_MODE off
        return lambda: kernel.SetConsoleMode(handle, old)
    except Exception:
        return None


def machine_name() -> str:
    return {"Windows": "Windows", "Darwin": "macOS"}.get(platform.system(), platform.system())
