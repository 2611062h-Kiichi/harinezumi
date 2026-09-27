"""T21 timing comparison (scratchpad only). Every external/slow step is faked
to take 1 second; no real API is called (keys are dummies, network is not used).
Run from backend/ against the current code, and again with the old code stashed."""

import asyncio
import os
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, os.getcwd())
for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TYPESAFE_API_KEY"):
    os.environ[k] = "timing-dummy"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models import schemas as S  # noqa: E402
from app.routers import contest as contest_router  # noqa: E402
from app.routers import review as review_router  # noqa: E402
from app.services import contest_scorer, jev_scorer, review_generator, slide_extractor, transcription  # noqa: E402

D = 1.0
SLIDES = S.SlideExtractionResult(filename="p.pptx", slides=[S.SlideContent(index=1, text="課題")])
LEVELS = ["1", "2", "3", "4", "5"]


def slow(result):
    def run(*a, **k):
        time.sleep(D)
        return result
    return run


class Whisper:
    def __init__(self, api_key):
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self.c))

    async def c(self, model, file):
        await asyncio.sleep(D)
        return SimpleNamespace(text="発表の書き起こし")


class Claude:
    def __init__(self, api_key):
        self.messages = SimpleNamespace(parse=self.p, create=self.v)

    async def p(self, output_format, **k):
        await asyncio.sleep(D)
        if output_format is S.GeneratedLevelsOutput:
            return SimpleNamespace(parsed_output=S.GeneratedLevelsOutput(
                criteria=[S.GeneratedCriterion(name=n, levels=LEVELS) for n in ("課題", "市場", "チーム")]))
        return SimpleNamespace(parsed_output=S.PitchReviewLLMOutput(
            overall_summary="s", criterion_comments=[], strengths=[], improvements=[], one_line_verdict="v"))

    async def v(self, **k):
        await asyncio.sleep(D)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="手振りを交えて話している")])


class Jev:
    def __init__(self, api_key): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False
    async def system_one(self, state, questions):
        await asyncio.sleep(D)
        return SimpleNamespace(scores={q: SimpleNamespace(score=2.0, confidence=0.8) for q in questions})


slide_extractor.extract_slides = slow(SLIDES)
review_router.extract_frames_base64 = slow(["AAAA"])
contest_router.read_slides = slow(SLIDES)
contest_scorer.extract_frames_base64 = slow(["AAAA"])
transcription.AsyncOpenAI = Whisper
review_generator.AsyncAnthropic = Claude
if hasattr(contest_scorer, "AsyncAnthropic"):
    contest_scorer.AsyncAnthropic = Claude
jev_scorer.AsyncTypeSafeClient = Jev
review_router.history.save_review = lambda r: None  # don't write review history

client = TestClient(app)
FILES = [("slide_file", ("p.pptx", b"x", "application/octet-stream")), ("media_file", ("p.mp4", b"v", "video/mp4"))]

t0 = time.perf_counter()
r = client.post("/api/review", data={"mode": "general", "criteria_names": "課題\n市場\nチーム"}, files=FILES)
review_s = time.perf_counter() - t0
print(f"ピッチ審査タブ（スライド＋動画＋項目名から評価基準を生成）: HTTP {r.status_code}、{review_s:.1f}秒")

from tests.test_contest_scorer import QUESTION_SET  # noqa: E402

t0 = time.perf_counter()
r = client.post("/api/contest/score", data={"question_set": QUESTION_SET.model_dump_json()}, files=FILES)
contest_s = time.perf_counter() - t0
print(f"コンテスト観点モード（スライド＋動画）: HTTP {r.status_code}、{contest_s:.1f}秒")
