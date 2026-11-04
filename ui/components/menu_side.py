from pathlib import Path
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from ui.colors import Colors


class SideMenu(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mal_id = None  # Pour stocker l'ID de l'animé affiché
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Label dédié à l'affichage de la couverture
        self.cover_label = QLabel(self)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setFixedSize(220, 310)

        # Au début, pas d'animé sélectionné : on cache la bordure et le fond du label de cover
        self.cover_label.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)
        self.cover_label.setText("")  # Pas de texte au démarrage

        # Rend le label cliquable visuellement (curseur en main)
        self.cover_label.setCursor(Qt.CursorShape.PointingHandCursor)

        # On surcharge l'événement de clic du QLabel
        self.cover_label.mousePressEvent = self.on_cover_clicked

        layout.addWidget(self.cover_label)
        layout.addStretch()

    def set_image(self, mal_id: int):
        """Charge et affiche l'image de couverture et stocke l'ID MAL."""
        self.current_mal_id = mal_id  # On garde l'ID en mémoire pour le lien

        # Chemin dynamique propre avec pathlib (plus de chemin en dur !)
        root_dir = next(p for p in Path(__file__).resolve().parents if p.name == 'Amoris')
        cache_path = root_dir / "cache" / "img"
        img_path = cache_path / f"{mal_id}.jpg"

        # Dès qu'un animé est sélectionné, on redonne son style visible au cadre de la cover
        self.cover_label.setStyleSheet(f"""
            background-color: {Colors.BG_DARKER};
            border: 1px solid {Colors.BORDER_COLOR};
            border-radius: 8px;
        """)

        if img_path.exists():
            pixmap = QPixmap(str(img_path))
            scaled_pixmap = pixmap.scaled(
                self.cover_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.cover_label.setPixmap(scaled_pixmap)
        else:
            self.cover_label.clear()
            self.cover_label.setText("Image introuvable")

    def on_cover_clicked(self, event):
        """Ouvre la page MyAnimeList dans le navigateur lorsqu'on clique sur l'image."""
        if self.current_mal_id:
            url_str = f"https://myanimelist.net/anime/{self.current_mal_id}/"
            QDesktopServices.openUrl(QUrl(url_str))

    def retranslate_ui(self):
        pass