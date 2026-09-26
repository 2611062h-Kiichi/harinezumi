# requirements.md — 要件と、事実・仮定の区別

> 書き換えてよいのは人間だけ。AIは変更案を `progress.md` の「提案」に書く。
> 各項目に **[事実]**（コードや資料で確認済み）か **[仮定]**（未確認・人間の確認待ち）を付けている。

---

## 1. 今ある機能（2026-09-26 時点の調査結果）

### 1-1. `main` ブランチ [事実]
| 機能 | 場所 |
|---|---|
| スライド（PDF/PPTX）からテキスト抽出 | `backend/app/services/slide_extractor.py` |
| 音声/動画 → 文字起こし（OpenAI Whisper） | `backend/app/services/transcription.py`、`POST /api/media/transcribe` |
| 動画 → 音声抽出（ffmpeg） | `backend/app/services/audio_extraction.py` |
| 7項目ルーブリックで Claude が採点・添削 | `backend/app/rubric.py`、`backend/app/services/review_generator.py`、`POST /api/review` |
| 審査結果を JSON 保存・履歴取得 | `backend/app/services/history.py`、`GET /api/reviews/history` |
| 画面（アップロード → 結果表示） | `frontend/src/` |

- 合計点はサーバーが計算で出す（AI に合計を任せない）。この方針は新機能でも守る。
- 自動テストは **まだ1つもない**。

### 1-2. `origin/feature/business-contest-rubric` ブランチ [事実]
`main` より12コミット進んでいて、**すでに Jev を使っている**。
- `backend/app/services/jev_scorer.py` … 固定ルーブリックの各項目を Jev の `Score` で採点
- `TYPESAFE_API_KEY` が無いときは Claude だけで採点する（フォールバック）
- ほかに: ビジネス/一般の審査モード切替、口調（甘口/普通/辛口）、URL からの音声取得、ffmpeg 廃止、Vercel 向け準備

→ **新機能はこのブランチを土台にする** [確定・Q1]

---

## 2. Jev（TypeSafe AI）の仕様 [事実]
出典: `typesafe-sdk` 0.7.1 のソースコード（PyPI から取得して確認）、
公式ドキュメント https://docs.typesafe.ai/ 、既存コード `jev_scorer.py`。

- Python パッケージ名: `typesafe-sdk`、呼び出し: `AsyncTypeSafeClient(api_key=...).system_one(state, questions)`
- `state` = 評価してほしい中身。**テキスト、JSON オブジェクト、配列** を受け取れる。
  **音声は直接渡せない** → だから先に文字起こしが必要。
- `questions` = `{名前: 質問}` の辞書。質問の型は3種類:
  | 型 | 用途 | 中身 |
  |---|---|---|
  | `Score` | 段階評価 | `instructions`（何を評価するか）＋ `criteria`（**低い順**に並べた各段階の説明。位置が点数 0,1,2…） |
  | `Choice` | 選択肢から選ぶ | `criteria` = `{ラベル: 説明}` |
  | `Noul` | はい/いいえ | `criteria` = `{true: 説明, false: 説明}` |
- `Score` の答え: `score`（0始まりの期待値。小数になる）、`confidence`（0〜1 の確信度）、`probabilities`（各段階の確率）、`legend`
- エラーの種類: 認証エラー、利用上限、接続エラーなど（`jev_scorer.py` で日本語化済み）
- API キーは `TYPESAFE_API_KEY`。**新規登録が一時停止中の場合がある**（feature ブランチの README より）

---

## 3. 用語の解釈
- [確定・Q2] ユーザーの言う **「Questions」= Jev の `questions` 引数**（観点ごとの `Score` 質問）。
  - 「審査員が発表者にする質疑応答の質問」という別解釈は、Q2 の回答で否定された。
- [確定・2026-09-26 人間の回答「あっています」] **「TypeSafe」= Jev の提供元 TypeSafe AI 社**。同時に「入力と出力の形（型）を決めて、形が違えばエラーにする」設計方針とも一致させる。

---

## 4. 新機能の要件

### 機能要件（FR）
- **FR-1 観点入力**: ユーザーは観点を1〜15個入力できる。各観点は「名前（必須）」「説明（任意）」「配点（1〜100 の整数、必須）」を持つ。
- **FR-2 Question 生成**: Claude が各観点を Jev の `Score` 質問に変換する。
  - 1観点につき1つの Question。観点との対応（`criterion_id`）を必ず持つ。
  - `criteria`（段階の説明）は **5段階**、低い順、各段階は具体的で観察できる内容にする。
  - 出力は Pydantic の型で検証し、形が違えばエラーにする（型安全）。
- **FR-3 Question 確認・編集**: 生成結果を画面に表示し、ユーザーが文言を直してから採点に進める。
- **FR-4 文字起こし**: 音声/動画ファイルを既存の `transcribe()` で文字起こしする。空の結果はエラー。
- **FR-5 Jev 採点**: 文字起こしテキストを `state`、Questions を `questions` として `system_one` を1回呼ぶ。
- **FR-6 配点換算（計算はサーバー）**: 観点の点数 = `score ÷ (段階数−1) × 配点`（小数第1位で四捨五入）。合計 = 観点の点数の合計。
- **FR-7 確信度の表示**: `confidence < 0.5` の観点には「判断材料が少ない」旨を表示する。 [仮定: しきい値 0.5]
- **FR-8 Questions の保存・再利用**: 名前を付けて JSON 保存し、一覧から選んで再利用できる。
- **FR-9 キーが無いとき**: `TYPESAFE_API_KEY` が未設定なら、分かりやすい日本語エラーを出す（黙って別方式にしない）。 [仮定]

### 非機能要件（NFR）
- **NFR-1** 既存機能を壊さない（既存テスト・ビルドが通る）。
- **NFR-2** 自動テストは偽物（モック）の Claude / OpenAI / Jev で動き、お金がかからない。
- **NFR-3** エラーメッセージは日本語で、次に何をすればいいかが分かる。
- **NFR-4** 秘密情報をログ・レスポンス・保存ファイルに含めない。

---

## 5. 未確定事項（人間の回答待ち）
| # | 質問 | 決まるまでの仮定 / 人間の回答 |
|---|---|---|
| Q1 | 土台のブランチは `feature/business-contest-rubric` でよいか | **回答済み（2026-09-26、人間）:「良いです」** |
| Q2 | 「Questions」の意味は Jev の questions でよいか | **回答済み（2026-09-26、人間）:「そうです」** |
| Q3 | TypeSafe の API キーは取得済みか | **回答済み（2026-09-26、人間）: Windows の環境変数 `TYPESAFE_API_KEY` について「僕のキーです」→ 取得済み。実通信テスト（T11）は引き続き承認制** |
| Q4 | 段階数は5固定でよいか | 5固定 |
| Q5 | 確信度のしきい値 | 0.5 |
| Q6 | 練習用のサンプル音声（個人情報なし）を用意できるか | T11 の前に人間が用意 |
