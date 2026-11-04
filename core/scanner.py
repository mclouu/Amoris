import json
from pathlib import Path
from core.parser import AnimeFilenameParser
import re


class LocalAnimeScanner:
    """Gère le scan du dossier d'animés et la persistance de la BDD JSON locale."""

    def __init__(self, target_path: str, cache_file: str = "cache/anime_db_local.json",
                 mal_db_file: str = "cache/anime_db_mal.json"):
        self.target_path = Path(target_path)
        self.cache_file = Path(cache_file)
        self.mal_db_file = Path(mal_db_file)
        self.mal_mapping = self._load_mal_mapping()
        self.database = {}

    def _load_mal_mapping(self) -> dict:
        """Charge une table de correspondance {titre_normalise: mal_id} depuis le cache MAL."""
        mapping = {}
        if self.mal_db_file.exists():
            try:
                with open(self.mal_db_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    for item in content.get("data", []):
                        node = item.get("node", {})
                        mal_id = node.get("id")

                        titles = [node.get("title", "")]
                        alt_titles = node.get("alternative_titles", {})
                        if alt_titles.get("en"):
                            titles.append(alt_titles.get("en"))
                        if alt_titles.get("ja"):
                            titles.append(alt_titles.get("ja"))
                        for syn in alt_titles.get("synonyms", []):
                            titles.append(syn)

                        for t in titles:
                            if t:
                                # Normalisation extrême (garde uniquement les lettres et chiffres en minuscules)
                                clean_t = re.sub(r'[^a-z0-9]', '', t.lower())
                                if clean_t:
                                    mapping[clean_t] = mal_id
            except Exception as e:
                print(f"[-] Erreur lors du chargement du mapping MAL: {e}")
        return mapping

    def _find_mal_id(self, anime_name: str) -> int | None:
        """Tente de trouver le mal_id correspondant au nom d'animé parsé de manière sécurisée."""
        clean_name = re.sub(r'[^a-z0-9]', '', anime_name.lower())

        if not clean_name or len(clean_name) < 2:
            return None

        # 1. Correspondance exacte prioritaire sur le slug
        if clean_name in self.mal_mapping:
            return self.mal_mapping[clean_name]

        # 2. Recherche par inclusion STRICTE uniquement si le nom est assez long (ex: > 4 caractères)
        for title, mal_id in self.mal_mapping.items():
            if len(clean_name) >= 4 and (title == clean_name or title in clean_name or clean_name in title):
                if abs(len(title) - len(clean_name)) < 15:
                    return mal_id

        return None

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

                # Récupération du chemin complet sous forme de chaîne pour analyser les dossiers parents
                full_path_str = str(file_path).lower()

                # 🛑 FILTRE ANTI FAN-KAI
                # Ignore les fichiers ou dossiers contenant "fan-kai" ou "fankai"
                if "fan-kai" in full_path_str or "fankai" in full_path_str:
                    continue

                anime, season, episode = AnimeFilenameParser.parser.parse(filename) if hasattr(AnimeFilenameParser,
                                                                                               'parser') else AnimeFilenameParser.parse(
                    filename)

                # Initialisation de l'œuvre
                if anime not in temp_db:
                    temp_db[anime] = {}

                # Initialisation de la saison avec l'ID MAL détecté automatiquement
                if season not in temp_db[anime]:
                    detected_mal_id = self._find_mal_id(anime)

                    temp_db[anime][season] = {
                        "mal_id": detected_mal_id,
                        "folder_path": str(file_path.parent.resolve()),
                        "episodes": []
                    }

                # Ajout de l'épisode
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