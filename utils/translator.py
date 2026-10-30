import json
from pathlib import Path


class Translator:
    def __init__(self, default_lang="fr"):
        self.current_lang = default_lang
        self.translations = {}
        self.load_languages()

    def load_languages(self):
        # On remonte d'un cran depuis utils/ pour trouver le dossier i18n à la racine
        i18n_dir = Path(__file__).resolve().parent.parent / "i18n"
        for lang_file in i18n_dir.glob("*.json"):
            lang_code = lang_file.stem  # "fr" ou "en"
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations[lang_code] = json.load(f)

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.current_lang = lang_code

    def get(self, key, **kwargs):
        """Récupère la traduction et gère l'injection de variables (ex: {count})"""
        lang_dict = self.translations.get(self.current_lang, {})
        text = lang_dict.get(key, key)  # Renvoie la clé elle-même si non trouvée

        # Si on passe des arguments (comme count=5), on les formate
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text


# Instance globale unique qu'on pourra importer partout
tr = Translator("fr")