from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QHeaderView, QMenu
from PyQt6.QtCore import Qt, QPoint
from ui.colors import Colors


class ContentView(QWidget):
    """Zone de contenu principale affichant le tableau des animés (façon Taiga)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        # Définition de toutes les colonnes disponibles
        self.columns_config = [
            {"id": "title", "label": "Anime title", "default_visible": True, "default_width": 320},
            {"id": "progress", "label": "Progress", "default_visible": True, "default_width": 320},
            {"id": "season", "label": "Season", "default_visible": True, "default_width": 110},
            {"id": "score", "label": "Score", "default_visible": True, "default_width": 80},
            {"id": "last_updated", "label": "Last updated", "default_visible": True, "default_width": 130},
            # Colonnes optionnelles (masquées par défaut)
            {"id": "average_score", "label": "Average score", "default_visible": False, "default_width": 100},
            {"id": "type", "label": "Type", "default_visible": False, "default_width": 80},
            {"id": "date_started", "label": "Date started", "default_visible": False, "default_width": 110},
            {"id": "date_completed", "label": "Date completed", "default_visible": False, "default_width": 110},
            {"id": "notes", "label": "Notes", "default_visible": False, "default_width": 100},
        ]

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Tableau pour la grille de données
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns_config))
        self.table.setHorizontalHeaderLabels([col["label"] for col in self.columns_config])

        # Style de la table et des en-têtes avec les bordures verticales
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_MAIN};
                color: {Colors.TEXT_PRIMARY};
                gridline-color: {Colors.BORDER_COLOR};
                border: none;
                border-radius: 6px;
            }}
            QHeaderView::section {{
                background-color: {Colors.BG_DARKER};
                color: {Colors.TEXT_PRIMARY};
                padding: 8px;
                border: none;
                border-right: 1px solid {Colors.BORDER_COLOR};
                border-bottom: 1px solid {Colors.BORDER_COLOR};
                font-weight: bold;
            }}
        """)

        # Configuration de l'en-tête
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # ⚡ Activation du Drag & Drop pour réordonner les colonnes à la souris !
        header.setSectionsMovable(True)

        # Activation du clic droit sur l'en-tête
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_context_menu)

        # Application des tailles, visibilités et ordres initiaux
        self.reset_to_defaults()

        layout.addWidget(self.table)

    def reset_to_defaults(self):
        """Réinitialise la visibilité, la taille et l'ordre initial de toutes les colonnes."""
        header = self.table.horizontalHeader()

        # Remet les colonnes dans leur ordre logique d'origine
        for logical_index in range(len(self.columns_config)):
            visual_index = header.visualIndex(logical_index)
            if visual_index != logical_index:
                header.moveSection(visual_index, logical_index)

        # Réapplique les tailles et visibilités par défaut
        for index, col in enumerate(self.columns_config):
            self.table.setColumnWidth(index, col["default_width"])
            self.table.setColumnHidden(index, not col["default_visible"])

    def _show_header_context_menu(self, pos: QPoint):
        """Affiche le menu contextuel du clic droit sur l'en-tête."""
        header = self.table.horizontalHeader()
        menu = QMenu(self)

        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.BG_DARKER};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_COLOR};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 28px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.ACCENT_BLUE};
                border-radius: 3px;
            }}
            QMenu::separator {{
                height: 1px;
                background: {Colors.BORDER_COLOR};
                margin: 4px 0px;
            }}
        """)

        for index, col in enumerate(self.columns_config):
            is_visible = not self.table.isColumnHidden(index)
            action = menu.addAction(col["label"])
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.triggered.connect(lambda checked, idx=index: self._toggle_column(idx, checked))

        menu.addSeparator()

        reset_action = menu.addAction("Reset to defaults")
        reset_action.triggered.connect(self.reset_to_defaults)

        header_global_pos = header.mapToGlobal(pos)
        menu.exec(header_global_pos)

        def _toggle_column(self, index: int, visible: bool):
            """Affiche ou masque une colonne spécifique."""
            self.table.setColumnHidden(index, not visible)