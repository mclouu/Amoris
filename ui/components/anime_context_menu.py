from pathlib import Path
import os
from PyQt6.QtWidgets import QMenu, QFileDialog
from PyQt6.QtCore import QPoint
from ui.colors import Colors
from utils.translator import tr


class AnimeContextMenu:
    """Gère le menu contextuel et les actions associées pour un animé."""

    def __init__(self, parent_widget, anime_title: str, anime_mal_id: int, local_cache_data: dict, save_cache_callback):
        self.parent = parent_widget
        self.anime_title = anime_title
        self.anime_mal_id = anime_mal_id
        self.local_cache_data = local_cache_data
        self.save_cache_callback = save_cache_callback

    def exec(self, global_pos: QPoint):
        """Affiche le menu contextuel à la position globale donnée."""
        menu = QMenu(self.parent)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.BG_DARKER};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 28px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.ACCENT_BLUE};
                border-radius: 3px;
            }}
        """)

        # Utilisation de la traduction
        open_folder_action = menu.addAction(tr.get("menu_open_folder"))
        open_folder_action.triggered.connect(self._open_anime_folder)

        menu.exec(global_pos)

    def _open_anime_folder(self):
        """Ouvre le dossier local de l'animé ou demande à l'utilisateur de le définir s'il est introuvable."""
        folder_path_str = None

        if self.local_cache_data:
            matched_entry = None
            if self.anime_mal_id:
                for local_name, seasons in self.local_cache_data.items():
                    if isinstance(seasons, dict):
                        for s_name, s_data in seasons.items():
                            if isinstance(s_data, dict) and s_data.get("mal_id") == self.anime_mal_id:
                                matched_entry = s_data
                                break
                    if matched_entry:
                        break

            if not matched_entry and self.anime_title in self.local_cache_data:
                seasons = self.local_cache_data[self.anime_title]
                if isinstance(seasons, dict) and seasons:
                    matched_entry = list(seasons.values())[0]

            if matched_entry and isinstance(matched_entry, dict):
                folder_path_str = matched_entry.get("folder_path")

        target_dir = Path(folder_path_str) if folder_path_str else None

        if target_dir and target_dir.exists():
            os.startfile(str(target_dir))
        else:
            base_path = str(Path(__file__).resolve().parent.parent.parent / "Vidéos" / "Animé")

            # Utilisation de la traduction avec formatage du titre
            dialog_title = tr.get("dialog_select_folder", anime_title=self.anime_title)
            selected_dir = QFileDialog.getExistingDirectory(
                self.parent,
                dialog_title,
                base_path
            )

            if selected_dir:
                if self.anime_title not in self.local_cache_data:
                    self.local_cache_data[self.anime_title] = {}

                existing_seasons = list(self.local_cache_data[self.anime_title].keys())
                target_season_key = existing_seasons[0] if existing_seasons else "Saison 1"

                if target_season_key not in self.local_cache_data[self.anime_title]:
                    self.local_cache_data[self.anime_title][target_season_key] = {
                        "mal_id": self.anime_mal_id,
                        "folder_path": selected_dir,
                        "episodes": []
                    }
                else:
                    self.local_cache_data[self.anime_title][target_season_key]["folder_path"] = selected_dir
                    if self.anime_mal_id:
                        self.local_cache_data[self.anime_title][target_season_key]["mal_id"] = self.anime_mal_id

                if self.save_cache_callback:
                    self.save_cache_callback()

                os.startfile(selected_dir)