import json
from pathlib import Path
from core.normalizer import parse, is_fankai, normalize_key


class LocalAnimeScanner:
    """Gère le scan du dossier d'animés et la persistance de la BDD JSON locale par ID MAL."""

    def __init__(self, target_path: str, cache_file: str = "cache/anime_db_local.json",
                 mal_db_file: str = "cache/anime_db_mal.json"):
        self.target_path = Path(target_path)
        self.cache_file = Path(cache_file)
        self.mal_db_file = Path(mal_db_file)
        self.mal_mapping = self._load_mal_mapping()
        self.database = {}

    def _load_mal_mapping(self) -> dict:
        """Charge l'index des titres MAL pour lier un titre normalisé à son ID unique."""
        mapping = {}
        if self.mal_db_file.exists():
            try:
                with open(self.mal_db_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    for item in content.get("data", []):
                        node = item.get("node", {})
                        mal_id = node.get("id")
                        alt = node.get("alternative_titles", {}) or {}
                        titles = [node.get("title"), alt.get("en"), alt.get("ja"), *(alt.get("synonyms") or [])]

                        for t in titles:
                            if t:
                                k = normalize_key(t)
                                if len(k) >= 3 and k not in mapping:
                                    mapping[k] = mal_id
            except Exception as e:
                print(f"[-] Erreur lors du chargement du mapping MAL: {e}")
        return mapping

    def _find_mal_id(self, parsed_obj) -> int | None:
        """Cherche le MAL ID correspondant aux variantes de titres du fichier parsé."""
        for v in parsed_obj.title_variants():
            k = normalize_key(v)
            if k in self.mal_mapping:
                return self.mal_mapping[k]
        return None

    def scan(self):
        if not self.target_path.exists():
            print(f"[-] Erreur : Le chemin {self.target_path} n'existe pas.")
            return False

        print(f"[*] Début du scan intelligent de : {self.target_path}")

        valid_extensions = {".mkv", ".mp4", ".avi", ".m4v"}
        temp_db = {}

        for file_path in self.target_path.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in valid_extensions:
                continue

            # Ignore les contenus spécifiques (type Fan-Kai, etc.)
            if is_fankai(str(file_path)):
                continue

            p = parse(file_path.name, folder_name=file_path.parent.name)
            if p.ignored:
                continue

            mal_id = self._find_mal_id(p)

            # Clé unique : Priorité au MAL ID, sinon repli sur le titre propre de la saison
            entry_key = str(mal_id) if mal_id else f"unmatched_{p.title_with_season or p.title}"

            if entry_key not in temp_db:
                temp_db[entry_key] = {
                    "mal_id": mal_id,
                    "title": p.title_with_season or p.title,
                    "folder_path": str(file_path.parent.resolve()),
                    "episodes": []
                }

            # On enregistre l'épisode s'il est identifié (avec juste le nom du fichier pour optimiser)
            if p.episode is not None:
                ep_data = {
                    "episode": p.episode,
                    "kind": p.kind,  # 'episode' ou 'special'
                    "filename": file_path.name
                }
                # Évite les doublons stricts d'épisodes
                if ep_data not in temp_db[entry_key]["episodes"]:
                    temp_db[entry_key]["episodes"].append(ep_data)

        # Tri des épisodes par numéro pour chaque entrée
        for entry in temp_db.values():
            entry["episodes"].sort(key=lambda x: x["episode"])

        self.database = temp_db
        print("[*] Scan terminé avec succès.")
        return True

    def save_cache(self):
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.database, f, ensure_ascii=False, indent=4)
        print(f"[*] BDD JSON générée avec succès dans : {self.cache_file.resolve()}")