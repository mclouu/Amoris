from pathlib import Path
import os
import json
from PyQt6.QtWidgets import QMenu, QFileDialog, QInputDialog
from PyQt6.QtCore import QPoint
from ui.colors import Colors
from utils.translator import tr


class AnimeContextMenu:
    """Gère le menu contextuel et les actions associées pour un animé (basé strictement sur l'ID MAL)."""

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

        # 1. Action : Ouvrir le dossier
        open_folder_action = menu.addAction(tr.get("menu_open_folder"))
        open_folder_action.triggered.connect(self._open_anime_folder)

        # 2. Action : Définir l'ID MAL manuellement 🚀
        set_id_action = menu.addAction("Définir l'ID MAL manuellement")
        set_id_action.triggered.connect(self._set_mal_id_manually)

        menu.exec(global_pos)

    def _trigger_ui_refresh(self):
        """Force le rechargement de l'interface principale pour actualiser les barres de progression."""
        p = self.parent
        while p is not None:
            if hasattr(p, "reload_local_data"):
                p.reload_local_data()
                break
            p = p.parent()

    def _set_mal_id_manually(self):
        """Associe ou migre l'entrée locale en se basant strictement sur le nouvel ID MAL fourni."""
        mal_id, ok = QInputDialog.getInt(
            self.parent,
            "Association d'ID MAL",
            f"Entrez l'ID MAL pour '{self.anime_title}' :",
            value=self.anime_mal_id if self.anime_mal_id else 0,
            min=1,
            max=999999
        )
        if not ok:
            return

        # Récupération du titre MAL officiel pour l'affichage
        root_dir = next((p for p in Path(__file__).resolve().parents if p.name == 'Amoris'), None)
        mal_db_path = root_dir / "cache" / "anime_db_mal.json" if root_dir else Path("cache/anime_db_mal.json")

        mal_title = self.anime_title
        if mal_db_path.exists():
            try:
                with open(mal_db_path, "r", encoding="utf-8") as f:
                    mal_data = json.load(f)
                    items = mal_data.get("data", []) if isinstance(mal_data, dict) else mal_data
                    for item in items:
                        node = item.get("node", {})
                        if node.get("id") == mal_id:
                            mal_title = node.get("title", self.anime_title)
                            break
            except Exception as e:
                print(f"[-] Erreur lecture base MAL : {e}")

        target_key = str(mal_id)
        old_key = str(self.anime_mal_id) if self.anime_mal_id else None

        # Migration propre de l'ancienne clé vers la nouvelle clé basée sur l'ID MAL
        if old_key and old_key in self.local_cache_data:
            entry_data = self.local_cache_data.pop(old_key)
            entry_data["mal_id"] = mal_id
            entry_data["title"] = mal_title
            self.local_cache_data[target_key] = entry_data
        else:
            self.local_cache_data[target_key] = {
                "mal_id": mal_id,
                "title": mal_title,
                "folder_path": "",
                "episodes": []
            }

        if self.save_cache_callback:
            self.save_cache_callback()

        print(f"[Cache] ID MAL {mal_id} enregistré avec succès pour l'entrée '{target_key}' !")

        # Ouverture directe de l'explorateur pour lier le dossier
        base_path = str(Path(__file__).resolve().parent.parent.parent / "Vidéos" / "Animé")
        dialog_title = tr.get("dialog_select_folder", anime_title=mal_title)

        selected_dir = QFileDialog.getExistingDirectory(
            self.parent,
            dialog_title,
            base_path
        )

        if selected_dir:
            self.local_cache_data[target_key]["folder_path"] = selected_dir
            if self.save_cache_callback:
                self.save_cache_callback()
            print(f"[Cache] Dossier local associé : {selected_dir}")

        self._trigger_ui_refresh()

    def _open_anime_folder(self):
        """Ouvre le dossier local en utilisant strictement la clé ID MAL."""
        target_key = str(self.anime_mal_id) if self.anime_mal_id else None
        folder_path_str = None

        if target_key and target_key in self.local_cache_data:
            folder_path_str = self.local_cache_data[target_key].get("folder_path")

        target_dir = Path(folder_path_str) if folder_path_str else None

        if target_dir and target_dir.exists():
            os.startfile(str(target_dir))
        else:
            base_path = str(Path(__file__).resolve().parent.parent.parent / "Vidéos" / "Animé")
            dialog_title = tr.get("dialog_select_folder", anime_title=self.anime_title)
            selected_dir = QFileDialog.getExistingDirectory(
                self.parent,
                dialog_title,
                base_path
            )

            if selected_dir:
                if target_key:
                    if target_key not in self.local_cache_data:
                        self.local_cache_data[target_key] = {
                            "mal_id": self.anime_mal_id,
                            "title": self.anime_title,
                            "folder_path": selected_dir,
                            "episodes": []
                        }
                    else:
                        self.local_cache_data[target_key]["folder_path"] = selected_dir

                    if self.save_cache_callback:
                        self.save_cache_callback()

                os.startfile(selected_dir)

        self._trigger_ui_refresh()