import pytest
from fastapi import HTTPException

from app.services import question_set_storage
from tests.test_contest_scorer import QUESTION_SET


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(question_set_storage, "DATA_DIR", str(tmp_path / "question_sets"))


def test_save_then_load_returns_the_same_content():
    saved = question_set_storage.save("学生ビジコン用", QUESTION_SET)

    loaded = question_set_storage.load(saved.id)

    assert loaded.id == saved.id
    assert loaded.name == "学生ビジコン用"
    assert loaded.question_set == QUESTION_SET
    assert loaded.saved_at == saved.saved_at


def test_list_returns_newest_first_with_summary_fields():
    first = question_set_storage.save("1つ目", QUESTION_SET)
    second = question_set_storage.save("2つ目", QUESTION_SET)

    summaries = question_set_storage.list_all()

    assert [s.id for s in summaries] == [second.id, first.id]
    assert summaries[0].name == "2つ目"
    assert summaries[0].contest_name == QUESTION_SET.rubric.contest_name
    assert summaries[0].criteria_count == len(QUESTION_SET.rubric.criteria)


def test_list_is_empty_when_nothing_saved():
    assert question_set_storage.list_all() == []


def test_loading_unknown_id_is_a_clear_404():
    with pytest.raises(HTTPException) as excinfo:
        question_set_storage.load("00000000-0000-0000-0000-000000000000")

    assert excinfo.value.status_code == 404


@pytest.mark.parametrize("bad_id", ["../../etc/passwd", "/etc/passwd", "..\\..\\backend\\.env", "not-a-uuid", ""])
def test_path_traversal_ids_are_rejected_as_not_found(bad_id):
    with pytest.raises(HTTPException) as excinfo:
        question_set_storage.load(bad_id)

    assert excinfo.value.status_code == 404


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected(name):
    with pytest.raises(HTTPException) as excinfo:
        question_set_storage.save(name, QUESTION_SET)

    assert excinfo.value.status_code == 400
