import shutil
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.models.schemas import PitchReviewResponse, SlideExtractionResult, TranscriptionResult
from app.rubric import DEFAULT_MODE, RUBRIC_MODES
from app.services import audio_extraction, history, review_generator, slide_extractor
from app.services.media_url import download_audio_from_url
from app.services.review_generator import DEFAULT_TONE, TONE_LABELS
from app.services.transcription import transcribe
from app.utils.file_validation import save_temp_upload, validate_upload

router = APIRouter(prefix="/api")

SLIDE_EXTS = {".pdf", ".pptx"}
MEDIA_EXTS = {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".mkv", ".webm", ".avi"}


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
        if audio_extraction.is_video_file(file.filename):
            try:
                path = audio_extraction.extract_audio(path, tmp_dir)
            except RuntimeError as e:
                raise HTTPException(status_code=500, detail=str(e)) from e
        return await transcribe(path, file.filename)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.post("/review", response_model=PitchReviewResponse)
async def create_review(
    slide_file: UploadFile | None = File(None),
    media_file: UploadFile | None = File(None),
    media_url: str | None = Form(None),
    mode: str = Form(DEFAULT_MODE),
    tone: str = Form(DEFAULT_TONE),
):
    if mode not in RUBRIC_MODES:
        raise HTTPException(status_code=400, detail=f"不明な審査モードです: {mode}")
    if tone not in TONE_LABELS:
        raise HTTPException(status_code=400, detail=f"不明なフィードバックトーンです: {tone}")
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
            media_filename = media_file.filename
            if audio_extraction.is_video_file(media_filename):
                try:
                    media_path = audio_extraction.extract_audio(media_path, tmp_dir)
                except RuntimeError as e:
                    raise HTTPException(status_code=500, detail=str(e)) from e
            transcription = await transcribe(media_path, media_filename)
            transcript = transcription.text
        elif media_url:
            media_path, media_filename = download_audio_from_url(media_url, tmp_dir, settings.max_media_mb)
            transcription = await transcribe(media_path, media_filename)
            transcript = transcription.text

        review = await review_generator.generate_review(slides, transcript, mode, tone)
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
