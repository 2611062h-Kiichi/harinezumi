"""Tests for the pitch-review features merged from feature/business-contest-rubric (T18).

That branch shipped without tests; these pin down its behaviour with Claude,
Jev and video decoding faked out: the three ways to pick a general-mode
rubric, the rubric preview API, and the best-effort video frame analysis.
"""

import asyncio
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    CriterionComment,
    CustomRubricLLMOutput,
    GeneratedCriterion,
    GeneratedLevelsOutput,
    PitchReviewLLMOutput,
    SlideContent,
    SlideExtractionResult,
)
from app.routers import review as review_router
from app.rubric import BUSINESS_RUBRIC_CRITERIA, GENERAL_RUBRIC_CRITERIA
from app.services import jev_scorer, review_generator, video_frames
from tests.test_jev_scorer import FakeTypeSafeClient

client = TestClient(app)

LEVELS = ["全く示されていない", "少し示されている", "ある程度示されている", "十分に示されている", "非常に説得力がある"]
SLIDES = SlideExtractionResult(filename="pitch.pptx", slides=[SlideContent(index=1, text="課題: 就活情報が多すぎる")])


def criteria(*names):
    return [GeneratedCriterion(name=n, levels=list(LEVELS)) for n in names]


class FakeClaude:
    """Stands in for AsyncAnthropic: answers each structured-output request by
    its schema, and the vision call (messages.create) with a fixed text."""

    parse_calls: list[dict] = []
    create_calls: list[dict] = []
    outputs: dict = {}
    create_error: Exception | None = None

    def __init__(self, api_key):
        self.messages = SimpleNamespace(parse=self._parse, create=self._create)

    async def _parse(self, **kwargs):
        FakeClaude.parse_calls.append(kwargs)
        return SimpleNamespace(parsed_output=FakeClaude.outputs[kwargs["output_format"]])

    async def _create(self, **kwargs):
        FakeClaude.create_calls.append(kwargs)
        if FakeClaude.create_error is not None:
            raise FakeClaude.create_error
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="発表者は聴衆を見て、身振りを交えて話している")])


@pytest.fixture
def fake_claude(monkeypatch):
    FakeClaude.parse_calls = []
    FakeClaude.create_calls = []
    FakeClaude.create_error = None
    FakeClaude.outputs = {
        CustomRubricLLMOutput: CustomRubricLLMOutput(criteria=criteria(*[f"大会の観点{i}" for i in range(1, 8)])),
        GeneratedLevelsOutput: GeneratedLevelsOutput(criteria=criteria("Claudeが言い換えた名前A", "B", "C")),
    }
    monkeypatch.setattr(review_generator, "AsyncAnthropic", FakeClaude)
    monkeypatch.setattr(review_router, "AsyncAnthropic", FakeClaude)
    return FakeClaude


@pytest.fixture
def fake_jev(monkeypatch):
    FakeTypeSafeClient.calls = []
    FakeTypeSafeClient.error = None
    monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)
    return FakeTypeSafeClient


def resolve(mode="general", event_context=None, names=None, custom=None):
    return asyncio.run(
        review_generator.resolve_rubric(FakeClaude("k"), "model", mode, event_context, names, custom)
    )


# --- choosing the rubric -----------------------------------------------------------


def test_general_mode_without_extras_uses_the_default_rubric_without_calling_claude(fake_claude):
    rubric, _, label = resolve()

    assert rubric == GENERAL_RUBRIC_CRITERIA
    assert label == "汎用ピッチ審査"
    assert fake_claude.parse_calls == []


def test_business_mode_ignores_custom_inputs(fake_claude):
    rubric, _, _ = resolve(mode="business", event_context="ハッカソン", names=["a", "b", "c"])

    assert rubric == BUSINESS_RUBRIC_CRITERIA
    assert fake_claude.parse_calls == []


def test_event_context_designs_a_rubric_with_web_search_available(fake_claude):
    rubric, intro, label = resolve(event_context="学生起業家選手権2026")

    assert [c["name"] for c in rubric] == [f"大会の観点{i}" for i in range(1, 8)]
    assert all(len(c["levels"]) == 5 for c in rubric)
    assert "学生起業家選手権2026" in label
    assert "学生起業家選手権2026" in intro
    call = fake_claude.parse_calls[0]
    assert call["tools"][0]["name"] == "web_search"
    assert "学生起業家選手権2026" in call["messages"][0]["content"]


def test_user_named_criteria_keep_the_users_names_and_order(fake_claude):
    rubric, _, label = resolve(names=["課題の明確さ", "市場性", "チーム"])

    # Claude echoed a different first name; the user's wording must win.
    assert [c["name"] for c in rubric] == ["課題の明確さ", "市場性", "チーム"]
    assert [c["id"] for c in rubric] == ["c1", "c2", "c3"]
    assert rubric[0]["levels"] == LEVELS
    assert label == "汎用ピッチ審査（カスタム評価項目）"
    assert "tools" not in fake_claude.parse_calls[0]


def test_edited_preview_takes_priority_over_names_and_event(fake_claude):
    custom = [{"id": "c1", "name": "手で直した項目", "levels": LEVELS}]

    rubric, _, _ = resolve(event_context="ハッカソン", names=["a", "b", "c"], custom=custom)

    assert rubric == custom
    assert fake_claude.parse_calls == []


# --- rubric preview API ------------------------------------------------------------


def test_preview_api_returns_the_rubric_that_review_would_use(fake_claude):
    response = client.post("/api/rubric/preview", data={"mode": "general", "criteria_names": "課題\n市場\nチーム"})

    assert response.status_code == 200
    body = response.json()
    assert [c["name"] for c in body["criteria"]] == ["課題", "市場", "チーム"]
    assert body["criteria"][0]["levels"] == LEVELS


@pytest.mark.parametrize(
    "data, message",
    [
        ({"criteria_names": "課題\n市場"}, "3〜10個"),
        ({"criteria_names": "\n".join(f"項目{i}" for i in range(11))}, "3〜10個"),
        ({"criteria_names": "課題\n市場\n" + "長" * 51}, "50文字以内"),
        ({"event_context": "あ" * 301}, "300文字以内"),
        ({"mode": "no-such-mode"}, "不明な審査モード"),
    ],
)
def test_preview_api_rejects_bad_input_in_japanese_without_calling_claude(fake_claude, data, message):
    response = client.post("/api/rubric/preview", data={"mode": "general", **data})

    assert response.status_code == 400
    assert message in response.json()["detail"]
    assert fake_claude.parse_calls == []


def test_review_api_rejects_a_malformed_edited_rubric(fake_claude):
    response = client.post(
        "/api/review",
        data={"mode": "general", "custom_rubric_json": "{not json"},
        files={"slide_file": ("pitch.pptx", b"x", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "評価基準の形式が正しくありません" in response.json()["detail"]


# --- review output and video analysis ------------------------------------------------


@pytest.fixture
def review_output(fake_claude):
    fake_claude.outputs[PitchReviewLLMOutput] = PitchReviewLLMOutput(
        overall_summary="総評",
        criterion_comments=[CriterionComment(id=c["id"], comment="コメント") for c in GENERAL_RUBRIC_CRITERIA],
        strengths=["強み"],
        improvements=[],
        one_line_verdict="一言",
    )
    return fake_claude


def test_review_includes_each_criterions_levels(review_output, fake_jev):
    review = asyncio.run(review_generator.generate_review(SLIDES, None, "general"))

    assert [c.levels for c in review.criteria] == [c["levels"] for c in GENERAL_RUBRIC_CRITERIA]


def test_video_frames_are_described_and_passed_to_jev(review_output, fake_jev):
    asyncio.run(review_generator.generate_review(SLIDES, "書き起こし", "general", video_frames_base64=["AAAA", "BBBB"]))

    images = [b for b in review_output.create_calls[0]["messages"][0]["content"] if b["type"] == "image"]
    assert [b["source"]["data"] for b in images] == ["AAAA", "BBBB"]
    state = fake_jev.calls[0]["state"]
    assert "# 発表映像から読み取れる非言語的表現" in state
    assert "身振りを交えて話している" in state


def test_failed_video_description_does_not_stop_the_review(review_output, fake_jev):
    review_output.create_error = RuntimeError("vision failed")

    review = asyncio.run(review_generator.generate_review(SLIDES, "書き起こし", "general", video_frames_base64=["AAAA"]))

    assert review.overall_summary == "総評"
    assert "非言語的表現" not in fake_jev.calls[0]["state"]


def test_no_frames_means_no_vision_call(review_output, fake_jev):
    asyncio.run(review_generator.generate_review(SLIDES, "書き起こし", "general"))

    assert review_output.create_calls == []


def test_frame_extraction_returns_empty_list_for_non_video_files(tmp_path):
    fake_video = tmp_path / "pitch.mp4"
    fake_video.write_bytes(b"this is not really a video")

    assert video_frames.extract_frames_base64(str(fake_video)) == []


@pytest.mark.parametrize("filename, expected", [("a.mp4", True), ("A.WEBM", True), ("a.mp3", False), ("a.m4a", False)])
def test_only_mp4_and_webm_count_as_video(filename, expected):
    assert video_frames.is_video_file(filename) is expected


def test_frame_extraction_returns_evenly_spaced_jpegs_from_a_real_video(tmp_path):
    import base64

    import av

    path = tmp_path / "pitch.mp4"
    with av.open(str(path), mode="w") as container:
        stream = container.add_stream("mpeg4", rate=10)
        stream.width, stream.height, stream.pix_fmt = 32, 32, "yuv420p"
        for i in range(30):  # 3 seconds
            frame = av.VideoFrame(32, 32, "rgb24")
            frame.planes[0].update(bytes([i * 8 % 256]) * (32 * 32 * 3))
            for packet in stream.encode(frame.reformat(format="yuv420p")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)

    frames = video_frames.extract_frames_base64(str(path))

    assert len(frames) == video_frames.NUM_FRAMES
    assert all(base64.b64decode(f).startswith(b"\xff\xd8") for f in frames)  # JPEG magic
