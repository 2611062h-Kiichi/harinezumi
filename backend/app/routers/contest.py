"""API for contest mode: criteria -> Jev questions, and audio + questions -> scores.

Input is validated here (not by FastAPI's automatic body parsing) so that
mistakes come back as 400 with Japanese messages instead of English 422s.
"""

import json
import shutil
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.models.contest import ContestRubric, ContestScoreResult, QuestionSet
from app.routers.review import MEDIA_EXTS
from app.services import contest_scorer, question_builder
from app.utils.file_validation import save_temp_upload, validate_upload
from app.utils.validation_messages import to_japanese

router = APIRouter(prefix="/api/contest")


def parse_json(raw: str | bytes, model: type[BaseModel], what: str):
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
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
async def score_pitch(
    media_file: UploadFile | None = File(None),
    question_set: str | None = Form(None),
):
    if media_file is None:
        raise HTTPException(status_code=400, detail="発表の音声または動画ファイルを指定してください。")
    if not question_set:
        raise HTTPException(status_code=400, detail="採点に使うQuestionを指定してください。")

    questions = parse_json(question_set, QuestionSet, "Question")
    validate_upload(media_file, MEDIA_EXTS, get_settings().max_media_mb)

    tmp_dir = tempfile.mkdtemp()
    try:
        media_path = save_temp_upload(media_file, tmp_dir)
        return await contest_scorer.score_audio(questions, media_path, media_file.filename)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
