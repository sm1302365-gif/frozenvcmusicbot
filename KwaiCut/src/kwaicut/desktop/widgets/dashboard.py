"""The dashboard view: project manager, recent projects and quick actions."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def _card(title: str, subtitle: str) -> QFrame:
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 16)
    name = QLabel(title)
    name.setObjectName("Title")
    desc = QLabel(subtitle)
    desc.setObjectName("Subtitle")
    desc.setWordWrap(True)
    layout.addWidget(name)
    layout.addWidget(desc)
    return card


class Dashboard(QWidget):
    """Landing surface with quick-create, recent projects and the asset library."""

    create_project_requested = pyqtSignal()
    open_project_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # Header row: greeting + quick create.
        header = QHBoxLayout()
        title = QLabel("Welcome to KwaiCut")
        title.setObjectName("Title")
        header.addWidget(title)
        header.addStretch(1)
        quick = QPushButton("+ Quick Create")
        quick.setObjectName("Accent")
        quick.clicked.connect(self.create_project_requested.emit)
        header.addWidget(quick)
        root.addLayout(header)

        # Feature cards.
        cards = QGridLayout()
        cards.setSpacing(16)
        cards.addWidget(_card("Project Manager", "Organise local & cloud projects"), 0, 0)
        cards.addWidget(_card("Template Marketplace", "Browse premium templates & packs"), 0, 1)
        cards.addWidget(_card("AI Assistant", "Generate, edit and caption with AI"), 0, 2)
        cards.addWidget(_card("Asset Library", "Manage media, music, fonts & stickers"), 1, 0)
        cards.addWidget(_card("Draft Recovery", "Restore unsaved work automatically"), 1, 1)
        cards.addWidget(_card("Cloud Projects", "Synced and ready on every device"), 1, 2)
        root.addLayout(cards)

        # Recent projects list.
        recent_label = QLabel("Recent Projects")
        recent_label.setObjectName("Subtitle")
        root.addWidget(recent_label)
        self.recent = QListWidget()
        self.recent.itemDoubleClicked.connect(
            lambda item: self.open_project_requested.emit(item.text())
        )
        root.addWidget(self.recent, stretch=1)

    def set_recent_projects(self, names: list[str]) -> None:
        self.recent.clear()
        self.recent.addItems(names or ["No recent projects yet — click Quick Create"])
        self.recent.setEnabled(bool(names))
        if not names:
            self.recent.setSelectionMode(QListWidget.SelectionMode.NoSelection)
            for i in range(self.recent.count()):
                self.recent.item(i).setForeground(Qt.GlobalColor.gray)
