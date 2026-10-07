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

import json
import os
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


def _http(request: urllib.request.Request) -> tuple[int, bytes]:
    """Default transport; tests replace it. Returns (status, body) without raising on 4xx/5xx."""
    try:
        # certifi's CA bundle: some Pythons (e.g. Homebrew on macOS) ship without one
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(request, timeout=30, context=context) as response:
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
            request = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={**headers, "Authorization": f"Bearer {self._token('access_token')}"},
            )
            status, raw = self._transport(request)
            if status == 401 and attempt == 1:
                self.refresh(force=True)  # token rejected despite looking fresh: renew once and retry
                continue
            break
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
