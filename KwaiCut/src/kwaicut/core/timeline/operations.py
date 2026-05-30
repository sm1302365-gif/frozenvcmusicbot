"""High-level, non-destructive editing operations on the timeline model.

Each operation mutates the model in place and returns the affected object(s) so
callers (UI commands, the API, automated AI editors) can compose them and build
undo/redo on top. They are written defensively: an illegal edit raises
:class:`~kwaicut.common.errors.TimelineError` rather than corrupting the model.
"""

from __future__ import annotations

import copy

from kwaicut.common.errors import TimelineError
from kwaicut.common.types import TimeCode
from kwaicut.core.timeline.models import Clip, Track


def split_clip(track: Track, clip_id: str, at: TimeCode) -> tuple[Clip, Clip]:
    """Split a clip into two at timeline position ``at``.

    The source in/out points are recomputed so the two halves play back
    seamlessly as if the cut never happened.
    """
    clip = _require_clip(track, clip_id)
    if not (clip.start < at < clip.end):
        raise TimelineError("split point must lie strictly inside the clip")

    # How far into the clip (in *source* time) the cut lands.
    offset_into_clip = at - clip.start
    source_offset = TimeCode(round(offset_into_clip.micros * clip.speed))
    split_source = clip.source_in + source_offset

    right = copy.deepcopy(clip)
    right.id = _regen_id(clip.id)
    right.start = at
    right.source_in = split_source

    clip.source_out = split_source  # left half ends at the cut

    track.clips.append(right)
    track.clips.sort(key=lambda c: c.start.micros)
    return clip, right


def trim_clip(
    clip: Clip,
    *,
    new_start: TimeCode | None = None,
    new_end: TimeCode | None = None,
) -> Clip:
    """Trim a clip's head and/or tail, adjusting source points accordingly."""
    if new_start is not None:
        delta = new_start - clip.start
        source_delta = TimeCode(round(delta.micros * clip.speed))
        candidate_in = clip.source_in + source_delta
        if candidate_in >= clip.source_out:
            raise TimelineError("trim would collapse the clip to zero length")
        clip.source_in = candidate_in
        clip.start = new_start
    if new_end is not None:
        if new_end <= clip.start:
            raise TimelineError("new_end must be after the clip start")
        new_source_duration = TimeCode(round((new_end - clip.start).micros * clip.speed))
        candidate_out = clip.source_in + new_source_duration
        if candidate_out <= clip.source_in:
            raise TimelineError("trim would collapse the clip to zero length")
        clip.source_out = candidate_out
    return clip


def ripple_delete(track: Track, clip_id: str) -> None:
    """Delete a clip and shift every later clip left to close the gap."""
    clip = _require_clip(track, clip_id)
    gap = clip.duration
    track.remove_clip(clip_id)
    for other in track.clips:
        if other.start >= clip.end:
            other.start = other.start - gap


def set_speed(clip: Clip, speed: float) -> Clip:
    """Change a clip's playback speed (speed ramping / slow-motion)."""
    if speed <= 0:
        raise TimelineError("speed must be positive")
    clip.speed = speed
    return clip


def _require_clip(track: Track, clip_id: str) -> Clip:
    for clip in track.clips:
        if clip.id == clip_id:
            return clip
    raise TimelineError(f"clip {clip_id} not found on track {track.id}")


def _regen_id(clip_id: str) -> str:
    import uuid

    base = clip_id.split("_")[0]
    return f"{base}_{uuid.uuid4().hex[:12]}"
