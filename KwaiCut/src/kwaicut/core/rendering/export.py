"""The export pipeline: timeline + preset -> rendered file on disk.

:class:`ExportPipeline` ties the :class:`RenderEngine` (which builds the command)
to the :class:`FFmpeg` wrapper (which runs it) and reports progress. It also
supports batch rendering of several jobs sequentially, which is what the
"Batch Rendering" feature in the UI dispatches to.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from kwaicut.common.logging_config import get_logger
from kwaicut.core.rendering.ffmpeg import FFmpeg
from kwaicut.core.rendering.presets import ExportPreset
from kwaicut.core.rendering.render_engine import AssetResolver, RenderEngine
from kwaicut.core.timeline.models import Timeline

logger = get_logger(__name__)

ProgressCallback = Callable[[float], None]


@dataclass
class ExportJob:
    timeline: Timeline
    output_path: Path
    preset: ExportPreset


class ExportPipeline:
    """Render timelines to disk via FFmpeg."""

    def __init__(self, resolve_asset: AssetResolver, ffmpeg: FFmpeg | None = None) -> None:
        self._engine = RenderEngine(resolve_asset)
        self._ffmpeg = ffmpeg or FFmpeg()

    def export(self, job: ExportJob, on_progress: ProgressCallback | None = None) -> Path:
        """Render a single job and return the output path."""
        job.output_path.parent.mkdir(parents=True, exist_ok=True)
        plan = self._engine.compile(job.timeline, str(job.output_path), job.preset)
        logger.info(
            "exporting timeline %s -> %s (%s, %.2fs)",
            job.timeline.id, job.output_path, job.preset.resolution.value, plan.duration_seconds,
        )
        self._ffmpeg.run(
            plan.args, on_progress=on_progress, total_seconds=plan.duration_seconds
        )
        return job.output_path

    def export_batch(
        self,
        jobs: list[ExportJob],
        on_progress: Callable[[int, float], None] | None = None,
    ) -> list[Path]:
        """Render multiple jobs sequentially, reporting (job_index, fraction)."""
        outputs: list[Path] = []
        for index, job in enumerate(jobs):
            cb = (lambda f, i=index: on_progress(i, f)) if on_progress else None
            outputs.append(self.export(job, on_progress=cb))
        return outputs
