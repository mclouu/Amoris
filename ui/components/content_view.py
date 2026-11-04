from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTableWidget, QHeaderView, QMenu, QTableWidgetItem, \
    QStyledItemDelegate
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
import json
from pathlib import Path
from ui.colors import Colors
from utils.translator import tr


class ProgressDelegate(QStyledItemDelegate):
    """Délégué personnalisé pour dessiner la barre de progression, le vert (vu) et la fine ligne rouge (local)."""

    def paint(self, painter: QPainter, option, index):
        painter.save()

        data = index.data(Qt.ItemDataRole.UserRole)
        if not data:
            super().paint(painter, option, index)
            painter.restore()
            return

        watched = data.get("watched", 0)
        total = data.get("total", 0)
        local = data.get("local", 0)
        season_prog = data.get("season_progress", 0.0)
        status = data.get("status", "")

        rect = option.rect

        if status == "completed":
            display_total = total if total > 0 else watched
            total_str = str(display_total)
        else:
            total_str = str(total) if total and total > 0 else "?"

        text = f"{watched}/{total_str}"

        text_width = 45
        padding_right = 10
        bar_height = 14
        margin_v = (rect.height() - bar_height) // 2
        bar_width = rect.width() - text_width - padding_right - 12
        bar_rect = QRectF(rect.left() + 8, rect.top() + margin_v, bar_width, bar_height)

        text_rect = QRectF(
            bar_rect.right() + padding_right,
            rect.top(),
            text_width,
            rect.height()
        )

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        # 1. Fond de la barre (Gris / PROGRESS_BG)
        painter.setBrush(QBrush(QColor(Colors.PROGRESS_BG)))
        painter.drawRoundedRect(bar_rect, 3, 3)

        max_val = total if total and total > 0 else max(watched, local, 1)

        # 2. Progression de la saison (Orange - si applicable)
        if season_prog > 0:
            season_width = bar_rect.width() * min(season_prog, 1.0)
            season_rect = QRectF(bar_rect.left(), bar_rect.top(), season_width, bar_rect.height())
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_SEASON)))
            painter.drawRoundedRect(season_rect, 3, 3)

        # 3. Barre principale des épisodes vus (Vert - PROGRESS_WATCHED)
        # Elle prend toute la hauteur de la barre
        if watched > 0:
            watched_width = bar_rect.width() * min(watched / max_val, 1.0)
            watched_rect = QRectF(bar_rect.left(), bar_rect.top(), watched_width, bar_rect.height())
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_WATCHED)))
            painter.drawRoundedRect(watched_rect, 3, 3)

        # 4. Fine ligne rouge pour les épisodes locaux (Rouge - PROGRESS_LOCAL)
        # Dessinée sous forme de fine bande horizontale au milieu de la barre (ex: hauteur de 4px)
            # 4. Fine ligne rouge pour les épisodes locaux (Rouge - PROGRESS_LOCAL) collée en bas
            # 4. Fine ligne rouge pour les épisodes locaux (Rouge - PROGRESS_LOCAL) collée tout en bas
            if local > 0:
                local_width = bar_rect.width() * min(local / max_val, 1.0)
                line_height = 4  # Épaisseur de la ligne
                # Collée strictement sur le bord inférieur du conteneur
                line_top = bar_rect.bottom() - line_height
                local_rect = QRectF(bar_rect.left(), line_top, local_width, line_height)
                painter.setBrush(QBrush(QColor(Colors.PROGRESS_LOCAL)))
                # Un léger arrondi de 1 pixel pour suivre la forme de la barre principale
                painter.drawRoundedRect(local_rect, 1, 1)

        # 5. Texte à droite
        painter.setPen(QColor(Colors.TEXT_PRIMARY))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()


class ContentView(QWidget):
    """Zone de contenu principale avec les onglets de statut (façon Taiga)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        self.local_db_data = self._load_test_database()
        self.local_cache_data = self._load_local_cache()

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

        self._init_ui()

    def _load_test_database(self) -> list:
        try:
            test_file_path = Path(__file__).resolve().parent.parent.parent / "test" / "api_test.json"
            if test_file_path.exists():
                with open(test_file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    return content.get("data", [])
        except Exception as e:
            print(f"[TEST WARNING] Impossible de charger le fichier de test MAL: {e}")
        return []

    def _load_local_cache(self) -> dict:
        """Charge le cache local des épisodes (anime_db.json)."""
        try:
            # S'adapte selon l'emplacement (cache/ ou test/)
            base_path = Path(__file__).resolve().parent.parent.parent
            cache_path = base_path / "cache" / "anime_db.json"
            if not cache_path.exists():
                cache_path = base_path / "test" / "anime_db.json"  # Fallback si test

            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[TEST WARNING] Impossible de charger le cache local anime_db.json: {e}")
        return {}

    def _get_local_episodes_count(self, anime_title: str) -> int:
        """Calcule le nombre d'épisodes disponibles en local pour un titre donné."""
        if not self.local_cache_data or not anime_title:
            return 0

        # Recherche exacte ou correspondance insensible à la casse / flexible dans le cache
        matched_entry = None
        if anime_title in self.local_cache_data:
            matched_entry = self.local_cache_data[anime_title]
        else:
            # Recherche souple si le nom diffère légèrement
            for key in self.local_cache_data:
                if key.lower() in anime_title.lower() or anime_title.lower() in key.lower():
                    matched_entry = self.local_cache_data[key]
                    break

        if not matched_entry:
            return 0

        # Somme des épisodes trouvés à travers toutes les saisons pour cet animé
        total_local = 0
        for season_name, season_data in matched_entry.items():
            if isinstance(season_data, dict) and "episodes" in season_data:
                total_local += len(season_data["episodes"])

        return total_local

    def _count_by_status(self, status_id: str) -> int:
        return sum(
            1 for item in self.local_db_data
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
            tab_name = tr.get(tab_info['key'], count=tab_info['count'])
            table_widget = self._create_table_for_status(tab_info['id'])
            self.tabs.addTab(table_widget, tab_name)
            self.tables[tab_info['id']] = table_widget

        layout.addWidget(self.tabs)

    def _create_table_for_status(self, status_id: str) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(len(self.columns_config))
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

        v_header = table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v_header.setDefaultSectionSize(36)

        table.setItemDelegateForColumn(1, ProgressDelegate(table))

        filtered_items = [
            item for item in self.local_db_data
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
            table.setItem(row_idx, 0, create_read_only_item(anime_title))

            watched = list_status.get("num_episodes_watched", 0)
            total_episodes = node.get("num_episodes", 0) or 0
            user_status = list_status.get("status", status_id)

            # Récupération du nombre d'épisodes dispo en local depuis le cache
            local_episodes = self._get_local_episodes_count(anime_title)

            progress_item = QTableWidgetItem()
            progress_item.setData(Qt.ItemDataRole.UserRole, {
                "watched": watched,
                "total": total_episodes,
                "local": local_episodes,  # 👈 Injecté ici pour la barre rouge !
                "season_progress": 0.0,
                "status": user_status
            })
            progress_item.setFlags(progress_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, 1, progress_item)

            table.setItem(row_idx, 2, create_read_only_item("-"))

            score = list_status.get("score", 0)
            table.setItem(row_idx, 3, create_read_only_item(str(score)))

            updated_at = list_status.get("updated_at", "-")
            table.setItem(row_idx, 4, create_read_only_item(updated_at))

            for col_i in range(5, len(self.columns_config)):
                table.setItem(row_idx, col_i, create_read_only_item("-"))

        self._apply_global_columns_visibility(table)
        return table

    def _apply_global_columns_visibility(self, table: QTableWidget):
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

        for table in self.tables.values():
            self._apply_global_columns_visibility(table)

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
            action = menu.addAction(tr.get(col["key"]))
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.triggered.connect(lambda checked, idx=index: self._set_column_visible_globally(idx, checked))

        menu.addSeparator()
        reset_action = menu.addAction(tr.get("menu_reset_defaults"))
        reset_action.triggered.connect(self._reset_all_tables_to_defaults)

        menu.exec(header.mapToGlobal(pos))

    def retranslate_ui(self):
        for index, tab_info in enumerate(self.tabs_data):
            new_tab_name = tr.get(tab_info['key'], count=tab_info['count'])
            self.tabs.setTabText(index, new_tab_name)

        for table in self.tables.values():
            table.setHorizontalHeaderLabels([tr.get(col["key"]) for col in self.columns_config])