from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from ui.colors import Colors
from core.detector import VideoDetector


class Footer(QWidget):
    """Pied de page affichant en temps réel le média en cours de lecture sur PotPlayer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.detector = VideoDetector(target_process="PotPlayerMini64.exe")

        self.setFixedHeight(35)
        self.setStyleSheet(f"""
            background-color: {Colors.BG_DARKER};
            border-top: 1px solid {Colors.BORDER_COLOR};
            color: {Colors.TEXT_PRIMARY};
            padding-left: 15px;
            font-size: 12px;
        """)

        self._init_ui()

        # Timer pour actualiser l'état du lecteur toutes les 1 seconde (1000 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_media_status)
        self.timer.start(1000)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 15, 0)

        self.status_label = QLabel("💤 En attente de PotPlayer...")
        self.status_label.setStyleSheet("color: #888888; border: none; background: transparent;")
        layout.addWidget(self.status_label)
        layout.addStretch()

    def update_media_status(self):
        """Interroge le détecteur pour récupérer le titre de la fenêtre active."""
        raw_title = self.detector.get_active_media_title()
        if raw_title:
            # On extrait proprement via ta méthode de parsing du detector
            anime_name, ep_num = self.detector.parse_anime_filename(raw_title)
            display_text = f"▶ En lecture : {anime_name} - Épisode {ep_num}"
            self.status_label.setText(display_text)
            self.status_label.setStyleSheet(
                "color: #4CAF50; border: none; background: transparent;")  # Vert discret quand actif
        else:
            self.status_label.setText("💤 Aucun média détecté dans PotPlayer")
            self.status_label.setStyleSheet("color: #888888; border: none; background: transparent;")

    def retranslate_ui(self):
        """Méthode de compatibilité pour les changements de langue globaux si besoin."""
        pass