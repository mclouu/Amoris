"""Connexion MyAnimeList (OAuth2 + PKCE 'plain'). Aucune UI, aucun texte affiché :
les erreurs portent un code (MalAuthError.code) que l'interface traduira via i18n."""
import html
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from core import token_store

AUTH_URL = "https://myanimelist.net/v1/oauth2/authorize"
TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "mal_config.json"

_session = {}  # jeton d'accès : en mémoire uniquement


class MalAuthError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


def _load_config() -> dict:
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise MalAuthError("config_missing")
    if not cfg.get("client_id"):
        raise MalAuthError("config_missing")
    cfg.setdefault("redirect_port", 8765)
    return cfg


def _post_token(data: dict) -> dict:
    req = urllib.request.Request(TOKEN_URL, data=urllib.parse.urlencode(data).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            tokens = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise MalAuthError("auth_rejected", e.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, TimeoutError):
        raise MalAuthError("network_error")
    tokens["expires_at"] = time.time() + tokens.get("expires_in", 3600) - 60
    return tokens


def _remember(tokens: dict):
    _session["access_token"] = tokens["access_token"]
    _session["expires_at"] = tokens["expires_at"]
    # MAL révoque l'ancien refresh token à chaque renouvellement : on sauvegarde le nouveau tout de suite.
    token_store.save_refresh_token(tokens["refresh_token"])


def login(timeout: int = 180, page_text: str = ""):
    """Ouvre le navigateur et attend l'autorisation. Bloquant : à lancer dans un thread depuis l'UI.
    page_text = message affiché dans le navigateur à la fin (fourni, traduit, par l'UI)."""
    cfg = _load_config()
    redirect_uri = f"http://localhost:{cfg['redirect_port']}/callback"
    verifier = secrets.token_urlsafe(64)  # PKCE 'plain' : le challenge est identique au verifier
    state = secrets.token_urlsafe(16)
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.urlparse(self.path).query
            received.update({k: v[0] for k, v in urllib.parse.parse_qs(query).items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<html><body>{html.escape(page_text)}</body></html>".encode("utf-8"))

        def log_message(self, *args):
            pass

    try:
        server = HTTPServer(("127.0.0.1", cfg["redirect_port"]), Handler)
    except OSError:
        raise MalAuthError("port_in_use")
    server.timeout = 1

    params = {
        "response_type": "code",
        "client_id": cfg["client_id"],
        "state": state,
        "redirect_uri": redirect_uri,
        "code_challenge": verifier,
        "code_challenge_method": "plain",
    }
    webbrowser.open(f"{AUTH_URL}?{urllib.parse.urlencode(params)}")

    deadline = time.time() + timeout
    try:
        while time.time() < deadline and not ({"code", "error"} & received.keys()):
            server.handle_request()
    finally:
        server.server_close()

    if "error" in received:
        raise MalAuthError("auth_denied", received["error"])
    if "code" not in received:
        raise MalAuthError("auth_timeout")
    if received.get("state") != state:
        raise MalAuthError("auth_state_mismatch")

    tokens = _post_token({
        "client_id": cfg["client_id"],
        "grant_type": "authorization_code",
        "code": received["code"],
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    })
    _remember(tokens)


def get_access_token() -> str:
    """Jeton valide pour les requêtes API : renouvelé automatiquement si expiré."""
    if _session.get("access_token") and time.time() < _session["expires_at"]:
        return _session["access_token"]
    refresh_token = token_store.load_refresh_token()
    if not refresh_token:
        raise MalAuthError("not_logged_in")
    cfg = _load_config()
    try:
        tokens = _post_token({
            "client_id": cfg["client_id"],
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        })
    except MalAuthError as e:
        if e.code == "auth_rejected":
            logout()
            raise MalAuthError("auth_expired")
        raise
    _remember(tokens)
    return tokens["access_token"]

def invalidate_access_token():
    """Force un renouvellement du jeton au prochain appel (ex : réponse 401)."""
    _session.pop("access_token", None)


def is_logged_in() -> bool:
    return bool(_session.get("access_token") or token_store.load_refresh_token())


def logout():
    _session.clear()
    token_store.clear()