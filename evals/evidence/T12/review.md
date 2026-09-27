# T12 検品記録（評価役）

- 対象: `603e792`（README.md・backend/.env.example・証拠）、`50d84fb`（作業ログ）
- 評価日: 2026-09-27
- 評価役: 新しいサブエージェント（docs/roles.md 3章）
- 外部API（Anthropic / OpenAI / TypeSafe）は一度も呼んでいない。`backend/.env` は読んでいない。

## 判定

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00c | ○ | 下の「AC-00c」参照。T12 の差分に本物のキーらしき値なし |
| AC-00d | ○ | `check_tasks.py` エラー0件（末尾に出力を貼付） |
| AC-14 | ○ | README だけで セットアップ→起動→コンテスト観点モード利用 がたどれる。記載事実はコードと一致。curl 例は偽物APIサーバーで再現成功 |

## AC-14 の確認内容

### 1. 初心者の手順をたどる
- 冒頭のタブ表 → 「コンテスト観点モード」節へのリンク → 使い方1〜6 → 前提条件 → ローカルセットアップ（バックエンド／フロントエンド）→ ブラウザで 5173 を開く、の順で迷わずたどれる。
- 画面の文言をフロントエンドと突き合わせた:
  - タブ名「コンテスト観点モード」: `frontend/src/App.tsx` と一致
  - 「コンテスト名」「観点を追加する」「Questionを生成する」「保存済みのQuestionsを使う」: `CriteriaForm.tsx` と一致
  - 「この内容で音声を採点する」: `QuestionSetReview.tsx` と一致
  - 「採点する」、スライド／音声のどちらか一方または両方: `AudioScoreForm.tsx` と一致
  - 「参考値」: `ContestScoreResultView.tsx` と一致
  - 「保存する」: 実際のボタンは「この内容を保存する」（意味は通じるので合否には影響しない）
- キーの扱いの注意（`.env` に本物のキー、`.env` を Git に入れない、他人やチャットに貼らない）が書かれている。`.gitignore` に `.env` があり、`git ls-files backend/.env` は0件。
- 料金がかかること、自動テストは偽物で料金なしで動くことが書かれている。

### 2. 事実とコードの突き合わせ
| README の記載 | コード | 一致 |
|---|---|---|
| 観点1〜15個、配点1〜100の整数、段階5つ | `models/contest.py`（MAX_CRITERIA=15, `Field(ge=1, le=100, strict=True)`, JEV_LEVEL_COUNT=5, min_length=1） | ○ |
| rubric.json の `id` は半角英数字 | `CriterionId` pattern `^[A-Za-z0-9_-]{1,40}$`（`_` `-` も可。記載は簡略化） | ○ |
| スライド60ページ・30,000文字（ノート含む）、`MAX_CONTEST_SLIDE_PAGES` / `MAX_CONTEST_SLIDE_CHARS` | `config.py`、`contest_scorer.check_slide_limits`（text+notes で数える） | ○ |
| 画面注記の数字は AudioScoreForm.tsx | `AudioScoreForm.tsx` MAX_SLIDE_PAGES=60 / MAX_SLIDE_CHARS=30000 | ○ |
| 表・グループ化図形の文字も読む、図・画像内は読めない | `slide_extractor.py`（GroupShape を再帰、has_table） | ○ |
| 受け付ける形式（mp3/m4a/wav/mp4/webm など）・25MB | `routers/review.py` MEDIA_EXTS、`config.py` max_media_mb=25、`contest.py` で validate_upload | ○ |
| Jev 必須・代わりの採点方法なし | `jev_scorer.run_system_one` がキー無しで 400、`contest_scorer` にフォールバック無し | ○ |
| ピッチ審査タブでは Jev 任意（Claude のみにフォールバック） | `review_generator.py` `jev_available = bool(settings.typesafe_api_key)` | ○ |
| Question 生成に ANTHROPIC_API_KEY 必須 | `question_builder.generate_questions` がキー無しで 400 | ○ |
| 書き起こしに OPENAI_API_KEY（音声・動画を使うとき） | `transcription.transcribe` | ○ |
| 動画(mp4/webm)なら静止画4枚で映像分析、Claude キーが無ければ映像なしで続行 | `video_frames.py` VIDEO_EXTS={.mp4,.webm}, NUM_FRAMES=4、`contest_scorer.describe_video` | ○ |
| 書き起こしが空なら採点しない（スライドだけで採点し直せる） | `contest_scorer.score_materials` | ○ |
| 保存先 `backend/data/question_sets/`、採点結果は保存しない | `question_set_storage.py` DATA_DIR、`.gitignore` の `data/question_sets/*.json` | ○ |
| API パス `/api/contest/questions`（JSON 本文）、`/api/contest/score`（multipart、`question_set` `slide_file` `media_file`） | `routers/contest.py` | ○ |
| 実測 Question 生成 約14秒・採点 約8秒（約2分音声＋スライド15枚、観点3つ） | `evals/evidence/T11/e2e.log`（13.6秒 / 7.9秒、約113.2秒の音声、15枚、c1〜c3） | ○ |
| `.env.example` に2項目追加（60 / 30000） | `config.py` の既定値と一致 | ○ |

### 3. curl 例の再現（評価役が自分で実行）
- 実行役の証拠 `evals/evidence/T12/readme-commands.log` を確認（① HTTP 200 → ② HTTP 200、スライドは PPTX に置換して実行）。
- 評価役も、リポジトリの外（scratchpad）で次の条件のサーバーを **ポート8765** で起動し、README のとおりに実行した。
  - `ANTHROPIC/OPENAI/TYPESAFE_API_KEY` をダミー値で上書き。作業ディレクトリをリポジトリ外にして `.env` を読ませない。
  - Claude（`question_builder._call_claude`）・Whisper（`contest_scorer.transcribe`）・Jev（`contest_scorer.run_system_one`）を偽物に置換。念のため本物のクライアント（AsyncOpenAI / AsyncTypeSafeClient / 採点側 AsyncAnthropic）は作られた瞬間に例外になるようにした。
  - `rubric.json` は README のコードブロックをそのまま抜き出して保存。`sample.pdf` は reportlab で作成（README どおり PDF で確認）。
- 結果:
  - ① `curl -X POST .../api/contest/questions -H "Content-Type: application/json" --data-binary "@rubric.json" -o questions.json` → HTTP 200、questions.json に QuestionSet が保存された
  - ② `curl -F "question_set=<questions.json" -F "slide_file=@sample.pdf" -F "media_file=@sample.mp3" .../api/contest/score` → HTTP 200、c1 15.0/30・c2 10.0/20・合計 25.0/50、`slides_included:true` `transcript_included:true`
  - 参考: 既存の `/api/slides/extract` 例も HTTP 200。対応外の形式を media_file に渡すと 400「対応していないファイル形式です」。
  - 1回目の起動では評価役の偽物設定の誤り（Claude クライアント生成を例外にしすぎた）で ① が 500 になったが、README ではなく評価用スクリプトの問題。直して再実行し上記のとおり成功。
- 自動テスト: `cd backend && .venv/Scripts/python -m pytest -q` → 222 passed。キーを空で上書きしても 222 passed（README の「キーが無くても動く」を確認）。
- 起動したサーバーは停止済み（8765 解放を確認）、scratchpad の作業フォルダは削除済み。8000 / 5173 の開発サーバーは触っていない。

### 4. 既存のピッチ審査タブの説明
- 既存説明は「## ピッチ審査タブ」見出しの下にそのまま残り、削除・書き換えは TypeSafe キーの行だけ。「ピッチ審査タブでは任意／コンテスト観点モードでは必須」と書き分けられ、既存の「未設定時はClaudeのみにフォールバック」（2か所）と矛盾しない。

## AC-00c（秘密情報）
```
$ git diff 603e792~1 50d84fb | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
195:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
```
- 唯一の一致は `secret-scan.log` に書かれた **検査コマンドそのもの**（キーではない）。
- `backend/.env.example` の `sk-ant-xxxxxxxx` 等は T12 より前からあるダミー値で、T12 では変更していない（追加は数値2行のみ）。
- `git diff --cached | grep ...` → 一致なし。README に本物のキーらしき値なし。`backend/.env` は Git 管理外。

## 合否に影響しない指摘（今後の改善候補）
1. 手順4のボタン名「保存する」→ 実際は「この内容を保存する」。
2. curl ②は `\` で改行しているため、Windows の PowerShell / コマンドプロンプトではそのまま貼ると失敗する（Git Bash なら動く）。`curl.exe` の注意はあるが、1行で書く例か「Git Bash で実行」の一言があると初心者に親切。
3. セットアップの `copy .env.example .env` と `.venv\Scripts\activate` は Windows 専用（Mac の手順が無い）。PowerShell では実行ポリシーで activate が止められることがある。いずれも T12 以前からの記載。
4. Anthropic / OpenAI のキーの取得先リンクが無い（TypeSafe だけある）。T12 以前からの記載。
5. バックエンドとフロントエンドを **別々のターミナルで同時に** 動かし続けることが明記されていない。
6. コンテスト観点モードの制限にスライドのファイルサイズ上限（20MB）が書かれていない（環境変数表の `MAX_SLIDE_MB` にはある）。
7. 冒頭表の「下の説明はこのタブのものです」は、前提条件・セットアップも「ピッチ審査タブ専用」と読める余地がある。
8. ① がエラー（例: キー未設定の 400）でも `-o questions.json` にエラー文が保存され、② で「QuestionをJSONとして読み取れませんでした」になる。① の後に中身を確かめる一言があると迷いにくい。

## check_tasks.py の出力（tasks.json 更新後）
```
$ backend/.venv/Scripts/python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 21/21 タスク
```
