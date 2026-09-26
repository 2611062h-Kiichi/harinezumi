import logging
from datetime import datetime, timezone
from typing import TypeVar

import anthropic
from anthropic import AsyncAnthropic
from fastapi import HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.models.schemas import (
    CriterionScore,
    CustomRubricLLMOutput,
    GeneratedLevelsOutput,
    PitchReviewLLMOutput,
    PitchReviewLLMOutputFallback,
    PitchReviewResponse,
    SlideExtractionResult,
)
from app.rubric import (
    BUSINESS_RUBRIC_CRITERIA,
    DEFAULT_MODE,
    GENERAL_RUBRIC_CRITERIA,
    SCALE_MAX,
    SCALE_MIN,
    compute_overall_score,
)
from app.services.jev_scorer import JevCriterionScore, score_with_jev

logger = logging.getLogger(__name__)

BUSINESS_INTRO = """あなたは学生・大学主催のビジネスプランコンテストの経験豊富な審査員です。
審査には田所雅之著「起業の科学」のリーンスタートアップ検証フレームワークを用います。
出場者はまだ起業前後の学生が多いため、資金調達の実績そのものよりも、
「顧客の課題は本物か」「解決策は検証されているか」「市場・収益性は数字で裏付けられているか」
という検証プロセスの質を重視して審査してください。

用語の定義（審査で厳密に区別すること）:
- CPF (Customer Problem Fit): 想定顧客が本当にその課題を抱えているかの検証
- PSF (Problem Solution Fit): その課題を今回の解決策が実際に解決できるかの検証
- PMF (Product Market Fit): プロダクト・サービスが市場に受け入れられ、使われ続けている状態
- ペインの質: 誰が(Whom)・どんな時に(Occasion)感じる痛みかが明確で、
  対価を払ってでも解決したい「痛み止め（Painkiller）」か、
  なくても困らない「ビタミン剤」かを見極める考え方"""

GENERAL_INTRO_DEFAULT = """あなたは経験豊富なピッチコンテストの審査員です。
ビジネス・研究・社会課題解決など業界やテーマを問わず、
提案されているアイデア・取り組みが課題解決として筋が通っているか、
実現可能か、具体的な根拠に裏付けられているかを公正に審査してください。"""


def build_general_intro(event_context: str | None) -> str:
    if not event_context:
        return GENERAL_INTRO_DEFAULT
    return f"""あなたは経験豊富なピッチ・発表審査員です。
今回審査するのは「{event_context}」というイベントでの発表です。
このイベントの性質・目的に沿った観点で、公正かつ具体的に審査してください。"""


DEFAULT_TONE = "normal"

TONE_LABELS = {
    "mild": "甘口（励まし重視）",
    "normal": "普通",
    "spicy": "辛口（VC級の厳しさ）",
}

TONE_INSTRUCTIONS = {
    "mild": (
        "フィードバックの口調は「甘口」です。良い点を先に具体的に褒め、"
        "改善点は励ますような前向きな言葉で伝えてください。"
        "高圧的な言い回しや突き放すような表現は避けてください。"
    ),
    "normal": "事実に基づいた誠実なフィードバックをしてください。",
    "spicy": (
        "フィードバックの口調は「辛口」です。投資家・審査員として一切の忖度をせず、"
        "弱点や詰めの甘さを遠慮なくストレートに指摘してください。"
        "曖昧な言い回しでごまかさず、率直かつ辛辣な表現を使って構いません"
        "（ただし人格攻撃や暴言は避け、あくまで内容への指摘に徹すること）。"
    ),
}

RUBRIC_GENERATION_SYSTEM_PROMPT = """あなたはピッチ・プレゼン審査のルーブリック設計の専門家です。
与えられたイベントの内容に基づいて、そのイベントの審査に最適な7つの評価項目を設計してください。

イベント内容が具体的な大会名・団体名など実在するイベントを指していると思われる場合は、
web検索ツールを使って、その大会の公式な審査基準・募集要項・テーマを調べ、
分かった実際の評価観点をルーブリックに反映してください。
検索しても情報が見つからない場合や、イベント内容が一般的な説明（例:「学生向けハッカソン」）の場合は、
無理に検索を繰り返さず、一般的な知見に基づいて設計してください。

各評価項目には以下を含めてください:
- name: 評価項目名（日本語、20文字程度）
- levels: 1点から5点までの5段階の水準説明（低い順に5つ）。各文は「〜が示されている」のように、
  発表内容を見れば該当するかどうか判定できる具体的な表現にすること。

項目はイベントの性質に応じて適切なものを選んでください
（例: ハッカソンなら技術的完成度やデモの動作、研究発表なら新規性や検証の厳密性、
商品プレゼンなら差別化ポイントや訴求力、政策提言なら実現可能性や関係者への配慮、など）。
最後の1項目には必ず、プレゼン自体の分かりやすさ・訴求力を評価する項目を含めてください。
"""

RUBRIC_GENERATION_TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 3},
]


async def generate_custom_rubric(client: AsyncAnthropic, model: str, event_context: str) -> list[dict]:
    """Asks Claude to design a 7-criterion rubric (name + 5-level descriptions
    each) tailored to a user-described event, in the same shape as the static
    rubrics in app/rubric.py so downstream code can treat them uniformly.
    Claude may use web search to look up a named real-world event's actual
    judging criteria before designing the rubric."""
    user_prompt = f"イベント内容: {event_context}\n\nこのイベントに最適な評価ルーブリックを設計してください。"
    result = await _call_claude(
        client, model, RUBRIC_GENERATION_SYSTEM_PROMPT, user_prompt, CustomRubricLLMOutput, tools=RUBRIC_GENERATION_TOOLS
    )
    return [
        {"id": f"c{i + 1}", "name": c.name, "levels": c.levels}
        for i, c in enumerate(result.criteria)
    ]


RUBRIC_FROM_NAMES_SYSTEM_PROMPT = """あなたはピッチ・プレゼン審査のルーブリック設計の専門家です。
ユーザーが指定した評価項目名それぞれについて、1点から5点までの5段階の水準説明を設計してください。

厳守事項:
- 項目名はユーザーが指定した通りに一字一句変更せず、指定された順番のまま使用すること。
- 項目を追加したり削除したりしないこと。
- 各levelsは低い順に5つ。各文は「〜が示されている」のように、
  発表内容を見れば該当するかどうか判定できる具体的な表現にすること。
"""


async def generate_rubric_from_names(client: AsyncAnthropic, model: str, names: list[str]) -> list[dict]:
    """Asks Claude to write 5-level descriptions for user-supplied criterion
    names, preserving the names and order exactly as given."""
    names_lines = chr(10).join(f"{i + 1}. {name}" for i, name in enumerate(names))
    user_prompt = f"評価項目名:\n{names_lines}\n\nそれぞれの項目について5段階の水準説明を設計してください。"
    result = await _call_claude(client, model, RUBRIC_FROM_NAMES_SYSTEM_PROMPT, user_prompt, GeneratedLevelsOutput)
    # Trust the user's names/order over whatever Claude echoed back; only take the levels.
    return [
        {"id": f"c{i + 1}", "name": name, "levels": result.criteria[i].levels if i < len(result.criteria) else []}
        for i, name in enumerate(names)
    ]


def build_system_prompt(mode_intro: str, criteria: list[dict], tone: str = DEFAULT_TONE, jev_available: bool = True) -> str:
    criteria_lines = chr(10).join(f"- {c['id']}: {c['name']}" for c in criteria)

    if jev_available:
        scoring_instructions = f"""以下の{len(criteria)}つの評価項目について、それぞれの点数はすでに確定しています
（採点は別のモデルが担当し、あなたはコメント執筆のみを担当します）。
{criteria_lines}

ユーザーメッセージ内の「各項目の確定スコア」セクションに記載された点数を踏まえ、
なぜその点数になるのかが分かる具体的なコメントを日本語で書いてください。
点数そのものを変更したり、独自に採点し直したりしないでください。"""
    else:
        scoring_instructions = f"""審査は必ず以下の{len(criteria)}つの評価項目に沿って行い、他の項目を追加しないでください。
各項目は{SCALE_MIN}〜{SCALE_MAX}点で採点し、採点根拠となる具体的なコメントを日本語で書いてください。
{criteria_lines}"""

    return f"""{mode_intro}

{scoring_instructions}

{TONE_INSTRUCTIONS[tone]}
改善提案は抽象的な精神論ではなく、実際にスライドや発表内容のどこをどう直すべきかが分かる具体的な内容にしてください。
ユーザーメッセージに「発表映像から読み取れる非言語的表現」のセクションがある場合、
プレゼンの分かりやすさ・訴求力に関する評価項目では、話の内容だけでなく
その非言語的な要素（身振り・表情など）も踏まえて判断してください。
"""


def build_user_prompt(
    slides: SlideExtractionResult | None,
    transcript: str | None,
    visual_description: str | None = None,
) -> str:
    parts = []
    if slides:
        slide_sections = []
        for slide in slides.slides:
            section = f"## スライド{slide.index}\n{slide.text or '(テキストなし)'}"
            if slide.notes:
                section += f"\n(スピーカーノート: {slide.notes})"
            slide_sections.append(section)
        parts.append(f"# ピッチ資料（{slides.filename}）")
        parts.append("\n\n".join(slide_sections))
    else:
        parts.append("# ピッチ資料\nスライド資料はありません。発表音声の書き起こしのみで審査してください。")

    if transcript:
        parts.append(f"# 発表音声の書き起こし\n{transcript}")
    else:
        parts.append("# 発表音声の書き起こし\n音声書き起こしはありません。スライドの内容のみで審査してください。")

    if visual_description:
        parts.append(f"# 発表映像から読み取れる非言語的表現\n{visual_description}")

    return "\n\n".join(parts)


def build_score_context(criteria: list[dict], jev_scores: dict[str, JevCriterionScore]) -> str:
    lines = []
    for c in criteria:
        s = jev_scores[c["id"]]
        lines.append(f"- {c['id']}（{c['name']}）: {s.score_1_5:.1f} / {SCALE_MAX}（確信度 {s.confidence * 100:.0f}%）")
    return "# 各項目の確定スコア（変更不可。この点数を踏まえてコメントを書くこと）\n" + "\n".join(lines)


T = TypeVar("T", bound=BaseModel)


async def _call_claude(
    client: AsyncAnthropic,
    model: str,
    system_prompt: str,
    user_prompt: str,
    output_format: type[T],
    tools: list[dict] | None = None,
) -> T:
    kwargs = {}
    if tools:
        kwargs["tools"] = tools

    try:
        response = await client.messages.parse(
            model=model,
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            output_format=output_format,
            **kwargs,
        )
    except anthropic.AuthenticationError as e:
        logger.exception("Anthropic authentication failed")
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEYが正しくありません。") from e
    except anthropic.BadRequestError as e:
        logger.exception("Anthropic API rejected the request")
        raise HTTPException(status_code=502, detail=f"Anthropic APIエラー: {e.message}") from e
    except anthropic.RateLimitError as e:
        logger.exception("Anthropic API rate limited")
        raise HTTPException(
            status_code=502,
            detail="Anthropic APIの利用上限に達しました。しばらく待ってから再度お試しください。",
        ) from e
    except anthropic.APIConnectionError as e:
        logger.exception("Anthropic API connection error")
        raise HTTPException(status_code=502, detail="Anthropic APIへの接続に失敗しました。ネットワークを確認してください。") from e
    except Exception as e:
        logger.exception("AI review generation failed")
        raise HTTPException(status_code=502, detail="AIレビューの生成に失敗しました。もう一度お試しください。") from e

    if response.parsed_output is None:
        raise HTTPException(status_code=502, detail="AIレビューの生成に失敗しました。もう一度お試しください。")
    return response.parsed_output


VISUAL_DESCRIPTION_SYSTEM_PROMPT = """あなたはピッチ発表の映像を分析する専門家です。
与えられた画像は、ある発表の動画から均等な間隔で抽出した複数枚の静止画です。
これらの画像から読み取れる、プレゼンテーションの非言語的な要素
（表情、姿勢、身振り手振り、資料の指し示し方、カメラ・聴衆へのアイコンタクトなど）を、
日本語で簡潔に説明してください。

- 画像から客観的に観察できる事実のみを記述し、断定しすぎないこと。
- スライドの内容そのものの説明は不要です。発表者の様子・非言語的な表現方法のみに注目してください。
- 数枚の静止画だけからの推測であることを踏まえ、過度に強い評価コメントは避けてください。
"""


async def describe_presentation_visuals(client: AsyncAnthropic, model: str, frames_base64: list[str]) -> str | None:
    """Asks Claude (vision) to describe non-verbal presentation delivery
    (posture, gestures, eye contact, etc.) from a handful of video frames.
    Returns None on any failure — this is a nice-to-have enrichment, not a
    required step, so callers should just proceed without it on failure."""
    if not frames_base64:
        return None

    content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": f}} for f in frames_base64
    ]
    content.append(
        {"type": "text", "text": "これらは発表動画から抽出した静止画です。発表者の非言語的な表現について説明してください。"}
    )

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=VISUAL_DESCRIPTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
    except Exception:
        logger.warning("Visual description generation failed; continuing without it", exc_info=True)
        return None

    text_blocks = [b.text for b in response.content if b.type == "text"]
    return "\n".join(text_blocks) if text_blocks else None


async def resolve_rubric(
    client: AsyncAnthropic,
    model: str,
    mode: str,
    event_context: str | None,
    criteria_names: list[str] | None = None,
    custom_criteria: list[dict] | None = None,
) -> tuple[list[dict], str, str]:
    """Resolves (rubric_criteria, mode_intro, rubric_label) for a mode +
    optional event_context/criteria_names/custom_criteria. Shared by
    generate_review() and the rubric preview endpoint so both see exactly
    the same rubric. Priority: custom_criteria (a previously-previewed
    rubric the user then edited by hand) > criteria_names > event_context."""
    if mode == "business":
        return BUSINESS_RUBRIC_CRITERIA, BUSINESS_INTRO, "ビジネスコンテスト向け（起業の科学ベース）"
    if custom_criteria:
        return custom_criteria, build_general_intro(event_context), "汎用ピッチ審査（カスタム評価項目）"
    if criteria_names:
        rubric_criteria = await generate_rubric_from_names(client, model, criteria_names)
        return rubric_criteria, build_general_intro(event_context), "汎用ピッチ審査（カスタム評価項目）"
    if event_context:
        rubric_criteria = await generate_custom_rubric(client, model, event_context)
        return rubric_criteria, build_general_intro(event_context), f"汎用ピッチ審査（{event_context}向け）"
    return GENERAL_RUBRIC_CRITERIA, GENERAL_INTRO_DEFAULT, "汎用ピッチ審査"


async def generate_review(
    slides: SlideExtractionResult | None,
    transcript: str | None,
    mode: str = DEFAULT_MODE,
    tone: str = DEFAULT_TONE,
    event_context: str | None = None,
    criteria_names: list[str] | None = None,
    custom_criteria: list[dict] | None = None,
    video_frames_base64: list[str] | None = None,
) -> PitchReviewResponse:
    if slides is None and not transcript:
        raise HTTPException(status_code=400, detail="スライド資料または音声/動画のいずれかを指定してください。")
    if mode not in ("business", "general"):
        raise HTTPException(status_code=400, detail=f"不明な審査モードです: {mode}")
    if tone not in TONE_INSTRUCTIONS:
        raise HTTPException(status_code=400, detail=f"不明なフィードバックトーンです: {tone}")

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEYが設定されていません。")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    event_context = event_context.strip() if event_context else None

    rubric_criteria, mode_intro, rubric_label = await resolve_rubric(
        client, settings.claude_model, mode, event_context, criteria_names, custom_criteria
    )

    visual_description = await describe_presentation_visuals(client, settings.claude_model, video_frames_base64 or [])
    pitch_content = build_user_prompt(slides, transcript, visual_description)
    jev_available = bool(settings.typesafe_api_key)

    if jev_available:
        # Jev scores every criterion (fast, calibrated); Claude only writes
        # the qualitative narrative around those fixed scores.
        jev_scores = await score_with_jev(pitch_content, rubric_criteria)
        system_prompt = build_system_prompt(mode_intro, rubric_criteria, tone, jev_available=True)
        user_prompt = pitch_content + "\n\n" + build_score_context(rubric_criteria, jev_scores)
        llm_output = await _call_claude(client, settings.claude_model, system_prompt, user_prompt, PitchReviewLLMOutput)

        comments_by_id = {c.id: c.comment for c in llm_output.criterion_comments}
        criteria_out = [
            CriterionScore(
                id=c["id"],
                name=c["name"],
                score=round(jev_scores[c["id"]].score_1_5),
                max_score=SCALE_MAX,
                comment=comments_by_id.get(c["id"], ""),
                confidence=jev_scores[c["id"]].confidence,
                levels=c["levels"],
            )
            for c in rubric_criteria
        ]
        overall_score = compute_overall_score([jev_scores[c["id"]].score_1_5 for c in rubric_criteria])
    else:
        # No TYPESAFE_API_KEY configured — Claude scores and comments in one call.
        logger.warning("TYPESAFE_API_KEY not set; falling back to Claude-only scoring")
        system_prompt = build_system_prompt(mode_intro, rubric_criteria, tone, jev_available=False)
        llm_output = await _call_claude(
            client, settings.claude_model, system_prompt, pitch_content, PitchReviewLLMOutputFallback
        )

        scores_by_id = {c.id: c for c in llm_output.criterion_scores}
        criteria_out = [
            CriterionScore(
                id=c["id"],
                name=c["name"],
                score=scores_by_id[c["id"]].score if c["id"] in scores_by_id else SCALE_MIN,
                max_score=SCALE_MAX,
                comment=scores_by_id[c["id"]].comment if c["id"] in scores_by_id else "",
                confidence=None,
                levels=c["levels"],
            )
            for c in rubric_criteria
        ]
        overall_score = compute_overall_score([float(c.score) for c in criteria_out])

    return PitchReviewResponse(
        overall_score=overall_score,
        overall_summary=llm_output.overall_summary,
        criteria=criteria_out,
        strengths=llm_output.strengths,
        improvements=llm_output.improvements,
        one_line_verdict=llm_output.one_line_verdict,
        generated_at=datetime.now(timezone.utc),
        transcript_included=transcript is not None,
        rubric_mode=mode,
        rubric_mode_label=rubric_label,
        feedback_tone=tone,
        feedback_tone_label=TONE_LABELS[tone],
    )
