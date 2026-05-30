"""Export presets: resolutions, containers and codecs.

These map the user-facing options ("4K", "H.265", "MP4") onto concrete FFmpeg
arguments. Keeping them declarative makes the export dialog trivially data-driven
and keeps codec knowledge in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from kwaicut.common.types import Resolution


class ResolutionPreset(str, Enum):
    P720 = "720p"
    P1080 = "1080p"
    P1440 = "2k"
    P2160 = "4k"
    P4320 = "8k"


RESOLUTIONS: dict[ResolutionPreset, Resolution] = {
    ResolutionPreset.P720: Resolution(1280, 720),
    ResolutionPreset.P1080: Resolution(1920, 1080),
    ResolutionPreset.P1440: Resolution(2560, 1440),
    ResolutionPreset.P2160: Resolution(3840, 2160),
    ResolutionPreset.P4320: Resolution(7680, 4320),
}


class VideoCodec(str, Enum):
    H264 = "h264"
    H265 = "h265"
    PRORES = "prores"
    VP9 = "vp9"


class Container(str, Enum):
    MP4 = "mp4"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"


# FFmpeg encoder name + pixel format for each codec.
_CODEC_ARGS: dict[VideoCodec, dict[str, str]] = {
    VideoCodec.H264: {"encoder": "libx264", "pix_fmt": "yuv420p"},
    VideoCodec.H265: {"encoder": "libx265", "pix_fmt": "yuv420p"},
    VideoCodec.PRORES: {"encoder": "prores_ks", "pix_fmt": "yuva444p10le"},
    VideoCodec.VP9: {"encoder": "libvpx-vp9", "pix_fmt": "yuv420p"},
}


@dataclass(frozen=True)
class ExportPreset:
    """A fully resolved export configuration."""

    resolution: ResolutionPreset = ResolutionPreset.P1080
    codec: VideoCodec = VideoCodec.H264
    container: Container = Container.MP4
    fps: int = 30
    # Constant Rate Factor: lower = higher quality / bigger file (x264/x265).
    crf: int = 20
    hdr: bool = False
    transparent: bool = False

    @property
    def size(self) -> Resolution:
        return RESOLUTIONS[self.resolution]

    def video_encoder_args(self) -> list[str]:
        """Build the ``-c:v ...`` portion of an FFmpeg command."""
        codec = self.codec
        if self.transparent:
            # Transparency requires an alpha-capable codec/container.
            codec = VideoCodec.PRORES
        spec = _CODEC_ARGS[codec]
        args = ["-c:v", spec["encoder"], "-pix_fmt", spec["pix_fmt"]]
        if codec in (VideoCodec.H264, VideoCodec.H265):
            args += ["-crf", str(self.crf), "-preset", "medium"]
        if self.hdr and codec is VideoCodec.H265:
            args += [
                "-color_primaries", "bt2020",
                "-color_trc", "smpte2084",
                "-colorspace", "bt2020nc",
            ]
        return args
