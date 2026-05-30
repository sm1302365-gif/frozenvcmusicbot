"""Desktop client entry point and main window.

Run with ``kwaicut-desktop`` (after ``pip install kwaicut[desktop]``) or
``python -m kwaicut.desktop.app``. PyQt6 is imported inside :func:`main` so the
console script fails with a helpful message rather than an ImportError traceback
when Qt is not installed.
"""

from __future__ import annotations

import sys

from kwaicut.common.logging_config import get_logger

logger = get_logger(__name__)


def main() -> int:
    """Launch the KwaiCut desktop application."""
    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QHBoxLayout,
            QMainWindow,
            QStackedWidget,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print(
            "PyQt6 is not installed. Install the desktop extra:\n"
            "    pip install 'kwaicut[desktop]'",
            file=sys.stderr,
        )
        return 1

    from kwaicut.core.timeline.models import Timeline, TrackKind
    from kwaicut.desktop.theme import stylesheet
    from kwaicut.desktop.widgets.ai_panel import AIPanel
    from kwaicut.desktop.widgets.dashboard import Dashboard
    from kwaicut.desktop.widgets.timeline_view import TimelineView

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("KwaiCut")
            self.resize(1280, 800)

            self._stack = QStackedWidget()
            self._dashboard = Dashboard()
            self._dashboard.create_project_requested.connect(self._open_editor)
            self._stack.addWidget(self._dashboard)
            self._stack.addWidget(self._build_editor(Timeline, TrackKind, TimelineView, AIPanel))
            self.setCentralWidget(self._stack)

            self._dashboard.set_recent_projects([])

        def _build_editor(self, Timeline, TrackKind, TimelineView, AIPanel) -> QWidget:
            editor = QWidget()
            layout = QHBoxLayout(editor)
            layout.setContentsMargins(0, 0, 0, 0)

            # A small demo timeline so the editor isn't empty on first open.
            timeline = Timeline()
            timeline.add_track(TrackKind.VIDEO, "Video 1")
            timeline.add_track(TrackKind.VIDEO, "Video 2")
            timeline.add_track(TrackKind.AUDIO, "Audio 1")

            center = QWidget()
            center_layout = QVBoxLayout(center)
            center_layout.addWidget(TimelineView(timeline), stretch=1)
            layout.addWidget(center, stretch=4)

            ai_panel = AIPanel()
            ai_panel.action_triggered.connect(lambda a: logger.info("AI action: %s", a))
            layout.addWidget(ai_panel, stretch=1)
            return editor

        def _open_editor(self) -> None:
            self._stack.setCurrentIndex(1)

    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet())
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
