# T03 評価役レビュー

- 対象: T03「観点・Jev用Question・採点結果の型を backend(Pydantic) と frontend(TypeScript) に定義し、入力チェックのテストを書く」
- 変更コミット: 4239f4f（`git show 4239f4f --stat`: contest.py / test_contest_models.py / contest.ts / 証拠4件 / progress.md / tasks.json の9ファイル）
- 評価日: 2026-09-26
- 手順: `docs/roles.md` 3章どおり（acceptance.md → tasks.json → evals/evidence/T03 → そのタスクの変更）

## 判定: 合格（全条件 ○）

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a テストが全部通る | ○ | 再実行で 52 passed（失敗0）。`pytest.log` も 52 passed、テスト名・並びも一致 |
| AC-00b フロントエンドがビルドできる | ○ | 再実行で `tsc -b && vite build` 成功。`build.log` も成功。`contest.ts` が tsc の対象に入っていることは `build.log` 末尾のファイル一覧で確認 |
| AC-00c 秘密情報なし | ○ | `secret-scan.log` は safety.md 3章のコマンド（`git diff --cached`）で「一致なし」。コミット済みのため、評価役はコミット全体 `git show 4239f4f` に同じパターンをかけ、一致は secret-scan.log 内の検索コマンド自身の1行だけ |
| AC-00d check_tasks エラー0件 | ○ | `check_tasks.log` はエラー0件。評価後の再実行結果は末尾に記載 |
| AC-05 型があり、おかしな入力をはじく | ○ | 下記 |

## AC-05 の詳細

型: `backend/app/models/contest.py`（ContestCriterion / ContestRubric / JevScoreQuestion / QuestionSet / ContestCriterionResult / ContestScoreResult）、`frontend/src/types/contest.ts`（同名の interface と定数）。
テスト: `backend/tests/test_contest_models.py`（29件）。

| ケース | テスト | 本当にそのケースで失敗しているか（評価役がリポジトリ外のスクリプトで型を直接試した結果） |
|---|---|---|
| 配点0 | `test_points_out_of_range_are_rejected[0]`（ほか -5, 101） | エラーは `max_points` の `greater_than_equal` だけ。他の理由ではない。20.5 も `int_from_float` で拒否 |
| 名前が空 | `test_empty_name_is_rejected[""]`, `["   "]` | エラーは `name` の `string_too_short` だけ（空白だけの名前も前後空白の除去後に拒否） |
| 観点16個 | `test_sixteen_criteria_are_rejected` | エラーは `criteria` の `too_long`（15個まで）だけ。ID は c0〜c15 で重複なし。15個は通る（`test_fifteen_criteria_is_the_upper_limit`） |
| 段階が5個でない | `test_level_count_other_than_five_is_rejected[0/1/4/6]` | 0/1/4/6 個いずれも自作の検査「段階の数が N個です。段階はちょうど5個に…」だけで拒否。0個もこの理由で失敗している（テストは0個のときだけ文言を確認していないが、実際の理由は正しい）。補助関数は `levels is None` 判定なので空リストが既定値にすり替わらない |
| ID重複 | `test_duplicate_criterion_ids_are_rejected` | 「観点のIDが重複しています: problem」で拒否。テストも「重複」を確認 |

追加で確認したこと:
- 要件との一致: FR-1（観点1〜15個・名前必須・説明任意で既定値""・配点1〜100の整数）、FR-2（1観点1Question を QuestionSet で保証・`criterion_id` を持つ・5段階・低い順をコメントで明記）、FR-7（`LOW_CONFIDENCE_THRESHOLD = 0.5`）と食い違いなし
- backend と frontend の型: 6つの型すべてで項目名と順番が一致（model_fields と interface を機械的に比較）。定数 5 / 15 / 0.5 も一致。`generated_at` は Python の datetime → JSON では ISO 文字列なので TS の `string` と合う
- 既存コード: コミットで変わったのは新規の contest.py / contest.ts / テスト / 証拠 / progress.md / tasks.json だけ。`backend/app` の他ファイル、`frontend` の他ファイルは変更なし
- 評価後の `git status --short`: tasks.json と本ファイル以外の変更なし（`npm run build` 後も package-lock.json は変化なし）

## 合否に影響しない指摘（今後のタスクで考慮）
1. AC-05 のテストの多くは `ValidationError` が出ることだけを確認し、どの項目で失敗したか（`loc`）までは見ていない。今は正しい理由で失敗しているが、将来ほかの制約を足したときに別の理由で通ってしまう余地がある。段階0個のケースも文言確認を省いている
2. `max_points` は Pydantic の標準（lax）モードのため、`"20"`（文字列）・`20.0`・`True` も受け付ける。API で JSON を受ける T06 以降で問題になるなら strict にするか検討
3. `ContestCriterionResult.low_confidence` は自由な bool で、`confidence < 0.5` と一致するかは型で確かめていない（T05 の換算処理でサーバーが計算する前提なら問題なし）
4. requirements.md FR-2 では段階の説明を Jev の用語で `criteria` と呼んでいるが、型では `levels`。Jev に渡すとき（T05）に名前の変換が必要
5. `ContestCriterionResult.name` / `ContestScoreResult.contest_name` は空文字を許す（結果側なので実害は小さい）

## 評価役が再実行したコマンドと結果

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
============================= 52 passed in 3.73s ==============================
```

```
$ cd frontend && npm run build
> harinezumi-frontend@0.0.1 build
> tsc -b && vite build
✓ 40 modules transformed.
✓ built in 532ms
```

```
$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
(一致なし、終了コード1)
$ git show 4239f4f | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
436:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（secret-scan.log に書かれた検索コマンド自身の1行のみ。秘密情報ではない）
```

```
$ PYTHONIOENCODING=utf-8 backend/.venv/Scripts/python <スクラッチ>/check_t03.py   # リポジトリ外に置いた確認用スクリプト
max_points=0 : [('max_points', 'greater_than_equal', ...)]
name='' : [('name', 'string_too_short', ...)]
name='   ': [('name', 'string_too_short', ...)]
16 criteria: [('criteria', 'too_long', 'List should have at most 15 items after validation, not 16')]
levels=0: [('', 'value_error', 'Value error, 観点 p の段階の数が0個です。段階はちょうど5個にしてください。')]
levels=1/4/6: 同じ理由（段階の数がN個です）
dup ids: [('', 'value_error', 'Value error, 観点のIDが重複しています: problem')]
ContestCriterion / ContestRubric / JevScoreQuestion / QuestionSet / ContestCriterionResult / ContestScoreResult: MATCH（backend と TS の項目名一致）
```

```
$ python evals/check_tasks.py
（下の「check_tasks の出力」を参照）
```

## check_tasks の出力（評価後、tasks.json を更新してから実行）

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 4/13 タスク
```
