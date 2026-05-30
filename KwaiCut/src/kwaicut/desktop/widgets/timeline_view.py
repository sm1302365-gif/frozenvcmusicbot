"""A custom-painted multi-track timeline widget.

Renders a :class:`~kwaicut.core.timeline.models.Timeline` as horizontal tracks of
clip blocks with a time ruler. It is read-oriented for now (the data model and
:mod:`kwaicut.core.timeline.operations` already implement the editing logic);
mouse interaction maps pixel positions back to :class:`TimeCode` via
:meth:`TimelineView.x_to_time`.
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from kwaicut.common.types import TimeCode
from kwaicut.core.timeline.models import Timeline, TrackKind

_TRACK_HEIGHT = 56
_RULER_HEIGHT = 28
_HEADER_WIDTH = 120


class TimelineView(QWidget):
    """Paints tracks and clips; pixels-per-second drives the zoom level."""

    def __init__(self, timeline: Timeline | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timeline = timeline or Timeline()
        self._pixels_per_second = 60.0
        self.setMinimumHeight(_RULER_HEIGHT + _TRACK_HEIGHT * 3)

    def set_timeline(self, timeline: Timeline) -> None:
        self._timeline = timeline
        self.update()

    def set_zoom(self, pixels_per_second: float) -> None:
        self._pixels_per_second = max(4.0, pixels_per_second)
        self.update()

    def x_to_time(self, x: float) -> TimeCode:
        seconds = max(0.0, (x - _HEADER_WIDTH) / self._pixels_per_second)
        return TimeCode.from_seconds(seconds)

    def time_to_x(self, time: TimeCode) -> float:
        return _HEADER_WIDTH + time.seconds * self._pixels_per_second

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0F1115"))

        self._paint_ruler(painter)
        for index, track in enumerate(self._timeline.tracks):
            top = _RULER_HEIGHT + index * _TRACK_HEIGHT
            self._paint_track(painter, track, top)

    def _paint_ruler(self, painter: QPainter) -> None:
        painter.fillRect(0, 0, self.width(), _RULER_HEIGHT, QColor("#1F232C"))
        painter.setPen(QColor("#9AA0AC"))
        seconds = int(self._timeline.duration.seconds) + 2
        for sec in range(seconds):
            x = self.time_to_x(TimeCode.from_seconds(sec))
            painter.drawLine(int(x), 0, int(x), _RULER_HEIGHT)
            painter.drawText(int(x) + 3, 18, f"{sec}s")

    def _paint_track(self, painter: QPainter, track, top: int) -> None:
        painter.fillRect(0, top, _HEADER_WIDTH, _TRACK_HEIGHT, QColor("#171A21"))
        painter.setPen(QColor("#E8EAED"))
        painter.drawText(10, top + _TRACK_HEIGHT // 2 + 4, track.name)

        clip_color = QColor("#6C5CE7") if track.kind is TrackKind.VIDEO else QColor("#00B894")
        for clip in track.clips:
            x = self.time_to_x(clip.start)
            width = clip.duration.seconds * self._pixels_per_second
            rect = QRectF(x, top + 6, max(2.0, width), _TRACK_HEIGHT - 12)
            painter.setBrush(clip_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
            painter.setPen(QColor("#FFFFFF"))
            label = clip.label or clip.asset_id
            painter.drawText(rect.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter, label)
