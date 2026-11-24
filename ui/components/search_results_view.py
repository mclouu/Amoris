from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from ui.colors import Colors
from utils.translator import tr
from ui.components.progress_delegate import ProgressDelegate

# (id de statut MAL, clé i18n du libellé) dans l'ordre d'affichage
STATUS_ORDER = [
    ("watching", "tab_watching"),
    ("completed", "tab_completed"),
    ("on_hold", "tab_on_hold"),
    ("dropped", "tab_dropped"),
    ("plan_to_watch", "tab_plan_to_watch"),
]


class SearchResultsView(QTreeWidget):
    """Résultats de recherche globale, regroupés par statut (façon Taiga)."""

    anime_selected = pyqtSignal(int)          # ligne sélectionnée : met à jour la jaquette
    anime_activated = pyqtSignal(int, str)    # double-clic : lance l'épisode (ID MAL, titre)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels([tr.get("col_title"), tr.get("col_progress")])
        self.setRootIsDecorated(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setItemDelegateForColumn(1, ProgressDelegate(self))
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Colors.BG_MAIN};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                selection-background-color: {Colors.BG_SURFACE};
                outline: none;
            }}
            QTreeWidget::item {{ padding: 4px 0px; }}
            QTreeWidget::item:selected {{
                background-color: {Colors.BG_SURFACE};
                color: {Colors.TEXT_PRIMARY};
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
        self.currentItemChanged.connect(self._on_current_changed)
        self.itemDoubleClicked.connect(self._on_double_clicked)
        self.header().setStretchLastSection(False)
        self.setColumnWidth(1, 300)

    def set_results(self, entries: list, local_count):
        """entries : animés MAL correspondants. local_count(entry) -> nombre d'épisodes locaux."""
        self.clear()

        if not entries:
            self.addTopLevelItem(QTreeWidgetItem([tr.get("search_no_results"), ""]))
            return

        for status_id, label_key in STATUS_ORDER:
            group = [e for e in entries if e.get("list_status", {}).get("status") == status_id]
            if not group:
                continue

            header = QTreeWidgetItem([tr.get(label_key, count=len(group)), ""])
            header.setFlags(Qt.ItemFlag.ItemIsEnabled)  # non sélectionnable
            font = header.font(0)
            font.setBold(True)
            header.setFont(0, font)
            self.addTopLevelItem(header)

            for entry in group:
                node = entry.get("node", {})
                ls = entry.get("list_status", {})

                child = QTreeWidgetItem([node.get("title", ""), ""])
                # L'ID MAL reste la référence, comme dans les tableaux
                child.setData(0, Qt.ItemDataRole.UserRole, node.get("id"))
                child.setData(1, Qt.ItemDataRole.UserRole, {
                    "watched": ls.get("num_episodes_watched", 0),
                    "total": node.get("num_episodes", 0) or 0,
                    "local": local_count(entry),
                    "season_progress": 0.0,
                    "status": status_id,
                })
                header.addChild(child)

        self.expandAll()
        self.resizeColumnToContents(0)

    def _on_current_changed(self, current, _previous):
        if current is None:
            return
        mal_id = current.data(0, Qt.ItemDataRole.UserRole)
        if mal_id:
            self.anime_selected.emit(mal_id)

    def _on_double_clicked(self, item, _column):
        mal_id = item.data(0, Qt.ItemDataRole.UserRole)
        if mal_id:
            self.anime_activated.emit(mal_id, item.text(0))