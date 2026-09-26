# T07 評価（評価役）

- 対象: T07「API を追加する: POST /api/contest/questions（観点→Questions）、POST /api/contest/score（音声＋Questions→点数）。TestClient でテストする」
- 変更: コミット 4451919
- 評価日: 2026-09-26
- **判定: 不合格**（AC-09 が ×）→ tasks.json の T07 を `"status": "in_progress", "passes": false` にした

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | 証拠の1行目のコマンドを再実行して 104 passed。テストごとの PASSED 行も証拠 `pytest.log` と完全に一致 |
| AC-00c 秘密情報が含まれていない | ○ | コミット 4451919 の差分に同じ grep をかけて、一致は `secret-scan.log` 内に書かれたコマンド文字列そのもの（587行目）だけ。キーの値は無い。`.env` はコミットに含まれない |
| AC-00d tasks.json のルール違反がない | ○ | `python evals/check_tasks.py` がエラー0件・警告0件（検品前・変更後とも） |
| AC-09 API が仕様どおりに応答する | **×** | 成功200・キー未設定の日本語エラー・通常の入力ミスの400はテストと自分の確認の両方で OK。しかし **不正な観点・不正な入力で 400（日本語）にならず、500 や 422（英語）が返る経路が 5 つある**（下記） |

---

## 自分で再実行したコマンドと結果

### AC-00a（証拠 `pytest.log` の1行目をそのまま実行）
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
...
============================= 104 passed in 3.65s =============================
```
- 証拠は `104 passed in 3.72s`。件数一致。さらに `-p no:cacheprovider` を付けてもう一度流し、`tests/... PASSED` の行を証拠と `diff` して差分なし（同じテストが同じ結果）
- T03（`test_contest_models.py`）・T04（`test_question_builder.py`）のテストは、`max_points` の strict 化と Question の並べ直しの後もすべて PASSED

### AC-00c
```
$ git show 4451919 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
587:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（出力なし）
```
- 587行目は証拠ファイルに書かれた grep コマンド自身で、秘密情報ではない

### AC-00d
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 7/15 タスク
```

### AC-09（リポジトリの外の確認スクリプト）
- スクラッチ用フォルダに確認スクリプトを置き、`PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 backend/.venv/Scripts/python <scratchpad>/probe_t07.py <backend の絶対パス>` で実行
- conftest 相当: ダミーのキーを環境変数に入れて `get_settings` のキャッシュを消す、作業フォルダを一時フォルダに移して `backend/.env` を読ませない、`socket.getaddrinfo`・`socket.connect`・asyncio の `sock_connect` でローカル以外への通信を遮断
- Claude（`AsyncAnthropic`）・Whisper（`AsyncOpenAI`）・Jev（`AsyncTypeSafeClient`）はすべて偽物に差し替え。実 API は一度も呼んでいない
- 実行の前後でリポジトリ内のファイル一覧（.venv・node_modules・.git を除く）を比較し、**新しいファイルは無し**（`__pycache__` も増えていない）

#### うまく動いたもの（抜粋）
| 入力 | 結果 |
|---|---|
| 正しい観点（JSON） | 200。Claude が逆順で返しても `problem, market` の観点の順 |
| content-type が text/plain・無し（中身は正しい JSON） | 200（受け付ける） |
| form-urlencoded・multipart・本文が空・UTF-8でないバイト列 | 400「採点観点をJSONとして読み取れませんでした。」 |
| JSON が配列・文字列・null・数値 | 400「採点観点に誤りがあります。入力の形が正しくありません」 |
| 配点 NaN・1e400・null・[1]・"20"・20.0・true | 400「観点1の配点: 整数で入力してください」 |
| 配点 4000 桁の整数 | 400「観点1の配点: 100以下にしてください」 |
| 観点16個 / 0個 / 無し | 400「観点: 15個以内にしてください」/「1個以上にしてください」/「入力してください」 |
| 説明 100万文字・コンテスト名101文字・日本語の ID | 400、どの項目か＋直し方が日本語で出る |
| ANTHROPIC / OPENAI / TYPESAFE のキー未設定 | 400「〜_API_KEYが設定されていません。」 |
| /score: question_set が配列・文字列・null・rubric だけ・段階4個・配点 "20"・空白だけ・空・無し | 400、日本語 |
| /score: ファイル無し・JSON 本文・本文無し・urlencoded | 400「発表の音声または動画ファイルを指定してください。」 |
| /score: 拡張子なし・.txt・26MB | 400、日本語 |
| /score: `P.MP4`（大文字）・空ファイル・`../../evil.mp3` | 200 |
| 既存 API: /api/health、/api/review（不正なモード・何も無し）、/api/reviews/history | 200 / 400（日本語）/ 400（日本語）/ 200。壊れていない |

#### 一時フォルダ
`tempfile.mkdtemp` を記録版に差し替えて、作られたフォルダが残っていないか毎回確認した。**すべての経路で残り0**。
- 作る前に止まる経路（拡張子エラー、Question の食い違い、question_set の形の誤り、26MB、ファイル無し 等）: 作成0・残り0
- 作った後に止まる経路（成功、空の書き起こし、OPENAI/TYPESAFE キー未設定、Jev が観点を返さない 502、Whisper が想定外の例外を出す 500）: 作成1・残り0

#### 秘密情報・内部情報
- すべての応答本文に、ダミーのキー値・一時フォルダのパス・backend のパス・`C:\`・`Users`・`Traceback` が含まれないことを確認（Whisper の例外メッセージにキーとパスを混ぜた場合も、応答は `Internal Server Error` だけ）。
- ただし下記 NG-5 の 422 は、Starlette の内部オブジェクトの中身（`_max_size`、`_TemporaryFileArgs` など）をそのまま返す。キーやパスは含まれないが、利用者に見せるべきでない内部情報

---

## 不合格の理由（直すべき点）

AC-09「不正な観点 400」と、作業計画 1（「形の誤りは 400 と日本語のエラーにする。FastAPI 標準の 422・英語のエラーにしない」）・NFR-3 に反する経路が 5 つある。どれも TestClient で再現できる。

| # | API | 入力 | 実際の応答 | 原因 |
|---|---|---|---|---|
| NG-1 | /questions | 配点に **5000 桁** の整数（`"max_points": 999…9`） | **500** `Internal Server Error`（英語） | Python の `json.loads` が 4300 桁を超える整数で `ValueError` を出す。`parse_json` は `JSONDecodeError`・`UnicodeDecodeError` しか捕まえていない |
| NG-2 | /questions | 深い入れ子の JSON（`[` × 20万） | **500** `Internal Server Error` | `json.loads` の `RecursionError` を捕まえていない |
| NG-3 | /score | question_set に NG-2 と同じ入れ子 | **500** | NG-2 と同じ |
| NG-4 | /score | `media_file` をファイルではなく文字列のフィールドで送る | **422**（英語）`Expected UploadFile, received: <class 'str'>` | 引数を FastAPI の `File(None)` で受けているため、型が違うと router の検査より前に FastAPI が 422 を返す |
| NG-5 | /score | `question_set` を **ファイルのパート**で送る（ブラウザで `FormData.append("question_set", new Blob([json], {type: "application/json"}))` とすると起きる） | **422**（英語）`Input should be a valid string`＋内部オブジェクトの中身 | NG-4 と同じ（`Form(None)` の str に UploadFile が来る） |

- NG-1〜3 は「巨大な値・壊れた JSON」として普通に起こりうる不正な観点で、AC-09 の「不正な観点 400」に直接反する。NG-5 は画面（T09）の作り方しだいで実際に起きる形で、英語の 422 がそのまま利用者に出る
- テスト（`test_contest_api.py`）はこれらの経路を確かめていない
- 直し方の例（評価役はコードを直さない。参考）:
  - `parse_json` で `json.loads` の `ValueError`（`JSONDecodeError`・`UnicodeDecodeError` を含む）と `RecursionError` も捕まえて、400「〜をJSONとして読み取れませんでした。」にする
  - /score は `File`/`Form` の引数をやめて `request.form()` から自分で取り出し、`media_file` が UploadFile でない・`question_set` が str でない場合も 400 と日本語にする（または contest の router だけに効く形で 422 を 400 に変換する）
  - 上の 5 経路をテストに加える

## 合否に影響しない指摘（記録のみ）
1. 同じ名前の `media_file` を2つ送ると、最後のもの（`b.txt`）だけが見られる（400 拡張子エラー）。害は無いが、1つだけに限る検査は無い
2. 405（GET で呼んだ等）は FastAPI 標準の英語 `Method Not Allowed`。利用者の入力ミスではないので対象外とした
3. 申し送り（配点の strict、Question の並び順、mp4 のテスト、一時フォルダの後片付けのテスト）はすべて対応済みで、テストもある。ただしエラー時の後片付けテストは「キー未設定」「空の書き起こし」だけで、拡張子エラーなど一時フォルダを作る前に止まる経路の「作らない」ことはテストしていない（自分の確認では作られていない）
4. 役割表（docs/roles.md 3章）では不合格理由を progress.md にも書くことになっているが、今回の依頼で変更を許されたのは tasks.json と本ファイルだけのため、progress.md は変更していない。メインのセッションで progress.md に転記すること

---

## `python evals/check_tasks.py` の出力（tasks.json 変更後）
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 7/15 タスク
```
