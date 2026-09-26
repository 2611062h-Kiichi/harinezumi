# T14 評価役レビュー（採用された提案 P4・P5 の反映）

- 対象コミット: `f761baa4fe754ec2edb3902ce218c277b4ab8dbc`（`Apply adopted proposals P4 and P5 (T14)`）
- 評価役: 新しいサブエージェント（docs/roles.md 3章に従う）
- 評価日: 2026-09-27

## 変更差分の確認

`git show f761baa --stat` の結果:
```
 backend/app/services/contest_scorer.py   |  19 +++-
 backend/app/services/question_builder.py |   7 +-
 backend/tests/test_contest_scorer.py     |  11 +++
 backend/tests/test_question_builder.py   |  46 ++++++++-
 evals/evidence/T14/check_tasks.log       |   2 +
 evals/evidence/T14/pytest.log            | 157 +++++++++++++++++++++++++++++++
 evals/evidence/T14/secret-scan.log       |   2 +
 progress.md                              |  22 ++++-
 tasks.json                               |  12 ++-
 9 files changed, 267 insertions(+), 11 deletions(-)
```
`test_question_set_storage.py` / `question_set_storage.py` はこの一覧に **含まれていない**（後述のP6・作業ログの記述と整合）。

## 各合格条件の判定

### AC-00a（既存のテストがすべて通る） ○
自分で再実行（すべて `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v` またはその `-q` 版）。

1回目:
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
============================= 145 passed in 3.66s =============================
```
2回目・3回目（同コマンド）:
```
============================= 145 passed in 3.91s =============================
============================= 145 passed in 3.93s =============================
```
さらに全体を8回連続実行（`-q`）:
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q   （8回連続）
1回目: 145 passed in 3.72s
2回目: 145 passed in 3.80s
3回目: 145 passed in 3.74s
4回目: 145 passed in 3.83s
5回目: 145 passed in 3.60s
6回目: 145 passed in 3.87s
7回目: FAILED tests/test_question_set_storage.py::test_list_returns_newest_first_with_summary_fields
       (1 failed, 144 passed in 4.27s)
8回目: 145 passed in 3.73s
```
証拠 `evals/evidence/T14/pytest.log`（145 passed）と一致。

**T14 の本来のテストが不安定でないことの確認**（`test_question_builder.py` / `test_contest_scorer.py` のみ、5回連続実行）:
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q tests/test_question_builder.py tests/test_contest_scorer.py  （5回連続）
33 passed in 1.71s
33 passed in 1.58s
33 passed in 1.55s
33 passed in 1.57s
33 passed in 1.57s
```
5回とも全件成功。今回のタスクの変更に起因する不安定さは無い。

**progress.md 記載の mtime フレークの切り分け**:
- `git show f761baa --stat` に `question_set_storage.py` / `test_question_set_storage.py` が含まれないこと → 確認済み（上記）。今回の diff はこのファイルに一切触れていない。
- 該当テストだけを単体で20回連続実行:
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q tests/test_question_set_storage.py::test_list_returns_newest_first_with_summary_fields  （20回連続）
```
  → 20回とも `1 passed`（単体では衝突が起きないため）。
- コードを読んで原因を特定: `backend/app/services/question_set_storage.py` の `list_all()` は `sorted(..., key=os.path.getmtime, reverse=True)` でファイルの更新時刻順に並べている。2件を短時間に連続保存すると、Windows のファイルシステムの mtime 分解能により同一時刻になり得るため、稀に順序が入れ替わる。上記の全体8回連続実行でも実際に7回目で1回だけ再現し、それ以外は成功しており、「稀に起きる」という progress.md の記述と一致する。
- 結論: このフレークは **今回の T14 の変更（question_builder.py / contest_scorer.py）とは無関係** の、既存コード（question_set_storage.py）由来の低頻度な問題であり、progress.md にも提案 P6 として正しく記録されている。T14 の本来のテスト（test_question_builder.py, test_contest_scorer.py）自体は上記の通り安定して全件成功しており、重大な問題として扱う必要はない。
- 判定: AC-00a は ○（今回の変更範囲のテストは常に全件成功。既知の無関係な低頻度フレークは原因を特定・追跡済みで、今回の合否判断に影響しない）。

### AC-00c（秘密情報が含まれていない） ○
`docs/safety.md` 3章のコマンドで確認:
```
$ git show f761baa | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
386:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
```
唯一のヒットは `evals/evidence/T14/secret-scan.log` に記録された「実行したコマンド行」自体であり、実際の秘密情報ではない。`backend/.env` は今回読んでいない・変更もされていない（diffに含まれない）。`evals/evidence/T14/secret-scan.log` の内容も同じコマンド・「一致なし」で一致。

### AC-00d（check_tasks エラー0件） ○
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 12/15 タスク
```
証拠 `evals/evidence/T14/check_tasks.log` と一致。

### AC-06（観点→Question生成、抜け・余分でエラーになる） ○
- コードを確認: `backend/app/services/question_builder.py` の `generate_questions` は `QuestionSet.model_validate` の `ValidationError` を捕まえ、`detail=f"...もう一度お試しください。（{to_japanese(e)}）"` で502を返す。`to_japanese` は `backend/app/utils/validation_messages.py`（contest router と共通で既に使われているもの）。
- 既存の抜け・余分・重複・段階数違反のテスト（`test_missing_question_is_rejected` / `test_extra_question_is_rejected` / `test_duplicate_question_is_rejected` / `test_wrong_level_count_is_rejected`）が期待する文言（`Questionが無い観点: market` 等）は、いずれも `app/models/contest.py` の `model_validator` が `raise ValueError("...")` で直接投げている日本語文そのもの。Pydantic は `value_error` 種別のエラーで `ctx["error"]`（例外オブジェクト、str化すると元のメッセージと同一）を保持するため、`to_japanese` の `_problem()` は `kind == "value_error"` で `ctx.get("error", msg)` を返し、旧 `_format_validation_error`（`msg` から "Value error, " を除去するだけ）と **同じ文字列** になる。実際に上記4テストは全て成功している（AC-00a の実行結果に含まれる）ので、文言が変わっていないことを実行結果でも確認済み。
- P4(b) の新規テスト `test_blank_level_in_generated_question_gets_japanese_error` は、`levels` の要素が空白のみ（`"  "`）のときに Pydantic 標準の `string_too_short`（`RequiredText` の `min_length=1`）が発生するケース。`to_japanese._location` のロジックをコードで追跡: `loc=('questions', 0, 'levels', 4)` → `NUMBERED_LISTS` の番号付けにより `"Question1の段階5"` になり、`_problem` は `min_length==1` のとき `"入力してください"` を返す。結果 `"Question1の段階5: 入力してください"` となり、テストの `assert "入力してください" in detail` / `assert "段階5" in detail` / `assert "String" not in detail`（旧実装なら英語の `"String should have at least 1 character"` が漏れていたはず）と整合することをコードレベルで確認した。テスト自体も実行で成功。
- P4(c)（`test_wrong_level_count_is_rejected` の入力を `LEVELS[:1] * count` から `[f"段階{i}の説明文" for i in range(count)]` に変更）も反映されており、同じ文の繰り返しという不自然な入力を避けた、より現実的なテストになっている。

### AC-07（Jev採点、配点換算がサーバー計算） ○
- `to_points` / `round_half_up`（`backend/app/services/contest_scorer.py`）は今回の diff で **変更されていない**（`git show f761baa` で該当関数に差分なし）。AC-07 の例（score 3.0, 5段階, 配点20 → 15.0）を確認するテスト `test_converts_jev_score_to_contest_points` は今回も変わらず成功している。
- P4(a) のコード対応確認（P4 は AC-06 だけでなく `_call_claude` の例外系全般の話だが、対応するテストが `test_question_builder.py` にあるため念のためここでも記載）: `backend/app/services/review_generator.py` の `_call_claude`（127〜167行目）を読み、
  - `except anthropic.APIConnectionError as e:` → `HTTPException(502, detail="Anthropic APIへの接続に失敗しました。ネットワークを確認してください。")`
  - `except Exception as e:` → `HTTPException(502, detail=failure_detail)`（`question_builder.generate_questions` は `failure_detail=FAILURE_DETAIL` を渡している）
  の2節が実装されていることを確認した。新規テスト `test_claude_connection_error_becomes_502`（`anthropic.APIConnectionError` を送出 → `"接続に失敗"` を含む502）と `test_claude_unexpected_exception_becomes_502_with_failure_detail`（`RuntimeError` を送出 → `question_builder.FAILURE_DETAIL` と一致する502）は、この2つの except 節に **正確に1対1で対応** している。
  - 補足: テストの `httpx2.Request(...)` / `httpx2.Headers()` は誤記ではなく、この環境の `anthropic==1.8.0`（`backend/.venv`）が内部で `httpx2`（インストール済みパッケージ、`anthropic/_exceptions.py` の `APIConnectionError.__init__` が `request: httpx2.Request` を要求）を使っているため、テストの型は実装と一致している。`grep -n "class APIConnectionError" -A5 backend/.venv/Lib/site-packages/anthropic/_exceptions.py` で確認。
- P5 の境界値確認（リポジトリ外のスクラッチファイルで実施。実 API は呼んでいない。確認用ファイルはリポジトリに残していない）:
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python <スクラッチ内の一時スクリプト（score_transcript を fake Jev で呼び出すだけ）>
JEV_SCORE_DRIFT_TOLERANCE = 0.001
within tolerance (+0.0005): score=4.0005 -> OK, jev_score=4.0, points=20.0
outside tolerance (+0.002): score=4.002 -> HTTPException 502: Jevから観点「課題の明確さ」の異常な採点結果が返ってきました。もう一度お試しください。
within tolerance (-0.0005): score=-0.0005 -> OK, jev_score=0.0, points=0.0
outside tolerance (-0.002): score=-0.002 -> HTTPException 502: Jevから観点「課題の明確さ」の異常な採点結果が返ってきました。もう一度お試しください。
exact boundary (+0.001): score=4.001 -> OK, jev_score=4.0, points=20.0
just past boundary (+0.0010001): score=4.0010001 -> HTTPException 502: Jevから観点「課題の明確さ」の異常な採点結果が返ってきました。もう一度お試しください。
```
  許容誤差 `0.001` のすぐ内側（`+0.0005`, `-0.0005`, ちょうど`0.001`）は成功して従来通りクランプ、すぐ外側（`+0.002`, `-0.002`, `0.0010001`）は502になることを実測で確認した。境界の判定式 `answer.score < -TOL or answer.score > top_level + TOL` は「以上／以下」ではなく厳密な不等号なので、ちょうど許容誤差ぴったり（0.001）は許容範囲内（成功）になる実装であり、実測結果と一致している。スクラッチファイルはセッションのスクラッチディレクトリに作成し、リポジトリには追加・コミットしていない。
- テスト `test_significantly_out_of_range_jev_score_is_rejected`（5.0, -1.0, 4.5, -0.5 → 502）、`test_slightly_out_of_range_jev_scores_are_clamped`（既存、4.0000001 / -0.0000001 → クランプして成功）はいずれも実行で成功を確認済み。

## 総合判定

| AC | 判定 |
|---|---|
| AC-00a | ○ |
| AC-00c | ○ |
| AC-00d | ○ |
| AC-06 | ○ |
| AC-07 | ○ |

全て ○ のため **合格**。`tasks.json` の T14 を `"status": "done"`, `"passes": true` に変更した。

## 合否に影響しない指摘

- `progress.md` の作業ログにある「P6」（`question_set_storage.list_all()` が `os.path.getmtime` に頼っているため稀に順序が入れ替わる）は、今回の再実行でも1/8回の頻度で実際に再現した。今回の判定には影響しないが、対応済みの提案（未採用・記録のみ）として残っているので、いずれ着手するタスクとして拾うとよい（`saved_at` で比較するようにすれば解消する、との記載どおり）。
- それ以外、コード・テスト・証拠・progress.md の記述に矛盾は見つからなかった。

## `python evals/check_tasks.py` の実行結果

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 12/15 タスク
```
