from PyQt6.QtWidgets import (
    QDialog, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from pathlib import Path
from ui.colors import Colors
from utils.translator import tr
from core import mal_auth, mal_client


class MalWorker(QThread):
    """Worker QThread pour exécuter les actions MAL en arrière-plan (login, logout, fetch profile)."""
    finished = pyqtSignal(object)  # Renvoie un dict de résultat ou une exception

    def __init__(self, action, **kwargs):
        super().__init__()
        self.action = action
        self.kwargs = kwargs

    def run(self):
        try:
            if self.action == "check":
                logged = mal_auth.is_logged_in()
                profile = None
                if logged:
                    try:
                        profile = mal_client.get_profile()
                    except Exception:
                        pass
                self.finished.emit({"action": "check", "logged": logged, "profile": profile})

            elif self.action == "login":
                browser_text = tr.get("mal_browser_page_text")
                mal_auth.login(timeout=180, page_text=browser_text)
                profile = mal_client.get_profile()
                self.finished.emit({"action": "login", "success": True, "profile": profile})

            elif self.action == "logout":
                mal_auth.logout()
                self.finished.emit({"action": "logout", "success": True})

        except Exception as e:
            self.finished.emit({"action": self.action, "error": e})


class SettingsWindow(QDialog):
    """Fenêtre de paramètres avec navigation latérale (style Taiga)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr.get("settings_title"))
        self.resize(600, 420)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN}; color: {Colors.TEXT_PRIMARY};")

        self.worker = None
        self._init_ui()
        self._check_initial_auth()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Menu latéral gauche (Navigation)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(175)
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

        icons_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

        # Élément 1 : Langue
        self.item_lang = QListWidgetItem(QIcon(str(icons_dir / "config_language.svg")), tr.get("settings_cat_language"))
        self.sidebar.addItem(self.item_lang)

        # Élément 2 : Thème
        self.item_theme = QListWidgetItem(QIcon(str(icons_dir / "config_theme.svg")), tr.get("settings_cat_theme"))
        self.sidebar.addItem(self.item_theme)

        # Élément 3 : Compte MAL 🚀
        mal_icon_path = icons_dir / "config_mal.svg"
        mal_icon = QIcon(str(mal_icon_path)) if mal_icon_path.exists() else QIcon()
        self.item_mal = QListWidgetItem(mal_icon, tr.get("settings_cat_mal"))
        self.sidebar.addItem(self.item_mal)

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

        self.btn_fr = QPushButton("Français")
        self.btn_fr.setFixedHeight(50)
        self.btn_fr.setStyleSheet(self._get_btn_style())
        self.btn_fr.clicked.connect(lambda: self._change_language("fr"))

        self.btn_en = QPushButton("English")
        self.btn_en.setFixedHeight(50)
        self.btn_en.setStyleSheet(self._get_btn_style())
        self.btn_en.clicked.connect(lambda: self._change_language("en"))

        flags_layout.addWidget(self.btn_fr)
        flags_layout.addWidget(self.btn_en)
        lang_layout.addLayout(flags_layout)
        lang_layout.addStretch()
        self.stack.addWidget(page_lang)

        # --- PAGE 2 : THÈME ---
        page_theme = QWidget()
        theme_layout = QVBoxLayout(page_theme)
        self.label_theme_placeholder = QLabel(tr.get("settings_theme_placeholder"))
        self.label_theme_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        theme_layout.addWidget(self.label_theme_placeholder)
        self.stack.addWidget(page_theme)

        # --- PAGE 3 : COMPTE MAL 🚀 ---
        page_mal = QWidget()
        mal_layout = QVBoxLayout(page_mal)
        mal_layout.setContentsMargins(30, 30, 30, 30)
        mal_layout.setSpacing(15)

        self.label_mal_title = QLabel(tr.get("settings_cat_mal"))
        self.label_mal_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        mal_layout.addWidget(self.label_mal_title)

        self.label_mal_status = QLabel(tr.get("mal_status_checking"))
        self.label_mal_status.setStyleSheet("font-size: 13px; color: #888888;")
        mal_layout.addWidget(self.label_mal_status)

        self.label_mal_error = QLabel("")
        self.label_mal_error.setStyleSheet("font-size: 12px; color: #E57373;")
        self.label_mal_error.setWordWrap(True)
        mal_layout.addWidget(self.label_mal_error)

        btns_mal_layout = QHBoxLayout()
        btns_mal_layout.setSpacing(10)

        self.btn_mal_connect = QPushButton(tr.get("mal_btn_connect"))
        self.btn_mal_connect.setFixedHeight(40)
        self.btn_mal_connect.setStyleSheet(self._get_btn_style())
        self.btn_mal_connect.clicked.connect(self._on_connect_clicked)

        self.btn_mal_disconnect = QPushButton(tr.get("mal_btn_disconnect"))
        self.btn_mal_disconnect.setFixedHeight(40)
        self.btn_mal_disconnect.setStyleSheet(self._get_btn_style())
        self.btn_mal_disconnect.clicked.connect(self._on_disconnect_clicked)
        self.btn_mal_disconnect.setVisible(False)  # Caché par défaut si non connecté

        btns_mal_layout.addWidget(self.btn_mal_connect)
        btns_mal_layout.addWidget(self.btn_mal_disconnect)
        btns_mal_layout.addStretch()

        mal_layout.addLayout(btns_mal_layout)
        mal_layout.addStretch()
        self.stack.addWidget(page_mal)

        main_layout.addWidget(self.stack, stretch=1)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

    def _get_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_COLOR};
                border-radius: 8px;
                font-size: 14px;
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
            QPushButton:disabled {{
                color: #666666;
                background-color: {Colors.BG_DARKER};
            }}
        """

    def _check_initial_auth(self):
        self.btn_mal_connect.setEnabled(False)
        self.label_mal_status.setText(tr.get("mal_status_checking"))
        self.label_mal_error.setText("")

        self.worker = MalWorker("check")
        self.worker.finished.connect(self._handle_worker_finished)
        self.worker.start()

    def _on_connect_clicked(self):
        self.btn_mal_connect.setEnabled(False)
        self.label_mal_status.setText(tr.get("mal_status_connecting"))
        self.label_mal_error.setText("")

        self.worker = MalWorker("login")
        self.worker.finished.connect(self._handle_worker_finished)
        self.worker.start()

    def _on_disconnect_clicked(self):
        self.btn_mal_connect.setEnabled(False)
        self.btn_mal_disconnect.setEnabled(False)

        self.worker = MalWorker("logout")
        self.worker.finished.connect(self._handle_worker_finished)
        self.worker.start()

    def _handle_worker_finished(self, result):
        action = result.get("action")
        error = result.get("error")

        if error:
            # Gestion des erreurs via l'attribut .code ou fallback inconnu
            err_code = getattr(error, "code", "unknown")
            translation_key = f"mal_err_{err_code}"
            err_msg = tr.get(translation_key)
            # Si la clé n'existe pas dans le traducteur, on prend l'inconnue
            if err_msg == translation_key:
                err_msg = tr.get("mal_err_unknown")

            self.label_mal_error.setText(err_msg)

            # Restauration de l'état UI déconnecté par sécurité
            self.label_mal_status.setText(tr.get("mal_status_disconnected"))
            self.btn_mal_connect.setVisible(True)
            self.btn_mal_connect.setEnabled(True)
            self.btn_mal_disconnect.setVisible(False)
            self.btn_mal_disconnect.setEnabled(True)
            return

        # Succès selon l'action
        if action in ("check", "login"):
            logged = result.get("logged", True) if action == "check" else result.get("success", False)
            profile = result.get("profile")

            if logged and profile and isinstance(profile, dict) and "name" in profile:
                username = profile.get("name")
                self.label_mal_status.setText(tr.get("mal_status_connected", username=username))
                self.btn_mal_connect.setVisible(False)
                self.btn_mal_disconnect.setVisible(True)
                self.btn_mal_disconnect.setEnabled(True)
            else:
                self.label_mal_status.setText(tr.get("mal_status_disconnected"))
                self.btn_mal_connect.setVisible(True)
                self.btn_mal_connect.setEnabled(True)
                self.btn_mal_disconnect.setVisible(False)

        elif action == "logout":
            self.label_mal_status.setText(tr.get("mal_status_disconnected"))
            self.label_mal_error.setText("")
            self.btn_mal_connect.setVisible(True)
            self.btn_mal_connect.setEnabled(True)
            self.btn_mal_disconnect.setVisible(False)
            self.btn_mal_disconnect.setEnabled(True)

    def _change_language(self, lang_code):
        tr.set_language(lang_code)
        self.retranslate_ui()

        from PyQt6.QtWidgets import QApplication
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "retranslate_ui") and widget != self:
                widget.retranslate_ui()

    def retranslate_ui(self):
        """Met à jour dynamiquement tous les textes de la fenêtre lors d'un changement de langue."""
        self.setWindowTitle(tr.get("settings_title"))
        self.item_lang.setText(tr.get("settings_cat_language"))
        self.item_theme.setText(tr.get("settings_cat_theme"))
        self.item_mal.setText(tr.get("settings_cat_mal"))

        self.label_lang_title.setText(tr.get("settings_lang_label"))
        self.label_theme_placeholder.setText(tr.get("settings_theme_placeholder"))

        self.label_mal_title.setText(tr.get("settings_cat_mal"))
        self.btn_mal_connect.setText(tr.get("mal_btn_connect"))
        self.btn_mal_disconnect.setText(tr.get("mal_btn_disconnect"))

        # Relance un check rapide pour rafraîchir le texte de status traduit si besoin
        if mal_auth.is_logged_in() and self.sidebar.currentRow() == 2:
            pass  # L'état textuel s'ajustera au prochain worker ou clic