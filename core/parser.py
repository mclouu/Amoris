import re


class AnimeFilenameParser:
    """Parse les noms de fichiers pour en extraire l'œuvre, la saison et l'épisode."""

    @staticmethod
    def parse(filename: str):
        # Nettoyage de l'extension
        clean_name = re.sub(r"\.(mkv|mp4|nfo|cue|flac|ass)$", "", filename, flags=re.IGNORECASE)

        # 1. Pattern type SxxExx (ex: Goblin Slayer S01E01 ou Ave Mujica - The Die is Cast S01E01)
        s_e_match = re.search(r"(.*?)\bS(\d+)(?:E|EP)(\d+)", clean_name, re.IGNORECASE)
        if s_e_match:
            anime_title = s_e_match.group(1).strip(" -_")
            season = f"Saison {int(s_e_match.group(2))}"
            episode = int(s_e_match.group(3))
            return anime_title, season, episode

        # 2. Pattern Erai-raws ou similaire avec tiret (ex: [Erai-raws] Bang Dream Yumemita - 01)
        erai_match = re.search(r"\[.*?]\s*(.*?)\s*-\s*(\d+)", clean_name)
        if erai_match:
            anime_title = erai_match.group(1).strip()
            season = "Saison 1"  # Par défaut si non spécifié
            episode = int(erai_match.group(2))
            return anime_title, season, episode

        # Fallback générique si aucun pattern strict n'est reconnu
        return clean_name, "Saison 1", 1