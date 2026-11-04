from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QPixmap
from pathlib import Path
import os

from utils.cover_downloader import CoverDownloaderThread
from ui.components.menu_side import SideMenu
from ui.components.content_view import ContentView
from ui.components.header import Header  # 👈 Import de ton header (vérifie le nom de ton fichier header)
from ui.colors import Colors


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.anime_widgets = {}

        self.setWindowTitle("Amoris")
        self.resize(1100, 700)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        self._init_ui()
        self.init_image_downloader()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layout principal horizontal global (SideMenu à gauche, et le reste à droite)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Menu latéral à gauche
        self.side_menu = SideMenu(self)
        main_layout.addWidget(self.side_menu)

        # 2. Conteneur de droite (Divisé verticalement en : Header en haut + ContentView en bas)
        right_container = QWidget(self)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Instanciation et ajout du Header
        self.header = Header(self)
        right_layout.addWidget(self.header)

        # Instanciation et ajout de la ContentView
        self.content_view = ContentView(self)
        right_layout.addWidget(self.content_view, stretch=1)

        # Ajout du conteneur de droite dans le layout principal
        main_layout.addWidget(right_container, stretch=1)

        # Connexion
        self.content_view.anime_selected.connect(self.side_menu.set_image)

    def init_image_downloader(self):
        # 🛡️ Chemin dynamique propre basé sur Amoris (compatible GitHub & multi-user)
        root_dir = next(p for p in Path(__file__).resolve().parents if p.name == 'Amoris')
        json_path = root_dir / "cache" / "anime_db_user.json"
        output_dir = root_dir / "cache" / "img"

        self.downloader_thread = CoverDownloaderThread(str(json_path), str(output_dir))

        self.downloader_thread.status_signal.connect(self.statusBar().showMessage)
        self.downloader_thread.image_downloaded_signal.connect(self.update_single_anime_poster)

        self.downloader_thread.start()

    def update_single_anime_poster(self, anime_id):
        if str(self.side_menu.current_mal_id) == str(anime_id):
            self.side_menu.set_image(int(anime_id))