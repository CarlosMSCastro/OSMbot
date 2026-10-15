"""Browserless client for OSM's web API: reads the saved session and renews it.

Reads the cookies saved by ``browser.py`` (``~/.osmbot/session.json``), keeps the
``access_token`` fresh through ``POST /api/tokenRefresh`` (observed 2026-10-03,
see DISCOVERY.md) and writes the new tokens back. The two OAuth client codes the
renewal needs are captured from the site's own request by ``browser.py`` and kept
in ``~/.osmbot/client.json`` (owner-only, never in the repo).

Reads are plain GETs. Writes (``put``/``post``) exist for the training commands only and
are only called by the owner-approved write commands (see D-014).
"""
from __future__ import annotations

import base64
import json
import threading
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import certifi

from osmbot.game.browser import STATE_FILE, _jwt_times

CLIENT_FILE = Path.home() / ".osmbot" / "client.json"
API_HOST = "https://web-api.onlinesoccermanager.com"
REFRESH_URL = f"{API_HOST}/api/tokenRefresh"
API_BASE = f"{API_HOST}/api/v1"
# Headers the HTTP library sets itself, or that carry the session (never copied)
SKIPPED_HEADERS = {"cookie", "authorization", "content-length", "content-type", "host", "connection", "accept-encoding"}
EXPIRY_MARGIN = 120  # seconds: renew a little before the 20 min access_token ends


class NeedsBrowserLogin(Exception):
    """The saved session can't be renewed without the owner opening the browser."""


class GameUnavailable(OSError):
    """A read the game's server could not answer (5xx, or 429 "too many requests"). Its text would otherwise reach the
    callers as if it were data ("string indices must be integers", 2026-10-14/15); as an OSError the loop waits and
    tries again, as it does when the network is down."""


def _excerpt(raw: bytes, size: int = 80) -> str:
    text = " ".join(raw.decode("utf-8", "replace").split())
    return text[:size] + ("…" if len(text) > size else "")


def save_private(path: Path, data: dict) -> None:
    """Write JSON readable only by the owner (session and client codes are secrets)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
    os.replace(tmp, path)


def _expiry(cookies: list[dict], name: str = "access_token") -> float:
    token = next((c["value"] for c in cookies if c["name"] == name), None)
    return ((_jwt_times(token) if token else None) or {}).get("exp", 0)


def save_browser_session(cookies: list[dict], state_file: Path = STATE_FILE) -> bool:
    """Keep the tokens a video's browser ended with, but only if they are newer than the saved ones: the
    HTTP client may have renewed the session while the video played, and an older refresh_token may no
    longer work (DISCOVERY.md, rotation). Returns True if saved."""
    if not any(c["name"] == "access_token" for c in cookies):
        return False
    try:
        saved = json.loads(state_file.read_text(encoding="utf-8"))["cookies"]
    except (OSError, ValueError, KeyError):
        saved = []
    if _expiry(cookies) <= _expiry(saved):
        return False
    save_private(state_file, {"cookies": cookies, "origins": []})
    return True


NEW_CLUB_RETRY = 600  # s: a club missing from the token is renewed for at most this often
_NEW_CLUB_TRIED: dict[str, float] = {}
_RENEW_LOCK = threading.RLock()  # one for the whole program: the bot and the window never renew at the same time
_ssl_context: ssl.SSLContext | None = None


def _context() -> ssl.SSLContext:
    """The HTTPS settings, built once: loading the certificates costs ~0.35 s of CPU each time (measured 2026-10-09)."""
    global _ssl_context
    if _ssl_context is None:
        # certifi's CA bundle: some Pythons (e.g. Homebrew on macOS) ship without one
        _ssl_context = ssl.create_default_context(cafile=certifi.where())
    return _ssl_context


def _http(request: urllib.request.Request) -> tuple[int, bytes]:
    """Default transport; tests replace it. Returns (status, body) without raising on 4xx/5xx."""
    try:
        with urllib.request.urlopen(request, timeout=30, context=_context()) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


class OsmClient:
    def __init__(self, state_file: Path = STATE_FILE, client_file: Path = CLIENT_FILE, transport=_http):
        self.state_file = state_file
        self.client_file = client_file
        self._transport = transport
        if not state_file.exists():
            raise NeedsBrowserLogin("Sem sessao guardada. Corre primeiro: osmbot login")
        self._state = json.loads(state_file.read_text(encoding="utf-8"))
        self._lock = _RENEW_LOCK  # shared by every client (board, bot, window): only one of them renews the session

    def _reload(self) -> None:
        """Take the saved session if it is newer than the one in memory: another client of the bot, or a
        video's browser, may have renewed it since (several clients live at the same time)."""
        try:
            saved = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if _expiry(saved.get("cookies", [])) > _expiry(self._state["cookies"]):
            self._state = saved

    def _cookie(self, name: str) -> dict | None:
        return next((c for c in self._state["cookies"] if c["name"] == name), None)

    def _token(self, name: str) -> str | None:
        cookie = self._cookie(name)
        return cookie["value"] if cookie else None

    def _token_clubs(self) -> set[str] | None:
        """The clubs the access token is for ("league,team", its `team` claim); None if it does not say. The game
        fills it when the token is issued: a club created since is missing until the next renewal (2026-10-14)."""
        token = self._token("access_token") or ""
        parts = token.split(".")
        try:
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
        except (IndexError, ValueError):
            return None
        clubs = payload.get("team") if isinstance(payload, dict) else None
        if isinstance(clubs, str):
            clubs = [clubs]
        return {str(c) for c in clubs} if isinstance(clubs, list) else None

    def _club_missing(self, path: str) -> str | None:
        """The club of ``path`` ("league,team") when the token does not list it, at most once per club every
        NEW_CLUB_RETRY seconds (other clubs' finances also answer 403, and must not renew every time)."""
        match = re.search(r"leagues/(\d+)/teams/(\d+)", path)
        clubs = self._token_clubs()
        if not match or clubs is None:
            return None
        club = f"{match[1]},{match[2]}"
        if club in clubs or time.time() - _NEW_CLUB_TRIED.get(club, 0) < NEW_CLUB_RETRY:
            return None
        _NEW_CLUB_TRIED[club] = time.time()
        return club

    def _access_is_fresh(self) -> bool:
        token = self._token("access_token")
        info = _jwt_times(token) if token else None
        return bool(info and info.get("exp", 0) - time.time() > EXPIRY_MARGIN)

    def refresh(self, force: bool = False) -> None:
        """Renew both tokens and save them. The old refresh_token stops working (hypothesis), so save at once.
        The saved file is read first: if someone else already renewed, their tokens are used instead
        (``force``: renew anyway, e.g. after the game rejected a token that looked fresh)."""
        self._reload()
        if self._access_is_fresh() and not force:
            return
        refresh_token = self._token("refresh_token")
        info = _jwt_times(refresh_token) if refresh_token else None
        if not info or info.get("exp", 0) <= time.time():
            raise NeedsBrowserLogin("Sessao expirou (mais de 7 dias parada). Corre: osmbot login")
        if not self.client_file.exists():
            raise NeedsBrowserLogin(
                "Faltam os codigos do cliente. Corre 'osmbot dashboard' e espera uns 30s "
                "depois de 20 min da ultima vez (o site renova e o bot apanha-os)."
            )
        codes = json.loads(self.client_file.read_text(encoding="utf-8"))
        body = urllib.parse.urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": codes["client_id"],
                "client_secret": codes["client_secret"],
                "refresh_token": refresh_token,
            }
        ).encode()
        request = urllib.request.Request(
            REFRESH_URL,
            data=body,
            method="POST",
            headers={
                **codes.get("headers", {}),  # app version etc., as the site sends them
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            },
        )
        status, raw = self._transport(request)
        if status == 400 and b"AppVersion" in raw:
            raise NeedsBrowserLogin(
                "O jogo atualizou e o bot ficou com a versao antiga. Corre 'osmbot dashboard', "
                "espera uns 30s e fecha a janela (o bot apanha a versao nova)."
            )
        if status != 200:
            raise NeedsBrowserLogin(f"Renovacao recusada (estado {status}). Corre: osmbot login")
        data = json.loads(raw)
        for name in ("access_token", "refresh_token"):
            cookie = self._cookie(name)
            if cookie:
                cookie["value"] = data[name]
        save_private(self.state_file, self._state)

    def _site_headers(self) -> dict:
        """Headers the site itself sends (app version etc.), saved by the browser step."""
        if not self.client_file.exists():
            return {}
        return json.loads(self.client_file.read_text(encoding="utf-8")).get("headers", {})

    def request(self, method: str, path: str, form: dict | None = None) -> tuple[int, object]:
        """Send ``method`` to ``path`` (relative to /api/v1, or a full URL); returns (status, parsed JSON or text).

        Writes (PUT/POST) repeat the site's own headers and send a form-encoded body, as observed.
        """
        if not self._access_is_fresh():
            with self._lock:
                self.refresh()
        url = path if path.startswith("http") else f"{API_BASE}/{path.lstrip('/')}"
        data, headers = None, {}
        if method != "GET":
            headers = dict(self._site_headers())
            if form is not None:
                data = urllib.parse.urlencode(form).encode()
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=utf-8"
            else:
                data = b""
                headers["Content-Type"] = "application/json; charset=utf-8"
        for attempt in (1, 2):
            used = self._token("access_token")
            request = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={**headers, "Authorization": f"Bearer {used}"},
            )
            status, raw = self._transport(request)
            if status == 403 and attempt == 1 and self._club_missing(path):
                with self._lock:  # a club created after the token was issued: renew once so the token lists it
                    self._reload()
                    if self._token("access_token") == used:
                        self.refresh(force=True)
                continue
            if status == 401 and attempt == 1:
                with self._lock:  # token rejected despite looking fresh: renew once (unless another client just did)
                    self._reload()
                    if self._token("access_token") == used:
                        self.refresh(force=True)
                continue
            break
        if method == "GET" and (status >= 500 or status == 429):
            said = _excerpt(raw)
            raise GameUnavailable(f"o jogo respondeu {status} a {path.split('?')[0]}" + (f": {said}" if said else ""))
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, raw.decode("utf-8", "replace")

    def get(self, path: str) -> tuple[int, object]:
        return self.request("GET", path)

    def put(self, path: str) -> tuple[int, object]:
        return self.request("PUT", path)

    def post(self, path: str, form: dict) -> tuple[int, object]:
        return self.request("POST", path, form)

def run_probe(path: str, slot: str = "0") -> None:
    """Discovery: GET one path and print status plus the shape of the answer (field names and types, never values)."""
    from osmbot.game.browser import _shape

    try:
        client = OsmClient()
        if "{L}" in path or "{T}" in path:  # fill in the ids of one of the owner's teams
            _, account = client.get("user/accounts")
            team = ((account.get("teamSlots") or {}).get(slot) or {}).get("team")
            if not team:
                raise SystemExit(f"Slot {slot} vazio.")
            path = path.replace("{L}", str(team["leagueId"])).replace("{T}", str(team["id"]))
        status, body = client.get(path)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    print(f"GET {path} -> {status}")
    print(json.dumps(_shape(body, depth=4) if not isinstance(body, str) else "texto", indent=2, ensure_ascii=False))
