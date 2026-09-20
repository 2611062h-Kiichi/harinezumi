# harinezumi — ピッチ審査を添削するAI

ピッチ資料（PDF/PPTX）と、任意で発表の音声・動画をアップロードすると、AIが学生・大学主催のビジネスプランコンテストの審査員として、「起業の科学」（田所雅之）のリーンスタートアップ検証フレームワーク（ペインの質・CPF・PSF・市場定量分析・PMF兆候など）に基づく7項目のルーブリックに沿って採点・添削するローカルWebアプリです。

- スライド抽出: `pdfplumber` (PDF) / `python-pptx` (PPTX)
- 音声書き起こし: OpenAI Whisper API
- 審査生成: Anthropic Claude API (`claude-sonnet-5`)
- フロントエンド: React + Vite + TypeScript
- バックエンド: FastAPI

## 前提条件

- Python 3.11 以上
- Node.js 18 以上
- ffmpeg（動画から音声を抽出する場合のみ必要。PATHに通しておくこと）
- Anthropic APIキー、および音声を使う場合はOpenAI APIキー

## セットアップ

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

# ピッチ審査（要 ANTHROPIC_API_KEY、音声を渡す場合は OPENAI_API_KEY も）
curl -F "slide_file=@sample.pdf" -F "media_file=@sample.mp3" http://localhost:8000/api/review
```

## 制約・今後の改善候補

- 現状は同期リクエスト1回で処理するMVPです。処理中の進捗はフロントエンドの目安表示のみで、実際のステージとは連動していません（本格的な進捗表示にはポーリングやWebSocketが必要）。
- Whisper APIのファイルサイズ上限（25MB相当）を超える長い録音は、事前に短く分割してください（自動分割は未実装）。
- 認証・データベースは実装していません（審査結果は `backend/data/reviews/` にJSONとして保存されるのみ）。
