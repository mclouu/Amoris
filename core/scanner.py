import json
from pathlib import Path
from core.parser import AnimeFilenameParser


class LocalAnimeScanner:
    """Gère le scan du dossier d'animés et la persistance de la BDD JSON locale."""

    def __init__(self, target_path: str, cache_file: str = "cache/anime_db.json"):
        self.target_path = Path(target_path)
        self.cache_file = Path(cache_file)
        self.database = {}

    def scan(self):
        """Parcourt le dossier cible et construit l'arborescence."""
        if not self.target_path.exists():
            print(f"[-] Erreur : Le chemin {self.target_path} n'existe pas.")
            return False

        print(f"[*] Début du scan de : {self.target_path}")

        valid_extensions = {".mkv", ".mp4"}
        temp_db = {}

        for file_path in self.target_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                filename = file_path.name

                anime, season, episode = AnimeFilenameParser.parse(filename)

                # Initialisation de l'œuvre
                if anime not in temp_db:
                    temp_db[anime] = {}

                # Initialisation de la saison avec l'ID MAL, le chemin du dossier et la liste d'épisodes
                if season not in temp_db[anime]:
                    temp_db[anime][season] = {
                        "mal_id": None,
                        "folder_path": str(file_path.parent.resolve()),  # Le path du dossier de la saison
                        "episodes": []
                    }

                # Ajout de l'épisode (plus besoin de stocker le path ou filename unitaire)
                ep_data = {"episode": episode}
                if ep_data not in temp_db[anime][season]["episodes"]:
                    temp_db[anime][season]["episodes"].append(ep_data)

        # Trier les épisodes par numéro pour chaque saison
        for anime in temp_db:
            for season in temp_db[anime]:
                temp_db[anime][season]["episodes"].sort(key=lambda x: x["episode"])

        self.database = temp_db
        print("[*] Scan terminé avec succès.")
        return True

    def save_cache(self):
        """Sauvegarde la structure dans un fichier JSON local."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.database, f, ensure_ascii=False, indent=4)
        print(f"[*] BDD JSON générée avec succès dans : {self.cache_file.resolve()}")