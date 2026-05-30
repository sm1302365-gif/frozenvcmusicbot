from __future__ import annotations

from kwaicut.common.types import TimeCode
from kwaicut.core.timeline.keyframes import Easing, Keyframe, KeyframeTrack


def _track() -> KeyframeTrack:
    track = KeyframeTrack(name="opacity", default=1.0)
    track.add(Keyframe(TimeCode.from_seconds(0), 0.0, Easing.LINEAR))
    track.add(Keyframe(TimeCode.from_seconds(2), 1.0, Easing.LINEAR))
    return track


def test_default_when_empty():
    assert KeyframeTrack("scale", default=0.5).value_at(TimeCode.from_seconds(3)) == 0.5


def test_linear_interpolation_midpoint():
    track = _track()
    assert track.value_at(TimeCode.from_seconds(1)) == 0.5


def test_clamping_outside_range():
    track = _track()
    assert track.value_at(TimeCode.from_seconds(-1)) == 0.0
    assert track.value_at(TimeCode.from_seconds(5)) == 1.0


def test_hold_easing_steps():
    track = KeyframeTrack("x")
    track.add(Keyframe(TimeCode.from_seconds(0), 10.0))
    track.add(Keyframe(TimeCode.from_seconds(2), 20.0, Easing.HOLD))
    # HOLD keeps the previous value until it reaches the next keyframe.
    assert track.value_at(TimeCode.from_seconds(1.9)) == 10.0


def test_add_replaces_same_time():
    track = KeyframeTrack("x")
    track.add(Keyframe(TimeCode.from_seconds(1), 5.0))
    track.add(Keyframe(TimeCode.from_seconds(1), 9.0))
    assert len(track.keyframes) == 1
    assert track.keyframes[0].value == 9.0


def test_is_animated():
    assert _track().is_animated is True
    assert KeyframeTrack("x").is_animated is False
