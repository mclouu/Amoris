from PyQt6.QtWidgets import QDialog, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from pathlib import Path
from ui.colors import Colors
from utils.translator import tr


class SettingsWindow(QDialog):
    """Fenêtre de paramètres avec navigation latérale (style Taiga)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr.get("settings_title"))
        self.resize(550, 400)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN}; color: {Colors.TEXT_PRIMARY};")

        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Menu latéral gauche (Navigation)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(160)
        self.sidebar.setStyleSheet(f"""
            QListWidget {{
                background-color: {Colors.BG_DARKER};
                border: none;
                border-right: 1px solid {Colors.BORDER_COLOR};
                outline: none;
            }}
            QListWidget::item {{
                height: 45px;
                padding-left: 15px;
                color: {Colors.TEXT_PRIMARY};
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.ACCENT_BLUE};
                font-weight: bold;
                border-left: 3px solid {Colors.ACCENT_BLUE};
            }}
            QListWidget::item:hover {{
                background-color: {Colors.HOVER_BTN};
            }}
        """)

        # Chemin vers les icônes SVG du dossier assets/icons/
        icons_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

        # Élément 1 : Langue
        self.item_lang = QListWidgetItem(QIcon(str(icons_dir / "config_language.svg")), tr.get("settings_cat_language"))
        self.sidebar.addItem(self.item_lang)

        # Élément 2 : Thème
        self.item_theme = QListWidgetItem(QIcon(str(icons_dir / "config_theme.svg")), tr.get("settings_cat_theme"))
        self.sidebar.addItem(self.item_theme)

        main_layout.addWidget(self.sidebar)

        # 2. Zone de contenu à droite (Pages empilées)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        # --- PAGE 1 : LANGUE ---
        page_lang = QWidget()
        lang_layout = QVBoxLayout(page_lang)
        lang_layout.setContentsMargins(30, 30, 30, 30)

        self.label_lang_title = QLabel(tr.get("settings_lang_label"))
        self.label_lang_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        lang_layout.addWidget(self.label_lang_title)

        flags_layout = QHBoxLayout()
        flags_layout.setSpacing(20)

        # Bouton Drapeau Français
        self.btn_fr = QPushButton("Français")
        self.btn_fr.setFixedHeight(50)
        self.btn_fr.setStyleSheet(self._get_flag_btn_style())
        self.btn_fr.clicked.connect(lambda: self._change_language("fr"))

        # Bouton Drapeau Anglais
        self.btn_en = QPushButton("English")
        self.btn_en.setFixedHeight(50)
        self.btn_en.setStyleSheet(self._get_flag_btn_style())
        self.btn_en.clicked.connect(lambda: self._change_language("en"))

        flags_layout.addWidget(self.btn_fr)
        flags_layout.addWidget(flags_layout.itemAt(0) and self.btn_en or self.btn_en)  # simple ajout
        lang_layout.addLayout(flags_layout)
        lang_layout.addStretch()

        self.stack.addWidget(page_lang)

        # --- PAGE 2 : THÈME (Vide / Placeholder) ---
        page_theme = QWidget()
        theme_layout = QVBoxLayout(page_theme)
        self.label_theme_placeholder = QLabel(tr.get("settings_theme_placeholder"))
        self.label_theme_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        theme_layout.addWidget(self.label_theme_placeholder)
        self.stack.addWidget(page_theme)

        main_layout.addWidget(self.stack, stretch=1)

        # Synchronisation du clic de la sidebar avec le changement de page
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

    def _get_flag_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_COLOR};
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                padding: 0px 20px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER_BTN};
                border: 1px solid {Colors.ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRESSED_BTN};
            }}
        """

    def _change_language(self, lang_code):
        """Change la langue à la volée et rafraîchit toute l'application."""
        tr.set_language(lang_code)

        # 1. Rafraîchit les textes de la fenêtre de paramètres elle-même
        self.setWindowTitle(tr.get("settings_title"))
        self.item_lang.setText(tr.get("settings_cat_language"))
        self.item_theme.setText(tr.get("settings_cat_theme"))
        self.label_lang_title.setText(tr.get("settings_lang_label"))
        self.label_theme_placeholder.setText(tr.get("settings_theme_placeholder"))

        # 2. Rafraîchit toutes les fenêtres principales ouvertes (dont MainWindow)
        from PyQt6.QtWidgets import QApplication
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()