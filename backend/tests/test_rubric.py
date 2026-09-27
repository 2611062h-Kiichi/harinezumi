import pytest

from app.rubric import (
    DEFAULT_MODE,
    RUBRIC_MODES,
    SCALE_MAX,
    SCALE_MIN,
    compute_overall_score,
    get_rubric_criteria,
    get_rubric_label,
)


@pytest.mark.parametrize("mode", list(RUBRIC_MODES))
def test_overall_score_is_100_when_every_criterion_is_max(mode):
    criteria = get_rubric_criteria(mode)
    assert compute_overall_score([SCALE_MAX] * len(criteria)) == 100


@pytest.mark.parametrize("mode", list(RUBRIC_MODES))
def test_overall_score_is_20_when_every_criterion_is_min(mode):
    criteria = get_rubric_criteria(mode)
    assert compute_overall_score([SCALE_MIN] * len(criteria)) == 20


def test_overall_score_accepts_fractional_jev_scores():
    criteria = get_rubric_criteria(DEFAULT_MODE)
    # 3.5 / 5 on every criterion -> 70
    assert compute_overall_score([3.5] * len(criteria)) == 70


@pytest.mark.parametrize("mode", list(RUBRIC_MODES))
def test_every_criterion_has_unique_id_and_five_levels(mode):
    criteria = get_rubric_criteria(mode)
    ids = [c["id"] for c in criteria]
    assert len(ids) == len(set(ids))
    for c in criteria:
        assert c["name"]
        assert len(c["levels"]) == SCALE_MAX - SCALE_MIN + 1


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        get_rubric_criteria("no-such-mode")
    with pytest.raises(ValueError):
        get_rubric_label("no-such-mode")


def test_overall_score_scales_to_any_number_of_criteria():
    # Custom rubrics (event-designed or user-named) can have 3-10 criteria.
    assert compute_overall_score([SCALE_MAX] * 3) == 100
    assert compute_overall_score([SCALE_MIN] * 10) == 20
