"""tasks.json と「人間だけが書き換えてよいファイル」のルール違反を検出する。

使い方:  python evals/check_tasks.py
基準（人間が承認した状態）は git タグ `harness-baseline`。
人間がルールやタスクを変えたときは、コミット後に `git tag -f harness-baseline` で基準を更新する。
標準ライブラリだけで動く。エラーが1件でもあれば終了コード1。
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = "harness-baseline"
STATUSES = {"todo", "in_progress", "review", "done", "blocked"}
REQUIRED = {"id": str, "task": str, "status": str, "passes": bool, "evidence": list, "dependencies": list}
PROTECTED_FIELDS = ("task", "dependencies", "acceptance", "owner")
HUMAN_ONLY_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "docs/mission.md",
    "docs/requirements.md",
    "docs/voice.md",
    "docs/safety.md",
    "docs/roles.md",
    "evals/acceptance.md",
    "evals/check_tasks.py",
]


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def check_structure(tasks: list, errors: list[str]) -> None:
    ids = [t.get("id") for t in tasks]
    if len(ids) != len(set(ids)):
        errors.append("タスクIDが重複しています。")
    for t in tasks:
        tid = t.get("id", "?")
        for field, typ in REQUIRED.items():
            if not isinstance(t.get(field), typ):
                errors.append(f"{tid}: 項目 '{field}' が無いか、型が違います。")
        if t.get("status") not in STATUSES:
            errors.append(f"{tid}: status '{t.get('status')}' は使えません（{sorted(STATUSES)}）。")
        for dep in t.get("dependencies", []):
            if dep not in ids:
                errors.append(f"{tid}: 依存先 {dep} が存在しません。")
        if t.get("passes") and t.get("status") != "done":
            errors.append(f"{tid}: passes が true なのに status が done ではありません。")
        if t.get("status") == "done" and not t.get("passes"):
            errors.append(f"{tid}: status が done なのに passes が false です（評価役の合格が必要）。")
        if t.get("passes") and not t.get("evidence"):
            errors.append(f"{tid}: 証拠（evidence）が空のまま合格になっています。")
        for ev in t.get("evidence", []):
            if isinstance(ev, str) and ev.startswith("evals/evidence/") and not (ROOT / ev).exists():
                errors.append(f"{tid}: 証拠ファイル {ev} が存在しません。")
        if t.get("passes") and t.get("owner") != "human":
            review = ROOT / "evals" / "evidence" / tid / "review.md"
            if not review.exists():
                errors.append(f"{tid}: 評価役の検品記録 {review.relative_to(ROOT).as_posix()} がありません。")
        dep_status = {d.get("id"): d.get("status") for d in tasks}
        if t.get("status") in {"in_progress", "review", "done"}:
            unfinished = [d for d in t.get("dependencies", []) if dep_status.get(d) != "done"]
            if unfinished:
                errors.append(f"{tid}: 依存タスク {unfinished} が終わっていないのに着手されています。")


def check_against_baseline(tasks: list, errors: list[str], warnings: list[str]) -> None:
    if git("rev-parse", "--verify", "--quiet", BASELINE).returncode != 0:
        warnings.append(f"基準タグ '{BASELINE}' が無いため、改ざんチェックを省略しました（T00 で人間が作成）。")
        return

    shown = git("show", f"{BASELINE}:tasks.json")
    if shown.returncode != 0:
        warnings.append("基準タグに tasks.json が無いため、タスクの改ざんチェックを省略しました。")
    else:
        base = {t["id"]: t for t in json.loads(shown.stdout)["tasks"]}
        current = {t.get("id"): t for t in tasks}
        for tid, bt in base.items():
            if tid not in current:
                errors.append(f"{tid}: タスクが削除されています（削除は禁止）。")
                continue
            for field in PROTECTED_FIELDS:
                if bt.get(field) != current[tid].get(field):
                    errors.append(f"{tid}: '{field}' が書き換えられています（人間のみ変更可）。")
        for tid in current.keys() - base.keys():
            warnings.append(f"{tid}: 基準に無い新しいタスクです。人間が追加したなら基準タグを更新してください。")

    for path in HUMAN_ONLY_FILES:
        if git("cat-file", "-e", f"{BASELINE}:{path}").returncode != 0:
            continue
        if git("diff", "--quiet", BASELINE, "--", path).returncode != 0:
            errors.append(f"{path}: 人間専用のファイルが基準から変更されています。")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        data = json.loads((ROOT / "tasks.json").read_text(encoding="utf-8"))
        tasks = data["tasks"]
    except (OSError, ValueError, KeyError) as e:
        print(f"ERROR: tasks.json を読めません: {e}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    check_structure(tasks, errors)
    check_against_baseline(tasks, errors, warnings)

    for w in warnings:
        print(f"WARN : {w}")
    for e in errors:
        print(f"ERROR: {e}")
    done = sum(1 for t in tasks if t.get("status") == "done")
    print(f"結果: エラー {len(errors)} 件 / 警告 {len(warnings)} 件 / 完了 {done}/{len(tasks)} タスク")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
