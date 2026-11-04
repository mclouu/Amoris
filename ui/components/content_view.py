from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTableWidget,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from ui.colors import Colors
from utils.translator import tr
from ui.components.anime_context_menu import AnimeContextMenu
from ui.components.anime_table_factory import AnimeTableFactory
from core.cache_repository import CacheRepository


class ContentView(QWidget):
    """Zone de contenu principale avec les onglets de statut (façon Taiga)."""

    # Signal émis avec l'ID MAL de l'animé sélectionné
    anime_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        self.cache_repo = CacheRepository()
        self.local_db_data = self.cache_repo.load_mal_database()
        self.local_cache_data = self.cache_repo.load_local_cache()

        self.tabs_data = [
            {"id": "watching", "key": "tab_watching", "count": self._count_by_status("watching")},
            {"id": "completed", "key": "tab_completed", "count": self._count_by_status("completed")},
            {"id": "on_hold", "key": "tab_on_hold", "count": self._count_by_status("on_hold")},
            {"id": "dropped", "key": "tab_dropped", "count": self._count_by_status("dropped")},
            {"id": "plan_to_watch", "key": "tab_plan_to_watch", "count": self._count_by_status("plan_to_watch")},
        ]

        self.columns_config = [
            {"id": "title", "key": "col_title", "default_visible": True, "default_width": 320},
            {"id": "progress", "key": "col_progress", "default_visible": True, "default_width": 200},
            {"id": "season", "key": "col_season", "default_visible": True, "default_width": 110},
            {"id": "score", "key": "col_score", "default_visible": True, "default_width": 80},
            {"id": "last_updated", "key": "col_last_updated", "default_visible": True, "default_width": 150},
            {"id": "average_score", "key": "col_average_score", "default_visible": False, "default_width": 100},
            {"id": "type", "key": "col_type", "default_visible": False, "default_width": 80},
            {"id": "date_started", "key": "col_date_started", "default_visible": False, "default_width": 110},
            {"id": "date_completed", "key": "col_date_completed", "default_visible": False, "default_width": 110},
            {"id": "notes", "key": "col_notes", "default_visible": False, "default_width": 100},
        ]

        # Initialisation de la fabrique de tableaux
        self.table_factory = AnimeTableFactory(
            parent_widget=self,
            columns_config=self.columns_config,
            local_db_data=self.local_db_data,
            cache_repo=self.cache_repo,
            show_context_menu_callback=self._show_row_context_menu
        )

        self._init_ui()

    def _save_local_cache(self):
        self.cache_repo.save_local_cache(self.local_cache_data)

    def _count_by_status(self, status_id: str) -> int:
        return sum(
            1
            for item in self.local_db_data
            if item.get("list_status", {}).get("status") == status_id
        )

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

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

        self.tables = {}

        for tab_info in self.tabs_data:
            tab_name = tr.get(tab_info["key"], count=tab_info["count"])
            table_widget = self.table_factory.create_table(tab_info["id"])

            table_widget.itemSelectionChanged.connect(
                lambda t=table_widget: self._on_row_selected(t)
            )

            self.tabs.addTab(table_widget, tab_name)
            self.tables[tab_info["id"]] = table_widget

        layout.addWidget(self.tabs)
        self._apply_global_columns_visibility_on_all()

    def _on_row_selected(self, table: QTableWidget):
        selected_items = table.selectedItems()
        if not selected_items:
            return

        row = table.row(selected_items[0])
        title_item = table.item(row, 0)
        if title_item:
            anime_title = title_item.text()
            for item in self.local_db_data:
                if item.get("node", {}).get("title") == anime_title:
                    mal_id = item.get("node", {}).get("id")
                    if mal_id:
                        self.anime_selected.emit(mal_id)
                    break

    def _show_row_context_menu(self, pos: QPoint, table: QTableWidget):
        index = table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        title_item = table.item(row, 0)
        if not title_item:
            return

        anime_title = title_item.text()
        anime_mal_id = None
        for item in self.local_db_data:
            if item.get("node", {}).get("title") == anime_title:
                anime_mal_id = item.get("node", {}).get("id")
                break

        context_menu = AnimeContextMenu(
            parent_widget=self,
            anime_title=anime_title,
            anime_mal_id=anime_mal_id,
            local_cache_data=self.local_cache_data,
            save_cache_callback=self._save_local_cache
        )
        context_menu.exec(table.viewport().mapToGlobal(pos))

    def _apply_global_columns_visibility_on_all(self):
        for table in self.tables.values():
            header = table.horizontalHeader()
            for logical_index in range(len(self.columns_config)):
                visual_index = header.visualIndex(logical_index)
                if visual_index != logical_index:
                    header.moveSection(visual_index, logical_index)

            for index, col in enumerate(self.columns_config):
                table.setColumnWidth(index, col["default_width"])
                table.setColumnHidden(index, not col["default_visible"])

    def _set_column_visible_globally(self, index: int, visible: bool):
        self.columns_config[index]["default_visible"] = visible
        for table in self.tables.values():
            table.setColumnHidden(index, not visible)

    def _reset_all_tables_to_defaults(self):
        defaults = [True, True, True, True, True, False, False, False, False, False]
        for idx, visible in enumerate(defaults):
            self.columns_config[idx]["default_visible"] = visible

        self._apply_global_columns_visibility_on_all()

    def retranslate_ui(self):
        """Met à jour dynamiquement les textes des onglets et des en-têtes de colonnes."""
        for index, tab_info in enumerate(self.tabs_data):
            new_tab_name = tr.get(tab_info["key"], count=tab_info["count"])
            self.tabs.setTabText(index, new_tab_name)

        for table in self.tables.values():
            table.setHorizontalHeaderLabels(
                [tr.get(col["key"]) for col in self.columns_config]
            )