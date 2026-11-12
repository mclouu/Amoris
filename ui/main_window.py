from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtGui import QPixmap
from pathlib import Path
import os

from utils.cover_downloader import CoverDownloaderThread
from ui.components.menu_side import SideMenu
from ui.components.content_view import ContentView
from ui.components.header import Header
from ui.components.footer import Footer  # 🚀 1. Import du Footer
from ui.colors import Colors
from utils.translator import tr
from core.scanner import LocalAnimeScanner


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.anime_widgets = {}

        self.setWindowTitle(tr.get("app_title"))
        self.resize(1100, 700)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        self._init_ui()

        # 🚀 Lancement du scan solo automatique au lancement !
        self.run_startup_scan()

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

        # 2. Conteneur de droite (Divisé verticalement en : Header + ContentView + Footer)
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

        # 🚀 2. Instanciation et ajout du Footer tout en bas !
        self.footer = Footer(self)
        right_layout.addWidget(self.footer)

        # Ajout du conteneur de droite dans le layout principal
        main_layout.addWidget(right_container, stretch=1)

        # Connexions
        self.content_view.anime_selected.connect(self.side_menu.set_image)

        # Connexion du signal de scan du Header pour rafraîchir les données en direct !
        self.header.local_scan_finished.connect(self.reload_local_data)

    def run_startup_scan(self):
        """Exécute le scan local automatiquement au lancement de l'application."""
        print("[Local] 🚀 Scan automatique au lancement en cours...")
        target_path = r"D:\Vidéos\Animé"

        try:
            scanner = LocalAnimeScanner(target_path=target_path, cache_file="cache/anime_db_local.json")
            if scanner.scan():
                scanner.save_cache()
                print("[Local] ✅ Scan de lancement terminé et cache mis à jour avec succès !")
        except Exception as e:
            print(f"[-] Erreur lors du scan automatique au lancement : {e}")

    def reload_local_data(self):
        """Recharge les données locales et met à jour l'interface des tableaux sans redémarrer."""
        print("[UI] Rechargement du cache local et rafraîchissement des tableaux...")

        self.content_view.local_cache_data = self.content_view.cache_repo.load_local_cache()

        central_layout = self.centralWidget().layout()
        right_container = central_layout.itemAt(1).widget()
        right_layout = right_container.layout()

        # On retire temporairement le footer pour recréer la content_view proprement au milieu
        right_layout.removeWidget(self.footer)
        right_layout.removeWidget(self.content_view)
        self.content_view.deleteLater()

        self.content_view = ContentView(self)

        # On remet dans l'ordre : Header (déjà là), ContentView, puis Footer en bas
        right_layout.insertWidget(1, self.content_view, stretch=1)
        right_layout.addWidget(self.footer)  # Remet le footer tout en bas

        self.content_view.anime_selected.connect(self.side_menu.set_image)
        print("[UI] Interface mise à jour avec succès !")

    def init_image_downloader(self):
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

    def retranslate_ui(self):
        """Propage le changement de langue à la fenêtre principale et ses enfants."""
        self.setWindowTitle(tr.get("app_title"))
        if hasattr(self, "header"):
            self.header.retranslate_ui()
        if hasattr(self, "content_view"):
            self.content_view.retranslate_ui()