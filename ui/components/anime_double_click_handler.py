import os
import glob
import re
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer
from core.cache_repository import CacheRepository


class ToastNotification(QLabel):
    def __init__(self, parent=None, text=""):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet("""
            background-color: #2b2d30;
            color: #ffffff;
            border: 1px solid #3f4246;
            border-radius: 6px;
            padding: 12px 18px;
            font-size: 13px;
            font-weight: bold;
        """)
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.adjustSize()

        if parent:
            global_bottom_right = parent.mapToGlobal(parent.rect().bottomRight())
            x = global_bottom_right.x() - self.width() - 30
            y = global_bottom_right.y() - self.height() - 30
            self.move(x, y)

        self.show()
        QTimer.singleShot(3500, self.deleteLater)


class AnimeDoubleClickHandler:
    def __init__(self, parent_widget=None, local_db_data=None):
        self.parent = parent_widget
        self.local_db_data = local_db_data
        self.cache_repo = CacheRepository()

    def handle_double_click(self, row, col, table):
        title_item = table.item(row, 0)
        if not title_item:
            return
        anime_title = title_item.text()
        mal_id = title_item.data(Qt.ItemDataRole.UserRole)
        self.handle_click(anime_title, target_mal_id=mal_id)

    def __call__(self, anime_title, mal_id=None):
        self.handle_click(anime_title, target_mal_id=mal_id)

    def show_toast(self, message):
        self._toast = ToastNotification(self.parent, message)

    def handle_click(self, anime_title, target_mal_id=None):
        if not target_mal_id:
            msg = f"⚠️ Aucun ID MAL valide pour l'animé '{anime_title}'."
            print(msg)
            self.show_toast(msg)
            return

        try:
            mal_data = self.cache_repo.load_mal_database()
            local_data = self.cache_repo.load_local_cache()
        except Exception as e:
            print(f"Erreur lors du chargement du cache : {e}")
            return

        if not local_data:
            print("Erreur : La base de données locale est introuvable ou vide.")
            return

        # Recherche directe et exclusive par ID MAL dans le cache local
        str_id = str(target_mal_id)
        matched_entry = local_data.get(str_id)

        if not matched_entry:
            msg = f"⚠️ L'entrée locale (ID: {target_mal_id}) est introuvable."
            print(msg)
            self.show_toast(msg)
            return

        folder_path = matched_entry.get("folder_path")

        # Récupération de l'avancement MAL via l'ID unique
        episodes_watched = 0
        total_episodes = 0
        raw_items = mal_data.get("data", []) if isinstance(mal_data, dict) else mal_data
        if raw_items:
            for item in raw_items:
                node = item.get("node", {})
                if node.get("id") == target_mal_id:
                    list_status = item.get("list_status", {})
                    episodes_watched = list_status.get("num_episodes_watched", 0)
                    total_episodes = node.get("num_episodes", 0)
                    break

        next_episode_num = episodes_watched + 1
        if total_episodes > 0 and next_episode_num > total_episodes:
            next_episode_num = total_episodes

        video_extensions = ("*.mkv", "*.mp4", "*.avi", "*.m4v")
        all_videos = []

        if folder_path and os.path.exists(folder_path):
            target_dir = folder_path if os.path.isdir(folder_path) else os.path.dirname(folder_path)
            for ext in video_extensions:
                all_videos.extend(glob.glob(os.path.join(target_dir, ext)))
                all_videos.extend(glob.glob(os.path.join(target_dir, "**", ext), recursive=True))

        all_videos = list(dict.fromkeys(all_videos))

        found_file = None
        ep_str_2 = f"{next_episode_num:02d}"
        ep_str_1 = str(next_episode_num)

        for video in all_videos:
            basename = os.path.basename(video)
            match_e = bool(re.search(rf'[Ee]{ep_str_2}\b', basename) or re.search(rf'[Ee]{ep_str_1}\b', basename))
            match_dash = bool(re.search(rf'[-_\s]0*{next_episode_num}(?:[^\d]|$)', basename))

            if match_e or match_dash:
                found_file = video
                break

        if not found_file and all_videos:
            all_videos.sort()
            if len(all_videos) >= next_episode_num:
                found_file = all_videos[next_episode_num - 1]

        if found_file and os.path.exists(found_file):
            os.startfile(found_file)
        else:
            display_name = matched_entry.get("title", anime_title)
            msg = f"⚠️ Épisode {next_episode_num} manquant pour '{display_name}'"
            print(msg)
            self.show_toast(msg)