"""Browserless client for OSM's web API: reads the saved session and renews it.

Reads the cookies saved by ``browser.py`` (``~/.osmbot/session.json``), keeps the
``access_token`` fresh through ``POST /api/tokenRefresh`` (observed 2026-10-03,
see DISCOVERY.md) and writes the new tokens back. The two OAuth client codes the
renewal needs are captured from the site's own request by ``browser.py`` and kept
in ``~/.osmbot/client.json`` (owner-only, never in the repo).

Read-only: only GET requests are exposed. The ``Authorization: Bearer`` header
is a hypothesis until a probe returns 200 (CLAUDE.md rule 7).
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

    def _cookie(self, name: str) -> dict | None:
        return next((c for c in self._state["cookies"] if c["name"] == name), None)

    def _token(self, name: str) -> str | None:
        cookie = self._cookie(name)
        return cookie["value"] if cookie else None

    def _access_is_fresh(self) -> bool:
        token = self._token("access_token")
        info = _jwt_times(token) if token else None
        return bool(info and info.get("exp", 0) - time.time() > EXPIRY_MARGIN)

    def refresh(self) -> None:
        """Renew both tokens and save them. The old refresh_token stops working (hypothesis), so save at once."""
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
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
        )
        status, raw = self._transport(request)
        if status != 200:
            raise NeedsBrowserLogin(f"Renovacao recusada (estado {status}). Corre: osmbot login")
        data = json.loads(raw)
        for name in ("access_token", "refresh_token"):
            cookie = self._cookie(name)
            if cookie:
                cookie["value"] = data[name]
        save_private(self.state_file, self._state)

    def get(self, path: str) -> tuple[int, object]:
        """GET ``path`` (relative to /api/v1, or a full /api/... path); returns (status, parsed JSON or text)."""
        if not self._access_is_fresh():
            self.refresh()
        url = path if path.startswith("http") else f"{API_BASE}/{path.lstrip('/')}"
        for attempt in (1, 2):
            request = urllib.request.Request(
                url, headers={"Authorization": f"Bearer {self._token('access_token')}"}
            )
            status, raw = self._transport(request)
            if status == 401 and attempt == 1:
                self.refresh()  # token rejected despite looking fresh: renew once and retry
                continue
            break
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, raw.decode("utf-8", "replace")


def run_probe(path: str) -> None:
    """Discovery: GET one path and print status plus the shape of the answer (field names and types, never values)."""
    from osmbot.game.browser import _shape

    try:
        status, body = OsmClient().get(path)
    except NeedsBrowserLogin as error:
        raise SystemExit(str(error))
    print(f"GET {path} -> {status}")
    print(json.dumps(_shape(body, depth=4) if not isinstance(body, str) else "texto", indent=2, ensure_ascii=False))
