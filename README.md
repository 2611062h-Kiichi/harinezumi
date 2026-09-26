# harinezumi — ピッチ審査を添削するAI

ピッチ資料（PDF/PPTX）と、任意で発表の音声・動画をアップロードすると、AIが学生・大学主催のビジネスプランコンテストの審査員として、「起業の科学」（田所雅之）のリーンスタートアップ検証フレームワーク（ペインの質・CPF・PSF・市場定量分析・PMF兆候など）に基づく7項目のルーブリックに沿って採点・添削するWebアプリです。

- スライド抽出: `pdfplumber` (PDF) / `python-pptx` (PPTX)
- 音声・動画の取得: ファイルアップロード、または直接リンク/YouTubeなどのURL（`yt-dlp`）
- 音声書き起こし: OpenAI Whisper API
- 採点: Jev（TypeSafe AI）— 7項目のルーブリックを構造化スコア＋確信度で判定（`TYPESAFE_API_KEY`未設定時はClaudeのみで採点する方式に自動フォールバック）
- 審査コメント生成: Anthropic Claude API (`claude-sonnet-5`)
- フロントエンド: React + Vite + TypeScript
- バックエンド: FastAPI

音声/動画は `.mp3` `.mp4` `.mpeg` `.mpga` `.m4a` `.wav` `.webm` のみ対応です（OpenAI Whisper APIが直接受け付ける形式のみを使うことで、ffmpeg等の外部バイナリを一切必要としない構成にしています。サーバーレス環境でも動作します）。

## 前提条件

- Python 3.11 以上
- Node.js 18 以上
- Anthropic APIキー（必須）
- OpenAI APIキー（音声・動画を使う場合に必須）
- TypeSafe (Jev) APIキー（任意。[typesafe.ai](https://typesafe.ai) で発行。新規登録が一時停止中の場合があります。未設定でもClaudeのみでの採点にフォールバックして動作します）

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

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:5173 を開いてください。（`/api` へのリクエストは vite.config.ts のプロキシ設定により自動で http://localhost:8000 に転送されます）

## 動作確認

```bash
# スライド抽出のみ（APIキー不要）
curl -F "file=@sample.pptx" http://localhost:8000/api/slides/extract

# ピッチ審査（要 ANTHROPIC_API_KEY。音声を渡す場合は OPENAI_API_KEY も。
# TYPESAFE_API_KEY未設定時はClaudeのみでの採点にフォールバックします）
curl -F "slide_file=@sample.pdf" -F "media_file=@sample.mp3" http://localhost:8000/api/review

# 音声・動画をURLで渡す場合（ファイルの代わりに media_url を指定）
curl -F "slide_file=@sample.pdf" -F "media_url=https://example.com/pitch.mp4" http://localhost:8000/api/review
```

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
