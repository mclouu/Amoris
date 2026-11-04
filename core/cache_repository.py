import json
from pathlib import Path


class CacheRepository:
    """Gère la persistance, le chargement et les requêtes sur les caches MAL et local."""

    def __init__(self):
        # Résout la racine du projet (en remontant de core/ vers la racine)
        base_path = Path(__file__).resolve().parent.parent
        self.mal_db_path = base_path / "cache" / "anime_db_mal.json"
        self.local_cache_path = base_path / "cache" / "anime_db_local.json"

    def load_mal_database(self) -> list:
        """Charge la base de données MAL depuis le cache local (anime_db_mal.json)."""
        try:
            if self.mal_db_path.exists():
                with open(self.mal_db_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    return content.get("data", [])
        except Exception as e:
            print(f"[MAL WARNING] Impossible de charger le fichier MAL anime_db_mal.json: {e}")
        return []

    def load_local_cache(self) -> dict:
        """Charge le cache local des épisodes (anime_db_local.json)."""
        try:
            if self.local_cache_path.exists():
                with open(self.local_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[CACHE WARNING] Impossible de charger le cache local anime_db_local.json: {e}")
        return {}

    def save_local_cache(self, local_cache_data: dict):
        """Sauvegarde les modifications dans anime_db_local.json."""
        try:
            self.local_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.local_cache_path, "w", encoding="utf-8") as f:
                json.dump(local_cache_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[CACHE ERROR] Impossible de sauvegarder le cache local: {e}")

    def get_local_episodes_count(self, local_cache_data: dict, anime_title: str, anime_mal_id: int = None) -> int:
        """Récupère le nombre d'épisodes locaux en cherchant d'abord par mal_id, puis par correspondance de titre."""
        if not local_cache_data:
            return 0

        matched_entry = None

        # 1. Recherche prioritaire par mal_id
        if anime_mal_id:
            for local_anime_name, seasons in local_cache_data.items():
                if isinstance(seasons, dict):
                    for season_name, season_data in seasons.items():
                        if isinstance(season_data, dict) and season_data.get("mal_id") == anime_mal_id:
                            matched_entry = {season_name: season_data}
                            break
                if matched_entry:
                    break

        # 2. Solution de repli : recherche textuelle
        if not matched_entry and anime_title:
            if anime_title in local_cache_data:
                matched_entry = local_cache_data[anime_title]
            else:
                for key in local_cache_data:
                    if (
                            key.lower() in anime_title.lower()
                            or anime_title.lower() in key.lower()
                    ):
                        matched_entry = local_cache_data[key]
                        break

        if not matched_entry:
            return 0

        total_local = 0
        for season_name, season_data in matched_entry.items():
            if isinstance(season_data, dict) and "episodes" in season_data:
                total_local += len(season_data["episodes"])

        return total_local