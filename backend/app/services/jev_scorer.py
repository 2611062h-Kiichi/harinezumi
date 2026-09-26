import logging
from dataclasses import dataclass

import typesafe_sdk
from fastapi import HTTPException
from typesafe_sdk import AsyncTypeSafeClient, Score

from app.config import get_settings
from app.rubric import SCALE_MIN

logger = logging.getLogger(__name__)


@dataclass
class JevCriterionScore:
    score_1_5: float  # continuous, SCALE_MIN..SCALE_MAX
    confidence: float  # 0..1


async def score_with_jev(state_text: str, criteria: list[dict]) -> dict[str, JevCriterionScore]:
    """Scores every given rubric criterion against `state_text` in a single
    parallel Jev request, returning a continuous 1-5 score and confidence per
    criterion id. `criteria` may be a static rubric or one generated on the
    fly for a user-described event."""
    settings = get_settings()
    if not settings.typesafe_api_key:
        raise HTTPException(status_code=400, detail="TYPESAFE_API_KEYが設定されていません。")

    questions = {
        c["id"]: Score(instructions=c["name"], criteria=c["levels"])
        for c in criteria
    }

    try:
        async with AsyncTypeSafeClient(api_key=settings.typesafe_api_key) as client:
            result = await client.system_one(state_text, questions)
    except typesafe_sdk.TypeSafeAuthenticationError as e:
        logger.exception("Jev authentication failed")
        raise HTTPException(status_code=400, detail="TYPESAFE_API_KEYが正しくありません。") from e
    except typesafe_sdk.TypeSafeRateLimitError as e:
        logger.exception("Jev rate limited")
        raise HTTPException(
            status_code=502,
            detail="Jev(TypeSafe API)の利用上限に達しました。しばらく待ってから再度お試しください。",
        ) from e
    except typesafe_sdk.TypeSafeAPIConnectionError as e:
        logger.exception("Jev connection error")
        raise HTTPException(status_code=502, detail="Jev(TypeSafe API)への接続に失敗しました。ネットワークを確認してください。") from e
    except typesafe_sdk.TypeSafeError as e:
        logger.exception("Jev scoring failed")
        raise HTTPException(status_code=502, detail=f"Jev(TypeSafe API)エラー: {e}") from e

    return {
        c["id"]: JevCriterionScore(
            score_1_5=result.scores[c["id"]].score + SCALE_MIN,
            confidence=result.scores[c["id"]].confidence,
        )
        for c in criteria
    }
