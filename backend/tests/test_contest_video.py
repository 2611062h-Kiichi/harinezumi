"""Contest-mode scoring with video (T20): frames are described by Claude and sent to Jev."""

import asyncio
import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import contest as contest_router
from app.services import contest_scorer, jev_scorer, transcription
from app.services.video_frames import extract_frames_base64 as real_extract_frames
from app.services.contest_scorer import build_jev_state
from tests.test_contest_audio import TRANSCRIPT, FakeOpenAI
from tests.test_contest_scorer import QUESTION_SET, FakeTypeSafeClient
from tests.test_contest_slides import SLIDES, post

client = TestClient(app)

DESCRIPTION = "発表者は聴衆に視線を向け、手振りを交えて話している"
VISUAL_HEADING = "# 発表映像から読み取れる非言語的表現"


class FakeVisionClaude:
    """Stands in for AsyncAnthropic in contest_scorer (only the vision call is used)."""

    calls: list[dict] = []
    error: Exception | None = None

    def __init__(self, api_key):
        self.messages = SimpleNamespace(create=self._create)

    async def _create(self, **kwargs):
        FakeVisionClaude.calls.append(kwargs)
        if FakeVisionClaude.error is not None:
            raise FakeVisionClaude.error
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=DESCRIPTION)])


@pytest.fixture
def fakes(monkeypatch):
    FakeOpenAI.calls = []
    FakeOpenAI.text = TRANSCRIPT
    FakeTypeSafeClient.calls = []
    FakeTypeSafeClient.answers = {"problem": (3.0, 0.8), "market": (2.0, 0.9)}
    FakeTypeSafeClient.error = None
    FakeVisionClaude.calls = []
    FakeVisionClaude.error = None
    frame_calls = []

    def fake_extract(path):
        frame_calls.append(path)
        return ["AAAA", "BBBB"]

    monkeypatch.setattr(transcription, "AsyncOpenAI", FakeOpenAI)
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)
    monkeypatch.setattr(contest_scorer, "AsyncAnthropic", FakeVisionClaude)
    monkeypatch.setattr(contest_scorer, "extract_frames_base64", fake_extract)
    return SimpleNamespace(jev=FakeTypeSafeClient, whisper=FakeOpenAI, claude=FakeVisionClaude, frames=frame_calls)


def score_media(tmp_path, filename, slides=None):
    media = tmp_path / filename
    media.write_bytes(b"fake-media-bytes")
    return asyncio.run(contest_scorer.score_audio(QUESTION_SET, str(media), filename, slides=slides))


# --- service ---------------------------------------------------------------------


@pytest.mark.parametrize("filename", ["pitch.mp4", "pitch.webm"])
def test_video_frames_are_described_and_sent_to_jev(fakes, tmp_path, filename):
    result = score_media(tmp_path, filename)

    images = [b for b in fakes.claude.calls[0]["messages"][0]["content"] if b["type"] == "image"]
    assert [b["source"]["data"] for b in images] == ["AAAA", "BBBB"]
    state = fakes.jev.calls[0]["state"]
    assert VISUAL_HEADING in state
    assert DESCRIPTION in state
    assert TRANSCRIPT in state
    assert result.visual_included is True
    assert result.visual_description == DESCRIPTION


def test_video_with_slides_sends_slides_transcript_and_visuals(fakes, tmp_path):
    result = score_media(tmp_path, "pitch.mp4", slides=SLIDES)

    state = fakes.jev.calls[0]["state"]
    assert "課題: 学生の8割が就活情報に困っている" in state
    assert TRANSCRIPT in state
    assert DESCRIPTION in state
    assert result.slides_included and result.transcript_included and result.visual_included


@pytest.mark.parametrize("filename", ["pitch.mp3", "pitch.m4a", "pitch.wav"])
def test_audio_only_is_unchanged_and_never_touches_video(fakes, tmp_path, filename):
    result = score_media(tmp_path, filename)

    assert fakes.jev.calls[0]["state"] == TRANSCRIPT  # AC-08: transcript passed through as-is
    assert fakes.frames == []
    assert fakes.claude.calls == []
    assert result.visual_included is False
    assert result.visual_description is None


def test_failed_visual_description_still_scores_without_it(fakes, tmp_path):
    fakes.claude.error = RuntimeError("vision failed")

    result = score_media(tmp_path, "pitch.mp4")

    assert fakes.jev.calls[0]["state"] == TRANSCRIPT
    assert result.visual_included is False
    assert len(result.results) == len(QUESTION_SET.rubric.criteria)


def test_video_without_usable_frames_scores_without_calling_claude(fakes, tmp_path, monkeypatch):
    monkeypatch.setattr(contest_scorer, "extract_frames_base64", lambda path: [])

    result = score_media(tmp_path, "pitch.mp4")

    assert fakes.claude.calls == []
    assert result.visual_included is False


def test_missing_anthropic_key_skips_visual_analysis(fakes, tmp_path, monkeypatch):
    monkeypatch.setattr(contest_scorer.get_settings(), "anthropic_api_key", "")

    result = score_media(tmp_path, "pitch.mp4")

    assert fakes.frames == []
    assert fakes.claude.calls == []
    assert result.visual_included is False
    assert fakes.jev.calls[0]["state"] == TRANSCRIPT


def test_blank_transcript_is_rejected_before_paying_for_visual_analysis(fakes, tmp_path):
    from fastapi import HTTPException

    fakes.whisper.text = "   "

    with pytest.raises(HTTPException) as excinfo:
        score_media(tmp_path, "pitch.mp4")

    assert excinfo.value.status_code == 400
    # Frame extraction is free and runs alongside Whisper (T21); the paid
    # Claude visual analysis must still never start.
    assert fakes.claude.calls == []
    assert fakes.jev.calls == []


def test_oversized_slides_are_rejected_before_whisper_or_video(fakes, tmp_path, monkeypatch):
    from fastapi import HTTPException

    monkeypatch.setattr(contest_scorer.get_settings(), "max_contest_slide_pages", 1)

    with pytest.raises(HTTPException):
        score_media(tmp_path, "pitch.mp4", slides=SLIDES)  # SLIDES has 2 pages

    assert fakes.whisper.calls == []
    # Frame extraction (free) may already have run alongside the slide check (T21).
    assert fakes.claude.calls == []
    assert fakes.jev.calls == []


def test_jev_state_is_the_transcript_itself_without_slides_or_video():
    assert build_jev_state(None, TRANSCRIPT, None) == TRANSCRIPT


# --- API ---------------------------------------------------------------------------


def make_mp4(path, seconds=3):
    """A tiny but real MPEG-4 video, so PyAV actually opens and decodes it."""
    import av

    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("mpeg4", rate=10)
        stream.width, stream.height, stream.pix_fmt = 32, 32, "yuv420p"
        for i in range(seconds * 10):
            frame = av.VideoFrame(32, 32, "rgb24")
            frame.planes[0].update(bytes([i * 8 % 256]) * (32 * 32 * 3))
            for packet in stream.encode(frame.reformat(format="yuv420p")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


def test_frame_extraction_releases_the_video_file(tmp_path):
    video = tmp_path / "pitch.mp4"
    make_mp4(video)

    assert len(real_extract_frames(str(video))) == 4
    os.remove(video)  # fails on Windows while PyAV still holds the file open
    assert not video.exists()


def test_api_real_mp4_is_analyzed_and_its_temp_dir_removed(fakes, tmp_path, monkeypatch):
    video = tmp_path / "pitch.mp4"
    make_mp4(video)
    monkeypatch.setattr(contest_scorer, "extract_frames_base64", real_extract_frames)
    created = []
    real_mkdtemp = contest_router.tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(contest_router.tempfile, "mkdtemp", recording_mkdtemp)

    response = post([("media_file", ("pitch.mp4", video.read_bytes(), "video/mp4"))])

    assert response.status_code == 200
    body = response.json()
    assert body["visual_included"] is True
    assert body["visual_description"] == DESCRIPTION
    images = [b for b in fakes.claude.calls[0]["messages"][0]["content"] if b["type"] == "image"]
    assert len(images) == 4  # frames really came out of the uploaded video
    assert DESCRIPTION in fakes.jev.calls[0]["state"]
    assert len(created) == 1 and not os.path.exists(created[0])  # upload's temp dir removed


def test_blank_visual_description_is_not_reported_as_used(fakes, tmp_path, monkeypatch):
    async def blank(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="  ")])

    monkeypatch.setattr(FakeVisionClaude, "_create", blank)

    result = score_media(tmp_path, "pitch.mp4")

    assert result.visual_included is False
    assert result.visual_description is None
    assert fakes.jev.calls[0]["state"] == TRANSCRIPT


def test_api_mp3_upload_reports_no_video(fakes):
    response = post([("media_file", ("pitch.mp3", b"fake-audio-bytes", "audio/mpeg"))])

    assert response.status_code == 200
    assert response.json()["visual_included"] is False
    assert fakes.claude.calls == []
