"""The timeline data model: clips, tracks and the timeline itself.

The model is deliberately decoupled from rendering and persistence. It only
describes *what* the edit is; :mod:`kwaicut.core.rendering` decides *how* to turn
it into pixels, and :mod:`kwaicut.db` decides how to store it. Every object is
JSON-serialisable via :meth:`to_dict` so projects can be saved, synced to the
cloud and diffed for version history.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

from kwaicut.common.errors import TimelineError
from kwaicut.common.types import Rect, TimeCode
from kwaicut.core.timeline.keyframes import KeyframeTrack


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TrackKind(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


class BlendMode(str, Enum):
    """Compositing modes available for video clips."""

    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    ADD = "add"
    DIFFERENCE = "difference"


@dataclass
class Transform:
    """Spatial placement of a clip on the canvas (normalised coordinates)."""

    position_x: float = 0.5
    position_y: float = 0.5
    scale: float = 1.0
    rotation: float = 0.0
    crop: Rect | None = None

    def to_dict(self) -> dict:
        return {
            "position_x": self.position_x,
            "position_y": self.position_y,
            "scale": self.scale,
            "rotation": self.rotation,
            "crop": list(self.crop) if self.crop else None,
        }


@dataclass
class Effect:
    """A named effect with a free-form parameter bag.

    Concrete effects (LUTs, glitch, chroma key, ...) are registered in the
    rendering layer; the timeline only stores the *intent* so the model stays
    backend-agnostic.
    """

    name: str
    params: dict = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> dict:
        return {"name": self.name, "params": self.params, "enabled": self.enabled}


@dataclass
class Clip:
    """A trimmed segment of a source asset placed on a track.

    Times split into two coordinate systems:

    * ``start`` is the clip's position **on the timeline**.
    * ``source_in`` / ``source_out`` define the in/out points **inside the
      source asset**. ``speed`` scales source time to timeline time.
    """

    asset_id: str
    kind: TrackKind
    start: TimeCode
    source_in: TimeCode
    source_out: TimeCode
    id: str = field(default_factory=lambda: _new_id("clip"))
    speed: float = 1.0
    reversed: bool = False
    opacity: float = 1.0
    volume: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    transform: Transform = field(default_factory=Transform)
    effects: list[Effect] = field(default_factory=list)
    animations: dict[str, KeyframeTrack] = field(default_factory=dict)
    label: str = ""

    def __post_init__(self) -> None:
        if self.source_out <= self.source_in:
            raise TimelineError("source_out must be greater than source_in")
        if self.speed <= 0:
            raise TimelineError("speed must be positive")

    @property
    def source_duration(self) -> TimeCode:
        """Length of the selected region inside the source asset."""
        return self.source_out - self.source_in

    @property
    def duration(self) -> TimeCode:
        """Length the clip occupies on the timeline (after speed scaling)."""
        return TimeCode(round(self.source_duration.micros / self.speed))

    @property
    def end(self) -> TimeCode:
        return self.start + self.duration

    def overlaps(self, other: Clip) -> bool:
        return self.start < other.end and other.start < self.end

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "kind": self.kind.value,
            "start_us": self.start.micros,
            "source_in_us": self.source_in.micros,
            "source_out_us": self.source_out.micros,
            "speed": self.speed,
            "reversed": self.reversed,
            "opacity": self.opacity,
            "volume": self.volume,
            "blend_mode": self.blend_mode.value,
            "transform": self.transform.to_dict(),
            "effects": [e.to_dict() for e in self.effects],
            "label": self.label,
        }


@dataclass
class Track:
    """An ordered lane of non-overlapping clips of a single kind."""

    kind: TrackKind
    name: str = ""
    id: str = field(default_factory=lambda: _new_id("track"))
    clips: list[Clip] = field(default_factory=list)
    muted: bool = False
    hidden: bool = False
    locked: bool = False

    def add_clip(self, clip: Clip) -> None:
        """Add ``clip`` keeping the track sorted and overlap-free."""
        if clip.kind is not self.kind:
            raise TimelineError(
                f"cannot add {clip.kind.value} clip to {self.kind.value} track"
            )
        for existing in self.clips:
            if existing.overlaps(clip):
                raise TimelineError(
                    f"clip {clip.id} overlaps existing clip {existing.id}"
                )
        self.clips.append(clip)
        self.clips.sort(key=lambda c: c.start.micros)

    def remove_clip(self, clip_id: str) -> Clip:
        for i, clip in enumerate(self.clips):
            if clip.id == clip_id:
                return self.clips.pop(i)
        raise TimelineError(f"clip {clip_id} not found on track {self.id}")

    def clip_at(self, time: TimeCode) -> Clip | None:
        for clip in self.clips:
            if clip.start <= time < clip.end:
                return clip
        return None

    @property
    def duration(self) -> TimeCode:
        return TimeCode(max((c.end.micros for c in self.clips), default=0))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "name": self.name,
            "muted": self.muted,
            "hidden": self.hidden,
            "locked": self.locked,
            "clips": [c.to_dict() for c in self.clips],
        }


@dataclass
class Timeline:
    """The full multi-track sequence being edited."""

    fps: Fraction = Fraction(30, 1)
    width: int = 1920
    height: int = 1080
    id: str = field(default_factory=lambda: _new_id("timeline"))
    tracks: list[Track] = field(default_factory=list)

    def add_track(self, kind: TrackKind, name: str = "") -> Track:
        track = Track(kind=kind, name=name or f"{kind.value.title()} {len(self.tracks) + 1}")
        self.tracks.append(track)
        return track

    def get_track(self, track_id: str) -> Track:
        for track in self.tracks:
            if track.id == track_id:
                return track
        raise TimelineError(f"track {track_id} not found")

    @property
    def video_tracks(self) -> list[Track]:
        return [t for t in self.tracks if t.kind is TrackKind.VIDEO]

    @property
    def audio_tracks(self) -> list[Track]:
        return [t for t in self.tracks if t.kind is TrackKind.AUDIO]

    @property
    def duration(self) -> TimeCode:
        return TimeCode(max((t.duration.micros for t in self.tracks), default=0))

    @property
    def frame_count(self) -> int:
        return self.duration.to_frames(self.fps)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fps": [self.fps.numerator, self.fps.denominator],
            "width": self.width,
            "height": self.height,
            "tracks": [t.to_dict() for t in self.tracks],
        }
