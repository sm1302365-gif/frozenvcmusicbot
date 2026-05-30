from __future__ import annotations

import pytest

from kwaicut.common.errors import TimelineError
from kwaicut.common.types import TimeCode
from kwaicut.core.timeline import (
    Clip,
    Timeline,
    TrackKind,
    ripple_delete,
    split_clip,
    trim_clip,
)


def _clip(start_s: float, dur_s: float, asset="a1") -> Clip:
    return Clip(
        asset_id=asset,
        kind=TrackKind.VIDEO,
        start=TimeCode.from_seconds(start_s),
        source_in=TimeCode.from_seconds(0),
        source_out=TimeCode.from_seconds(dur_s),
    )


def test_clip_duration_and_end():
    clip = _clip(1, 4)
    assert clip.duration.seconds == 4
    assert clip.end.seconds == 5


def test_clip_speed_scales_duration():
    clip = _clip(0, 4)
    clip.speed = 2.0
    assert clip.duration.seconds == 2  # 2x speed halves timeline duration


def test_track_rejects_overlap():
    timeline = Timeline()
    track = timeline.add_track(TrackKind.VIDEO)
    track.add_clip(_clip(0, 5))
    with pytest.raises(TimelineError):
        track.add_clip(_clip(2, 5))


def test_track_rejects_wrong_kind():
    timeline = Timeline()
    audio = timeline.add_track(TrackKind.AUDIO)
    with pytest.raises(TimelineError):
        audio.add_clip(_clip(0, 5))  # a video clip


def test_split_clip():
    timeline = Timeline()
    track = timeline.add_track(TrackKind.VIDEO)
    clip = _clip(0, 10)
    track.add_clip(clip)
    left, right = split_clip(track, clip.id, TimeCode.from_seconds(4))
    assert left.duration.seconds == 4
    assert right.start.seconds == 4
    assert right.duration.seconds == 6
    assert len(track.clips) == 2


def test_split_outside_clip_raises():
    timeline = Timeline()
    track = timeline.add_track(TrackKind.VIDEO)
    clip = _clip(0, 5)
    track.add_clip(clip)
    with pytest.raises(TimelineError):
        split_clip(track, clip.id, TimeCode.from_seconds(10))


def test_trim_clip_head():
    clip = _clip(0, 10)
    trim_clip(clip, new_start=TimeCode.from_seconds(2))
    assert clip.start.seconds == 2
    assert clip.source_in.seconds == 2
    assert clip.duration.seconds == 8


def test_ripple_delete_closes_gap():
    timeline = Timeline()
    track = timeline.add_track(TrackKind.VIDEO)
    a = _clip(0, 5)
    b = _clip(5, 5)
    track.add_clip(a)
    track.add_clip(b)
    ripple_delete(track, a.id)
    assert len(track.clips) == 1
    assert track.clips[0].start.seconds == 0  # b shifted left to fill the gap


def test_timeline_duration():
    timeline = Timeline()
    v = timeline.add_track(TrackKind.VIDEO)
    v.add_clip(_clip(0, 8))
    assert timeline.duration.seconds == 8
    assert timeline.frame_count == 240  # 8s * 30fps


def test_serialisation_roundtrip_keys():
    timeline = Timeline()
    track = timeline.add_track(TrackKind.VIDEO)
    track.add_clip(_clip(0, 3))
    data = timeline.to_dict()
    assert data["tracks"][0]["clips"][0]["asset_id"] == "a1"
    assert data["fps"] == [30, 1]
