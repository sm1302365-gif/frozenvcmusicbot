from __future__ import annotations

from kwaicut.ai.base import Transcript, TranscriptSegment
from kwaicut.ai.captions import transcript_to_srt


def test_transcript_text_join():
    transcript = Transcript(
        language="en",
        segments=[
            TranscriptSegment(0.0, 1.0, "Hello"),
            TranscriptSegment(1.0, 2.0, "world"),
        ],
    )
    assert transcript.text == "Hello world"


def test_transcript_to_srt_format():
    transcript = Transcript(
        language="en",
        segments=[TranscriptSegment(0.0, 1.5, "Hello world")],
    )
    srt = transcript_to_srt(transcript)
    assert "1\n" in srt
    assert "00:00:00,000 --> 00:00:01,500" in srt
    assert "Hello world" in srt
