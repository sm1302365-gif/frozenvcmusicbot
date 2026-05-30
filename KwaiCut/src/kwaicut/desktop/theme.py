"""The KwaiCut dark theme (Qt Style Sheet).

A single QSS string implements the premium dark / glassmorphism look from the
spec: deep neutral surfaces, a vivid accent, soft rounded cards and subtle
borders that read as frosted panels. Loaded once in :func:`kwaicut.desktop.app`.
"""

from __future__ import annotations

# Palette ------------------------------------------------------------------
ACCENT = "#6C5CE7"
ACCENT_HOVER = "#7D6FF0"
BG = "#0F1115"
SURFACE = "#171A21"
SURFACE_2 = "#1F232C"
BORDER = "#2A2F3A"
TEXT = "#E8EAED"
TEXT_MUTED = "#9AA0AC"


def stylesheet() -> str:
    """Return the application-wide QSS string."""
    return f"""
    * {{
        color: {TEXT};
        font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QWidget {{ background-color: {BG}; }}

    #Sidebar {{
        background-color: {SURFACE};
        border-right: 1px solid {BORDER};
    }}

    QPushButton {{
        background-color: {SURFACE_2};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{ background-color: #262B36; }}
    QPushButton#Accent {{
        background-color: {ACCENT};
        border: none;
        font-weight: 600;
    }}
    QPushButton#Accent:hover {{ background-color: {ACCENT_HOVER}; }}

    QFrame#Card {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 16px;
    }}

    QLabel#Title {{ font-size: 22px; font-weight: 700; }}
    QLabel#Subtitle {{ color: {TEXT_MUTED}; font-size: 12px; }}

    QListWidget {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 6px;
    }}
    QListWidget::item {{ padding: 8px; border-radius: 8px; }}
    QListWidget::item:selected {{ background-color: {ACCENT}; }}

    #TimelineRuler {{ background-color: {SURFACE_2}; border-bottom: 1px solid {BORDER}; }}
    #TrackHeader {{ background-color: {SURFACE}; border-right: 1px solid {BORDER}; }}
    .ClipBlock {{ background-color: {ACCENT}; border-radius: 6px; }}
    """
