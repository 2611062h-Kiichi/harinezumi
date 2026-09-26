"""Saves, lists and loads named Question sets for reuse (FR-8).

One JSON file per saved set, named by a server-generated id (never the
user-supplied name), mirroring app/services/history.py.
"""

import os
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.models.contest import QuestionSet, SavedQuestionSet, SavedQuestionSetSummary

# backend/app/services/question_set_storage.py -> backend/data/question_sets
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data", "question_sets")

# ids are our own uuid4()s; reject anything else before it ever touches a path
# (e.g. "../../.env" or an absolute path) instead of relying on isfile() alone.
_ID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


_last_saved_at: datetime | None = None


def _next_saved_at() -> datetime:
    """Current time, but always strictly after the previous save in this process.

    The clock can return the same value for back-to-back calls (notably on
    Windows), and list_all() orders by saved_at, so ties would make the order
    of two quick saves arbitrary.
    """
    global _last_saved_at
    now = datetime.now(timezone.utc)
    if _last_saved_at is not None and now <= _last_saved_at:
        now = _last_saved_at + timedelta(microseconds=1)
    _last_saved_at = now
    return now


def save(name: str, question_set: QuestionSet) -> SavedQuestionSet:
    if not name.strip():
        raise HTTPException(status_code=400, detail="保存する名前を入力してください。")

    saved = SavedQuestionSet(
        id=str(uuid.uuid4()),
        name=name,
        question_set=question_set,
        saved_at=_next_saved_at(),
    )
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{saved.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(saved.model_dump_json(indent=2))
    return saved


def list_all() -> list[SavedQuestionSetSummary]:
    if not os.path.isdir(DATA_DIR):
        return []
    saved_sets = []
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
            saved_sets.append(SavedQuestionSet.model_validate_json(f.read()))
    # Order by the saved_at stored in the file, not the file's mtime: mtime
    # resolution can tie for quick successive saves and changes if the file
    # is copied or synced (e.g. OneDrive).
    saved_sets.sort(key=lambda s: s.saved_at, reverse=True)

    summaries = []
    for saved in saved_sets:
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
