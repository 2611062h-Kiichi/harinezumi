# T02 検品結果（評価役）

- 日付: 2026-09-26
- 対象: tasks.json T02「pytest を導入し、既存機能（配点計算、スライド抽出、/api/health、jev_scorer、transcription）の回帰テストをモックで書く」
- 対象コミット: `8132d2d`（= `HEAD`。検品開始時の作業ツリーは差分なし）
- 読んだ順: `docs/roles.md` 3章 → `evals/acceptance.md` → `tasks.json` の T02 → `evals/evidence/T02/`（pytest.log / secret-scan.log / check_tasks.log）→ `git show 8132d2d`（テストコード全部と、テスト対象のアプリ本体のコード）
- 読んでいないもの: `backend/.env`、環境変数の値（指示どおり）

## 判定: **合格**（全て○）→ `status: "done"`, `passes: true`

| 条件 | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | 自分で再実行して 23 passed / 失敗0件。証拠 `pytest.log` と、実行時間の行以外は完全に一致 |
| AC-00c 秘密情報が含まれていない | ○ | コミット `8132d2d` の全差分を `docs/safety.md` 3章のパターンで検索し、一致は検索コマンドを書いた行（secret-scan.log 自身）の1件だけ。`.env` はコミットされていない。テストで使うキーは `test-anthropic-key` などのダミー値のみ（ただし下の「指摘1」参照） |
| AC-00d `check_tasks.py` がエラー0件 | ○ | 検品前の再実行で「エラー 0 件 / 警告 0 件 / 完了 2/13」（証拠 `check_tasks.log` と同じ）。tasks.json 更新と本ファイル作成の後の結果は末尾に貼付 |
| AC-03 pytest で自動テストが動き、既存機能のテストが5件以上 | ○ | `pytest.ini`（testpaths=tests）で `pytest` だけで動く。既存機能のテストは17件（ネットワーク遮断の確認6件を除く）。5つの既存機能すべてにテストがあり、テスト名と対象が対応している（下の表） |
| AC-04 外部 API を呼ばずにテストが通る（モック使用がコードで確認できる） | ○ | Jev は `FakeTypeSafeClient`、Whisper は `FakeOpenAI` に `monkeypatch.setattr` で差し替え。加えて `tests/conftest.py` の autouse フィクスチャで、全23テストに外部通信遮断とダミーキーが自動でかかることを `--setup-plan` で確認。前回の抜け穴（名前解決・asyncio の接続）が塞がれていることをコードと `test_network_guard.py`、評価役の追加テスト（リポジトリ外）で確認 |

## 自分で再実行したコマンドと結果

すべて Windows の Git Bash で実行。

1. テストの再実行（AC-00a / AC-03）
   ```
   cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
   ```
   → `collected 23 items` … `23 passed in 3.74s`（exit=0）。テスト名・順番・PASSED の並びは証拠 `pytest.log` と同じ。

2. 証拠との照合（出力をスクラッチフォルダの `rerun.log` に保存して比較）
   ```
   PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v > "$S/rerun.log" 2>&1
   diff <(tail -n +2 ../evals/evidence/T02/pytest.log | grep -v " in [0-9.]*s") <(grep -v " in [0-9.]*s" "$S/rerun.log") && echo SAME_EXCEPT_TIME
   ```
   → `SAME_EXCEPT_TIME`（違いは最後の「in 3.72s」の実行時間だけ）。`$S` は評価役のスクラッチフォルダ（リポジトリ外）。

3. AC-00a の書き方どおり `-q` でも実行
   ```
   PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
   ```
   → `23 passed in 3.61s`

4. 遮断とダミーキーが全テストにかかるか（AC-04）
   ```
   PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest --setup-plan -q 2>&1 | grep -c "SETUP    F block_network"
   PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest --setup-plan -q 2>&1 | grep -c "SETUP    F dummy_settings"
   ```
   → どちらも `23`（全23テストで、`block_network` と `dummy_settings` が自動でセットアップされる）。

5. 評価役の追加テスト（リポジトリ外のスクラッチフォルダ `$S/evalT02/test_eval_guard_extra.py`。`tests/conftest.py` をプラグインとして読み込み、遮断が付いた状態でだけ実行。遮断を外した実験はしていない）
   ```
   cd backend && PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -m pytest -p tests.conftest -p no:cacheprovider -v "$S/evalT02/test_eval_guard_extra.py"
   ```
   → `8 passed in 3.34s`。確かめた内容:
   - `test_guard_is_active_here`: この実行でも遮断が効いている（`api.openai.com` の名前解決が `NetworkAccessBlocked`）
   - `test_socket_create_connection_ip_literal`: `socket.create_connection(("1.1.1.1", 443))`（名前解決なしの IP 直指定）も止まる
   - `test_selector_event_loop_ip_literal`: Proactor ではない `SelectorEventLoop` + IP 直指定の `create_connection` も止まる（`socket.connect` の遮断で止まる）
   - `test_sync_http_client`（`https://api.anthropic.com/`、`https://8.8.8.8/`）: 同期の HTTP クライアントも止まる
   - `test_unmocked_openai_whisper_is_blocked`: モック無しの `transcription.transcribe` が 502「接続に失敗」になり、原因が遮断（=OpenAI に届いていない）
   - `test_unmocked_anthropic_is_blocked`: モック無しの `AsyncAnthropic(...).messages.create` が `APIConnectionError` になり、原因が遮断
   - `test_localhost_still_allowed`: 127.0.0.1 への接続は許可されたまま（asyncio 内部の socketpair が壊れない）

   実行後 `git status --short` は空（リポジトリにファイルは残っていない）。

6. 秘密情報（AC-00c）
   ```
   git show 8132d2d | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
   ```
   → 1件: `542:+$ git diff -- backend | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"`（secret-scan.log に書かれた検索コマンド自体）。それ以外は一致なし。
   ```
   git show 8132d2d --name-only --format= | grep -i "\.env"
   ```
   → 出力なし（exit=1）。`.env` はコミットに含まれない。

7. アプリ本体が変わっていないか
   ```
   git diff 38cda67 8132d2d --stat -- backend/app
   ```
   → 出力なし。`git show 8132d2d --stat` でも、変更は `backend/.gitignore`、`backend/pytest.ini`、`backend/requirements-dev.txt`、`backend/tests/*`、証拠、`progress.md`、`tasks.json` だけ。

8. `python evals/check_tasks.py`（検品前）→ `結果: エラー 0 件 / 警告 0 件 / 完了 2/13 タスク`

## 確認項目ごとの結果

### 1. テストが中身を確かめているか（空っぽのテストが無いか）→ ○
23件すべてに具体的な値の `assert` か `pytest.raises` がある。常に通るだけのテストは無かった。

| 既存機能 | テスト | 確かめている中身 |
|---|---|---|
| 配点計算（`app/rubric.py`） | `test_overall_score_is_100_...`（2モード）、`..._is_20_...`（2モード）、`..._accepts_fractional_jev_scores`、`test_every_criterion_has_unique_id_and_five_levels`（2モード）、`test_unknown_mode_raises` | 満点→100、最低点→20、全項目3.5→70 を `compute_overall_score` で計算。ID の重複なし・名前あり・段階が5個。未知のモードで `ValueError` |
| スライド抽出（`app/services/slide_extractor.py`） | `test_extracts_text_and_notes_from_pptx`、`test_unsupported_extension_is_rejected` | その場で作った PPTX から、スライド番号 [1,2]、本文、ノート（空のノートは ""）を取り出せる。`.key` は 400 |
| /api/health（`app/main.py`） | `test_health_endpoint_returns_ok` | TestClient で 200 と `{"status": "ok"}` |
| jev_scorer | `test_sends_pitch_text_and_score_questions_to_jev`、`test_missing_typesafe_key_is_a_clear_error`、`test_authentication_error_becomes_japanese_400` | 偽の Jev に渡った `state` が書き起こし文そのもの、`questions` のキーが全観点 ID、値が `Score` 型で `criteria` が観点の5段階と一致、ダミーキーが渡る。0始まりの 2.0 → 3.0 への変換と確信度。キー空で 400（Jev を呼ばない）。認証エラーで日本語の 400 |
| transcription | `test_returns_whisper_text`、`test_missing_openai_key_is_a_clear_error`、`test_file_over_whisper_limit_is_rejected` | 偽の Whisper に渡ったキー・モデル名・ファイルの中身と、返り値の文字列。キー空で 400、25MB+1 バイトで 400（どちらも Whisper を呼ばない） |

アプリ本体のコード（`jev_scorer.py` の `score + SCALE_MIN`、`transcription.py` の `WHISPER_MAX_BYTES` 判定、`rubric.py` の `compute_overall_score` など）と照らし、テストの期待値がコードの動きと合っていることを確認した。

### 2. AC-04: 外部 API が偽物に差し替えられているか → ○
- TypeSafe（Jev）: `test_jev_scorer.py` の `fake_jev` フィクスチャが `jev_scorer.AsyncTypeSafeClient` を `FakeTypeSafeClient` に差し替え。Jev を使う3テストすべてがこのフィクスチャを使う。
- OpenAI（Whisper）: `test_transcription.py` の `fake_openai` フィクスチャが `transcription.AsyncOpenAI` を `FakeOpenAI` に差し替え。3テストすべてが使う。
- Anthropic: T02 の対象機能（配点計算、スライド抽出、/api/health、jev_scorer、transcription）には Anthropic を呼ぶものが無いため、差し替えるテストは無い。代わりにダミーキー＋遮断で守られていることを追加テストで確認した（`test_unmocked_anthropic_is_blocked`）。
- `test_network_guard.py` の `test_unmocked_jev_call_never_leaves_the_machine` だけはわざとモック無しで Jev を呼ぶが、遮断で「接続失敗（502）」になり、原因が `NetworkAccessBlocked` であることまで確かめている（外に出ていない証明）。

### 3. conftest の遮断とダミーキーが全テストに自動でかかるか → ○
- `block_network` と `dummy_settings` はどちらも `@pytest.fixture(autouse=True)` で `backend/tests/conftest.py` にあるので、`tests/` 以下の全テストにかかる。`--setup-plan` で23件すべてに付くことを確認（再実行コマンド4）。
- `dummy_settings` は `monkeypatch.setenv` で3つのキーをダミー値にしてから `get_settings.cache_clear()` する。pydantic-settings では環境変数が `.env` より優先されるので、Windows の環境変数や `backend/.env` の本物のキーは使われない。`test_real_api_keys_are_replaced_with_dummies` で3つとも確認している。

### 4. 前回の抜け穴（名前解決・asyncio の接続）が塞がれているか → ○
- progress.md の記録: 最初の遮断は `socket.socket.connect` だけで、Windows の非同期通信（`getaddrinfo` での名前解決 → Proactor の `ConnectEx`）はそこを通らず、ダミーキー付きのリクエストが1回 api.typesafe.ai に届いた。
- 今の `conftest.py` は3か所を止めている:
  1. `socket.getaddrinfo`（名前解決。asyncio の `loop.getaddrinfo` も呼び出し時にこのモジュール属性を参照するので止まる）
  2. `socket.socket.connect`（同期の接続、SelectorEventLoop の接続）
  3. `BaseEventLoop.sock_connect` と `BaseProactorEventLoop.sock_connect`（Windows の ConnectEx 経路。IP 直指定で名前解決を通らない場合もここで止まる）
- `test_network_guard.py` で、名前解決（`api.typesafe.ai`）、同期接続、非同期 HTTP クライアント（ホスト名と IP 直指定の両方）、モック無しの Jev 呼び出しが止まることを確認している。モック無しの Jev が「認証エラー」ではなく「接続失敗」になるテストは、前回の事故（認証エラー＝TypeSafe に届いていた）の再発をまさに検出できる。
- 評価役の追加テスト（再実行コマンド5）でも、IP 直指定の `socket.create_connection`、SelectorEventLoop、同期 HTTP クライアント、モック無しの OpenAI と Anthropic が止まり、localhost は通ることを確認した。

### 5. アプリ本体のコードが変わっていないか → ○
`git diff 38cda67 8132d2d --stat -- backend/app` が空（再実行コマンド7）。

## 合否に影響しない指摘

1. **証拠 `secret-scan.log` のコマンドが `docs/safety.md` 3章と違う**: safety.md は `git diff --cached | grep ...`、証拠は `git diff -- backend | grep ...`。`git diff`（`--cached` なし）は、まだ `git add` していない新しいファイル（今回の `backend/tests/*` など）を含まないので、このコマンドではテストファイルを検査できていなかった可能性がある。また `backend` に絞っているので、progress.md・tasks.json・証拠も対象外。今回は評価役がコミット全体（`git show 8132d2d`）を検索して一致が無いことを確かめたので ○ にしたが、次からは safety.md のとおり `git add` の後に `git diff --cached` で検査し、そのコマンドを証拠に残すこと。
2. **計画と証拠のずれ**: progress.md の作業計画4には `pytest-offline.log`（通信禁止の確認テストを含むログ）を残すとあるが、`evals/evidence/T02/` に無い。遮断の確認テストは通常の `pytest.log` に含まれているので実害はないが、計画を変えたなら作業ログにそう書くこと。
3. **テストの抜け（次のタスクで補うとよい）**: スライド抽出の PDF 経路（`extract_from_pdf`）のテストが無い。jev_scorer で `Score` の `instructions` が観点名になっているかは確かめていない。どちらも T02 の合格条件（5件以上・既存機能に対応）には影響しない。
4. `test_jev_scorer.py` と `test_transcription.py` の偽クライアントは記録をクラス変数に持つ。フィクスチャで毎回リセットしているので今は問題ないが、並列実行（pytest-xdist 等）を入れるときは注意。

## `python evals/check_tasks.py` の出力（tasks.json 更新・本ファイル作成後）

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 3/13 タスク
```
