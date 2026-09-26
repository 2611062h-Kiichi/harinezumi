"""Turns Pydantic validation errors into short Japanese messages for the UI.

Each message says where the problem is ("観点2の配点") and what to fix.
Our own model validators already raise Japanese text, which is kept as-is.
"""

from pydantic import ValidationError

FIELD_NAMES = {
    "rubric": "採点観点",
    "contest_name": "コンテスト名",
    "criteria": "観点",
    "id": "ID",
    "name": "名前",
    "description": "説明",
    "max_points": "配点",
    "questions": "Question",
    "criterion_id": "観点ID",
    "instructions": "質問文",
    "levels": "段階",
}

# Lists whose items are numbered for the user (1-based).
NUMBERED_LISTS = {"criteria": "観点", "questions": "Question", "levels": "段階"}


def _location(loc: tuple) -> str:
    parts: list[str] = []
    for i, key in enumerate(loc):
        if isinstance(key, int):
            parent = loc[i - 1] if i > 0 else None
            label = NUMBERED_LISTS.get(parent)
            if label and parts and parts[-1] == FIELD_NAMES.get(parent):
                parts[-1] = f"{label}{key + 1}"
            else:
                parts.append(f"{key + 1}番目")
        elif key in FIELD_NAMES:
            parts.append(FIELD_NAMES[key])
    return "の".join(parts)


def _problem(error: dict) -> str:
    kind = error["type"]
    ctx = error.get("ctx", {})
    if kind == "value_error":
        return str(ctx.get("error", error["msg"]))
    if kind == "missing":
        return "入力してください"
    if kind == "string_too_short":
        return "入力してください" if ctx.get("min_length") == 1 else f"{ctx.get('min_length')}文字以上にしてください"
    if kind == "string_too_long":
        return f"{ctx.get('max_length')}文字以内にしてください"
    if kind == "string_pattern_mismatch":
        return "半角英数字・_・- の40文字以内にしてください"
    if kind == "greater_than_equal":
        return f"{ctx.get('ge')}以上にしてください"
    if kind == "less_than_equal":
        return f"{ctx.get('le')}以下にしてください"
    if kind in ("int_type", "int_parsing", "int_from_float"):
        return "整数で入力してください"
    if kind == "too_short":
        return f"{ctx.get('min_length')}個以上にしてください"
    if kind == "too_long":
        return f"{ctx.get('max_length')}個以内にしてください"
    if kind in ("string_type", "list_type", "model_type", "dict_type", "model_attributes_type"):
        return "入力の形が正しくありません"
    if kind == "json_invalid":
        return "JSONとして読み取れません"
    return "入力が正しくありません"


def to_japanese(error: ValidationError) -> str:
    messages = []
    for e in error.errors():
        where = _location(tuple(e["loc"]))
        problem = _problem(e)
        messages.append(f"{where}: {problem}" if where else problem)
    return " / ".join(dict.fromkeys(messages))  # drop exact duplicates, keep order
