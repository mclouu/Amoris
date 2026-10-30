import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon
from ui.components.header import Header
from ui.components.content_view import ContentView
from utils.translator import tr  # 👈 Import de notre traducteur

# ⚡ Astuce Windows : Permet d'afficher la vraie icône dans la barre des tâches
# au lieu de l'icône par défaut de Python.
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("amoris.app.desktop")
except Exception:
    pass


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application Amoris."""

    def __init__(self):
        super().__init__()
        # Utilisation de la clé de traduction pour le titre
        self.setWindowTitle(tr.get("app_title"))
        self.resize(1000, 650)

        # Application de l'icône de la fenêtre avec pathlib (zéro warning)
        # On remonte d'un dossier (ui -> racine) pour aller chercher asset/amoris.ico
        icon_path = Path(__file__).resolve().parent.parent / "asset" / "amoris.ico"
        self.setWindowIcon(QIcon(str(icon_path)))

        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Le Header
        self.header = Header()
        main_layout.addWidget(self.header)

        # 2. Le ContentView
        self.content_view = ContentView()
        main_layout.addWidget(self.content_view, stretch=1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())