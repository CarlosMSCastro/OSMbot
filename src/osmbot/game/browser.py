"""Real browser session for OSM, saved between runs.

The session cookies are exported to a file under the owner's home directory
(never inside the repo, never committed) and loaded again on the next run. A
plain persistent Firefox profile was not enough: OSM's ``access_token`` and
``refresh_token`` are session cookies (no expiry date), which Firefox drops
when it closes, so the login was lost. Only cookies are saved: no localStorage
was observed, and Playwright's ``storage_state()`` opens temporary windows that
break the Facebook login popup. No credentials are ever read,
typed, or stored by this code - the owner logs in by hand in the window this
opens.
"""
from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

STATE_FILE = Path.home() / ".osmbot" / "session.json"
LOGIN_URL = "https://www.onlinesoccermanager.com/"
HOME_URL = "https://en.onlinesoccermanager.com/"


def _capture_client_codes(request) -> None:
    """Keep the OAuth codes the site sends when renewing tokens (owner-only file, never printed).

    The browserless client needs them to renew the session on its own.
    """
    try:
        if not request.url.split("?")[0].endswith("/api/tokenRefresh"):
            return
        form = parse_qs(request.post_data or "")
        codes = {k: form[k][0] for k in ("client_id", "client_secret") if k in form}
        if len(codes) == 2:
            from osmbot.game.client import CLIENT_FILE, save_private

            save_private(CLIENT_FILE, codes)
    except Exception:
        pass  # never let a bad event break the session


def _run_session(
    state_file: Path, url: str, message: str, interval: float = 3.0, on_context=None
) -> None:
    """Open a visible Firefox with the saved session; save it back when the window closes.

    Needs no keyboard input (works under ``!`` in Claude Code): the owner just
    closes the window. The state is only overwritten if the session still holds
    OSM tokens, so closing a logged-out window never wipes a good session.
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state = None
    caller_hook = on_context

    def on_context(context) -> None:
        context.on("request", _capture_client_codes)
        if caller_hook:
            caller_hook(context)

    with sync_playwright() as playwright:
        # Firefox, not Chromium: Facebook's login popup blocks Playwright's
        # "Chrome for Testing" build outright, even for a real manual login.
        browser = playwright.firefox.launch(headless=False)
        try:
            context = browser.new_context(
                storage_state=str(state_file) if state_file.exists() else None
            )
            if on_context:
                on_context(context)
            page = context.new_page()
            page.goto(url)
            print(message, flush=True)
            while browser.is_connected() and context.pages:
                try:
                    # cookies() only: storage_state() opens temporary windows to
                    # read localStorage, which breaks the Facebook login popup.
                    cookies = context.cookies()
                    if any(c["name"] == "access_token" for c in cookies):
                        state = {"cookies": cookies, "origins": []}
                except Exception:
                    pass  # page navigating or closing; keep the previous snapshot
                try:
                    page.wait_for_timeout(interval * 1000)  # also delivers events
                except Exception:
                    time.sleep(interval)
        finally:
            try:
                browser.close()
            except Exception:
                pass
    if state is None:
        print("Sem sessao do OSM detetada; nada foi guardado.")
        return
    state_file.write_text(json.dumps(state), encoding="utf-8")
    state_file.chmod(0o600)  # holds live session cookies: owner-only
    print(f"Sessao guardada em {state_file}")


def open_login_session(state_file: Path = STATE_FILE, url: str = LOGIN_URL) -> None:
    """Open a real browser window for the owner to log into OSM, then save the session."""
    _run_session(
        state_file,
        url,
        "Faz login e espera ate estares dentro do jogo. Depois FECHA a janela.",
    )


def open_dashboard(state_file: Path = STATE_FILE, url: str = HOME_URL) -> None:
    """Open the saved session on the club/team area, for the owner to look at.

    Discovery step: we don't yet know the page's structure (rule 7, CLAUDE.md -
    never guess it), so this just shows it to the owner instead of scraping.
    """
    if not state_file.exists():
        raise SystemExit("Sem sessao guardada. Corre primeiro: osmbot login")
    _run_session(state_file, url, "Ve o que aparece. Quando quiseres, FECHA a janela.")


def _snapshot(context) -> str:
    """Names/domains/expiry/value lengths of cookies and web storage. Never values."""
    lines = ["== Cookies (nome | dominio | expira | tamanho) =="]
    now = time.time()
    for c in context.cookies():
        exp = c["expires"]
        when = "sessao" if exp == -1 else f"{(exp - now) / 3600:.1f}h"
        lines.append(f"{c['name']} | {c['domain']} | {when} | {len(c['value'])}")
    for p in context.pages:
        if "onlinesoccermanager" not in p.url:
            continue
        for kind in ("localStorage", "sessionStorage"):
            items = p.evaluate(f"Object.entries({kind}).map(([k, v]) => [k, v.length])")
            lines.append(f"\n== {kind} em {p.url} (chave | tamanho) ==")
            lines.extend(f"{key} | {size}" for key, size in items)
    return "\n".join(lines)


def inspect_session(url: str = LOGIN_URL, interval: float = 3.0) -> None:
    """Discovery: after a manual login, print WHERE the session is stored.

    Needs no keyboard input: it snapshots every ``interval`` seconds while the
    window is open and prints the last snapshot once the owner closes the
    window. Prints only names, domains, expiry and value lengths - never
    values - and writes nothing to disk. Fresh context, nothing saved is loaded.
    """
    last = "(sem dados: a janela fechou antes da primeira leitura)"
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=False)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(url)
            print(
                "Faz login, clica em 'Continuar como ...' e espera ate estares "
                "dentro do jogo. Depois FECHA a janela do Firefox.",
                flush=True,
            )
            while browser.is_connected() and context.pages:
                try:
                    last = _snapshot(context)
                except Exception:
                    pass  # page navigating or closing; keep the previous snapshot
                time.sleep(interval)
        finally:
            try:
                browser.close()
            except Exception:
                pass
    print("\n" + last)


def _jwt_times(token: str) -> dict | None:
    """exp/iat/nbf and claim NAMES of a JWT-shaped token; None if it is not one.

    Reads the (unsigned, readable) payload only; claim values other than the
    timestamps are never returned.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    return {
        "claims": sorted(payload),
        **{k: payload[k] for k in ("iat", "nbf", "exp") if isinstance(payload.get(k), (int, float))},
    }


def token_info(state_file: Path = STATE_FILE) -> None:
    """Print token lifetimes from the saved session. Local only: no network, no values."""
    if not state_file.exists():
        raise SystemExit("Sem sessao guardada. Corre primeiro: osmbot login")
    cookies = json.loads(state_file.read_text(encoding="utf-8"))["cookies"]
    now = time.time()
    for name in ("access_token", "refresh_token", "session"):
        for c in (c for c in cookies if c["name"] == name):
            info = _jwt_times(c["value"])
            print(f"== {name} ({c['domain']}) ==")
            if info is None:
                print("  nao tem formato JWT (opaco): validade nao legivel")
                continue
            print(f"  campos: {', '.join(info['claims'])}")
            for key in ("iat", "nbf", "exp"):
                if key in info:
                    when = datetime.fromtimestamp(info[key], timezone.utc).astimezone()
                    print(f"  {key}: {when:%Y-%m-%d %H:%M:%S} ({(info[key] - now) / 3600:+.2f}h)")
            if "iat" in info and "exp" in info:
                print(f"  duracao total: {(info['exp'] - info['iat']) / 3600:.2f}h")


_OSM_HOSTS = ("onlinesoccermanager.com", "osm.cloud")
_TOKEN_COOKIES = ("access_token", "refresh_token")


def _shape(value, depth: int = 3):
    """Structure of parsed JSON with values replaced by type names (never values)."""
    if isinstance(value, dict):
        return {k: _shape(v, depth - 1) if depth > 0 else "..." for k, v in value.items()}
    if isinstance(value, list):
        return [f"{len(value)} items", _shape(value[0], depth - 1)] if value and depth > 0 else []
    return type(value).__name__


def _body_shape(text: str, content_type: str):
    """Field names of a JSON or form-encoded body, no values; None if unreadable."""
    try:
        if "json" in content_type or text.lstrip().startswith(("{", "[")):
            return _shape(json.loads(text))
        return {k: "str" for k in parse_qs(text, keep_blank_values=True)}
    except ValueError:
        return None


def inspect_network(state_file: Path = STATE_FILE, url: str = HOME_URL) -> None:
    """Discovery: list the requests OSM's own site makes while the owner uses it.

    Records only method, URL without query string and status code, plus a flag
    when a request body mentions ``refresh_token`` or a response sets one of the
    token cookies (by name, never value). Headers and bodies are not kept;
    nothing is written except the session refresh that ``_run_session`` does.
    """
    if not state_file.exists():
        raise SystemExit("Sem sessao guardada. Corre primeiro: osmbot login")
    seen: dict[tuple[str, str, int], list[str]] = {}
    others: set[str] = set()
    refresh_shapes: list[str] = []

    def on_response(response) -> None:
        try:
            request = response.request
            host = urlsplit(response.url).hostname or ""
            if not host.endswith(_OSM_HOSTS):
                others.add(host)
                return
            flags = []
            if "refresh_token" in (request.post_data or ""):
                flags.append("BODY:refresh_token")
            set_cookie = response.headers.get("set-cookie", "")
            flags += [f"SET-COOKIE:{n}" for n in _TOKEN_COOKIES if f"{n}=" in set_cookie]
            if response.url.split("?")[0].endswith("/api/tokenRefresh"):
                req_type = request.headers.get("content-type", "?")
                res_type = response.headers.get("content-type", "?")
                refresh_shapes.append(
                    f"pedido  [{req_type}]: {_body_shape(request.post_data or '', req_type)}\n"
                    f"resposta [{res_type}] {response.status}: "
                    f"{_body_shape(response.text(), res_type)}"
                )
            key = (request.method, response.url.split("?")[0], response.status)
            known = seen.setdefault(key, [])
            known += [f for f in flags if f not in known]
        except Exception:
            pass  # never let a bad event break the session

    _run_session(
        state_file,
        url,
        "Usa o jogo normalmente durante ~30s (abre o plantel, etc.). Depois FECHA a janela.",
        on_context=lambda context: context.on("response", on_response),
    )
    print("\n== tokenRefresh: estrutura (so nomes de campos e tipos) ==")
    print("\n".join(refresh_shapes) or "(nenhuma renovacao observada: o access_token ainda era valido)")
    print("\n== Pedidos a web-api (metodo | endereco sem query | estado | marcas) ==")
    for (method, address, status), flags in sorted(seen.items(), key=lambda kv: kv[0][1]):
        if urlsplit(address).hostname == "web-api.onlinesoccermanager.com":
            print(f"{method} | {address} | {status} | {' '.join(flags)}")
    print(f"\n(+ {len(others)} hosts de terceiros ignorados: anuncios/analytics)")
