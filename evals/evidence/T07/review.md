# T07 評価（評価役・2回目の検品）

- 対象: T07「API を追加する: POST /api/contest/questions（観点→Questions）、POST /api/contest/score（音声＋Questions→点数）。TestClient でテストする」
- 変更: 元の実装 4451919、1回目の不合格（`review-1.md`）を受けた修正 9183c83・e88b2f9
- 評価日: 2026-09-26
- **判定: 合格**（全条件 ○）→ tasks.json の T07 を `"status": "done", "passes": true` にした

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | 証拠 `pytest.log` の1行目のコマンドをそのまま再実行して 114 passed。テストごとの PASSED 行（114行）が証拠と完全に一致 |
| AC-00c 秘密情報が含まれていない | ○ | 修正コミットの差分に同じ grep をかけ、一致は3行とも review-1.md に書かれた grep コマンドの文字列だけ（注記どおり）。キーの値は無い |
| AC-00d tasks.json のルール違反がない | ○ | `python evals/check_tasks.py` がエラー0件・警告0件（検品前、および本ファイル作成後） |
| AC-09 API が仕様どおりに応答する | ○ | 成功200・不正な観点400（日本語）・キー未設定の日本語エラーをテストと自分の確認の両方で確認。review-1.md の5経路と実行役が見つけた6つ目の経路はすべて 400＋日本語になり、それぞれテストがあり、そのテストは修正前のコードで失敗する。新たに約50通りの異常な入力を試し、英語のエラー・422・500 になる経路は見つからなかった |

参照した資料: `docs/roles.md` 3章、`evals/acceptance.md`、`tasks.json`（T07）、`docs/requirements.md` 4章（FR-1・FR-9、NFR-3・NFR-4）、`evals/evidence/T07/`（pytest.log・secret-scan.log・check_tasks.log・review-1.md）、`progress.md` 作業ログ T07、`git show 9183c83`・`git show e88b2f9`、`backend/app/routers/contest.py`、`backend/app/utils/validation_messages.py`、`backend/tests/test_contest_api.py`、`backend/tests/conftest.py`、Starlette 1.7.0 の `requests.py`・`formparsers.py`

---

## 自分で再実行したコマンドと結果

### AC-00a（証拠 `pytest.log` の1行目をそのまま実行）
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
...
============================= 114 passed in 3.75s =============================
```
- 証拠は `114 passed in 3.88s`。件数一致。`tests/... PASSED` の行を（進み具合の `[ nn%]` を除いて）証拠と `diff` して差分なし。同じテストが同じ結果
- T03（`test_contest_models.py`）・T04（`test_question_builder.py`）・既存の審査のテストもすべて PASSED（修正で壊れていない）
- 実行の前後でリポジトリ内のファイル一覧（.venv・node_modules・.git を除く）を比べ、新しいファイルは無し（`__pycache__` も増えていない）

### AC-00c
```
$ git diff 4451919 9183c83 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
418:+$ git show 4451919 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
419:+587:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
420:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
503: $ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
505:+418:+$ git show 4451919 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
506:+419:+587:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
507:+420:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
$ git diff 9183c83 e88b2f9 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
5:@@ -2,3 +2,4 @@ $ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]
6: 418:+$ git show 4451919 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
7: 419:+587:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
8: 420:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
```
- 418〜420行目の3行（secret-scan.log に書かれた一致3行と同じ）は、`git diff 4451919 9183c83 | sed -n '405,422p'` で前後を見ると、review-1.md の「### AC-00c」の中のコードブロック（1回目の評価役が実行した grep コマンドとその出力）だった。**注記「検査コマンドそのもの」は正しい**
- 503〜507行目、e88b2f9 の差分の一致は、secret-scan.log 自身の中身（grep コマンドと上の一致行の写し）。どれもキーの値ではない
- 作業ツリーに未コミットの変更は無い（`git status --short` が空。検品前）。backend/.env は読んでいない

### AC-00d
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 7/15 タスク
```
（検品前。変更後の出力は末尾）

### AC-09 (1) 新しいテストが修正前のコードで失敗すること（リポジトリの外のコピー）
```
$ git archive 4451919 backend | tar -x -C <scratchpad>/old
$ cp backend/tests/test_contest_api.py <scratchpad>/old/backend/tests/
$ cd <scratchpad>/old/backend && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 <repo>/backend/.venv/Scripts/python -m pytest -p no:cacheprovider -q tests/test_contest_api.py
FAILED tests/test_contest_api.py::test_huge_integer_points_is_400 - ValueErro...
FAILED tests/test_contest_api.py::test_deeply_nested_rubric_json_is_400 - Rec...
FAILED tests/test_contest_api.py::test_deeply_nested_question_set_is_400 - Re...
FAILED tests/test_contest_api.py::test_media_file_sent_as_text_is_400_in_japanese
FAILED tests/test_contest_api.py::test_question_set_sent_as_file_part_is_accepted
FAILED tests/test_contest_api.py::test_two_media_files_are_400 - assert 200 =...
FAILED tests/test_contest_api.py::test_broken_multipart_body_is_400_in_japanese[multipart/form-data; boundary=xyz-garbage without boundary]
FAILED tests/test_contest_api.py::test_broken_multipart_body_is_400_in_japanese[multipart/form-data---x\r\n]
8 failed, 21 passed in 3.82s
```
- コピーの `app` が読まれていることを `app.routers.contest.__file__` で確認（scratchpad/old/backend/app/routers/contest.py）。コピーは確認後に削除
- 経路とテストの対応:

| # | 経路 | テスト | 修正前 | 修正後 |
|---|---|---|---|---|
| NG-1 | 配点に 5000 桁の整数 | `test_huge_integer_points_is_400` | 失敗（ValueError→500） | 400「採点観点をJSONとして読み取れませんでした。」 |
| NG-2 | /questions に20万段の入れ子 | `test_deeply_nested_rubric_json_is_400` | 失敗（RecursionError） | 400 同上 |
| NG-3 | question_set に同じ入れ子 | `test_deeply_nested_question_set_is_400` | 失敗（RecursionError） | 400「QuestionをJSONとして読み取れませんでした。」 |
| NG-4 | media_file を文字列で送る | `test_media_file_sent_as_text_is_400_in_japanese` | 失敗（422） | 400「発表の音声または動画ファイルを指定してください。」 |
| NG-5 | question_set をファイルのパートで送る | `test_question_set_sent_as_file_part_is_accepted` | 失敗（422） | 200（受け付ける） |
| 6つ目 | 形の崩れた multipart | `test_broken_multipart_body_is_400_in_japanese`（2通り） | 失敗（英語 "Invalid multipart data." 等） | 400「送信データの形が正しくありません。画面からもう一度送信してください。」 |
| 追加 | media_file が2つ | `test_two_media_files_are_400` | 失敗（200） | 400「…1つだけ指定してください。」 |

- `test_no_temp_dir_is_created_when_input_is_rejected`（2通り）は修正前でも通る（修正前も検査の後に一時フォルダを作っていたため）。後戻りを防ぐテストとして妥当

### AC-09 (2) 異常な入力の確認（リポジトリの外の確認スクリプト）
```
$ PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 "$B/.venv/Scripts/python" "$S/probe_t07_2.py" "$B" "$(cygpath -w "$S/tmp")"
```
（`$B` = backend の絶対パス、`$S` = scratchpad。スクリプトと一時フォルダは確認後に削除）
- conftest 相当の準備: ダミーのキーを環境変数に入れて `get_settings` のキャッシュを消す、作業フォルダを scratchpad の一時フォルダに移して `backend/.env` を読ませない、`socket.getaddrinfo`・`socket.socket.connect`・asyncio の `sock_connect` でローカル以外への通信を遮断、`TMP`/`TEMP`/`tempfile.tempdir` も scratchpad に向ける
- Claude（`AsyncAnthropic`）・Whisper（`AsyncOpenAI`）・Jev（`AsyncTypeSafeClient`）はテストの偽物に差し替え。実 API は呼んでいない
- `TestClient(app, raise_server_exceptions=False)` で 500 も応答として受け取る。各応答について「200、または 400 かつ detail が日本語で英語の定型文（Invalid / Expected / Field / Missing / Too many / exceeded / Input should / Internal Server Error）を含まない」こと、本文にダミーのキー値・一時フォルダのパス・backend のパス・`C:\`・`Users`・`Traceback` が無いこと、記録版 `mkdtemp` で作った一時フォルダが残っていないことを確かめた。**全件 OK（NG は0件）**

| 分類 | 入力 | 結果 |
|---|---|---|
| 基本 | 正しい観点 / 正しい音声＋Question | 200 / 200（一時フォルダ 作成1・残り0） |
| 1回目の経路 | NG-1〜NG-6（上の表）、NG-3 をファイルのパートで送る形 | すべて 400＋日本語（NG-5 は 200） |
| question_set | ファイルのパート 5MB / 1MB+1 バイト | 400「Questionのデータが大きすぎます。」 |
| | 文字列のパート 2MB | 400「送信データの形が正しくありません。…」（Starlette のパート上限 1MB） |
| | ファイルのパートに UTF-8 でないバイト列 / 文字列のパートに UTF-8 でないバイト列 | 400「QuestionをJSONとして読み取れませんでした。」 |
| | ファイルのパートが空 | 400「採点に使うQuestionを指定してください。」 |
| | UTF-16 の JSON（ファイルのパート） | 200（json が自動判別） |
| | 孤立したサロゲート `\ud800`、5000 桁の配点 | 400、日本語 |
| | question_set が2つ | 200（後ろのものが使われる。下の指摘1） |
| media_file | ファイル名が空 `filename=""` / `.mp3` だけ / NUL 入り | 400「対応していないファイル形式です（…）。」 |
| | filename 無し（文字列のパート）/ ファイルと文字列が同名で2つ | 400「発表の音声…を指定してください。」/「1つだけ指定してください。」 |
| | ファイル名が UTF-8 でないバイト列 / `../../x.mp3` | 200（保存名は拡張子だけを使うので問題なし） |
| | 26MB | 400「ファイルサイズが大きすぎます（上限 25MB）。」 |
| multipart の形 | 文字列のフィールド 1001 個 / ファイルのパート 1001 個（上限 1000） | 400「送信データの形が正しくありません。…」 |
| | Content-Disposition 無し / name 無し / コロンの無いヘッダ行 / 2MB のヘッダ | 400 同上 |
| | 空の boundary / 200 文字の boundary / 存在しない charset | 200 |
| | 終わりの区切りが無い本文 / 本文が空 | 400「採点に使うQuestionを…」/「発表の音声…」（下の指摘2） |
| | urlencoded の壊れた `%` / 1001 フィールド / 2MB のフィールド | 400、日本語 |
| | multipart/mixed / JSON 本文 | 400「発表の音声…を指定してください。」 |
| /questions | 孤立したサロゲート（コンテスト名・説明） | 400「…コンテスト名: 入力が正しくありません」等 |
| | UTF-16 本文 / BOM 付き UTF-8 / 余分な項目 | 200 |
| | criteria が辞書 / `NaN` / 900 段の入れ子 / 文字列の項目に5000段の入れ子 / multipart 本文 | 400、日本語 |
| キー未設定 | ANTHROPIC（/questions）/ OPENAI・TYPESAFE（/score） | 400「〜_API_KEYが設定されていません。」。/score のエラー時も一時フォルダ 作成1・残り0 |
| 既存 API | /api/health、/api/review（不正なモード・何も無し）、/api/reviews/history | 200 / 400「不明な審査モードです: nope」/ 400（日本語）/ 200。壊れていない |

- **1回目で問題なしとされた点の再確認**
  - 一時フォルダの後片付け: 上のとおり全経路で残り0。さらに、`request.form()` に変えたことで FastAPI の自動の後片付けを通らなくなったため、アップロードの一時ファイル（Starlette の SpooledTemporaryFile。1MB を超えるとディスクに書く）が残らないかも確認した。3MB の送信を成功・拡張子エラーで3回ずつ行い、`TMP` の新しい項目は **直後も gc 後も 0**
  - 漏れてはいけない情報: 全応答でダミーのキー・パス・`Traceback` 無し。Starlette の内部オブジェクトの中身（1回目の NG-5）も出なくなった
  - 既存の審査 API・T03・T04 のテスト: 上のとおり壊れていない
- 実行の前後でリポジトリ内のファイル一覧を比べ、新しいファイルは無し（`__pycache__` を含む）。`git status --short` も tasks.json と本ファイル以外の変更なし

---

## 合否に影響しない指摘（記録のみ）
1. `question_set` を2つ送ると、黙って後ろのものが使われる（`form.get` の動き）。`media_file` は2つで 400 にしているので、揃えるなら question_set も 400 にしてよい
2. 終わりの区切りが無い multipart は Starlette が途中まで読んで止まるため、「送信データの形が正しくありません」ではなく「採点に使うQuestionを指定してください。」になる（400・日本語なので AC は満たす。原因と違う案内になるだけ）
3. `question_set` の文字列のパートが 1MB を超えると「送信データの形が正しくありません」になり、ファイルのパートの「Questionのデータが大きすぎます。」と文言が揃っていない
4. `test_deeply_nested_rubric_json_is_400` と `test_deeply_nested_question_set_is_400` は状態コード 400 だけを確かめ、日本語の detail までは見ていない（自分の確認では日本語）
5. 孤立したサロゲートなど、`to_japanese` が知らない種類のエラーは「入力が正しくありません」になり、どう直せばよいかまでは分からない（NFR-3 の「次に何をすればいいか」としては弱いが、どの項目かは出る）

---

## `python evals/check_tasks.py` の出力（tasks.json 変更・本ファイル作成後）
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 8/15 タスク
```
