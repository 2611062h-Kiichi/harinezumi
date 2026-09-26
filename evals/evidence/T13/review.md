# T13 評価役レビュー（採用された提案 P2(a)・P3 の反映）

対象コミット: `e19c040dd3e3afb7c182b46c387d0d6931ce7247`
参照: `progress.md` の「作業計画」T13、「作業ログ」2026-09-27 T13、`tasks.json` の T13、`evals/acceptance.md`

## 結論

**合格（すべて○）**

## 条件ごとの判定

### AC-00a（既存のテストがすべて通る）: ○
- 証拠: `evals/evidence/T13/pytest.log`（`138 passed`）
- 再実行コマンドと結果（自分の環境で再実行）:
  ```
  $ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
  ...
  ============================= 138 passed in 3.86s ==============================
  ```
  証拠ログの `138 passed`（既存132＋新規6）と一致。失敗0件。

### AC-00c（秘密情報が含まれていない）: ○
- 証拠: `evals/evidence/T13/secret-scan.log`（一致なし）
- 再実行コマンドと結果（docs/safety.md 3章のコマンドを、コミット e19c040 の差分に対して実行）:
  ```
  $ git show e19c040 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
  418:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
  ```
  ヒットしたのは `evals/evidence/T13/secret-scan.log` 自体に書かれた「実行したコマンド文字列」（その文字列中に `api_key=...` というパターン文字列が含まれるため、grep パターン自身に一致しただけ）であり、実際の秘密情報ではない。差分中に実キー・パスワードは無い。`backend/.env` は読んでいない。

### AC-00d（tasks.json のルール違反がない）: ○
- 証拠: `evals/evidence/T13/check_tasks.log`（エラー0件 / 警告0件 / 完了11/15）
- 再実行コマンドと結果:
  ```
  $ python evals/check_tasks.py
  結果: エラー 0 件 / 警告 0 件 / 完了 11/15 タスク
  ```
  証拠ログと一致。

### AC-03（pytest で自動テストが動き、既存機能のテストが5件以上ある）: ○
- 上記 AC-00a の再実行で138件のテストが実際に動作していることを確認。既存機能（`test_rubric.py`、`test_question_set_storage.py`、`test_transcription.py` など）に対応するテストが多数含まれる。新規は `test_slide_extractor.py` に2件、`test_contest_models.py` に既存強化＋新規4件（空白name/contest_nameのパラメトライズ2件ずつ）。

### AC-05（型があり、おかしな入力をはじく。テストが「どの項目のエラーか」まで確認する）: ○
- `git show e19c040 -- backend/tests/test_contest_models.py` を確認。すべての AC-05 系テストが `excinfo.value.errors()` の `loc`（`error_locations` ヘルパー）や `type`、具体的な日本語メッセージまで assert するように強化されている。
- **PDF抽出テストの実質性**: `test_slide_extractor.py` の `make_pdf()` が reportlab で実際にPDFバイト列を生成していること、`extract_slides()` が本番依存の `pdfplumber` で実際にそのファイルを解析していることを、スクラッチ環境（リポジトリ外の一時フォルダ、レビュー後に削除済み）で該当関数を直接呼び出して確認した。
  - 2ページPDF（本文あり）→ `slides[0].text` に "Problem"、`slides[1].text` に "Solution" が実際に入る（ページごとの本文がそのまま反映）。生成されたPDFファイルは1845バイトの実ファイル。
  - 本文なしページ（`c.showPage()` のみ）→ `slides[0].text == ""`。空文字テストは意味のある検証（実際に「本文なしのページを解析したら空文字になる」ことを確かめている）と判断。
- **reportlab の依存先**: `backend/requirements-dev.txt` にのみ追記されており、`backend/requirements.txt`（本番依存）には入っていないことをファイル確認済み。コメントも「test-only」と明記。
- **`loc`/文言チェックの実効性の検証（意図的に緩めたケースで本当に失敗するか、リポジトリ外のスクラッチで3ケース実施。確認後は削除済み）**:
  1. `max_points` の下限/上限チェックを（本来の `Field(ge=1, le=100)` ではなく）`id` フィールドの `field_validator` に付け替えて `loc=("id",)` を返すよう改変 → 強化後のテスト `test_points_out_of_range_are_rejected` は3ケースとも `AssertionError: assert ('max_points',) in [('id',)]` で確実に失敗することを確認。旧テスト（`pytest.raises(ValidationError)` のみ）なら見逃していたはずのバグを検出できる。
  2. `ContestCriterionResult.name` / `ContestScoreResult.contest_name` を `RequiredText` から元の `str` に戻す（P3(b)の巻き戻し）→ 新規テスト `test_result_with_blank_criterion_name_is_rejected` / `test_score_result_with_blank_contest_name_is_rejected` の4ケースすべてが `Failed: DID NOT RAISE ValidationError` で確実に失敗することを確認。
  3. `JevScoreQuestion._level_count` で段階数0個のときだけ「ちょうど5個」を含まない別メッセージ（`観点 problem の段階がありません。`）を返すよう改変 → 強化後のテスト（0個のケースも含め全ケースで `"ちょうど5個" in error_text` を確認する版）は `count=0` のケースで確実に失敗することを確認。旧テスト（0個のときは文言確認を飛ばす版）なら見逃していたはずのバグを検出できる。
  - 以上3ケースとも、「テストの検査が正しく効いている（緩めると落ちる）」ことを実証した。
- **型変更が既存コードを壊していないかの確認**: `backend/app/services/contest_scorer.py` を目視確認。`ContestCriterionResult(name=criterion.name, ...)` の `criterion.name` は `ContestCriterion.name`（既に `RequiredText` で空文字禁止済み）から来ており、`ContestScoreResult(contest_name=question_set.rubric.contest_name, ...)` の `contest_name` も `ContestRubric.contest_name`（既に `RequiredText`）から来ている。したがって型変更後も実際に渡る値は元から非空文字列であり、動作に影響なし。`grep` で `ContestCriterionResult(` / `ContestScoreResult(` の呼び出し箇所は `contest_scorer.py` の2箇所のみであることも確認済み。既存テスト138件全通過も上記で確認済み。
- **progress.md の記載（段階数0個のときの文言確認を全ケースに広げた）の裏取り**: 実際に `JevScoreQuestion.model_validate({..., "levels": []})` を呼び出し、エラーメッセージが `観点 problem の段階の数が0個です。段階はちょうど5個にしてください。` であり、「ちょうど5個」も `0個です` も含まれることを直接確認した。progress.md の記載は事実と一致する。

## 再実行コマンド一覧（本レビューで実行したもの）
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
$ git show e19c040 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
$ python evals/check_tasks.py
```
（加えて、リポジトリ外のスクラッチフォルダで PDF 抽出関数の直接呼び出しと、3種類の意図的な劣化改変に対するテスト再実行を行った。スクラッチフォルダはレビュー後に削除済み。実 API は呼んでいない。`backend/.env` は読んでいない。）

## 合否に影響しない指摘
- なし。

## 判定
- AC-00a: ○
- AC-00c: ○
- AC-00d: ○
- AC-03: ○
- AC-05: ○

**全て○のため、`status: "done"`, `passes: true` とする。**

---

## `python evals/check_tasks.py` の出力（tasks.json の T13 を status: "done", passes: true に更新した後の最終実行）
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 12/15 タスク
```
