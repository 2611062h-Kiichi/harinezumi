# progress.md — 途中経過と引き継ぎ

> AI はこのファイルに **追記** する（過去の記録は消さない）。
> セッションが切れても、別の AI に移っても、ここを読めば続きから再開できるように書く。

---

## 引き継ぎメモ（常に最新の状態に書き換える欄）
- **最終更新**: 2026-09-26
- **今の作業ブランチ**: `feature/contest-jev-questions`（土台: origin/feature/business-contest-rubric の b2dfe7f。upstream は未設定＝まだ push していない）
- **最後に終わったこと**: T02 実装完了 → 評価役の検品待ち（status: review）
- **次にやること**: T02 の検品 → 合格なら T03（観点・Question・採点結果の型定義）
- **止まっていること / 人間待ち**: なし（基準タグ `harness-baseline` = 86bd2d7）
- **注意**:
  - 依存関係は作業ブランチの内容で入れ直し済み（typesafe-sdk 0.7.1 の import、`npm run build` の成功を確認）
  - バックエンドのテスト: `cd backend && .venv/Scripts/python -m pytest -q`（開発用の道具は `pip install -r requirements-dev.txt`）
  - `npm install` を実行すると、npm のバージョン差で `frontend/package-lock.json` の `libc` 行が消える。機能には関係ないので `git checkout -- frontend/package-lock.json` で戻す
  - APIキーの有無（値は見ていない）: `TYPESAFE_API_KEY` は Windows の環境変数で設定済み。`ANTHROPIC_API_KEY` は未設定（`backend/.env` がダミー値のまま）。`backend/.env` には `TYPESAFE_API_KEY` の行が無い（main の .env.example から作ったため）

---

## 作業計画（計画役が書く・タスクごとに上書き）
### T02 pytest 導入と既存機能の回帰テスト（AC-00a, AC-00c, AC-00d, AC-03, AC-04）
1. `backend/requirements-dev.txt`（`-r requirements.txt` + `pytest`）と `backend/pytest.ini`（testpaths=tests, pythonpath=.）を追加
2. `backend/tests/conftest.py`: 全テストで自動的に
   - 外部への通信を禁止（localhost 以外への socket 接続でエラー）→ AC-04 をしくみで保証
   - APIキーをダミー値に差し替え（Windows の環境変数や .env の本物のキーを使わない）＋ `get_settings` のキャッシュをクリア
3. テストを書く（外部 API は偽物のクライアントに差し替え。非同期関数は `asyncio.run` で呼ぶので pytest-asyncio は不要）
   - `test_rubric.py`: 合計点の計算（満点→100、最低点→20）、全項目が5段階、未知のモードはエラー
   - `test_slide_extractor.py`: その場で作った PPTX から本文とノートを抽出、未対応の拡張子は 400
   - `test_health.py`: `GET /api/health` が 200
   - `test_jev_scorer.py`: Jev に渡す state と Score 型の questions、0始まり→1〜5への変換、キー無しで 400、認証エラーで日本語の 400
   - `test_transcription.py`: Whisper の結果をそのまま返す、キー無しで 400、25MB 超で 400
4. 証拠: `evals/evidence/T02/` に pytest.log（通常）、pytest-offline.log（通信禁止の確認テスト含む）、secret-scan.log、check_tasks.log（1行目に実行コマンド）
- 変更予定ファイル: `backend/requirements-dev.txt`, `backend/pytest.ini`, `backend/tests/*`（アプリ本体のコードは変えない）
- 承認が必要な操作: なし（pytest はテスト用の道具で、safety.md 1章の例外。実 API は呼ばない）

---

## 要確認（人間に聞きたいこと）
- docs/requirements.md 5章の Q1〜Q6

---

## 提案（AI からの変更提案。人間が採用したら該当ファイルに反映する）
- **P1（2026-09-26）**: 「証拠に、実行したコマンドを書いていない」という指摘が T00・T01 の2回続いた。`docs/roles.md` 2章の「証拠の保存例」に「ログの1行目に `$ 実行したコマンド` を書く」を追加してはどうか。→ **採用（2026-09-26、人間）。docs/roles.md 2章に反映済み**

---

## 作業ログ（新しいものを下に追記）
### 2026-09-26 ハーネス作成
- 既存コード（main と origin/feature/business-contest-rubric）を調査し、docs/requirements.md 1〜2章にまとめた
- typesafe-sdk 0.7.1 のソースで Jev の入出力の型を確認した
- 作成: AGENTS.md, CLAUDE.md, docs/*, tasks.json, progress.md, evals/*, .claude/skills/next-task/SKILL.md, .claude/settings.json
- 証拠: `python evals/check_tasks.py` の結果（エラー0件）

### 2026-09-26 T00 作業ブランチ作成（ユーザーの許可を得て AI が実行）
- `git switch -c feature/contest-jev-questions origin/feature/business-contest-rubric` → ハーネスをコミット（2472589）→ `harness-baseline` タグを付けた
- 新しいブランチが origin/feature/business-contest-rubric を upstream として追跡していたため、`git branch --unset-upstream` で外した（そのままだと `git push` が別のブランチに入ってしまう）
- 依存関係を入れ直し、バックエンドの import とフロントエンドのビルドが通ることを確認
- 証拠: `evals/evidence/T00/`（git.log, secret-scan.log, check_tasks.log, review.md）。評価役サブエージェントが5条件すべて○と判定

### 2026-09-26 T01 未確定事項への回答記録
- 人間の回答（原文）: 「Q1、良いです」「Q2、そうです」「Q3、僕のキーです」→ docs/requirements.md 5章に記録（54ef02b）。人間が `git tag -f harness-baseline` で基準を更新
- **評価役の判定: 不合格（AC-02 ×）**。理由: 3章の見出しに `[確定・Q2]` を付けたため、Q2 で聞いていない「TypeSafe = TypeSafe AI 社」の項目まで確定に見えた（AIの推測を確定扱い）
- 修正: 確定の印を「Questions」の項目だけに付け、「TypeSafe」の項目は `[仮定・人間に未確認]` に戻した。証拠を作り直した（実行コマンドを記録、secret-scan.log を追加）
- 人間の追加回答（原文）: TypeSafe の解釈について「あっています」、提案 P1 について「採用してください」→ requirements.md 3章を確定に、roles.md 2章に P1 を反映
- 人間が基準タグを付け直し（86bd2d7）→ 評価役の再検品で **合格**（AC-02/AC-00c/AC-00d すべて○）。証拠: `evals/evidence/T01/review.md`

### 2026-09-26 T02 pytest 導入と既存機能の回帰テスト
- 追加: `backend/requirements-dev.txt`（pytest）、`backend/pytest.ini`、`backend/tests/`（23テスト）、`backend/.gitignore` に `.pytest_cache/`。アプリ本体のコードは変更なし
- テスト対象: 配点計算・ルーブリック構造、PPTX 抽出、/api/health、jev_scorer（Jev に渡す内容・点数変換・エラー）、transcription（Whisper の結果・エラー）
- `tests/conftest.py` が全テストで、APIキーをダミー値に差し替え、外部への通信を遮断する
- **発見と修正**: 最初の通信遮断は `socket.connect` しか止めておらず、確認のためにモック無しで Jev を呼んだところ、**ダミーキー `test-typesafe-key` を付けた1回分のリクエストが api.typesafe.ai に届いた**（認証エラーで拒否。本物のキーは送られておらず、料金も発生していない）。原因は、非同期の通信がホスト名の解決（getaddrinfo）と Windows 専用の接続方式（ConnectEx）を使い、`socket.connect` を通らないこと。名前解決と asyncio の接続も遮断するよう直し、`test_network_guard.py` に再発防止テストを入れた（モック無しの Jev 呼び出しが「認証エラー」ではなく「接続失敗」になることを確認）
- 証拠: `evals/evidence/T02/`（pytest.log: 23 passed、secret-scan.log: 一致なし、check_tasks.log）

---

## 学んだこと（改善の蓄積）
> 失敗やつまずきを1行で書く。同じ内容が **2回** 出たら、ルール化の提案を「提案」欄に書く。
> 人間が採用したら、AGENTS.md / docs/safety.md / SKILL.md のどこかに反映し、ここに「→反映済み（ファイル名）」と書く。

- （例）Windows では `python` が別の環境を指すことがある → `backend/.venv/Scripts/python` を明示する
- T00: `git switch -c <新> origin/<別ブランチ>` を使うと、新しいブランチがその別ブランチを追跡する設定になる。作ったらすぐ `git branch --unset-upstream` で外す
- T00: 複数のコマンドを `&&` でつなぐと、途中のコマンドがわざと失敗させるもの（例: upstream が無いことの確認）でも、そこで後ろが止まる。証拠を取るコマンドはつなげずに1つずつ実行する
- T00（評価役の指摘）: 秘密情報チェックの証拠に、実際に使ったコマンドと違う書き方を残していた。証拠には、実行したコマンドをそのまま記録する
- T01（評価役の指摘・不合格）: 見出しに「確定」の印を付けると、その下の項目すべてが確定に見える。確定・仮定の印は、項目ごとに付ける
- T01: `check_tasks.log` にも実行したコマンド行を入れる（T00 と同じ種類の指摘が2回目 → P1 として docs/roles.md に反映済み）
- T02: 「テストが全部通った」だけでは安全装置が効いている証明にならない。わざと失敗するはずの状況（モック無しの呼び出し）を作って、本当に止まるか確かめる。今回それで遮断の抜け穴が見つかった
- T02: Windows の非同期通信は `socket.connect` を通らない。通信を止めるときは名前解決（getaddrinfo）と asyncio の接続も止める
