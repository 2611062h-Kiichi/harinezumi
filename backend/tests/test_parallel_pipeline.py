"""T21: stage-1 steps run at the same time; stage 2 starts once they are all in.

Each fake step sleeps briefly and records when it started and finished, so
"ran at the same time" is checked as "every step started before any finished".
"""

import asyncio
import os
import threading
import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    CriterionComment,
    GeneratedCriterion,
    GeneratedLevelsOutput,
    PitchReviewLLMOutput,
    SlideContent,
    SlideExtractionResult,
)
from app.routers import contest as contest_router
from app.routers import review as review_router
from app.services import contest_scorer, jev_scorer, review_generator, slide_extractor, transcription
from app.utils.concurrency import Stage
from tests.test_contest_scorer import QUESTION_SET
from tests.test_contest_slides import post as contest_post

client = TestClient(app)

STEP = 0.3  # seconds each fake stage-1 step takes
LEVELS = ["1", "2", "3", "4", "5"]
SLIDES = SlideExtractionResult(filename="pitch.pptx", slides=[SlideContent(index=1, text="課題: 就活情報が多すぎる")])


class Timeline:
    """Thread-safe record of when each named step started and finished."""

    def __init__(self):
        self._lock = threading.Lock()
        self.start: dict[str, float] = {}
        self.end: dict[str, float] = {}
        self.cancelled: set[str] = set()

    def begin(self, name):
        with self._lock:
            self.start[name] = time.perf_counter()

    def finish(self, name):
        with self._lock:
            self.end[name] = time.perf_counter()

    def overlapped(self, *names):
        return max(self.start[n] for n in names) < min(self.end[n] for n in names)


def slow_sync(timeline, name, result, error=None, seconds=STEP):
    def run(*args, **kwargs):
        timeline.begin(name)
        time.sleep(seconds)
        timeline.finish(name)
        if error is not None:
            raise error
        return result

    return run


# --- Stage ---------------------------------------------------------------------------


def test_stage_runs_threads_and_coroutines_at_the_same_time():
    timeline = Timeline()

    async def network():
        timeline.begin("network")
        await asyncio.sleep(STEP)
        timeline.finish("network")
        return "n"

    async def main():
        stage = Stage()
        a = stage.in_thread(slow_sync(timeline, "thread-a", "a"))
        b = stage.in_thread(slow_sync(timeline, "thread-b", "b"))
        n = stage.call(network())
        await stage.wait()
        return a.result(), b.result(), n.result()

    t0 = time.perf_counter()
    assert asyncio.run(main()) == ("a", "b", "n")
    assert time.perf_counter() - t0 < STEP * 2.5  # sequential would take 3 * STEP
    assert timeline.overlapped("thread-a", "thread-b", "network")


def test_stage_failure_cancels_network_steps_but_waits_for_threads():
    timeline = Timeline()

    async def slow_network():
        timeline.begin("network")
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            timeline.cancelled.add("network")
            raise

    async def failing():
        await asyncio.sleep(0.05)
        raise HTTPException(status_code=400, detail="スライドが壊れています")

    async def main():
        stage = Stage()
        stage.call(slow_network())
        stage.in_thread(slow_sync(timeline, "thread", None))
        stage.call(failing())
        with pytest.raises(HTTPException) as excinfo:
            await stage.wait()
        return excinfo.value

    t0 = time.perf_counter()
    error = asyncio.run(main())
    assert error.detail == "スライドが壊れています"
    assert "network" in timeline.cancelled  # paid call stopped, not waited 10s for
    assert "thread" in timeline.end  # the thread step had finished before wait() raised
    assert time.perf_counter() - t0 < 5


def test_stage_with_no_steps_returns_immediately():
    asyncio.run(Stage().wait())


# --- pitch-review tab ------------------------------------------------------------------


class SlowWhisper:
    timeline: Timeline
    error: Exception | None = None

    def __init__(self, api_key):
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._create))

    async def _create(self, model, file):
        SlowWhisper.timeline.begin("transcription")
        try:
            await asyncio.sleep(STEP if SlowWhisper.error is None else 10)
        except asyncio.CancelledError:
            SlowWhisper.timeline.cancelled.add("transcription")
            raise
        SlowWhisper.timeline.finish("transcription")
        return SimpleNamespace(text="私たちは就活情報をAIで要約します。")


class SlowClaude:
    timeline: Timeline

    def __init__(self, api_key):
        self.messages = SimpleNamespace(parse=self._parse, create=self._create)

    async def _parse(self, output_format, **kwargs):
        if output_format is GeneratedLevelsOutput:  # rubric generation (stage 1)
            SlowClaude.timeline.begin("rubric")
            try:
                await asyncio.sleep(STEP)
            except asyncio.CancelledError:
                SlowClaude.timeline.cancelled.add("rubric")
                raise
            SlowClaude.timeline.finish("rubric")
            names = ["課題", "市場", "チーム"]
            return SimpleNamespace(
                parsed_output=GeneratedLevelsOutput(criteria=[GeneratedCriterion(name=n, levels=LEVELS) for n in names])
            )
        SlowClaude.timeline.begin("comments")
        return SimpleNamespace(
            parsed_output=PitchReviewLLMOutput(
                overall_summary="総評",
                criterion_comments=[CriterionComment(id=f"c{i}", comment="c") for i in range(1, 4)],
                strengths=[],
                improvements=[],
                one_line_verdict="一言",
            )
        )

    async def _create(self, **kwargs):  # body-language analysis (stage 2)
        SlowClaude.timeline.begin("visual")
        SlowClaude.timeline.finish("visual")
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="手振りを交えて話している")])


class RecordingJev:
    timeline: Timeline
    states: list[str] = []

    def __init__(self, api_key):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def system_one(self, state, questions):
        RecordingJev.timeline.begin("jev")
        RecordingJev.states.append(state)
        return SimpleNamespace(scores={k: SimpleNamespace(score=2.0, confidence=0.8) for k in questions})


@pytest.fixture
def review_timeline(monkeypatch):
    timeline = Timeline()
    SlowWhisper.timeline = SlowClaude.timeline = RecordingJev.timeline = timeline
    SlowWhisper.error = None
    RecordingJev.states = []
    created = []
    real_mkdtemp = review_router.tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(review_router.tempfile, "mkdtemp", recording_mkdtemp)
    monkeypatch.setattr(slide_extractor, "extract_slides", slow_sync(timeline, "slides", SLIDES))
    monkeypatch.setattr(review_router, "extract_frames_base64", slow_sync(timeline, "frames", ["AAAA"]))
    monkeypatch.setattr(transcription, "AsyncOpenAI", SlowWhisper)
    monkeypatch.setattr(review_generator, "AsyncAnthropic", SlowClaude)
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", RecordingJev)
    timeline.temp_dirs = created
    return timeline


def post_review():
    return client.post(
        "/api/review",
        data={"mode": "general", "criteria_names": "課題\n市場\nチーム"},
        files=[
            ("slide_file", ("pitch.pptx", b"x", "application/octet-stream")),
            ("media_file", ("pitch.mp4", b"fake-video", "video/mp4")),
        ],
    )


def test_review_runs_stage_one_in_parallel_then_stage_two(review_timeline):
    t0 = time.perf_counter()
    response = post_review()
    elapsed = time.perf_counter() - t0

    assert response.status_code == 200, response.text
    t = review_timeline
    assert t.overlapped("slides", "transcription", "frames", "rubric")
    stage_one_done = max(t.end[n] for n in ("slides", "transcription", "frames", "rubric"))
    # Stage 2 waits for all of stage 1, and body language comes before scoring.
    assert t.start["visual"] >= stage_one_done
    assert t.start["jev"] >= t.end["visual"]
    assert t.start["comments"] >= t.start["jev"]
    assert elapsed < STEP * 3  # sequential stage 1 alone would take 4 * STEP
    # The visual notes still reach Jev (T20 behaviour kept).
    assert "手振りを交えて話している" in RecordingJev.states[0]
    assert [c["name"] for c in response.json()["criteria"]] == ["課題", "市場", "チーム"]
    assert len(t.temp_dirs) == 1 and not os.path.exists(t.temp_dirs[0])


def test_review_failure_cancels_paid_calls_and_removes_temp_dir(review_timeline, monkeypatch):
    SlowWhisper.error = RuntimeError("never returns in time")
    monkeypatch.setattr(
        slide_extractor,
        "extract_slides",
        slow_sync(review_timeline, "slides", None, HTTPException(status_code=400, detail="スライドを読めません")),
    )

    t0 = time.perf_counter()
    response = post_review()

    assert response.status_code == 400
    assert response.json()["detail"] == "スライドを読めません"
    assert "transcription" in review_timeline.cancelled  # Whisper cut off, not waited for
    assert "frames" in review_timeline.end  # thread step finished before cleanup
    assert "jev" not in review_timeline.start
    assert time.perf_counter() - t0 < 5
    assert len(review_timeline.temp_dirs) == 1 and not os.path.exists(review_timeline.temp_dirs[0])


def test_review_without_claude_key_fails_fast_without_waiting_for_whisper(review_timeline, monkeypatch):
    SlowWhisper.error = RuntimeError("would take 10s")
    monkeypatch.setattr(review_generator.get_settings(), "anthropic_api_key", "")

    t0 = time.perf_counter()
    response = post_review()

    assert response.status_code == 400
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]
    assert "transcription" in review_timeline.cancelled
    assert time.perf_counter() - t0 < 5


# --- contest mode ----------------------------------------------------------------------


@pytest.fixture
def contest_timeline(monkeypatch):
    timeline = Timeline()
    SlowWhisper.timeline = SlowClaude.timeline = RecordingJev.timeline = timeline
    SlowWhisper.error = None
    RecordingJev.states = []
    monkeypatch.setattr(contest_router, "read_slides", slow_sync(timeline, "slides", SLIDES))
    # Decoding a video usually outlasts reading the slides, so it keeps going
    # while Whisper runs.
    monkeypatch.setattr(contest_scorer, "extract_frames_base64", slow_sync(timeline, "frames", ["AAAA"], seconds=STEP * 2))
    monkeypatch.setattr(transcription, "AsyncOpenAI", SlowWhisper)
    monkeypatch.setattr(contest_scorer, "AsyncAnthropic", SlowClaude)
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", RecordingJev)
    return timeline


def post_contest():
    return contest_post([
        ("slide_file", ("pitch.pptx", b"x", "application/octet-stream")),
        ("media_file", ("pitch.mp4", b"fake-video", "video/mp4")),
    ])


def test_contest_extracts_frames_alongside_slides_and_transcription(contest_timeline):
    response = post_contest()

    assert response.status_code == 200, response.text
    t = contest_timeline
    # Frames run alongside both; Whisper waits for the slide check (T17 rule kept).
    assert t.overlapped("frames", "slides")
    assert t.overlapped("frames", "transcription")
    assert t.start["transcription"] >= t.end["slides"]
    assert t.start["visual"] >= max(t.end["frames"], t.end["transcription"])
    assert t.start["jev"] >= t.end["visual"]
    assert "手振りを交えて話している" in RecordingJev.states[0]
    assert response.json()["visual_included"] is True


def test_contest_bad_slides_never_start_whisper_and_wait_for_frames(contest_timeline, monkeypatch):
    monkeypatch.setattr(
        contest_router,
        "read_slides",
        slow_sync(contest_timeline, "slides", None, HTTPException(status_code=400, detail="スライド資料を読み込めませんでした。")),
    )

    response = post_contest()

    assert response.status_code == 400
    assert "transcription" not in contest_timeline.start
    assert "frames" in contest_timeline.end
    assert "visual" not in contest_timeline.start
