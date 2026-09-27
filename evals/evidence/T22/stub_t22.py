"""Scratchpad-only stub for T22 screenshots. Not part of the repo.

Only the external AI clients (Claude, Whisper, Jev) are faked; every key is
overwritten with a dummy so a real API can never be reached, and review
history is not written to backend/data/reviews.
"""

import asyncio
import os
import sys
from types import SimpleNamespace

BACKEND_DIR = r"C:\Users\tomo2\OneDrive\Desktop\エンジニアリング\ハリネズミ\backend"
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)
for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TYPESAFE_API_KEY"):
    os.environ[k] = "screenshot-dummy"

from app.models import contest as C  # noqa: E402
from app.models import schemas as S  # noqa: E402
from app.routers import review as review_router  # noqa: E402
from app.services import contest_scorer, history, jev_scorer, question_builder, review_generator, transcription  # noqa: E402

DELAY = float(os.environ.get("STUB_DELAY", "0"))
LEVELS = [
    "発表で全く触れていない",
    "触れているが、誰のどんな課題かが曖昧",
    "誰の課題かは分かるが、根拠が弱い",
    "具体的で、一定の根拠がある",
    "具体的な数値や一次調査で裏付けられている",
]
NAMES = ["課題の明確さ", "技術力", "チームワーク"]


class FakeClaude:
    def __init__(self, api_key):
        self.messages = SimpleNamespace(parse=self._parse, create=self._create)

    async def _parse(self, output_format, **kw):
        await asyncio.sleep(DELAY)
        if output_format is S.GeneratedLevelsOutput:
            return SimpleNamespace(parsed_output=S.GeneratedLevelsOutput(
                criteria=[S.GeneratedCriterion(name=n, levels=LEVELS) for n in NAMES]))
        if output_format is S.CustomRubricLLMOutput:
            return SimpleNamespace(parsed_output=S.CustomRubricLLMOutput(
                criteria=[S.GeneratedCriterion(name=f"観点{i}", levels=LEVELS) for i in range(1, 8)]))
        return SimpleNamespace(parsed_output=S.PitchReviewLLMOutput(
            overall_summary="課題設定は明確で、デモも安定して動いていました。市場規模の根拠をもう一歩示すと説得力が増します。",
            criterion_comments=[S.CriterionComment(id=f"c{i}", comment="スライド2で対象ユーザーと困りごとが具体的に示されています。") for i in range(1, 11)],
            strengths=["課題が具体的で、聞き手が自分ごととして想像しやすい", "デモが止まらずに最後まで動いた"],
            improvements=[
                S.ImprovementSuggestion(point="市場規模の根拠", suggestion="出典つきの数値をスライド4に入れ、どこまでが推計かを明記する"),
                S.ImprovementSuggestion(point="競合との違い", suggestion="既存の就活サイトとの比較表を1枚追加する"),
            ],
            one_line_verdict="筋の良いアイデア。根拠の厚みで上位を狙える。"))

    async def _create(self, **kw):
        await asyncio.sleep(DELAY)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="発表者は正面を向いて聴衆に視線を配り、要所で手を広げる身振りを交えて話している。表情は落ち着いており、スライドを指し示す動作も見られる。")])


class FakeJev:
    def __init__(self, api_key):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *e):
        return False

    async def system_one(self, state, questions):
        await asyncio.sleep(DELAY)
        fixed = [(3.2, 0.82), (1.4, 0.38), (2.6, 0.71), (3.6, 0.9), (2.9, 0.77), (2.2, 0.64), (3.1, 0.8)]
        return SimpleNamespace(scores={k: SimpleNamespace(score=fixed[i % 7][0], confidence=fixed[i % 7][1]) for i, k in enumerate(questions)})


class FakeWhisper:
    def __init__(self, api_key):
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._c))

    async def _c(self, model, file):
        await asyncio.sleep(DELAY)
        return SimpleNamespace(text="私たちは、学生が就活情報を集めきれない課題を、AIの要約で解決します。")


async def fake_generate_questions(rubric):
    await asyncio.sleep(DELAY)
    return C.QuestionSet(rubric=rubric, questions=[
        C.JevScoreQuestion(criterion_id=c.id, instructions=f"{c.name}をどの程度満たしているか", levels=list(LEVELS))
        for c in rubric.criteria
    ])


review_generator.AsyncAnthropic = FakeClaude
review_router.AsyncAnthropic = FakeClaude
contest_scorer.AsyncAnthropic = FakeClaude
jev_scorer.AsyncTypeSafeClient = FakeJev
transcription.AsyncOpenAI = FakeWhisper
question_builder.generate_questions = fake_generate_questions
history.save_review = lambda review: None

import uvicorn  # noqa: E402
from app.main import app  # noqa: E402

uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
