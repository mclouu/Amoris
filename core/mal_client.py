"""Requêtes vers l'API officielle MAL. Aucune UI : les erreurs portent un code (MalApiError.code)."""
import json
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from core import mal_auth

API = "https://api.myanimelist.net/v2"
CACHE_PATH = Path(__file__).resolve().parent.parent / "cache" / "anime_db_mal.json"

# Mêmes champs que ta requête Postman, pour garder le format de ton cache.
LIST_FIELDS = (
    "alternative_titles,num_episodes,start_season,mean,media_type,start_date,finish_date,"
    "list_status{status,score,num_episodes_watched,is_rewatching,num_times_rewatched,"
    "comments,start_date,finish_date,updated_at}"
)

_HTTP_CODES = {400: "bad_request", 403: "forbidden", 404: "not_found", 429: "rate_limited"}


class MalApiError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


def _request(method: str, url: str, form: dict | None = None, _retry: bool = True) -> dict:
    token = mal_auth.get_access_token()  # peut lever MalAuthError (not_logged_in, auth_expired...)
    data = urllib.parse.urlencode(form).encode() if form else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "Amoris/0.1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401 and _retry:
            mal_auth.invalidate_access_token()
            return _request(method, url, form, _retry=False)
        detail = e.read().decode("utf-8", "replace")
        raise MalApiError("auth_expired" if e.code == 401 else _HTTP_CODES.get(e.code, "api_error"), detail)
    except (urllib.error.URLError, TimeoutError):
        raise MalApiError("network_error")


def get_profile() -> dict:
    return _request("GET", f"{API}/users/@me")


def fetch_my_list() -> list:
    """Récupère toute la liste (pagination incluse). Ne modifie aucun fichier."""
    query = f"fields={urllib.parse.quote(LIST_FIELDS, safe=',{}')}&limit=1000"
    url = f"{API}/users/@me/animelist?{query}"
    items = []
    while url:
        page = _request("GET", url)
        items.extend(page.get("data", []))
        url = page.get("paging", {}).get("next")
    return items


def save_list_cache(items: list):
    """Écrit cache/anime_db_mal.json (format {"data": [...]}) de façon sûre, avec une copie .bak."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"data": items}, ensure_ascii=False), encoding="utf-8")
    if CACHE_PATH.exists():
        shutil.copy2(CACHE_PATH, CACHE_PATH.with_suffix(".json.bak"))
    os.replace(tmp, CACHE_PATH)


def refresh_list_cache() -> int:
    """Télécharge la liste et met à jour le cache. Retourne le nombre d'entrées."""
    items = fetch_my_list()
    if not items:
        raise MalApiError("empty_list")  # on ne remplace jamais ton cache par du vide
    save_list_cache(items)
    return len(items)


def update_episodes(anime_id: int, watched: int, status: str | None = None, score: int | None = None) -> dict:
    """Met à jour la progression d'un animé sur ton compte MAL (PATCH)."""
    form = {"num_watched_episodes": watched}
    if status:
        form["status"] = status  # watching / completed / on_hold / dropped / plan_to_watch
    if score is not None:
        form["score"] = score
    return _request("PATCH", f"{API}/anime/{anime_id}/my_list_status", form)