"""Turns a contest's scoring criteria into Jev Score questions using Claude.

Claude is asked for a deliberately simple shape (the SDK strips JSON-schema
constraints the API does not support), and the result is then validated as a
QuestionSet, which enforces exactly one 5-level question per criterion.
Invalid output is rejected rather than silently repaired.
"""

import json
import logging

from anthropic import AsyncAnthropic
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.models.contest import JEV_LEVEL_COUNT, ContestRubric, QuestionSet
from app.services.review_generator import _call_claude

logger = logging.getLogger(__name__)

FAILURE_DETAIL = "Questionの生成に失敗しました。もう一度お試しください。"


class GeneratedQuestion(BaseModel):
    criterion_id: str
    instructions: str
    levels: list[str]


class GeneratedQuestions(BaseModel):
    """Schema requested from Claude. Checked against QuestionSet afterwards."""

    questions: list[GeneratedQuestion]


SYSTEM_PROMPT = f"""あなたはピッチコンテストの採点設計の専門家です。
コンテスト主催者が公開している採点観点を、採点AI「Jev」に渡す段階評価の質問（Score Question）に変換してください。
Jev は発表音声の書き起こしテキストを読み、各質問について「どの段階に当てはまるか」を判定します。

各観点につき、ちょうど1つの質問を作ってください。
- criterion_id: 入力された観点の id をそのまま書く（変更・追加・省略しない）
- instructions: その観点だけを「〜をどの程度満たしているか」の形で聞く1文。複数の観点を混ぜない
- levels: ちょうど{JEV_LEVEL_COUNT}個の段階の説明を、低い段階から高い段階の順に並べる
  - 1つ目は「その観点について発表で全く触れていない・満たしていない」状態にする
  - 各段階は、発表を聞いた人が確認できる事実で書く（「すごい」「弱い」のような感想語だけにしない）
  - 隣り合う段階の違いがはっきり分かるようにする

主催者の観点の意味を変えないでください。観点の説明に書かれていない基準を付け足す場合も、主催者の意図から外れないようにしてください。
出力はすべて日本語で書いてください。"""


def build_user_prompt(rubric: ContestRubric) -> str:
    criteria = [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description or "（説明なし）",
            "max_points": c.max_points,
        }
        for c in rubric.criteria
    ]
    return (
        f"# コンテスト名\n{rubric.contest_name}\n\n"
        f"# 採点観点（{len(criteria)}個）\n"
        f"{json.dumps(criteria, ensure_ascii=False, indent=2)}\n\n"
        f"上の{len(criteria)}個の観点それぞれについて、Jev の質問を1つずつ作ってください。"
    )


def _format_validation_error(error: ValidationError) -> str:
    return " / ".join(e["msg"].removeprefix("Value error, ") for e in error.errors())


async def generate_questions(rubric: ContestRubric) -> QuestionSet:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEYが設定されていません。")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    generated = await _call_claude(
        client,
        settings.claude_model,
        SYSTEM_PROMPT,
        build_user_prompt(rubric),
        GeneratedQuestions,
        failure_detail=FAILURE_DETAIL,
    )

    try:
        question_set = QuestionSet.model_validate(
            {"rubric": rubric, "questions": [q.model_dump() for q in generated.questions]}
        )
    except ValidationError as e:
        logger.warning("Claude returned questions that do not match the rubric: %s", e)
        raise HTTPException(
            status_code=502,
            detail=f"AIが作ったQuestionが観点と合いませんでした。もう一度お試しください。（{_format_validation_error(e)}）",
        ) from e

    # Claude may answer in any order; present questions in the organizer's order.
    position = {c.id: i for i, c in enumerate(rubric.criteria)}
    question_set.questions.sort(key=lambda q: position[q.criterion_id])
    return question_set
