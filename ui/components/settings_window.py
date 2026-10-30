from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from ui.colors import Colors
from utils.translator import tr


class SettingsWindow(QDialog):
    """Fenêtre de paramètres de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr.get("settings_title"))
        self.resize(400, 300)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN}; color: {Colors.TEXT_PRIMARY};")

        layout = QVBoxLayout(self)
        label = QLabel(tr.get("settings_placeholder"))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)