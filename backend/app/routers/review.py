import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.models.schemas import PitchReviewResponse, SlideExtractionResult, TranscriptionResult
from app.services import audio_extraction, history, review_generator, slide_extractor
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
    slide_file: UploadFile = File(...),
    media_file: UploadFile | None = File(None),
):
    settings = get_settings()
    validate_upload(slide_file, SLIDE_EXTS, settings.max_slide_mb)
    if media_file is not None:
        validate_upload(media_file, MEDIA_EXTS, settings.max_media_mb)

    tmp_dir = tempfile.mkdtemp()
    try:
        slide_path = save_temp_upload(slide_file, tmp_dir)
        slides = slide_extractor.extract_slides(slide_path, slide_file.filename)

        transcript = None
        if media_file is not None:
            media_path = save_temp_upload(media_file, tmp_dir)
            if audio_extraction.is_video_file(media_file.filename):
                try:
                    media_path = audio_extraction.extract_audio(media_path, tmp_dir)
                except RuntimeError as e:
                    raise HTTPException(status_code=500, detail=str(e)) from e
            transcription = await transcribe(media_path, media_file.filename)
            transcript = transcription.text

        review = await review_generator.generate_review(slides, transcript)
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
