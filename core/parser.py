import re


class AnimeFilenameParser:
    """Parse les noms de fichiers pour en extraire l'œuvre, la saison et l'épisode."""

    @staticmethod
    def parse(filename: str):
        # Nettoyage de l'extension
        clean_name = re.sub(r"\.(mkv|mp4|nfo|cue|flac|ass)$", "", filename, flags=re.IGNORECASE)

        # 1. Pattern type SxxExx (ex: Goblin Slayer S01E01 ou The.Rising.Of.The.Shield.Hero.S01E01)
        s_e_match = re.search(r"(.*?)\bS(\d+)(?:E|EP)(\d+)", clean_name, re.IGNORECASE)
        if s_e_match:
            raw_title = s_e_match.group(1)
            # Si le nom est bourré de points (ex: The.Rising.Of.The.Shield.Hero.), on remplace par des espaces
            anime_title = raw_title.replace(".", " ").replace("_", " ").strip(" -_")
            # Nettoyage des espaces multiples
            anime_title = re.sub(r'\s+', ' ', anime_title)

            season = f"Saison {int(s_e_match.group(2))}"
            episode = int(s_e_match.group(3))
            return anime_title, season, episode

        # 2. Pattern Erai-raws ou similaire avec tiret (ex: [Erai-raws] Bang Dream Yumemita - 01)
        erai_match = re.search(r"\[.*?]\s*(.*?)\s*-\s*(\d+)", clean_name)
        if erai_match:
            raw_title = erai_match.group(1)
            anime_title = raw_title.replace(".", " ").replace("_", " ").strip()
            anime_title = re.sub(r'\s+', ' ', anime_title)
            season = "Saison 1"
            episode = int(erai_match.group(2))
            return anime_title, season, episode

        # Fallback générique
        clean_title = clean_name.replace(".", " ").replace("_", " ").strip(" -_")
        clean_title = re.sub(r'\s+', ' ', clean_title)
        return clean_title, "Saison 1", 1