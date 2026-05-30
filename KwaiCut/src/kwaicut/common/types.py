"""Value objects shared by the editing engine and the rest of the app.

These are intentionally small, immutable dataclasses. Immutability makes them
safe to share across threads (timeline reads happen on the UI thread while the
renderer runs on a worker) and trivial to hash/compare in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import NamedTuple

__all__ = ["TimeCode", "Resolution", "Rect", "RGBAColor", "Fraction"]


@dataclass(frozen=True, order=True)
class TimeCode:
    """A point in (or span of) time, stored as whole microseconds.

    Microsecond precision avoids the floating point drift that plagues naive
    ``float`` seconds when you accumulate thousands of edits, while still being
    convertible to frames for any frame rate.
    """

    micros: int

    @classmethod
    def from_seconds(cls, seconds: float) -> TimeCode:
        return cls(round(seconds * 1_000_000))

    @classmethod
    def from_frames(cls, frame: int, fps: Fraction) -> TimeCode:
        return cls(round(frame / fps * 1_000_000))

    @property
    def seconds(self) -> float:
        return self.micros / 1_000_000

    def to_frames(self, fps: Fraction) -> int:
        return round(self.seconds * fps)

    def __add__(self, other: TimeCode) -> TimeCode:
        return TimeCode(self.micros + other.micros)

    def __sub__(self, other: TimeCode) -> TimeCode:
        return TimeCode(self.micros - other.micros)


class Resolution(NamedTuple):
    """Pixel dimensions of a frame or canvas."""

    width: int
    height: int

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height else 0.0

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.width}x{self.height}"


class Rect(NamedTuple):
    """An axis-aligned rectangle in normalised [0, 1] canvas coordinates."""

    x: float
    y: float
    width: float
    height: float


class RGBAColor(NamedTuple):
    """An 8-bit-per-channel colour with alpha."""

    r: int
    g: int
    b: int
    a: int = 255

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.a:02x}"
