# harinezumi — ピッチ審査を添削するAI

画面上部のタブで、2つの使い方を切り替えられます。

| タブ | できること |
|---|---|
| **ピッチ審査** | 用意された審査基準（またはAIが作った基準）で、ピッチを採点・添削します。下の説明はこのタブのものです |
| **コンテスト観点モード** | 出場する大会の審査観点と配点を自分で入力し、その基準でピッチを採点します。→ [コンテスト観点モード](#コンテスト観点モード大会の審査観点で採点する) |

## ピッチ審査タブ

ピッチ資料（PDF/PPTX）と、任意で発表の音声・動画をアップロードすると、AIが学生・大学主催のビジネスプランコンテストの審査員として、「起業の科学」（田所雅之）のリーンスタートアップ検証フレームワーク（ペインの質・CPF・PSF・市場定量分析・PMF兆候など）に基づく7項目のルーブリックに沿って採点・添削するWebアプリです。

- スライド抽出: `pdfplumber` (PDF) / `python-pptx` (PPTX)
- 音声・動画の取得: ファイルアップロード、または直接リンク/YouTubeなどのURL（`yt-dlp`）
- 音声書き起こし: OpenAI Whisper API
- 採点: Jev（TypeSafe AI）— 7項目のルーブリックを構造化スコア＋確信度で判定（`TYPESAFE_API_KEY`未設定時はClaudeのみで採点する方式に自動フォールバック）
- 審査コメント生成: Anthropic Claude API (`claude-sonnet-5`)
- 審査モードは「ビジネスコンテスト向け」「汎用ピッチ審査」の2種類。汎用モードでは評価基準を3通りから選べます: ①既定の汎用ルーブリック（何も指定しない場合）、②「イベント内容」を自由記述してAIに専用ルーブリックを設計させる（具体的な大会名を書くとweb検索で実際の審査基準を調べて反映）、③評価項目名（3〜10個）を自分で直接指定し、各項目の1〜5点の判定基準だけAIに生成させる
- 審査前に「評価基準を確認する」ボタンで、実際に使われる7項目の判定基準（1〜5点の水準説明）をその場でプレビューできます
- 動画（`.mp4`/`.webm`）アップロード時は、動画から均等な間隔で静止画を数枚抽出し、Claudeが身振り・表情・アイコンタクトなどの非言語的な表現を分析します（`PyAV`使用。ffmpeg不要でサーバーレス環境でも動作）。結果は「プレゼンの分かりやすさ・訴求力」の評価に反映されます
- フロントエンド: React + Vite + TypeScript
- バックエンド: FastAPI

音声/動画は `.mp3` `.mp4` `.mpeg` `.mpga` `.m4a` `.wav` `.webm` のみ対応です（OpenAI Whisper APIが直接受け付ける形式のみを使うことで、ffmpeg等の外部バイナリを一切必要としない構成にしています。サーバーレス環境でも動作します）。

## コンテスト観点モード（大会の審査観点で採点する）

大会ごとに違う審査基準で、自分のピッチが何点になるかを本番前に確かめるためのモードです。
「観点（審査で見るポイント）と配点」を入力すると、AIが観点ごとに5段階の採点基準（Question）を作り、それを使って発表を採点します。
点数をつけるのは Jev（TypeSafe AI）で、配点への換算と合計はプログラムが計算します（AIに計算させないので、同じ採点結果からは必ず同じ点数になります）。

### 使い方

1. 画面上部の **「コンテスト観点モード」** タブを押します。
2. **コンテスト名** と **観点**（名前・説明・配点）を入力します。観点は「観点を追加する」で最大15個まで増やせます。説明欄には、大会の募集要項にある審査基準の文をそのまま貼り付けるのがおすすめです。
3. **「Questionを生成する」** を押すと、Claude が観点ごとに Jev への質問文と5段階の基準を作ります（15秒ほど）。
4. 作られた Question を読み、必要なら文言を直します。**「保存する」** で名前をつけて保存しておくと、次からは「保存済みのQuestionsを使う」で呼び出せます。
5. **「この内容で音声を採点する」** を押し、次の **どちらか一方、または両方** を選んで **「採点する」** を押します。
   - スライド資料（PDF / PPTX）… スライドの文字とスピーカーノートを読み取ります
   - 発表の音声・動画（mp3 / m4a / wav / mp4 / webm など、25MBまで）… Whisper が文字に起こします。**動画（mp4 / webm）** なら、静止画4枚から表情・姿勢・身振り手振りも Claude が読み取り、採点の材料にします
6. 観点別の点数・合計点が表示されます。判断材料が少なく Jev の確信度が低い観点には「参考値」の注意が出ます。

実測の目安（2026-09-27、約2分の音声＋スライド15枚、観点3つ）: Question 生成 約14秒、採点 約8秒。

### 必要なAPIキー（コンテスト観点モード）

| やること | 使うAPI | 必要なキー |
|---|---|---|
| Question の生成 | Claude | `ANTHROPIC_API_KEY`（必須） |
| 音声・動画の書き起こし | Whisper | `OPENAI_API_KEY`（音声・動画を使うとき必須） |
| 採点 | Jev | `TYPESAFE_API_KEY`（**必須**。ピッチ審査タブと違い、Jev が無いときの代わりの採点方法はありません） |
| 動画の映像の分析 | Claude | `ANTHROPIC_API_KEY`（無いときは映像なしで採点を続けます） |

どのAPIも、使うたびに料金がかかります。映像の分析は画像を読む分、音声だけのときより少し高くなります。

### 制限と注意

- 観点は1〜15個、配点は各1〜100点（整数）です。Question の段階は必ず5つです。
- スライドは **60ページ・30,000文字（スピーカーノートを含む）まで** です（`.env` の `MAX_CONTEST_SLIDE_PAGES` / `MAX_CONTEST_SLIDE_CHARS` で変更できます。変えたときは画面の注記 `frontend/src/components/contest/AudioScoreForm.tsx` の数字も合わせてください）。表やグループ化した図形の中の文字も読み取りますが、図や画像の中の文字は読み取れません。
- Whisper は固有名詞（サービス名・団体名など）を聞き違えることがあります。スライドも一緒に送ると、スライドの正しい表記も Jev に渡るので、聞き違いの影響を減らせます。
- 音声が無音などで書き起こしが空のときは採点しません（スライドがあれば、スライドだけで採点し直せます）。
- 映像の分析は、動画から取り出した数枚の静止画だけをもとにした簡易的なものです。声の抑揚や話す速さは見ていません。
- 保存した Question は `backend/data/question_sets/` にJSONで保存されます。ローカル実行専用で、Vercel上では保存が残りません。採点結果は保存されません。

## 前提条件

- Python 3.11 以上
- Node.js 18 以上
- Anthropic APIキー（必須）
- OpenAI APIキー（音声・動画を使う場合に必須）
- TypeSafe (Jev) APIキー（[typesafe.ai](https://typesafe.ai) で発行。新規登録が一時停止中の場合があります。**ピッチ審査タブでは任意**（未設定でもClaudeのみでの採点にフォールバックして動作します）、**コンテスト観点モードでは必須**です）

## ローカルセットアップ

### バックエンド

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # .env を編集して実際のAPIキーを設定
uvicorn app.main:app --reload --port 8000
```

- `.env` には本物のAPIキーを書きます。**`.env` は Git に入れないでください**（`.gitignore` 済み）。キーを他人に見せたり、チャットやファイルに貼り付けたりしないでください。
- Windows で `--reload` を付けて起動すると、止めたあとも裏でポート8000を使い続けることがあります。再起動できないときは `--reload` を外して起動してください。

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:5173 を開いてください。（`/api` へのリクエストは vite.config.ts のプロキシ設定により自動で http://localhost:8000 に転送されます）

`npm run dev` の表示が `http://localhost:5174` など 5173 以外になったときは、前に起動した開発サーバーが残っています。古いサーバーが古い画面を表示し続けることがあるので、残っている `node`（vite）を止めてから起動し直してください。

### 自動テスト（お金はかかりません）

外部API（Claude・Whisper・Jev）はすべて偽物に置き換えて動くので、キーが無くても、料金をかけずに実行できます。

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

フロントエンドは `cd frontend && npm run build` で型チェックとビルドを確かめられます。

## 動作確認

```bash
# スライド抽出のみ（APIキー不要）
curl -F "file=@sample.pptx" http://localhost:8000/api/slides/extract

# ピッチ審査（要 ANTHROPIC_API_KEY。音声を渡す場合は OPENAI_API_KEY も。
# TYPESAFE_API_KEY未設定時はClaudeのみでの採点にフォールバックします）
curl -F "slide_file=@sample.pdf" -F "media_file=@sample.mp3" http://localhost:8000/api/review

# 音声・動画をURLで渡す場合（ファイルの代わりに media_url を指定）
curl -F "slide_file=@sample.pdf" -F "media_url=https://example.com/pitch.mp4" http://localhost:8000/api/review

# コンテスト観点モード ① 観点から Question を作る（要 ANTHROPIC_API_KEY）
#   先に下の rubric.json を UTF-8 で保存しておく
curl -X POST http://localhost:8000/api/contest/questions -H "Content-Type: application/json" \
  --data-binary "@rubric.json" -o questions.json

# コンテスト観点モード ② その Question で採点する（要 TYPESAFE_API_KEY。音声・動画を渡すなら OPENAI_API_KEY も）
curl -F "question_set=<questions.json" -F "slide_file=@sample.pdf" -F "media_file=@sample.mp3" \
  http://localhost:8000/api/contest/score
```

`rubric.json` の例（`id` は半角英数字、`max_points` は1〜100の整数）:

```json
{
  "contest_name": "学生ビジネスプランコンテスト",
  "criteria": [
    { "id": "c1", "name": "課題の明確さ", "description": "", "max_points": 30 },
    { "id": "c2", "name": "市場性", "description": "", "max_points": 20 }
  ]
}
```

- 日本語を含む JSON をコマンドの中に直接書くと、Windows では文字化けして「JSONとして読み取れませんでした」になることがあります。上のようにファイルに保存して `--data-binary "@ファイル名"` で送ってください。
- Windows PowerShell では `curl` が別のコマンドを指すことがあります。その場合は `curl.exe` と書いてください。

## Vercelへのデプロイ（チーム共有用）

フロントエンドとバックエンドをそれぞれ別のVercelプロジェクトとしてデプロイします。

> **⚠️ 認証なしで公開する場合の注意:** このアプリには認証機能がありません。公開すると誰でも審査機能を使え、その都度あなたのAnthropic/OpenAI/TypeSafeのAPIクレジットが消費されます。URLを知っている人だけが使う前提で、共有範囲に注意してください。

### 1. バックエンドをデプロイ

Vercel CLIで `backend/` ディレクトリをプロジェクトルートとしてデプロイします。

```bash
npm install -g vercel   # 未インストールの場合
cd backend
vercel login
vercel deploy --prod
```

デプロイ後、Vercelダッシュボードの当該プロジェクト → **Settings → Environment Variables** で以下を設定し、再デプロイしてください:

| 変数名 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic APIキー |
| `OPENAI_API_KEY` | OpenAI APIキー |
| `TYPESAFE_API_KEY` | TypeSafe (Jev) APIキー（未取得の場合は空のままでOK。Claudeのみでの採点にフォールバックします） |
| `CLAUDE_MODEL` | `claude-sonnet-5` |
| `WHISPER_MODEL` | `whisper-1` |
| `MAX_SLIDE_MB` | `20` |
| `MAX_MEDIA_MB` | `25`（Whisperの25MB上限に合わせる。yt-dlp経由のダウンロードもこの値で制限されます） |
| `CORS_ORIGIN` | 手順2でフロントエンドをデプロイした後のURL（例: `https://harinezumi-frontend.vercel.app`） |
| `MAX_CONTEST_SLIDE_PAGES` | `60`（任意。コンテスト観点モードで受け付けるスライドのページ数の上限） |
| `MAX_CONTEST_SLIDE_CHARS` | `30000`（任意。同じく文字数の上限。スピーカーノートを含む） |

> コンテスト観点モードを使う場合、`TYPESAFE_API_KEY` は空にできません（Jev が必須のため）。

デプロイされたバックエンドのURL（例: `https://harinezumi-backend.vercel.app`）を控えておいてください。

### 2. フロントエンドをデプロイ

```bash
cd frontend
vercel login
vercel deploy --prod
```

Vercelダッシュボードの当該プロジェクト → **Settings → Environment Variables** で以下を設定し、再デプロイしてください:

| 変数名 | 値 |
|---|---|
| `VITE_API_BASE_URL` | 手順1で控えたバックエンドのURL |

### 3. CORSを反映

手順2で分かったフロントエンドのURLを、手順1のバックエンド側 `CORS_ORIGIN` に設定し直し、バックエンドを再デプロイしてください。

これでフロントエンドのURLをチームメンバーに共有すれば、誰でもブラウザからアクセスできます。

### 審査履歴について

`backend/data/reviews/` へのJSON保存はVercel上のサーバーレス環境では永続化されません（ファイルシステムが再起動のたびにリセットされるため）。ローカル実行時のみ有効な機能です。

## 制約・今後の改善候補

- 現状は同期リクエスト1回で処理するMVPです。処理中の進捗はフロントエンドの目安表示のみで、実際のステージとは連動していません（本格的な進捗表示にはポーリングやWebSocketが必要）。
- Whisper APIのファイルサイズ上限（25MB）を超える長い録音は、事前に短く分割してください（自動分割は未実装）。
- 音声・動画のURL指定は `yt-dlp` で取得しています。対応可否はサイトによって異なり、非公開・年齢制限つきコンテンツなどは取得できない場合があります。著作権・利用規約上、指定者に権利のあるコンテンツのみ使用してください。
- **YouTube等のURL指定は、Vercelなどクラウド環境にデプロイした場合は動作しません。** YouTube側がクラウド/データセンターのIPアドレスからのアクセスをボット対策でブロックするためです（ローカル実行時は問題なく動作します）。デプロイ環境では音声・動画は**ファイルを直接アップロード**してください（こちらはVercel上でも問題なく動作することを確認済みです）。
- 認証機能はありません。Vercelなどに公開する際は上記の注意事項を参照してください。
- データベースは実装していません（審査結果はローカル実行時のみ `backend/data/reviews/` にJSONとして保存されます）。
- 動画の非言語的表現分析は、動画から均等に抽出した数枚の静止画のみに基づく簡易的な分析です。声のトーン・抑揚・話す速さといった音声側の表現力までは分析していません（現状は書き起こしテキストの内容のみで判断）。動画がテスト映像など発表者が映っていないものだった場合は、その旨がそのまま反映されます。
