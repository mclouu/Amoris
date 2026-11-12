import json
from pathlib import Path


class CacheRepository:
    """Gère le chargement et la sauvegarde des caches MAL et locaux."""

    def __init__(self, local_cache_path: str = "cache/anime_db_local.json", mal_db_path: str = "cache/anime_db_mal.json"):
        self.local_cache_path = Path(local_cache_path)
        self.mal_db_path = Path(mal_db_path)

    def load_local_cache(self) -> dict:
        if self.local_cache_path.exists():
            try:
                with open(self.local_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[-] Erreur chargement cache local : {e}")
        return {}

    def save_local_cache(self, data: dict):
        self.local_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.local_cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_mal_database(self) -> dict | list:
        if self.mal_db_path.exists():
            try:
                with open(self.mal_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[-] Erreur chargement base MAL : {e}")
        return {}

    def get_local_episodes_count(self, local_cache_data: dict, anime_title: str, anime_mal_id: int = None) -> int:
        """Récupère le nombre d'épisodes locaux en cherchant par mal_id ou par titre dans la structure plate."""
        if not local_cache_data:
            return 0

        matched_entry = None

        # 1. Recherche par mal_id
        if anime_mal_id:
            str_id = str(anime_mal_id)
            if str_id in local_cache_data:
                matched_entry = local_cache_data[str_id]
            else:
                for entry in local_cache_data.values():
                    if isinstance(entry, dict) and entry.get("mal_id") == anime_mal_id:
                        matched_entry = entry
                        break

        # 2. Repli textuel
        if not matched_entry and anime_title:
            for entry in local_cache_data.values():
                if isinstance(entry, dict) and entry.get("title", "").lower() == anime_title.lower():
                    matched_entry = entry
                    break

        if not matched_entry or not isinstance(matched_entry, dict):
            return 0

        episodes = matched_entry.get("episodes", [])
        return len(episodes)