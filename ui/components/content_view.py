from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTableWidget, QHeaderView, QMenu
from PyQt6.QtCore import Qt, QPoint
from ui.colors import Colors
from utils.translator import tr  # 👈 Import de notre traducteur


class ContentView(QWidget):
    """Zone de contenu principale avec les onglets de statut (façon Taiga)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        # Définition des catégories d'animés avec leurs clés i18n et compteurs
        self.tabs_data = [
            {"id": "watching", "key": "tab_watching", "count": 59},
            {"id": "completed", "key": "tab_completed", "count": 344},
            {"id": "on_hold", "key": "tab_on_hold", "count": 36},
            {"id": "dropped", "key": "tab_dropped", "count": 91},
            {"id": "plan_to_watch", "key": "tab_plan_to_watch", "count": 144},
        ]

        # Définition de toutes les colonnes disponibles avec leurs clés i18n
        self.columns_config = [
            {"id": "title", "key": "col_title", "default_visible": True, "default_width": 320},
            {"id": "progress", "key": "col_progress", "default_visible": True, "default_width": 320},
            {"id": "season", "key": "col_season", "default_visible": True, "default_width": 110},
            {"id": "score", "key": "col_score", "default_visible": True, "default_width": 80},
            {"id": "last_updated", "key": "col_last_updated", "default_visible": True, "default_width": 130},
            {"id": "average_score", "key": "col_average_score", "default_visible": False, "default_width": 100},
            {"id": "type", "key": "col_type", "default_visible": False, "default_width": 80},
            {"id": "date_started", "key": "col_date_started", "default_visible": False, "default_width": 110},
            {"id": "date_completed", "key": "col_date_completed", "default_visible": False, "default_width": 110},
            {"id": "notes", "key": "col_notes", "default_visible": False, "default_width": 100},
        ]

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Création du composant d'onglets (QTabWidget)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {Colors.BG_MAIN};
            }}
            QTabBar::tab {{
                background-color: {Colors.BG_DARKER};
                color: {Colors.TEXT_PRIMARY};
                padding: 8px 14px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.ACCENT_BLUE};
                border-bottom: 2px solid {Colors.ACCENT_BLUE};
            }}
            QTabBar::tab:hover {{
                background-color: {Colors.BG_SURFACE};
            }}
        """)

        # Dictionnaire pour garder une référence sur nos tables par onglet
        self.tables = {}

        # Génération dynamique des onglets avec traduction et formatage du compteur
        for tab_info in self.tabs_data:
            tab_name = tr.get(tab_info['key'], count=tab_info['count'])
            table_widget = self._create_table()
            self.tabs.addTab(table_widget, tab_name)
            self.tables[tab_info['id']] = table_widget

        layout.addWidget(self.tabs)

    def _create_table(self) -> QTableWidget:
        """Crée et retourne une instance de tableau configurée avec toutes nos options."""
        table = QTableWidget()
        table.setColumnCount(len(self.columns_config))

        # Récupération des labels traduits pour les en-têtes
        table.setHorizontalHeaderLabels([tr.get(col["key"]) for col in self.columns_config])

        table.setStyleSheet(f"""
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

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(lambda pos, t=table: self._show_header_context_menu(pos, t))

        # Applique les largeurs et visibilités par défaut
        self._reset_table_to_defaults(table)

        return table

    def _reset_table_to_defaults(self, table: QTableWidget):
        header = table.horizontalHeader()
        for logical_index in range(len(self.columns_config)):
            visual_index = header.visualIndex(logical_index)
            if visual_index != logical_index:
                header.moveSection(visual_index, logical_index)

        for index, col in enumerate(self.columns_config):
            table.setColumnWidth(index, col["default_width"])
            table.setColumnHidden(index, not col["default_visible"])

    def _show_header_context_menu(self, pos: QPoint, table: QTableWidget):
        header = table.horizontalHeader()
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
            is_visible = not table.isColumnHidden(index)
            # Utilisation de la traduction pour chaque item du menu
            action = menu.addAction(tr.get(col["key"]))
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.triggered.connect(lambda checked, idx=index, t=table: t.setColumnHidden(idx, not checked))

        menu.addSeparator()

        reset_action = menu.addAction(tr.get("menu_reset_defaults"))
        reset_action.triggered.connect(lambda: self._reset_table_to_defaults(table))

        header_global_pos = header.mapToGlobal(pos)
        menu.exec(header_global_pos)