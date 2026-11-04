from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTableWidget, QHeaderView, QMenu, QTableWidgetItem, \
    QStyledItemDelegate
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
import json
from pathlib import Path
from ui.colors import Colors
from utils.translator import tr


class ProgressDelegate(QStyledItemDelegate):
    """Délégué personnalisé pour dessiner la barre de progression et le texte à droite."""

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

        rect = option.rect

        # Format du texte (ex: 17/?)
        total_str = str(total) if total and total > 0 else "?"
        text = f"{watched}/{total_str}"

        # Calcul de la largeur réservée pour le texte à droite (environ 45-50 pixels)
        text_width = 45
        padding_right = 10

        # Rectangle de la barre (laissé un peu plus court à droite pour laisser de la place au texte)
        bar_height = 14
        margin_v = (rect.height() - bar_height) // 2
        bar_width = rect.width() - text_width - padding_right - 12
        bar_rect = QRectF(rect.left() + 8, rect.top() + margin_v, bar_width, bar_height)

        # Rectangle pour le texte à droite de la barre
        text_rect = QRectF(
            bar_rect.right() + padding_right,
            rect.top(),
            text_width,
            rect.height()
        )

        # 1. Dessin du fond de la barre (PROGRESS_BG)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.PROGRESS_BG)))
        painter.drawRoundedRect(bar_rect, 3, 3)

        max_val = total if total and total > 0 else max(watched, local, 1)

        # 2. Dessin de la progression de la saison
        if season_prog > 0:
            season_width = bar_rect.width() * min(season_prog, 1.0)
            season_rect = QRectF(bar_rect.left(), bar_rect.top(), season_width, bar_rect.height())
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_SEASON)))
            painter.drawRoundedRect(season_rect, 3, 3)

        # 3. Dessin des épisodes locaux (Rouge)
        if local > 0:
            local_width = bar_rect.width() * min(local / max_val, 1.0)
            local_rect = QRectF(bar_rect.left(), bar_rect.top(), local_width, bar_rect.height())
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_LOCAL)))
            painter.drawRoundedRect(local_rect, 3, 3)

        # 4. Dessin des épisodes vus (Vert/Teal)
        if watched > 0:
            watched_width = bar_rect.width() * min(watched / max_val, 1.0)
            watched_rect = QRectF(bar_rect.left(), bar_rect.top(), watched_width, bar_rect.height())
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_WATCHED)))
            painter.drawRoundedRect(watched_rect, 3, 3)

        # 5. Dessin du texte à droite de la barre
        painter.setPen(QColor(Colors.TEXT_PRIMARY))
        # Optionnel : rendre un peu plus discret le '?' si le total est inconnu
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()


class ContentView(QWidget):
    """Zone de contenu principale avec les onglets de statut (façon Taiga)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_MAIN};")

        self.local_db_data = self._load_test_database()

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
            print(f"[TEST WARNING] Impossible de charger le fichier de test: {e}")
        return []

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

        # Application du délégué personnalisé sur la colonne Progression (index 1)
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

            # Colonne 0 : Titre
            table.setItem(row_idx, 0, create_read_only_item(node.get("title", "Unknown")))

            # Colonne 1 : Progression (On injecte les données structurées via UserRole)
            watched = list_status.get("num_episodes_watched", 0)
            total_episodes = node.get("num_episodes", 0)  # Récupéré si présent dans le JSON, sinon 0 / inconnu

            progress_item = QTableWidgetItem()
            progress_item.setData(Qt.ItemDataRole.UserRole, {
                "watched": watched,
                "total": total_episodes,
                "local": 0,  # Sera branché plus tard avec le scanner local
                "season_progress": 0.0  # Sera branché plus tard avec la date/saison
            })
            progress_item.setFlags(progress_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, 1, progress_item)

            # Colonne 2 : Saison
            table.setItem(row_idx, 2, create_read_only_item("-"))

            # Colonne 3 : Score
            score = list_status.get("score", 0)
            table.setItem(row_idx, 3, create_read_only_item(str(score)))

            # Colonne 4 : Dernière mise à jour
            updated_at = list_status.get("updated_at", "-")
            table.setItem(row_idx, 4, create_read_only_item(updated_at))

            for col_i in range(5, len(self.columns_config)):
                table.setItem(row_idx, col_i, create_read_only_item("-"))

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
            action = menu.addAction(tr.get(col["key"]))
            action.setCheckable(True)
            action.setChecked(is_visible)
            action.triggered.connect(lambda checked, idx=index, t=table: t.setColumnHidden(idx, not checked))

        menu.addSeparator()
        reset_action = menu.addAction(tr.get("menu_reset_defaults"))
        reset_action.triggered.connect(lambda: self._reset_table_to_defaults(table))

        menu.exec(header.mapToGlobal(pos))

    def retranslate_ui(self):
        for index, tab_info in enumerate(self.tabs_data):
            new_tab_name = tr.get(tab_info['key'], count=tab_info['count'])
            self.tabs.setTabText(index, new_tab_name)

        for table in self.tables.values():
            table.setHorizontalHeaderLabels([tr.get(col["key"]) for col in self.columns_config])