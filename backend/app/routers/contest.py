"""API for contest mode: criteria -> Jev questions, and audio + questions -> scores.

Input is validated here (not by FastAPI's automatic body/form parsing) so
that mistakes come back as 400 with Japanese messages instead of English 422s
or 500s.
"""

import json
import shutil
import tempfile

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ValidationError
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.models.contest import (
    ContestRubric,
    ContestScoreResult,
    QuestionSet,
    SavedQuestionSet,
    SavedQuestionSetSummary,
)
from app.models.schemas import SlideExtractionResult
from app.routers.review import MEDIA_EXTS, SLIDE_EXTS
from app.services import contest_scorer, question_builder, question_set_storage, slide_extractor
from app.utils.file_validation import save_temp_upload, validate_upload
from app.utils.validation_messages import to_japanese

router = APIRouter(prefix="/api/contest")

MAX_QUESTION_SET_BYTES = 1024 * 1024


def parse_json(raw: str | bytes, model: type[BaseModel], what: str):
    try:
        data = json.loads(raw)
    # ValueError covers malformed JSON, bad UTF-8 and integers over Python's
    # digit limit; RecursionError covers absurdly deep nesting.
    except (ValueError, RecursionError) as e:
        raise HTTPException(status_code=400, detail=f"{what}をJSONとして読み取れませんでした。") from e
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"{what}に誤りがあります。{to_japanese(e)}") from e


class SaveQuestionSetRequest(BaseModel):
    name: str
    question_set: QuestionSet


@router.post("/questions", response_model=QuestionSet)
async def create_questions(request: Request):
    rubric = parse_json(await request.body(), ContestRubric, "採点観点")
    return await question_builder.generate_questions(rubric)


@router.post("/question-sets", response_model=SavedQuestionSet)
async def save_question_set(request: Request):
    body = parse_json(await request.body(), SaveQuestionSetRequest, "保存内容")
    return question_set_storage.save(body.name, body.question_set)


@router.get("/question-sets", response_model=list[SavedQuestionSetSummary])
async def list_question_sets():
    return question_set_storage.list_all()


@router.get("/question-sets/{saved_id}", response_model=SavedQuestionSet)
async def get_question_set(saved_id: str):
    return question_set_storage.load(saved_id)


@router.post("/score", response_model=ContestScoreResult)
async def score_pitch(request: Request):
    try:
        form = await request.form()
    except StarletteHTTPException as e:
        # Starlette answers broken multipart bodies with an English 400.
        raise HTTPException(
            status_code=400, detail="送信データの形が正しくありません。画面からもう一度送信してください。"
        ) from e

    media_file = single_file(
        form, "media_file",
        too_many="音声または動画ファイルは1つだけ指定してください。",
        not_a_file="発表の音声または動画ファイルを指定してください。",
    )
    slide_file = single_file(
        form, "slide_file",
        too_many="スライド資料は1つだけ指定してください。",
        not_a_file="スライド資料はPDFまたはPPTXのファイルで指定してください。",
    )
    if media_file is None and slide_file is None:
        raise HTTPException(status_code=400, detail="スライド資料、または発表の音声・動画ファイルを指定してください。")

    raw_question_set = form.get("question_set")
    if isinstance(raw_question_set, UploadFile):
        # Browsers send a file part when a Blob is appended to FormData.
        raw_question_set = await raw_question_set.read(MAX_QUESTION_SET_BYTES + 1)
        if len(raw_question_set) > MAX_QUESTION_SET_BYTES:
            raise HTTPException(status_code=400, detail="Questionのデータが大きすぎます。")
    if not raw_question_set:
        raise HTTPException(status_code=400, detail="採点に使うQuestionを指定してください。")

    questions = parse_json(raw_question_set, QuestionSet, "Question")
    settings = get_settings()
    if slide_file is not None:
        validate_upload(slide_file, SLIDE_EXTS, settings.max_slide_mb)
    if media_file is not None:
        validate_upload(media_file, MEDIA_EXTS, settings.max_media_mb)

    tmp_dir = tempfile.mkdtemp()
    try:
        slides = None
        if slide_file is not None:
            slides = read_slides(save_temp_upload(slide_file, tmp_dir), slide_file.filename)
        if media_file is None:
            return await contest_scorer.score_materials(questions, slides=slides)
        media_path = save_temp_upload(media_file, tmp_dir)
        return await contest_scorer.score_audio(questions, media_path, media_file.filename, slides=slides)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def single_file(form, field: str, *, too_many: str, not_a_file: str) -> UploadFile | None:
    values = form.getlist(field)
    if len(values) > 1:
        raise HTTPException(status_code=400, detail=too_many)
    if not values:
        return None
    if not isinstance(values[0], UploadFile):
        raise HTTPException(status_code=400, detail=not_a_file)
    return values[0]


def read_slides(path: str, filename: str) -> SlideExtractionResult:
    try:
        return slide_extractor.extract_slides(path, filename)
    except HTTPException:
        raise
    # pdfplumber / python-pptx raise assorted errors on corrupt or mislabeled
    # files; report those as a user-fixable 400 instead of a 500.
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="スライド資料を読み込めませんでした。ファイルが壊れていないか、PDFまたはPPTXとして保存されているか確認してください。",
        ) from e
