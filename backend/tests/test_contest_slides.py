"""Contest-mode scoring with slides (T15): slides only, transcript only, or both."""

import asyncio
import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SlideContent, SlideExtractionResult
from app.routers import contest as contest_router
from app.services import contest_scorer, jev_scorer, transcription
from tests.test_contest_audio import TRANSCRIPT, FakeOpenAI
from tests.test_contest_scorer import QUESTION_SET, FakeTypeSafeClient
from tests.test_slide_extractor import make_pdf, make_pptx

client = TestClient(app)

SLIDES = SlideExtractionResult(
    filename="pitch.pptx",
    slides=[
        SlideContent(index=1, text="課題: 学生の8割が就活情報に困っている", notes="ここで間を取る"),
        SlideContent(index=2, text="解決策: AIが企業情報を要約する"),
    ],
)
BLANK_SLIDES = SlideExtractionResult(
    filename="images.pdf", slides=[SlideContent(index=1, text=""), SlideContent(index=2, text="  ")]
)


@pytest.fixture
def fakes(monkeypatch):
    FakeOpenAI.calls = []
    FakeOpenAI.text = TRANSCRIPT
    FakeTypeSafeClient.calls = []
    FakeTypeSafeClient.answers = {"problem": (3.0, 0.8), "market": (2.0, 0.9)}
    FakeTypeSafeClient.error = None
    monkeypatch.setattr(transcription, "AsyncOpenAI", FakeOpenAI)
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)
    return FakeTypeSafeClient


def score(**kwargs):
    return asyncio.run(contest_scorer.score_materials(QUESTION_SET, **kwargs))


# --- service ---------------------------------------------------------------------


def test_slides_and_transcript_both_reach_jev(fakes):
    result = score(slides=SLIDES, transcript=TRANSCRIPT)

    state = fakes.calls[0]["state"]
    assert "## スライド1" in state
    assert "課題: 学生の8割が就活情報に困っている" in state
    assert "(スピーカーノート: ここで間を取る)" in state
    assert "解決策: AIが企業情報を要約する" in state
    assert TRANSCRIPT in state
    assert result.slides_included is True
    assert result.transcript_included is True
    assert result.transcript == TRANSCRIPT


def test_slides_only_scores_without_a_transcript(fakes):
    result = score(slides=SLIDES)

    state = fakes.calls[0]["state"]
    assert "課題: 学生の8割が就活情報に困っている" in state
    assert "音声書き起こしはありません" in state
    assert result.slides_included is True
    assert result.transcript_included is False
    assert result.transcript == ""


def test_transcript_only_is_passed_through_unchanged(fakes):
    result = score(transcript=TRANSCRIPT)

    assert fakes.calls[0]["state"] == TRANSCRIPT
    assert result.slides_included is False
    assert result.transcript_included is True


def test_neither_slides_nor_transcript_is_400(fakes):
    with pytest.raises(HTTPException) as excinfo:
        score()

    assert excinfo.value.status_code == 400
    assert fakes.calls == []


def test_slides_without_any_text_and_no_audio_is_400(fakes):
    with pytest.raises(HTTPException) as excinfo:
        score(slides=BLANK_SLIDES)

    assert excinfo.value.status_code == 400
    assert "文字を読み取れませんでした" in excinfo.value.detail
    assert fakes.calls == []


def test_slides_without_text_are_fine_alongside_audio(fakes):
    result = score(slides=BLANK_SLIDES, transcript=TRANSCRIPT)

    assert TRANSCRIPT in fakes.calls[0]["state"]
    assert result.slides_included is True


def test_blank_transcript_is_still_rejected_even_with_slides(fakes):
    with pytest.raises(HTTPException) as excinfo:
        score(slides=SLIDES, transcript="   ")

    assert excinfo.value.status_code == 400
    assert "文字起こしが空" in excinfo.value.detail


# --- API ---------------------------------------------------------------------------


@pytest.fixture
def temp_dirs(monkeypatch):
    created = []
    real_mkdtemp = contest_router.tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(contest_router.tempfile, "mkdtemp", recording_mkdtemp)
    return created


@pytest.fixture
def pptx_bytes(tmp_path):
    path = tmp_path / "pitch.pptx"
    make_pptx(path, [("課題", "学生の8割が就活情報に困っている", "ここで間を取る")])
    return path.read_bytes()


def post(files, question_set=None):
    data = {"question_set": question_set if question_set is not None else QUESTION_SET.model_dump_json()}
    return client.post("/api/contest/score", data=data, files=files)


def test_api_pptx_and_audio(fakes, pptx_bytes, temp_dirs):
    response = post([
        ("slide_file", ("pitch.pptx", pptx_bytes, "application/octet-stream")),
        ("media_file", ("pitch.mp3", b"fake-audio-bytes", "audio/mpeg")),
    ])

    assert response.status_code == 200
    body = response.json()
    assert body["slides_included"] is True
    assert body["transcript_included"] is True
    state = fakes.calls[0]["state"]
    assert "学生の8割が就活情報に困っている" in state
    assert TRANSCRIPT in state
    assert len(temp_dirs) == 1 and not os.path.exists(temp_dirs[0])


def test_api_pptx_only_never_calls_whisper(fakes, pptx_bytes):
    response = post([("slide_file", ("pitch.pptx", pptx_bytes, "application/octet-stream"))])

    assert response.status_code == 200
    assert response.json()["transcript_included"] is False
    assert FakeOpenAI.calls == []
    assert "学生の8割が就活情報に困っている" in fakes.calls[0]["state"]


def test_api_pdf_only(fakes, tmp_path):
    path = tmp_path / "pitch.pdf"
    make_pdf(path, ["Problem: students struggle to find job info"])

    response = post([("slide_file", ("pitch.pdf", path.read_bytes(), "application/pdf"))])

    assert response.status_code == 200
    assert "Problem: students struggle to find job info" in fakes.calls[0]["state"]


@pytest.mark.parametrize("filename", ["broken.pdf", "broken.pptx"])
def test_api_corrupt_slide_file_is_400_and_cleans_up(fakes, temp_dirs, filename):
    response = post([("slide_file", (filename, b"this is not really a slide deck", "application/octet-stream"))])

    assert response.status_code == 400
    assert "スライド資料を読み込めませんでした" in response.json()["detail"]
    assert fakes.calls == []
    assert len(temp_dirs) == 1 and not os.path.exists(temp_dirs[0])


def test_api_slides_with_no_text_only_is_400(fakes, tmp_path):
    path = tmp_path / "blank.pdf"
    make_pdf(path, [""])

    response = post([("slide_file", ("blank.pdf", path.read_bytes(), "application/pdf"))])

    assert response.status_code == 400
    assert "文字を読み取れませんでした" in response.json()["detail"]


def test_api_unsupported_slide_extension_is_400_without_temp_dir(fakes, temp_dirs):
    response = post([("slide_file", ("pitch.key", b"x", "application/octet-stream"))])

    assert response.status_code == 400
    assert "対応していないファイル形式" in response.json()["detail"]
    assert temp_dirs == []


def test_api_two_slide_files_is_400(fakes, pptx_bytes, temp_dirs):
    response = post([
        ("slide_file", ("a.pptx", pptx_bytes, "application/octet-stream")),
        ("slide_file", ("b.pptx", pptx_bytes, "application/octet-stream")),
    ])

    assert response.status_code == 400
    assert "1つだけ" in response.json()["detail"]
    assert temp_dirs == []


def test_api_slide_sent_as_text_is_400(fakes):
    response = client.post(
        "/api/contest/score",
        data={"slide_file": "not-a-file", "question_set": QUESTION_SET.model_dump_json()},
    )

    assert response.status_code == 400
    assert "PDFまたはPPTXのファイルで指定してください" in response.json()["detail"]
