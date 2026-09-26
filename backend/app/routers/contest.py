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
from app.models.contest import ContestRubric, ContestScoreResult, QuestionSet
from app.routers.review import MEDIA_EXTS
from app.services import contest_scorer, question_builder
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


@router.post("/questions", response_model=QuestionSet)
async def create_questions(request: Request):
    rubric = parse_json(await request.body(), ContestRubric, "採点観点")
    return await question_builder.generate_questions(rubric)


@router.post("/score", response_model=ContestScoreResult)
async def score_pitch(request: Request):
    try:
        form = await request.form()
    except StarletteHTTPException as e:
        # Starlette answers broken multipart bodies with an English 400.
        raise HTTPException(
            status_code=400, detail="送信データの形が正しくありません。画面からもう一度送信してください。"
        ) from e

    media_files = form.getlist("media_file")
    if len(media_files) > 1:
        raise HTTPException(status_code=400, detail="音声または動画ファイルは1つだけ指定してください。")
    media_file = media_files[0] if media_files else None
    if not isinstance(media_file, UploadFile):
        raise HTTPException(status_code=400, detail="発表の音声または動画ファイルを指定してください。")

    raw_question_set = form.get("question_set")
    if isinstance(raw_question_set, UploadFile):
        # Browsers send a file part when a Blob is appended to FormData.
        raw_question_set = await raw_question_set.read(MAX_QUESTION_SET_BYTES + 1)
        if len(raw_question_set) > MAX_QUESTION_SET_BYTES:
            raise HTTPException(status_code=400, detail="Questionのデータが大きすぎます。")
    if not raw_question_set:
        raise HTTPException(status_code=400, detail="採点に使うQuestionを指定してください。")

    questions = parse_json(raw_question_set, QuestionSet, "Question")
    validate_upload(media_file, MEDIA_EXTS, get_settings().max_media_mb)

    tmp_dir = tempfile.mkdtemp()
    try:
        media_path = save_temp_upload(media_file, tmp_dir)
        return await contest_scorer.score_audio(questions, media_path, media_file.filename)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
