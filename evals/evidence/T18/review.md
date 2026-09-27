# T18 検品記録（評価役）

- 対象: マージコミット `3d0c0b9`（親1 = `8055eea` こちらのブランチ、親2 = `161f8d7` = `origin/feature/business-contest-rubric` の最新）
- 検品日: 2026-09-27
- 判定: **合格（全 AC ○、task 文の要件もすべて満たす）**

## 共通 AC

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存テストがすべて通る | ○ | `pytest.log`（200 passed）。評価役が `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q` を再実行 → **200 passed in 4.56s**（証拠と同じ件数・失敗0） |
| AC-00b フロントがビルドできる | ○ | `build.log`。評価役が `cd frontend && npm run build` を再実行 → `tsc -b && vite build` 成功、出力ファイル名・サイズ（index-BQsVL9te.css 9.08kB / index-vEwb3NHC.js 176.65kB）も証拠と一致 |
| AC-00c 秘密情報が含まれていない | ○ | `secret-scan.log`。評価役が `git diff 8055eea 3d0c0b9 \| grep -nE "sk-\|ts-[A-Za-z0-9]{8,}\|api_key\s*=\s*['\"][^'\"]+"` を実行 → 一致は1行のみで、`secret-scan.log` に書かれた検査コマンドの文字列そのもの（キーではない）。`git diff 161f8d7 3d0c0b9` の一致も、すべてこちらのハーネス資料・証拠に書かれた検査コマンド文字列だけ。`.env` は追跡されていない。`backend/.env` は読んでいない |
| AC-00d tasks.json のルール違反がない | ○ | `check_tasks.log`。評価役の再実行結果は末尾に記載（エラー0件。警告1件は想定内の「T18 が基準に無い新しいタスク」） |

## task 文の要件

### 1. 相手の機能が欠けずに入っているか — ○
`git diff 161f8d7 3d0c0b9 -- backend/app frontend/src README.md backend/requirements.txt` を確認。

- 相手側のファイル `schemas.py`、`routers/review.py`、`rubric.py`、`video_frames.py`、`reviewApi.ts`、`types/review.ts`、`UploadForm.tsx`、`RubricPreviewPanel.tsx`、`CriterionCard.tsx`、`PoweredBy.tsx`、`ReviewResult.tsx`、`README.md`、`requirements.txt`（`av` 追加）は **161f8d7 と完全に同一**（差分に現れない）。
- 差分に出るのは: こちらの新規ファイル（contest 系モデル・ルーター・サービス・画面・テスト）、`config.py`/`main.py` への contest 設定・ルーター追加、`slide_extractor.py`（こちらの T17 の改良）、`App.tsx` のモード切替タブ、`LoadingState.tsx` の `stages` 引数（既定値は元の3段階のまま）、衝突解消した3ファイル、`index.css`。
- 評価基準の3方式（`resolve_rubric`）、web検索ツール（`RUBRIC_GENERATION_TOOLS`）、プレビューAPI `/api/rubric/preview`、判定基準（`levels`）の返却、動画静止画分析（`describe_presentation_visuals` → `build_user_prompt(..., visual_description)` → Jev の state）、Powered by 表示、README 追記は、いずれも相手の実装のまま残っており、弱められていない。

### 2. こちらの機能が壊れていないか — ○
- `git diff 8055eea 3d0c0b9` の対象に `contest_scorer.py`、`routers/contest.py`、`question_builder.py`、`models/contest.py`、contest 系フロント・テストは **一つも含まれない**（完全に同一）。
- 呼び出し側の整合: `contest_scorer.py` は `run_system_one(state, questions)` と `build_user_prompt(slides, transcript)` を呼ぶ。マージ後の `run_system_one` はこちらの版と同じ形・同じエラー変換。`build_user_prompt` は第3引数 `visual_description=None` が追加されただけで、None のとき出力はマージ前と1文字も変わらない（`if visual_description:` のときだけ節を足す）。`question_builder.py` の `_call_claude(..., failure_detail=FAILURE_DETAIL)` はキーワード指定なので、`tools` 引数の追加と衝突しない。
- contest 系テスト（test_contest_api / audio / models / scorer / slide_limits / slides、question_builder、question_set_storage）は再実行でも全て通過。スクショ3でコンテスト観点モード画面が表示されている。

### 3. 衝突解消が正しいか — ○
- `jev_scorer.py`: こちらの `run_system_one`（SDK エラー→日本語 HTTP エラー）をそのまま残し、相手の `score_with_jev(state_text, criteria: list[dict])` をその上に載せた形。エラー処理は4種すべて残り、キー未設定チェックも `run_system_one` 内にある。相手版の挙動（一度の system_one 呼び出し、`score + SCALE_MIN`、confidence）と一致。
- `review_generator.py` の `_call_claude`: 相手の `tools` 引数（あれば kwargs に入れる）とこちらの `failure_detail` 引数を両方持つ。例外の並び・文言はこちら側の版と同一で、最後の汎用エラーと `parsed_output is None` のときだけ `failure_detail` を使う。既定値は元の文言と同じ。
- `index.css`: マージ前（8055eea）のこちらのファイルは **一行も変わっておらず**、末尾に相手の新部品（`.powered-by*`、`.rubric-preview*`、`.criterion-levels*`、`.criterion-level-achieved` 等）のスタイルをこちらの CSS 変数（`--accent`、`--card-bg`、`--border`、`--radius-*`）で書き直して追加しただけ。`glass`、`gradient`、`backdrop` 等の暗いテーマの名残は grep で0件。

### 4. 既存テストの書き換えが必要最小限か — ○
- `test_jev_scorer.py`（3か所）、`test_network_guard.py`（1か所＋import）: `score_with_jev("…", DEFAULT_MODE)` → `score_with_jev("…", get_rubric_criteria(DEFAULT_MODE))` に変えただけ。渡している中身は同じ既定ルーブリックで、確かめる内容（state・questions の形、キー未設定、認証エラー、ネットワーク遮断）は変わっていない。
- `test_rubric.py`: `compute_overall_score(scores, mode)` → `compute_overall_score(scores)`（相手が引数を減らしたため）に追従。期待値（100 / 20 / 70）は同じ。さらに項目数が3や10でも正しく換算されるテストを1件追加しており、むしろ強くなっている。

### 5. 追加テスト `test_merged_review_features.py` が要点を確かめているか — ○
リポジトリ外（scratchpad に `git worktree` で 3d0c0b9 を展開。確認後に削除済み）で、相手の実装を1か所ずつ壊して、このテストファイルだけを実行した。**9通りすべてでテストが失敗（＝壊れたことを検出）**:

| 壊し方 | 結果 |
|---|---|
| イベント内容からの設計で web検索ツールを渡さない | 失敗を検出 |
| 項目名指定で、ユーザーの名前ではなく Claude の返した名前を使う | 失敗を検出 |
| 手で直したプレビュー（custom）を優先しない | 失敗を検出 |
| 結果の各項目に判定基準（levels）を入れない | 失敗を検出 |
| 映像の説明を Jev に渡す文章に入れない | 失敗を検出 |
| 映像説明の失敗を握りつぶさない（審査が止まる） | 失敗を検出 |
| mp3 を動画扱いにする | 失敗を検出 |
| プレビュー API のパスを変える（消える） | 失敗を検出 |
| 静止画を1枚しか送らない | 失敗を検出 |

外部 API はすべて偽物（FakeClaude / FakeTypeSafeClient）で、本物は呼んでいない。

### 6. 見た目 — ○
スクショ3枚を画像として確認。
- screenshot-01: 明るい背景・白カード・オレンジ（#b8543a 系）のタブとボタン。Powered by 行、評価基準の指定方法ラジオ、「評価基準を確認する」ボタン、プレビュー（折りたたみ・1〜5点の判定基準）が崩れずに表示。
- screenshot-02: 結果画面。項目カードの「審査基準を見る」を開くと1〜5点が並び、該当する4点が薄いオレンジで強調。
- screenshot-03: コンテスト観点モードの画面が従来のデザインのまま表示。
- 暗いテーマの色は画面にもCSSにも見当たらない。

## 合否に影響しない指摘
1. `frontend/index.html` に相手側由来の Google Fonts（Space Grotesk / Inter）の読み込みが残っているが、`index.css` はこれらを使っていない（`font-family` は Hiragino / Yu Gothic / system-ui）。見た目に影響はないが、使わないフォントを毎回読み込むので、消してよいか人間に確認するとよい。
2. `PoweredBy.tsx` の `.powered-by-sep` にはスタイルが無い（親の色を受け継ぐだけなので見た目上の問題はない）。
3. スクショ3で「観点を追加する」と「Questionを生成する」のボタンの間に隙間がない。マージで変わった部分ではない（contest 系の画面・CSSはマージ前と同一）ので T18 の範囲外。
4. `test_merged_review_features.py` の `test_review_includes_each_criterions_levels` などは Jev がある場合の経路だけを確かめている。TYPESAFE_API_KEY が無いときの（Claude だけで採点する）経路で `levels` が返ることはテストされていない（コード上は両経路とも `levels=c["levels"]` を入れている）。
5. `tasks.json` の書き換えで「LF will be replaced by CRLF」という警告が出る（改行コードの扱いの注意。内容の差分は status と passes の2行のみ）。

## check_tasks.py の再実行結果（tasks.json 更新・本ファイル作成後）

```
$ backend/.venv/Scripts/python evals/check_tasks.py
WARN : T18: 基準に無い新しいタスクです。人間が追加したなら基準タグを更新してください。
結果: エラー 0 件 / 警告 1 件 / 完了 17/19 タスク
exit=0
```
