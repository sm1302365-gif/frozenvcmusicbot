"""Compile a :class:`~kwaicut.core.timeline.models.Timeline` into FFmpeg args.

This is the heart of the rendering pipeline. It walks the timeline and builds a
single ``-filter_complex`` graph that:

* trims each clip to its source in/out points,
* applies speed (``setpts`` / ``atempo``) and reverse,
* scales/places video clips onto a base canvas and overlays them in track order,
* delays, gain-adjusts and mixes audio clips.

The output is a plain ``list[str]`` of FFmpeg arguments, which keeps this module
pure and unit-testable (no process is spawned here). Path resolution is injected
via ``resolve_asset`` so the engine never touches the database directly.
"""

from __future__ import annotations

from collections.abc import Callable

from kwaicut.core.rendering.presets import ExportPreset
from kwaicut.core.timeline.models import Clip, Timeline, TrackKind

AssetResolver = Callable[[str], str]


class RenderPlan:
    """The compiled FFmpeg invocation for a timeline render."""

    def __init__(self, args: list[str], duration_seconds: float) -> None:
        self.args = args
        self.duration_seconds = duration_seconds


class RenderEngine:
    """Translate the timeline model into an FFmpeg filter graph."""

    def __init__(self, resolve_asset: AssetResolver) -> None:
        self._resolve = resolve_asset

    def compile(
        self, timeline: Timeline, output_path: str, preset: ExportPreset
    ) -> RenderPlan:
        size = preset.size
        duration = timeline.duration.seconds

        inputs: list[str] = []
        filters: list[str] = []

        # Base canvas: a solid colour source spanning the whole timeline. Every
        # video clip is overlaid on top of this in track/clip order.
        filters.append(
            f"color=c=black:s={size.width}x{size.height}:r={preset.fps}:d={duration:.3f}[base]"
        )
        last_video_label = "base"
        input_index = 0
        audio_labels: list[str] = []

        for track in timeline.tracks:
            if track.hidden or track.muted and track.kind is TrackKind.AUDIO:
                if track.muted and track.kind is TrackKind.AUDIO:
                    continue
            for clip in track.clips:
                path = self._resolve(clip.asset_id)
                inputs += ["-i", path]
                if clip.kind is TrackKind.VIDEO and not track.hidden:
                    last_video_label = self._video_clip_filter(
                        filters, clip, input_index, last_video_label, size, preset
                    )
                elif clip.kind is TrackKind.AUDIO and not track.muted:
                    label = self._audio_clip_filter(filters, clip, input_index)
                    audio_labels.append(label)
                input_index += 1

        # Mix all audio streams (or synthesise silence if there is none).
        if audio_labels:
            joined = "".join(audio_labels)
            filters.append(
                f"{joined}amix=inputs={len(audio_labels)}:normalize=0[aout]"
            )
        else:
            filters.append("anullsrc=channel_layout=stereo:sample_rate=48000[aout]")

        filter_complex = ";".join(filters)
        args: list[str] = [*inputs, "-filter_complex", filter_complex]
        args += ["-map", f"[{last_video_label}]", "-map", "[aout]"]
        args += preset.video_encoder_args()
        args += ["-c:a", "aac", "-b:a", "192k", "-t", f"{duration:.3f}", output_path]
        return RenderPlan(args, duration)

    # -- per-clip filter builders -----------------------------------------
    def _video_clip_filter(
        self, filters, clip: Clip, idx: int, base_label: str, size, preset
    ) -> str:
        src_in = clip.source_in.seconds
        src_out = clip.source_out.seconds
        v = f"v{idx}"
        chain = (
            f"[{idx}:v]trim=start={src_in:.3f}:end={src_out:.3f},"
            f"setpts=(PTS-STARTPTS)/{clip.speed}"
        )
        if clip.reversed:
            chain += ",reverse"
        scaled_w = int(size.width * clip.transform.scale)
        scaled_h = int(size.height * clip.transform.scale)
        chain += f",scale={scaled_w}:{scaled_h}[{v}]"
        filters.append(chain)

        # Overlay onto the running composite, enabled only during the clip span.
        out = f"comp{idx}"
        start = clip.start.seconds
        end = clip.end.seconds
        x = f"(W-w)*{clip.transform.position_x:.4f}"
        y = f"(H-h)*{clip.transform.position_y:.4f}"
        filters.append(
            f"[{base_label}][{v}]overlay=x={x}:y={y}:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{out}]"
        )
        return out

    def _audio_clip_filter(self, filters, clip: Clip, idx: int) -> str:
        src_in = clip.source_in.seconds
        src_out = clip.source_out.seconds
        delay_ms = int(clip.start.seconds * 1000)
        a = f"a{idx}"
        chain = (
            f"[{idx}:a]atrim=start={src_in:.3f}:end={src_out:.3f},"
            f"asetpts=PTS-STARTPTS,volume={clip.volume:.3f},"
            f"adelay={delay_ms}|{delay_ms}[{a}]"
        )
        filters.append(chain)
        return f"[{a}]"
