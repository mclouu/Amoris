from pathlib import Path
from PyQt6.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QMenu,
    QTableWidgetItem,
)
from PyQt6.QtCore import Qt, QPoint
from ui.colors import Colors
from utils.translator import tr
from ui.components.progress_delegate import ProgressDelegate
from ui.components.anime_double_click_handler import AnimeDoubleClickHandler
from utils.date_reformat import format_date, format_season


class AnimeTableFactory:
    """Fabrique et configure les tableaux d'animés par statut (basé 100% sur le mal_id)."""

    def __init__(self, parent_widget, columns_config: list, local_db_data: list, cache_repo,
                 show_context_menu_callback):
        self.parent = parent_widget
        self.columns_config = columns_config
        self.local_db_data = local_db_data
        self.cache_repo = cache_repo
        self.show_context_menu_callback = show_context_menu_callback
        self.double_click_handler = AnimeDoubleClickHandler(self.parent, self.local_db_data)

    def create_table(self, status_id: str) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(self.columns_config))
        table.setHorizontalHeaderLabels(
            [tr.get(col["key"]) for col in self.columns_config]
        )

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Connexion du double-clic sur une ligne/cellule
        table.cellDoubleClicked.connect(
            lambda row, col, t=table: self.double_click_handler.handle_double_click(row, col, t)
        )

        # Clic droit sur les lignes (menu contextuel des animés)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos, t=table: self.show_context_menu_callback(pos, t)
        )

        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BG_MAIN};
                color: {Colors.TEXT_PRIMARY};
                gridline-color: {Colors.BORDER_COLOR};
                border: none;
                border-radius: 6px;
                selection-background-color: {Colors.BG_SURFACE};
                outline: none;
            }}
            QTableWidget::item {{
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item:focus {{
                border: none;
                outline: none;
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

        # Clic droit sur l'en-tête (gestion des colonnes)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(
            lambda pos, t=table: self._show_header_context_menu(pos, t)
        )

        v_header = table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v_header.setDefaultSectionSize(36)
        v_header.setVisible(False)

        table.setItemDelegateForColumn(1, ProgressDelegate(table))

        filtered_items = [
            item
            for item in self.local_db_data
            if item.get("list_status", {}).get("status") == status_id
        ]

        table.setRowCount(len(filtered_items))
        for row_idx, anime_entry in enumerate(filtered_items):
            node = anime_entry.get("node", {})
            list_status = anime_entry.get("list_status", {})

            def create_read_only_item(text: str) -> QTableWidgetItem:
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                return item

            anime_title = node.get("title", tr.get("unknown_title"))
            mal_id = node.get("id")

            # 🚀 Stockage direct du mal_id dans l'item de la colonne 0 (titre)
            title_item = create_read_only_item(anime_title)
            title_item.setData(Qt.ItemDataRole.UserRole, mal_id)
            table.setItem(row_idx, 0, title_item)

            watched = list_status.get("num_episodes_watched", 0)
            total_episodes = node.get("num_episodes", 0) or 0
            user_status = list_status.get("status", status_id)

            # 🚀 Récupération directe et exclusive par ID dans le cache local
            local_entry = self.parent.local_cache_data.get(str(mal_id), {})
            local_episodes = len(local_entry.get("episodes", []))

            progress_item = QTableWidgetItem()
            progress_item.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "watched": watched,
                    "total": total_episodes,
                    "local": local_episodes,
                    "season_progress": 0.0,
                    "status": user_status,
                },
            )
            progress_item.setFlags(
                progress_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            table.setItem(row_idx, 1, progress_item)

            table.setItem(row_idx, 2, create_read_only_item(format_season(node.get("start_season"))))
            score = list_status.get("score", 0)
            table.setItem(row_idx, 3, create_read_only_item(str(score)))

            updated_at = list_status.get("updated_at")
            table.setItem(row_idx, 4, create_read_only_item(format_date(updated_at)))

            for col_i in range(5, len(self.columns_config)):
                table.setItem(row_idx, col_i, create_read_only_item("-"))

        return table

    def _show_header_context_menu(self, pos: QPoint, table: QTableWidget):
        header = table.horizontalHeader()
        menu = QMenu(self.parent)

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
            action = menu.addAction(tr.get(col["key"]))
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.triggered.connect(
                lambda checked, idx=index: self.parent._set_column_visible_globally(
                    idx, checked
                )
            )

        menu.addSeparator()
        reset_action = menu.addAction(tr.get("menu_reset_defaults"))
        reset_action.triggered.connect(self.parent._reset_all_tables_to_defaults)

        menu.exec(header.mapToGlobal(pos))