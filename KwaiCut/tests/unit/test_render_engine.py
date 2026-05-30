from __future__ import annotations

from kwaicut.common.types import TimeCode
from kwaicut.core.rendering.presets import (
    Container,
    ExportPreset,
    ResolutionPreset,
    VideoCodec,
)
from kwaicut.core.rendering.render_engine import RenderEngine
from kwaicut.core.timeline import Clip, Timeline, TrackKind


def _timeline() -> Timeline:
    timeline = Timeline()
    video = timeline.add_track(TrackKind.VIDEO)
    audio = timeline.add_track(TrackKind.AUDIO)
    video.add_clip(
        Clip(
            asset_id="vid",
            kind=TrackKind.VIDEO,
            start=TimeCode.from_seconds(0),
            source_in=TimeCode.from_seconds(0),
            source_out=TimeCode.from_seconds(5),
        )
    )
    audio.add_clip(
        Clip(
            asset_id="aud",
            kind=TrackKind.AUDIO,
            start=TimeCode.from_seconds(0),
            source_in=TimeCode.from_seconds(0),
            source_out=TimeCode.from_seconds(5),
        )
    )
    return timeline


def test_compile_builds_expected_args():
    engine = RenderEngine(resolve_asset=lambda asset_id: f"/media/{asset_id}.mp4")
    preset = ExportPreset(resolution=ResolutionPreset.P1080, codec=VideoCodec.H264)
    plan = engine.compile(_timeline(), "/tmp/out.mp4", preset)

    # Both assets are wired as inputs.
    assert plan.args.count("-i") == 2
    assert "/media/vid.mp4" in plan.args
    assert "/media/aud.mp4" in plan.args

    # A filter graph and output mapping are present.
    assert "-filter_complex" in plan.args
    fc = plan.args[plan.args.index("-filter_complex") + 1]
    assert "overlay" in fc
    assert "amix" in fc
    assert plan.args[-1] == "/tmp/out.mp4"
    assert plan.duration_seconds == 5


def test_resolution_preset_sizes():
    assert ExportPreset(resolution=ResolutionPreset.P2160).size.width == 3840
    assert ExportPreset(resolution=ResolutionPreset.P720).size.height == 720


def test_transparent_export_forces_alpha_codec():
    preset = ExportPreset(transparent=True, container=Container.MOV)
    args = preset.video_encoder_args()
    assert "prores_ks" in args
