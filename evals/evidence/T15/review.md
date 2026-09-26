# T15 検品記録（評価役）

- 対象: T15「コンテスト観点モードの採点でスライド資料（PDF/PPTX）も使えるようにする」
- 変更: コミット a53b628（20ファイル。backend: models/contest.py, routers/contest.py, services/contest_scorer.py, tests/test_contest_api.py（1件書き換え）, tests/test_contest_slides.py（新規16件）／frontend: contestApi.ts, AudioScoreForm.tsx, ContestQuestionsPage.tsx, ContestScoreResultView.tsx, types/contest.ts）
- 評価日: 2026-09-27
- 判定: **合格**（全条件 ○）→ tasks.json の T15 を `"status": "done", "passes": true` に変更

## 条件ごとの判定

| 条件 | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存テストがすべて通る | ○ | 証拠 `pytest.log` の1行目のコマンドを再実行し `161 passed`（証拠と一致）。`pytest -q` でも `161 passed`。ただし下記「指摘1」の既知の不安定テスト（T15とは無関係）が、計13回の全体実行中3回失敗した |
| AC-00b フロントがビルドできる | ○ | `npm run build` を再実行し `tsc -b && vite build` 成功（49 modules, built in 528ms）。package-lock.json の変更なし |
| AC-00c 秘密情報が無い | ○ | `git diff --cached | grep -nE ...`（docs/safety.md 3章）で一致なし。コミット a53b628 全体に同じ grep をかけても、一致は secret-scan.log 内のコマンド文字列そのもの1件のみ。.env・DB・保存データ等はコミットに含まれない |
| AC-00d tasks.json のルール違反なし | ○ | `python evals/check_tasks.py` でエラー0件。警告1件（T15 が基準に無い新タスク）は人間の依頼で追加したタスクの基準タグ更新待ちで、既知のもの |
| AC-08 音声→文字起こし→Jev 入力がつながる／空の書き起こしはエラー | ○ | `contest_scorer.build_jev_state` は `slides is None` のとき `transcript or ""` を返すだけで、書き起こしをそのまま state にする（T15 前と同じ）。既存テスト `test_contest_audio.py::test_whisper_text_becomes_jev_state_unchanged`・`test_surrounding_whitespace_is_passed_through_as_is`・`test_empty_transcript_is_rejected_before_jev` は変更されずに合格。新規 `test_transcript_only_is_passed_through_unchanged` も `state == TRANSCRIPT` を確認。自分の確認スクリプトでも、前後に空白・改行のある Whisper 出力が API 経由で state に **完全一致** で入ることを確認。スライド付きでも書き起こしが空なら 400（`test_blank_transcript_is_still_rejected_even_with_slides`） |
| AC-09 API が仕様どおり（成功200・不正入力400・キー未設定で日本語） | ○ | 成功: スライドのみ／音声のみ／両方で200（テスト＋確認スクリプト）。不正入力: 下表の異常入力32通り＋500ページPDFで、500 や英語のエラーは0件、一時フォルダの残りも0件。キー未設定: スライドのみで TYPESAFE_API_KEY 空→400「TYPESAFE_API_KEYが設定されていません。」、スライド＋音声で OPENAI_API_KEY 空→400「OPENAI_API_KEYが設定されていません。」（Whisper・Jev とも呼ばれない）。スライドのみなら OPENAI_API_KEY が空でも 200（Whisper を使わないので正しい） |
| AC-12 画面で送ると観点別の点数・合計・確信度の注意が表示される | ○ | スクショ3枚を画像で確認（下記）。build 成功も確認済み |
| task 文の要件 | ○ | スライドのみ・音声のみ・両方で採点可（テスト・確認スクリプト・スクショ）／スピーカーノートを含む（`test_slides_and_transcript_both_reach_jev` と jev-state-from-ui.log の「(スピーカーノート: …)」）／音声のみは書き起こしをそのまま（AC-08 参照）／壊れたファイル・文字の無いスライドは日本語の400（下表）／画面にスライド欄（スクショ01、AudioScoreForm.tsx） |

## 自分で再実行したコマンドと結果

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
→ 1回目: 1 failed, 160 passed（test_question_set_storage.py::test_list_returns_newest_first_with_summary_fields）
→ 続けて11回: 9回 161 passed、2回 1 failed（同じテスト）
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
→ 161 passed in 4.08s
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q tests/test_question_set_storage.py （8回）
→ 7回 11 passed、1回 1 failed（同じテスト）
$ cd frontend && npm run build
→ tsc -b && vite build 成功（✓ built in 528ms）。git status に package-lock.json の変更なし
$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
→ 一致なし（exit=1）
$ git show a53b628 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
→ 742行目の secret-scan.log 内のコマンド文字列のみ（秘密情報ではない）
$ python evals/check_tasks.py
→ 末尾に貼付
```

失敗したテストは T08 で作られた `question_set_storage.list_all()` の並び順（`os.path.getmtime` 頼み）のもので、T15 では `question_set_storage.py`・そのテストとも変更されていない（`git log -- tests/test_question_set_storage.py app/services/question_set_storage.py` は T08 のコミット 7406c0e のみ）。progress.md に提案 P6 として既に記録されている既知の不安定テストのため、T15 の不合格理由にはしない（指摘1）。

### 異常入力の確認（リポジトリ外の scratchpad の確認スクリプト）

- 方法: `t15_probe.py`・`t15_keys.py` を scratchpad に置き、作業フォルダも scratchpad（backend/.env を読み込ませないため）にして `PYTHONPATH=backend` で実行。環境変数にダミーキーを設定、`transcription.AsyncOpenAI` と `jev_scorer.AsyncTypeSafeClient` を既存テストの偽物（FakeOpenAI / FakeTypeSafeClient）に差し替え、`socket.getaddrinfo`・`socket.socket.connect`・asyncio の `sock_connect` をローカル以外拒否に差し替え。`contest_router.tempfile.mkdtemp` を記録版にして、リクエスト後に一時フォルダが残っていないかを確認。FastAPI の TestClient（`raise_server_exceptions=False`）で実行。ポート8000/5173 は使っていない
- 実行: `cd <scratchpad> && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 PYTHONPATH="<repo>/backend" "<repo>/backend/.venv/Scripts/python" t15_probe.py`
- 結果: **NG 0件**、外部通信の試み 0件（`blocked_outbound_attempts=[]`）、一時フォルダの残り 0件

| 入力 | 結果 |
|---|---|
| 0バイトPDF（スライドのみ）／0バイトPPTX／0バイトPDF＋音声 | 400「スライド資料を読み込めませんでした。…」、Jev 呼ばれず |
| 拡張子 .pptx で中身PDF／.pdf で中身PPTX／.pptx で中身ただのZIP | 400「スライド資料を読み込めませんでした。…」 |
| パスワード付きPDF（閲覧パスワード必須、単独・音声付き） | 400「スライド資料を読み込めませんでした。…」 |
| 途中で切れたPDF／`%PDF-1.4` の後がランダムなバイト | 400「スライド資料を読み込めませんでした。…」 |
| スライド0枚のPPTX（単独）／文字の無い図形だけのPPTX／白紙3ページのPDF | 400「スライド資料から文字を読み取れませんでした。画像だけのスライドや…」 |
| スライド0枚のPPTX＋音声 | 200（音声で採点。slides_included=true） |
| ファイル名が空（中身あり／中身も空＝ブラウザ未選択相当） | 400「スライド資料はPDFまたはPPTXのファイルで指定してください。」、一時フォルダ作成なし |
| ファイル名が `.pdf` だけ／`old.ppt` | 400「対応していないファイル形式です（対応形式: .pdf/.pptx）。」 |
| ファイル名 `../../x.pdf`／`A.PDF`／`発表資料.pptx` | 200（保存先は mkstemp の一時名で、パスは使われない） |
| 21MB の .pdf（単独）／21MB の .pptx＋音声 | 400「ファイルサイズが大きすぎます（上限 20MB）。」、一時フォルダ作成なし |
| slide_file と media_file が両方文字列 | 400「発表の音声または動画ファイルを指定してください。」 |
| slide_file が文字列＋正しい音声／空文字列 | 400「スライド資料はPDFまたはPPTXのファイルで指定してください。」 |
| media_file が文字列＋正しいスライド | 400「発表の音声または動画ファイルを指定してください。」 |
| スライド2つ（PDF＋PPTX） | 400「スライド資料は1つだけ指定してください。」 |
| question_set 無し＋スライド | 400「採点に使うQuestionを指定してください。」 |
| 500ページのPDF（218KB） | 200、0.37秒、Jev の state は約1.3万文字 |
| 正常系: PDFのみ／PPTX＋音声／音声のみ | 200。PDFのみは Whisper 呼び出し0回、音声のみは slides_included=false |
| 音声のみで Whisper 出力が `"  前後に空白のある書き起こし。\n"` | Jev の state と完全一致（True） |

### 音声のみの動き（T15 前との比較）
`git show a53b628 -- backend/app/services/contest_scorer.py` を読んだ。`score_audio` → `score_materials(slides=None, transcript=text)` → 空チェック（`transcript.strip()` が空なら従来と同じ文言の400）→ `run_system_one(build_jev_state(None, text), …)` で、`build_jev_state` は `slides is None` なら書き起こしを加工せずに返す。結果の `transcript` も従来どおり書き起こしそのもの。追加されたのは結果の `slides_included=false`・`transcript_included=true` の2項目のみ。挙動は変わっていない。

### 書き換えられた既存テスト（test_missing_media_file_is_400）
旧テストは「media_file が無い → 400『…音声または動画ファイルを指定してください』」を確認していた。T15 で音声は任意になり（task 文「スライドのみ…でも採点でき」）、音声が無いだけでは正常系になりうるため、旧テストの前提そのものが仕様変更で無くなった。書き換え後の `test_missing_both_media_and_slides_is_400` は `post_score(filename=None)`（ファイル部分を一切付けない）で「両方無い → 400、文言が完全一致」を確認しており、部分一致から完全一致に **むしろ厳しく** なっている。「音声だけ無い（スライドあり）→ 200」は `test_api_pptx_only_never_calls_whisper`・`test_api_pdf_only` が確認。テストを弱めて合格させたものではなく、仕様変更に伴う正当な書き換えと判断する。

### jev-state-from-ui.log とコードの整合
`review_generator.build_user_prompt` の組み立て（`# ピッチ資料（ファイル名）` → `## スライドN\n本文` → ノートがあれば `\n(スピーカーノート: …)` → 空行 → `# 発表音声の書き起こし\n…`／書き起こし無しなら「音声書き起こしはありません。スライドの内容のみで審査してください。」）と、ログの2つの state は一致する。PPTX の各図形のテキストを改行で連結する `slide_extractor.extract_from_pptx` の出力（「課題\n学生の8割が…」）とも矛盾しない。スライドのみの採点で書き起こし欄が「ありません」の文になっている点も、`score_materials(slides=…, transcript=None)` → `build_user_prompt(slides, None)` と整合。

### スクリーンショット（3枚とも画像で確認）
- `screenshot-01-upload-both.png`: 「発表を採点する」画面に「スライド資料（PDF / PPTX、任意）」欄（sample-pitch.pptx 選択済み）と「発表の音声・動画（任意）」欄（fake-pitch.mp3）、スピーカーノートを含む旨の注記、「採点する」ボタン
- `screenshot-02-result-both.png`: 「スライド資料と発表の音声で採点しました。」、合計 26.5 / 50、観点別「課題の明確さ 16 / 20」「市場規模・成長性 10.5 / 30」、確信度の注意「発表の中に判断材料が少ないため、この点数は参考値です。」
- `screenshot-03-result-slides-only.png`: 「スライド資料だけで採点しました（発表の音声なし）。」、同じく合計・観点別の点数・確信度の注意
- 偽物 Jev の答え（problem 3.0/0.8, market 2.0/0.9 相当）から、16/20・10.5/30・合計26.5 はサーバー側の換算と整合

### 画面側のコード（送信の可否）
`AudioScoreForm.tsx`: `mediaFile`・`slideFile` を別々の state で持ち、ボタンは `disabled={!mediaFile && !slideFile}`、`handleSubmit` も両方 null なら日本語のエラーを出して送らない。どちらか一方でも送れる。`contestApi.scorePitch` は null でない方だけ FormData に追加するため、未選択の欄は送られない（サーバー側の「空ファイル名」400 には当たらない）。サイズ超過（スライド20MB／音声25MB）は選択時に日本語エラーにして選択を取り消す。`ContestQuestionsPage.tsx` は選んだ材料に応じて読み込み中の段階表示を変える。

## 合否に影響しない指摘
1. **既知の不安定テスト（P6）の頻度**: `test_list_returns_newest_first_with_summary_fields` が今回の全体実行13回中3回・単体8回中1回失敗した。progress.md の P6 では「数百回に1回程度」と見積もられているが、この環境では1〜2割程度で起きる。T15 とは無関係だが、評価のたびに誤判定の原因になるので、P6（`saved_at` での並べ替え）の採用を人間に勧める。
2. **PDF のページ数・抽出文字量に上限が無い**: 500ページのPDFでも問題なく処理されたが、20MB 近い文字の多い PDF だと Jev に非常に長い state が渡りうる。必要なら将来、ページ数や文字数の上限を検討。
3. **PPTX の表・グループ化された図形の文字は読まれない**: `slide_extractor`（ピッチ審査と共通、T15 では未変更）は `has_text_frame` の図形だけを読むため。画面の注記は「図や画像の中の文字は読み取れません」だけなので、表の文字も対象外である点は利用者に伝わりにくい。
4. **スライドに文字があっても、音声の書き起こしが空なら400**: 仕様（空の書き起こしはエラー）どおりで、文言も分かりやすいが、「スライドだけで採点し直す」導線は画面に無い（音声を外して再送すれば可能）。
5. ファイル名が空のスライド部分に対する文言が「PDFまたはPPTXのファイルで指定してください」になる（日本語の400なので問題なし）。

## check_tasks.py の出力（tasks.json 更新後・review.md 作成後）
```
$ python evals/check_tasks.py
WARN : T15: 基準に無い新しいタスクです。人間が追加したなら基準タグを更新してください。
結果: エラー 0 件 / 警告 1 件 / 完了 14/16 タスク
```
