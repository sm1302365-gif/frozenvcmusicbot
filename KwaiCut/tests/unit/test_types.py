from __future__ import annotations

from fractions import Fraction

from kwaicut.common.types import Resolution, RGBAColor, TimeCode


def test_timecode_seconds_roundtrip():
    tc = TimeCode.from_seconds(2.5)
    assert tc.micros == 2_500_000
    assert tc.seconds == 2.5


def test_timecode_frame_conversion():
    fps = Fraction(30, 1)
    tc = TimeCode.from_frames(45, fps)
    assert tc.to_frames(fps) == 45


def test_timecode_arithmetic_and_ordering():
    a = TimeCode.from_seconds(1)
    b = TimeCode.from_seconds(2)
    assert (a + b).seconds == 3
    assert (b - a).seconds == 1
    assert a < b


def test_resolution_aspect_ratio():
    assert Resolution(1920, 1080).aspect_ratio == 1920 / 1080
    assert str(Resolution(1280, 720)) == "1280x720"


def test_rgba_hex():
    assert RGBAColor(255, 0, 128).to_hex() == "#ff0080ff"
