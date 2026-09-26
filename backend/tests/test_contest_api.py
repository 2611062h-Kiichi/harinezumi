"""Contest API through FastAPI's TestClient, with Claude, Whisper and Jev faked."""

import json
import os
import tempfile
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import contest as contest_router
from app.services import jev_scorer, question_builder, transcription
from app.services.question_builder import GeneratedQuestion, GeneratedQuestions
from tests.test_contest_audio import TRANSCRIPT, FakeOpenAI
from tests.test_contest_scorer import QUESTION_SET, FakeTypeSafeClient
from tests.test_question_builder import LEVELS, FakeAnthropic

RUBRIC = {
    "contest_name": "学生ビジコン2026",
    "criteria": [
        {"id": "problem", "name": "課題の明確さ", "description": "誰のどんな課題か", "max_points": 20},
        {"id": "market", "name": "市場性", "max_points": 30},
    ],
}

client = TestClient(app)


@pytest.fixture
def fakes(monkeypatch):
    FakeAnthropic.calls = []
    # Claude answers in the reverse order of the rubric on purpose.
    FakeAnthropic.parsed_output = GeneratedQuestions(
        questions=[
            GeneratedQuestion(criterion_id=cid, instructions=f"{cid} をどの程度満たしているか", levels=LEVELS)
            for cid in ("market", "problem")
        ]
    )
    FakeOpenAI.calls = []
    FakeOpenAI.text = TRANSCRIPT
    FakeTypeSafeClient.calls = []
    FakeTypeSafeClient.answers = {"problem": (3.0, 0.8), "market": (2.0, 0.4)}
    FakeTypeSafeClient.error = None
    monkeypatch.setattr(question_builder, "AsyncAnthropic", FakeAnthropic)
    monkeypatch.setattr(transcription, "AsyncOpenAI", FakeOpenAI)
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)
    return SimpleNamespace(claude=FakeAnthropic, whisper=FakeOpenAI, jev=FakeTypeSafeClient)


@pytest.fixture
def temp_dirs(monkeypatch):
    """Records every temp dir the score endpoint creates."""
    created = []
    real_mkdtemp = tempfile.mkdtemp

    def recording_mkdtemp(*args, **kwargs):
        path = real_mkdtemp(*args, **kwargs)
        created.append(path)
        return path

    monkeypatch.setattr(contest_router.tempfile, "mkdtemp", recording_mkdtemp)
    return created


# --- POST /api/contest/questions --------------------------------------------------


def test_questions_success_returns_rubric_order(fakes):
    response = client.post("/api/contest/questions", json=RUBRIC)

    assert response.status_code == 200
    body = response.json()
    assert body["rubric"]["contest_name"] == "学生ビジコン2026"
    assert [q["criterion_id"] for q in body["questions"]] == ["problem", "market"]
    assert body["questions"][0]["levels"] == LEVELS
    assert len(fakes.claude.calls) == 1


@pytest.mark.parametrize(
    "points, expected",
    [(0, "観点1の配点: 1以上にしてください"), (101, "観点1の配点: 100以下にしてください"),
     ("20", "観点1の配点: 整数で入力してください"), (20.0, "観点1の配点: 整数で入力してください"),
     (True, "観点1の配点: 整数で入力してください")],
)
def test_invalid_points_are_400_in_japanese(fakes, points, expected):
    rubric = json.loads(json.dumps(RUBRIC))
    rubric["criteria"][0]["max_points"] = points

    response = client.post("/api/contest/questions", json=rubric)

    assert response.status_code == 400
    assert expected in response.json()["detail"]
    assert fakes.claude.calls == []


def test_several_mistakes_are_reported_together(fakes):
    rubric = {"contest_name": "", "criteria": [{"id": "a", "name": " ", "max_points": 5}, {"id": "a", "name": "B", "max_points": 5}]}

    detail = client.post("/api/contest/questions", json=rubric).json()["detail"]

    assert "コンテスト名: 入力してください" in detail
    assert "観点1の名前: 入力してください" in detail


def test_duplicate_ids_are_400(fakes):
    rubric = {"contest_name": "x", "criteria": [{"id": "a", "name": "A", "max_points": 5}, {"id": "a", "name": "B", "max_points": 5}]}

    response = client.post("/api/contest/questions", json=rubric)

    assert response.status_code == 400
    assert "観点のIDが重複しています: a" in response.json()["detail"]


def test_broken_json_is_400(fakes):
    response = client.post(
        "/api/contest/questions", content=b"{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert "JSONとして読み取れませんでした" in response.json()["detail"]


def test_questions_without_anthropic_key_is_japanese_error(fakes, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    question_builder.get_settings.cache_clear()

    response = client.post("/api/contest/questions", json=RUBRIC)

    assert response.status_code == 400
    assert response.json()["detail"] == "ANTHROPIC_API_KEYが設定されていません。"


# --- POST /api/contest/score -------------------------------------------------------


def post_score(filename="pitch.mp3", content=b"fake-audio-bytes", question_set=None):
    data = {"question_set": question_set if question_set is not None else QUESTION_SET.model_dump_json()}
    files = {"media_file": (filename, content, "application/octet-stream")} if filename else None
    return client.post("/api/contest/score", data=data, files=files)


def test_score_success(fakes, temp_dirs):
    response = post_score()

    assert response.status_code == 200
    body = response.json()
    assert body["contest_name"] == "学生ビジコン2026"
    assert [r["criterion_id"] for r in body["results"]] == ["problem", "market"]
    assert body["results"][0]["points"] == 15.0
    assert body["results"][1]["low_confidence"] is True
    assert body["total_points"] == 30.0
    assert body["max_total_points"] == 50
    assert body["transcript"] == TRANSCRIPT
    assert fakes.jev.calls[0]["state"] == TRANSCRIPT
    assert len(temp_dirs) == 1 and not os.path.exists(temp_dirs[0])


def test_mp4_video_reaches_whisper(fakes):
    response = post_score(filename="pitch.mp4", content=b"fake-mp4-bytes")

    assert response.status_code == 200
    assert fakes.whisper.calls == [{"model": "whisper-1", "content": b"fake-mp4-bytes"}]


def test_unsupported_extension_is_400(fakes):
    response = post_score(filename="pitch.txt")

    assert response.status_code == 400
    assert "対応していないファイル形式" in response.json()["detail"]
    assert fakes.whisper.calls == []


def test_missing_media_file_is_400(fakes):
    response = post_score(filename=None)

    assert response.status_code == 400
    assert "音声または動画ファイルを指定してください" in response.json()["detail"]


def test_missing_question_set_is_400(fakes):
    response = client.post(
        "/api/contest/score", files={"media_file": ("pitch.mp3", b"x", "application/octet-stream")}
    )

    assert response.status_code == 400
    assert "Questionを指定してください" in response.json()["detail"]


def test_broken_question_set_json_is_400(fakes):
    response = post_score(question_set="{not json")

    assert response.status_code == 400
    assert "QuestionをJSONとして読み取れませんでした" in response.json()["detail"]
    assert fakes.whisper.calls == []


def test_question_set_not_matching_rubric_is_400(fakes):
    data = QUESTION_SET.model_dump(mode="json")
    data["questions"] = data["questions"][:1]  # drop one question

    response = post_score(question_set=json.dumps(data))

    assert response.status_code == 400
    assert "Questionが無い観点: problem" in response.json()["detail"]
    assert fakes.whisper.calls == []


def test_score_without_typesafe_key_is_japanese_error(fakes, temp_dirs, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "")
    jev_scorer.get_settings.cache_clear()

    response = post_score()

    assert response.status_code == 400
    assert response.json()["detail"] == "TYPESAFE_API_KEYが設定されていません。"
    # The temp dir is removed even though scoring failed.
    assert len(temp_dirs) == 1 and not os.path.exists(temp_dirs[0])


def test_temp_dir_is_removed_when_transcript_is_empty(fakes, temp_dirs):
    fakes.whisper.text = "   "

    response = post_score()

    assert response.status_code == 400
    assert len(temp_dirs) == 1 and not os.path.exists(temp_dirs[0])
