"""Saves, lists and loads named Question sets for reuse (FR-8).

One JSON file per saved set, named by a server-generated id (never the
user-supplied name), mirroring app/services/history.py.
"""

import os
import re
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException

from app.models.contest import QuestionSet, SavedQuestionSet, SavedQuestionSetSummary

# backend/app/services/question_set_storage.py -> backend/data/question_sets
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data", "question_sets")

# ids are our own uuid4()s; reject anything else before it ever touches a path
# (e.g. "../../.env" or an absolute path) instead of relying on isfile() alone.
_ID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def save(name: str, question_set: QuestionSet) -> SavedQuestionSet:
    if not name.strip():
        raise HTTPException(status_code=400, detail="保存する名前を入力してください。")

    saved = SavedQuestionSet(
        id=str(uuid.uuid4()),
        name=name,
        question_set=question_set,
        saved_at=datetime.now(timezone.utc),
    )
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{saved.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(saved.model_dump_json(indent=2))
    return saved


def list_all() -> list[SavedQuestionSetSummary]:
    if not os.path.isdir(DATA_DIR):
        return []
    files = sorted(
        (os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".json")),
        key=os.path.getmtime,
        reverse=True,
    )
    summaries = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            saved = SavedQuestionSet.model_validate_json(f.read())
        summaries.append(
            SavedQuestionSetSummary(
                id=saved.id,
                name=saved.name,
                contest_name=saved.question_set.rubric.contest_name,
                criteria_count=len(saved.question_set.rubric.criteria),
                saved_at=saved.saved_at,
            )
        )
    return summaries


def load(saved_id: str) -> SavedQuestionSet:
    if not _ID_PATTERN.match(saved_id):
        raise HTTPException(status_code=404, detail="指定されたQuestionセットが見つかりません。")
    path = os.path.join(DATA_DIR, f"{saved_id}.json")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="指定されたQuestionセットが見つかりません。")
    with open(path, "r", encoding="utf-8") as f:
        return SavedQuestionSet.model_validate_json(f.read())
