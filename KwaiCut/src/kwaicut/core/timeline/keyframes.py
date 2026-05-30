"""Keyframe animation: easing curves and an animatable property track.

A :class:`KeyframeTrack` holds an ordered list of :class:`Keyframe` points for a
single scalar property (opacity, scale, volume, ...). Querying it with
:meth:`KeyframeTrack.value_at` returns the interpolated value at any time, which
is what both the renderer (to build FFmpeg expressions) and the UI (to draw the
property curve) rely on.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from kwaicut.common.types import TimeCode


class Easing(str, Enum):
    """Interpolation curve used between two keyframes."""

    HOLD = "hold"            # step: keep previous value until the next keyframe
    LINEAR = "linear"
    EASE_IN = "ease_in"      # quadratic
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


def _apply_easing(t: float, easing: Easing) -> float:
    """Map a normalised progress ``t`` in [0, 1] through an easing curve."""
    t = min(1.0, max(0.0, t))
    if easing is Easing.HOLD:
        return 0.0
    if easing is Easing.LINEAR:
        return t
    if easing is Easing.EASE_IN:
        return t * t
    if easing is Easing.EASE_OUT:
        return 1.0 - (1.0 - t) * (1.0 - t)
    if easing is Easing.EASE_IN_OUT:
        return 0.5 * (1.0 - math.cos(math.pi * t))
    return t  # pragma: no cover - exhaustive above


@dataclass(frozen=True, order=True)
class Keyframe:
    """A single animation control point.

    ``order=True`` plus ``time`` being the first field means keyframes sort
    chronologically out of the box.
    """

    time: TimeCode
    value: float
    easing: Easing = field(default=Easing.LINEAR, compare=False)


@dataclass
class KeyframeTrack:
    """An animatable scalar property defined by a set of keyframes."""

    name: str
    default: float = 0.0
    keyframes: list[Keyframe] = field(default_factory=list)

    def add(self, keyframe: Keyframe) -> None:
        """Insert a keyframe, replacing any existing one at the same time."""
        self.keyframes = [k for k in self.keyframes if k.time != keyframe.time]
        self.keyframes.append(keyframe)
        self.keyframes.sort()

    @property
    def is_animated(self) -> bool:
        return len(self.keyframes) >= 2

    def value_at(self, time: TimeCode) -> float:
        """Return the interpolated value at ``time``.

        Before the first / after the last keyframe the value is clamped to that
        keyframe (a standard NLE convention). With no keyframes the property's
        :attr:`default` is returned.
        """
        if not self.keyframes:
            return self.default
        if time <= self.keyframes[0].time:
            return self.keyframes[0].value
        if time >= self.keyframes[-1].time:
            return self.keyframes[-1].value

        # Find the bracketing pair [left, right].
        for left, right in zip(self.keyframes, self.keyframes[1:], strict=False):
            if left.time <= time <= right.time:
                span = (right.time - left.time).micros
                if span == 0:
                    return right.value
                progress = (time - left.time).micros / span
                eased = _apply_easing(progress, right.easing)
                return left.value + (right.value - left.value) * eased
        return self.keyframes[-1].value  # pragma: no cover - unreachable
