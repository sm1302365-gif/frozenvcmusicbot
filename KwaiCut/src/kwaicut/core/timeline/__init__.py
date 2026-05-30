"""Timeline model + editing operations."""

from __future__ import annotations

from kwaicut.core.timeline.keyframes import Easing, Keyframe, KeyframeTrack
from kwaicut.core.timeline.models import (
    BlendMode,
    Clip,
    Effect,
    Timeline,
    Track,
    TrackKind,
    Transform,
)
from kwaicut.core.timeline.operations import (
    ripple_delete,
    set_speed,
    split_clip,
    trim_clip,
)

__all__ = [
    "Easing",
    "Keyframe",
    "KeyframeTrack",
    "BlendMode",
    "Clip",
    "Effect",
    "Timeline",
    "Track",
    "TrackKind",
    "Transform",
    "split_clip",
    "trim_clip",
    "ripple_delete",
    "set_speed",
]
