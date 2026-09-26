import json
import shutil
import tempfile

from anthropic import AsyncAnthropic
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.config import get_settings
from app.models.schemas import (
    GeneratedCriterion,
    PitchReviewResponse,
    RubricCriterionPreview,
    RubricPreviewResponse,
    SlideExtractionResult,
    TranscriptionResult,
)
from app.rubric import DEFAULT_MODE, RUBRIC_MODES
from app.services import history, review_generator, slide_extractor
from app.services.media_url import download_audio_from_url
from app.services.review_generator import DEFAULT_TONE, TONE_LABELS, resolve_rubric
from app.services.transcription import transcribe
from app.utils.file_validation import save_temp_upload, validate_upload

router = APIRouter(prefix="/api")

SLIDE_EXTS = {".pdf", ".pptx"}
# Whisper accepts these directly (including video containers with an audio
# track), so no local ffmpeg extraction step is needed.
MEDIA_EXTS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}
MAX_EVENT_CONTEXT_LENGTH = 300
MAX_CRITERION_NAME_LENGTH = 50
MIN_CRITERIA_NAMES = 3
MAX_CRITERIA_NAMES = 10


def parse_criteria_names(raw: str | None) -> list[str] | None:
    """Parses the newline-separated `criteria_names` form field into a
    validated list, or None if the field was empty/omitted."""
    if not raw or not raw.strip():
        return None
    names = [line.strip() for line in raw.splitlines() if line.strip()]
    if not (MIN_CRITERIA_NAMES <= len(names) <= MAX_CRITERIA_NAMES):
        raise HTTPException(
            status_code=400,
            detail=f"評価項目は{MIN_CRITERIA_NAMES}〜{MAX_CRITERIA_NAMES}個で入力してください。",
        )
    if any(len(name) > MAX_CRITERION_NAME_LENGTH for name in names):
        raise HTTPException(
            status_code=400,
            detail=f"評価項目名は1つあたり{MAX_CRITERION_NAME_LENGTH}文字以内で入力してください。",
        )
    return names


def parse_custom_rubric(raw: str | None) -> list[dict] | None:
    """Parses the `custom_rubric_json` form field — a JSON array of
    {name, levels} objects, typically a previously-previewed rubric the user
    then edited by hand — into the same shape as the static rubrics."""
    if not raw or not raw.strip():
        return None
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="評価基準の形式が正しくありません。") from e
    if not isinstance(items, list) or not (1 <= len(items) <= MAX_CRITERIA_NAMES):
        raise HTTPException(
            status_code=400, detail=f"評価基準は1〜{MAX_CRITERIA_NAMES}項目で指定してください。"
        )
    try:
        parsed = [GeneratedCriterion.model_validate(item) for item in items]
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"評価基準の形式が正しくありません: {e}") from e
    return [{"id": f"c{i + 1}", "name": c.name, "levels": c.levels} for i, c in enumerate(parsed)]


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/slides/extract", response_model=SlideExtractionResult)
async def extract_slides_endpoint(file: UploadFile = File(...)):
    settings = get_settings()
    validate_upload(file, SLIDE_EXTS, settings.max_slide_mb)
    tmp_dir = tempfile.mkdtemp()
    try:
        path = save_temp_upload(file, tmp_dir)
        return slide_extractor.extract_slides(path, file.filename)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/media/transcribe", response_model=TranscriptionResult)
async def transcribe_media_endpoint(file: UploadFile = File(...)):
    settings = get_settings()
    validate_upload(file, MEDIA_EXTS, settings.max_media_mb)
    tmp_dir = tempfile.mkdtemp()
    try:
        path = save_temp_upload(file, tmp_dir)
        return await transcribe(path, file.filename)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/rubric/preview", response_model=RubricPreviewResponse)
async def preview_rubric(
    mode: str = Form(DEFAULT_MODE),
    event_context: str | None = Form(None),
    criteria_names: str | None = Form(None),
):
    if mode not in RUBRIC_MODES:
        raise HTTPException(status_code=400, detail=f"不明な審査モードです: {mode}")
    if event_context and len(event_context) > MAX_EVENT_CONTEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"イベント内容は{MAX_EVENT_CONTEXT_LENGTH}文字以内で入力してください。",
        )
    parsed_criteria_names = parse_criteria_names(criteria_names)

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEYが設定されていません。")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    event_context = event_context.strip() if event_context else None
    criteria, _, rubric_label = await resolve_rubric(
        client, settings.claude_model, mode, event_context, parsed_criteria_names
    )

    return RubricPreviewResponse(
        rubric_mode_label=rubric_label,
        criteria=[RubricCriterionPreview(id=c["id"], name=c["name"], levels=c["levels"]) for c in criteria],
    )


@router.post("/review", response_model=PitchReviewResponse)
async def create_review(
    slide_file: UploadFile | None = File(None),
    media_file: UploadFile | None = File(None),
    media_url: str | None = Form(None),
    mode: str = Form(DEFAULT_MODE),
    tone: str = Form(DEFAULT_TONE),
    event_context: str | None = Form(None),
    criteria_names: str | None = Form(None),
    custom_rubric_json: str | None = Form(None),
):
    if mode not in RUBRIC_MODES:
        raise HTTPException(status_code=400, detail=f"不明な審査モードです: {mode}")
    if tone not in TONE_LABELS:
        raise HTTPException(status_code=400, detail=f"不明なフィードバックトーンです: {tone}")
    if event_context and len(event_context) > MAX_EVENT_CONTEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"イベント内容は{MAX_EVENT_CONTEXT_LENGTH}文字以内で入力してください。",
        )
    parsed_criteria_names = parse_criteria_names(criteria_names)
    parsed_custom_rubric = parse_custom_rubric(custom_rubric_json)
    if media_file is not None and media_url:
        raise HTTPException(status_code=400, detail="音声/動画はファイルとURLのどちらか一方のみ指定してください。")
    if slide_file is None and media_file is None and not media_url:
        raise HTTPException(status_code=400, detail="スライド資料または音声/動画のいずれかを指定してください。")

    settings = get_settings()
    if slide_file is not None:
        validate_upload(slide_file, SLIDE_EXTS, settings.max_slide_mb)
    if media_file is not None:
        validate_upload(media_file, MEDIA_EXTS, settings.max_media_mb)

    tmp_dir = tempfile.mkdtemp()
    try:
        slides = None
        if slide_file is not None:
            slide_path = save_temp_upload(slide_file, tmp_dir)
            slides = slide_extractor.extract_slides(slide_path, slide_file.filename)

        transcript = None
        if media_file is not None:
            media_path = save_temp_upload(media_file, tmp_dir)
            transcription = await transcribe(media_path, media_file.filename)
            transcript = transcription.text
        elif media_url:
            media_path, media_filename = download_audio_from_url(media_url, tmp_dir, settings.max_media_mb)
            transcription = await transcribe(media_path, media_filename)
            transcript = transcription.text

        review = await review_generator.generate_review(
            slides, transcript, mode, tone, event_context, parsed_criteria_names, parsed_custom_rubric
        )
        try:
            history.save_review(review)
        except OSError:
            pass
        return review
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/reviews/history", response_model=list[PitchReviewResponse])
async def get_history(n: int = 10):
    return history.list_recent(n)
