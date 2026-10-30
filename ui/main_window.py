import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon
from ui.components.header import Header
from ui.components.content_view import ContentView

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
        self.setWindowTitle("Amoris")
        self.resize(1000, 650)

        # Application de l'icône de la fenêtre
        # On remonte d'un dossier (ui -> racine) pour aller chercher asset/amoris.ico
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "asset", "amoris.ico"))
        self.setWindowIcon(QIcon(icon_path))

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