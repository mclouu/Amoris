from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from pathlib import Path
from ui.colors import Colors
from utils.translator import tr
from ui.components.settings_window import SettingsWindow  # 👈 Import propre de la modale


class Header(QWidget):
    """En-tête principal de l'application contenant la recherche et les actions globales."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(65)
        self.setStyleSheet(f"""
            background-color: {Colors.BG_DARKER}; 
            border-bottom: 1px solid {Colors.BORDER_COLOR};
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)

        # 1. Barre de recherche globale
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr.get("search_placeholder"))
        self.search_input.setFixedHeight(35)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding-left: 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {Colors.ACCENT_BLUE};
            }}
        """)
        layout.addWidget(self.search_input, stretch=1)

        layout.addSpacing(20)

        # Style commun pour les boutons icônes du header basé sur colors.py
        icon_btn_style = f"""
            QPushButton {{
                background-color: {Colors.BG_SURFACE};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER_BTN};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRESSED_BTN};
            }}
        """

        # Chemin propre vers le dossier d'icônes avec pathlib (zéro warning !)
        icons_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

        # 2. Bouton 1 : Actualisation MAL (Update)
        self.btn_refresh_mal = QPushButton()
        self.btn_refresh_mal.setIcon(QIcon(str(icons_dir / "update.svg")))
        self.btn_refresh_mal.setFixedSize(35, 35)
        self.btn_refresh_mal.setStyleSheet(icon_btn_style)
        self.btn_refresh_mal.setToolTip(tr.get("tooltip_refresh"))
        self.btn_refresh_mal.clicked.connect(self._on_refresh_mal_clicked)
        layout.addWidget(self.btn_refresh_mal)

        # 3. Bouton 2 : Scan local (Scan)
        self.btn_scan_local = QPushButton()
        self.btn_scan_local.setIcon(QIcon(str(icons_dir / "scan.svg")))
        self.btn_scan_local.setFixedSize(35, 35)
        self.btn_scan_local.setStyleSheet(icon_btn_style)
        self.btn_scan_local.setToolTip(tr.get("tooltip_scan"))
        self.btn_scan_local.clicked.connect(self._on_scan_local_clicked)
        layout.addWidget(self.btn_scan_local)

        # 4. Bouton 3 : Paramètres (Config)
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(str(icons_dir / "config.svg")))
        self.btn_settings.setFixedSize(35, 35)
        self.btn_settings.setStyleSheet(icon_btn_style)
        self.btn_settings.setToolTip(tr.get("tooltip_settings"))
        self.btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(self.btn_settings)

    def _on_refresh_mal_clicked(self):
        print("[API] Rafraîchissement MAL demandé (Placeholder)")

    def _on_scan_local_clicked(self):
        print("[Local] Scan du dossier demandé (Placeholder)")

    def _open_settings(self):
        """Ouvre la fenêtre modale des paramètres."""
        self.settings_window = SettingsWindow(self)
        self.settings_window.exec()