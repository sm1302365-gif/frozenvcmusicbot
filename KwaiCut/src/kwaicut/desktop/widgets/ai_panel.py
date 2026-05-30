"""The AI Studio side panel.

Exposes the AI capabilities as buttons. Each emits a signal carrying the action
id so the main window can dispatch to the backend / provider registry without
this widget knowing anything about the implementation.
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

_ACTIONS: list[tuple[str, str]] = [
    ("auto_edit", "AI Auto Editor"),
    ("text_to_video", "AI Text-to-Video"),
    ("image_to_video", "AI Image-to-Video"),
    ("auto_captions", "Auto Captions"),
    ("scene_detect", "Smart Scene Detection"),
    ("highlight", "Highlight Detection"),
    ("bg_replace", "Background Replacement"),
    ("object_removal", "Object Removal"),
    ("voice_generate", "AI Voice Generator"),
    ("noise_removal", "AI Noise Removal"),
    ("dub", "AI Dubbing"),
    ("thumbnail", "Thumbnail Generator"),
]


class AIPanel(QScrollArea):
    """Scrollable list of AI action buttons."""

    action_triggered = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title = QLabel("AI Studio")
        title.setObjectName("Title")
        layout.addWidget(title)

        for action_id, label in _ACTIONS:
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, a=action_id: self.action_triggered.emit(a))
            layout.addWidget(button)

        layout.addStretch(1)
        self.setWidget(container)
