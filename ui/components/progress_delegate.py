from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QBrush
from ui.colors import Colors


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

        # 1. Fond de la barre
        painter.setBrush(QBrush(QColor(Colors.PROGRESS_BG)))
        painter.drawRoundedRect(bar_rect, 3, 3)

        max_val = total if total and total > 0 else max(watched, local, 1)

        # 2. Progression de la saison
        if season_prog > 0:
            season_width = bar_rect.width() * min(season_prog, 1.0)
            season_rect = QRectF(bar_rect.left(), bar_rect.top(), season_width, bar_rect.height())
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_SEASON)))
            painter.drawRoundedRect(season_rect, 3, 3)

        # 3. Épisodes vus (Vert)
        if watched > 0:
            watched_width = bar_rect.width() * min(watched / max_val, 1.0)
            watched_rect = QRectF(bar_rect.left(), bar_rect.top(), watched_width, bar_rect.height())
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_WATCHED)))
            painter.drawRoundedRect(watched_rect, 3, 3)

        # 4. Épisodes locaux (Fine ligne rouge en bas)
        if local > 0:
            local_width = bar_rect.width() * min(local / max_val, 1.0)
            line_height = 4
            line_top = bar_rect.bottom() - line_height
            local_rect = QRectF(bar_rect.left(), line_top, local_width, line_height)
            painter.setBrush(QBrush(QColor(Colors.PROGRESS_LOCAL)))
            painter.drawRoundedRect(local_rect, 1, 1)

        # 5. Texte
        painter.setPen(QColor(Colors.TEXT_PRIMARY))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)

        painter.restore()