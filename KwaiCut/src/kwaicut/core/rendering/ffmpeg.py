"""A thin, testable wrapper around the FFmpeg / ffprobe binaries.

The wrapper does two things: probe media for metadata, and run an FFmpeg command
while parsing its progress output. Everything is funnelled through
:meth:`FFmpeg.run` so it can be mocked in unit tests without spawning a real
process.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from kwaicut.common.errors import AssetError, RenderError
from kwaicut.common.logging_config import get_logger
from kwaicut.config import get_settings

logger = get_logger(__name__)


@dataclass(frozen=True)
class MediaInfo:
    """Subset of ffprobe output we care about."""

    duration_seconds: float
    width: int
    height: int
    fps: float
    has_audio: bool
    has_video: bool


class FFmpeg:
    """Wrapper around the configured ffmpeg/ffprobe binaries."""

    def __init__(self, ffmpeg: str | None = None, ffprobe: str | None = None) -> None:
        settings = get_settings()
        self.ffmpeg = ffmpeg or settings.ffmpeg_binary
        self.ffprobe = ffprobe or settings.ffprobe_binary

    # -- probing -----------------------------------------------------------
    def probe(self, path: str | Path) -> MediaInfo:
        """Return metadata for a media file using ffprobe."""
        path = Path(path)
        if not path.exists():
            raise AssetError(f"media file does not exist: {path}")
        cmd = [
            self.ffprobe, "-v", "error",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(path),
        ]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            raise AssetError(f"ffprobe failed for {path}: {exc}") from exc
        return self._parse_probe(json.loads(out.stdout))

    @staticmethod
    def _parse_probe(data: dict) -> MediaInfo:
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
        duration = float(data.get("format", {}).get("duration", 0.0) or 0.0)
        fps = 0.0
        width = height = 0
        if video is not None:
            width = int(video.get("width", 0))
            height = int(video.get("height", 0))
            rate = video.get("avg_frame_rate", "0/1")
            num, _, den = rate.partition("/")
            fps = float(num) / float(den) if den and float(den) else 0.0
        return MediaInfo(
            duration_seconds=duration,
            width=width,
            height=height,
            fps=fps,
            has_audio=audio is not None,
            has_video=video is not None,
        )

    # -- running -----------------------------------------------------------
    def build_command(self, args: Iterable[str]) -> list[str]:
        """Prefix raw FFmpeg args with the binary and a quiet/overwrite flag."""
        return [self.ffmpeg, "-y", "-hide_banner", "-loglevel", "error", *args]

    def run(
        self,
        args: Iterable[str],
        *,
        on_progress: Callable[[float], None] | None = None,
        total_seconds: float | None = None,
    ) -> None:
        """Execute an FFmpeg command, optionally reporting fractional progress.

        ``on_progress`` receives a value in [0, 1] derived from FFmpeg's
        ``-progress`` output. Raises :class:`RenderError` on non-zero exit.
        """
        cmd = self.build_command(args)
        if on_progress is not None and total_seconds:
            cmd += ["-progress", "pipe:1", "-nostats"]
        logger.debug("running ffmpeg: %s", " ".join(cmd))

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if on_progress is not None and total_seconds and proc.stdout is not None:
            for line in proc.stdout:
                if line.startswith("out_time_ms="):
                    micros = line.strip().split("=", 1)[1]
                    if micros.isdigit():
                        frac = min(1.0, (int(micros) / 1_000_000) / total_seconds)
                        on_progress(frac)
        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RenderError(f"ffmpeg exited with {proc.returncode}: {stderr}")
        if on_progress is not None:
            on_progress(1.0)
