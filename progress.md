# progress.md — 途中経過と引き継ぎ

> AI はこのファイルに **追記** する（過去の記録は消さない）。
> セッションが切れても、別の AI に移っても、ここを読めば続きから再開できるように書く。

---

## 引き継ぎメモ（常に最新の状態に書き換える欄）
- **最終更新**: 2026-09-26
- **今の作業ブランチ**: `feature/contest-jev-questions`（土台: origin/feature/business-contest-rubric の b2dfe7f。upstream は未設定＝まだ push していない）
- **最後に終わったこと**: T07 合格（2回目の検品。`evals/evidence/T07/review.md`）
- **次にやること**: T08（Questions セットの保存・一覧・読み込み）
- **人間待ち**: なし（人間が T14 を確認して基準タグを更新済み: `harness-baseline` = f901d4b）
- **後続タスクへの申し送り**（T03 評価役の指摘より。該当タスクの作業計画に入れること）:
  - T05: Jev に渡す `Score` の `instructions` が観点名（または観点の内容）になっていることをテストで確かめる（採用された P2(b)）
  - T05: 型の `levels` を、Jev の `Score(criteria=...)` に名前を変えて渡す。`low_confidence` は必ず `confidence < LOW_CONFIDENCE_THRESHOLD` から計算する（型では確かめていない）
  - T07/T09: Claude が観点と違う順番で Question を返しても今はそのまま通る。API か画面で観点の順に並べ直すか決める（T04 評価役の指摘2）
  - T09: voice.md 2章「付け足した解釈は画面で人間に見せる」は、今の出力の型では解釈を区別できない。Question 確認画面（FR-3）で、観点の説明と Question を並べて見せるなどの方法を決める（T04 評価役の指摘1）
  - T07: 受け付ける音声・動画の拡張子を決め、動画（mp4 など）でも Whisper に渡るかテストする（T06 評価役の指摘2）
  - T07: `score_audio` に渡す一時ファイルの作成と削除は API 側の責任。エラーのときも一時ファイルが消えることをテストで確かめる（T06 評価役の指摘3）
  - T07: API で観点を受け取るとき、配点に `"20"`・`20.0`・`true` が通らないよう strict にするか決める（今の型は Pydantic の標準の検査なので受け付ける）
- **注意**:
  - 依存関係は作業ブランチの内容で入れ直し済み（typesafe-sdk 0.7.1 の import、`npm run build` の成功を確認）
  - バックエンドのテスト: `cd backend && .venv/Scripts/python -m pytest -q`（開発用の道具は `pip install -r requirements-dev.txt`）
  - `npm install` を実行すると、npm のバージョン差で `frontend/package-lock.json` の `libc` 行が消える。機能には関係ないので `git checkout -- frontend/package-lock.json` で戻す
  - APIキーの有無（値は見ていない）: `TYPESAFE_API_KEY` は Windows の環境変数で設定済み。`ANTHROPIC_API_KEY` は未設定（`backend/.env` がダミー値のまま）。`backend/.env` には `TYPESAFE_API_KEY` の行が無い（main の .env.example から作ったため）

---

## 作業計画（計画役が書く・タスクごとに上書き）
### T07 API: 観点→Questions、音声＋Questions→点数（AC-00a, AC-00c, AC-00d, AC-09）
1. `backend/app/routers/contest.py` を新規作成し、`main.py` に登録する
   - `POST /api/contest/questions`: JSON で観点（ContestRubric）を受け取り、`generate_questions` の結果（QuestionSet）を返す
   - `POST /api/contest/score`: multipart で `media_file`（音声/動画）と `question_set`（QuestionSet の JSON 文字列）を受け取り、`score_audio` の結果（ContestScoreResult）を返す
   - 入力の検査は自分で行い、形の誤りは **400 と日本語のエラー**にする（FastAPI 標準の 422・英語のエラーにしない。AC-09「不正な観点400」、NFR-3）。ファイルや question_set が無いときも 400
2. Pydantic の英語のエラーを日本語に直す小さな関数 `backend/app/utils/validation_messages.py`（どの観点のどの項目か＋何が悪いか。例:「観点2の配点: 1以上にしてください」）
3. 申し送りへの対応（ここで決めること）:
   - 配点は **厳密に整数だけ** 受け付ける（`"20"`・`20.0`・`true` は 400）。`contest.py` の `max_points` を strict にする（T03 の型に1か所追加）
   - Question の並び順: `generate_questions` が返す前に **観点の順に並べ直す**（T04 の指摘2）
   - 受け付ける音声・動画の拡張子は既存の審査と同じ（mp3/mp4/mpeg/mpga/m4a/wav/webm）。**mp4 のテスト** を入れる（T06 の指摘2）
   - 一時ファイル: 保存用の一時フォルダは成功でもエラーでも必ず消す。**エラーのときも消えるテスト** を入れる（T06 の指摘3）
4. `backend/tests/test_contest_api.py`（TestClient。Claude・Whisper・Jev は偽物）: 各 API の成功 200、不正な観点 400（日本語）、配点 "20" 400、壊れた JSON 400、キー未設定の日本語エラー、対応外の拡張子 400、question_set の観点と Question の食い違い 400、mp4、一時フォルダの後片付け（成功・エラー両方）
5. 証拠: `evals/evidence/T07/` に pytest.log、secret-scan.log、check_tasks.log（1行目は実行コマンドと同じ変数から）
- 変更予定ファイル: 新規 `routers/contest.py`・`utils/validation_messages.py`・テスト、`main.py`（登録1行）、`models/contest.py`（strict 1か所）、`services/question_builder.py`（並べ直し）
- 承認が必要な操作: なし（実 API は呼ばない）

---

## 要確認（人間に聞きたいこと）
- docs/requirements.md 5章の Q1〜Q6

---

## 提案（AI からの変更提案。人間が採用したら該当ファイルに反映する）
- **P5（2026-09-26、T05 評価役の指摘2より）**: Jev の score が 0〜4 から大きく外れた（例: 0.001 より大きくずれた）ときは、黙って収めずにログを残して 502 にする。わずかな誤差だけ収める。→ **採用（2026-09-26、人間「提案2つを採用します」）。T14 として tasks.json に追加**
- **P4（2026-09-26、T04 評価役の指摘3〜5より）**: (a) Claude の呼び出し中に SDK が例外を出した場合も 502 になることをテストで確かめる。(b) 段階が空のときのエラーの括弧内が英語（Pydantic 標準の文）になるので、日本語にする（NFR-3）。(c) 段階数のテストの入力を別々の文にする。どれも小さな変更。→ **採用（2026-09-26、人間「提案2つを採用します」）。T14 として tasks.json に追加**
- **P3（2026-09-26、T03 評価役の指摘1・5より）**: (a) AC-05 のテストを「エラーになるか」だけでなく「どの項目のエラーか」まで確かめるようにする（将来ほかの制約を足したとき、別の理由で通ってしまうのを防ぐ）。(b) 採点結果の `name` と `contest_name` も空文字を禁止する。どちらも小さな変更。→ **採用（2026-09-26、人間「提案の2つを採用します」）。T13 として tasks.json に追加**
- **P2（2026-09-26、T02 評価役の指摘3より）**: 今あるテストの抜けを、関係するタスクで補ってはどうか。(a) スライド抽出の PDF 経路のテスト、(b) Jev に渡す `Score` の `instructions` が観点名になっているかの確認。(b) は T05（Jev 採点）の作業計画に含めるのが自然。→ **採用（2026-09-26、人間「提案の2つを採用します」）。(a) は T13 に、(b) は T05 の申し送りに入れた**
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
- 計画からの変更: 計画にあった `pytest-offline.log` は作らなかった。遮断の確認テスト（test_network_guard.py）が通常の pytest.log に含まれるため（評価役の指摘2を受けて記録）
- 評価役の検品で **合格**（AC-00a/00c/00d/03/04 すべて○）。証拠: `evals/evidence/T02/review.md`。評価役はリポジトリの外で追加の遮断テスト8件（IP直指定、別のイベントループ、同期クライアント、モック無しの Whisper と Anthropic など）も実行し、すべて止まることを確認した
- 評価役の指摘1への対応: 秘密情報チェックが safety.md の手順（`--cached`）と違い、まだ追加していない新規ファイルが検査対象外だった可能性があった → コミット全体を safety.md のパターンで検査し直した（`secret-scan-commit.log`。一致は検索コマンド自身の1行だけ）

### 2026-09-26 T03 観点・Question・採点結果の型定義
- 追加: `backend/app/models/contest.py`（ContestCriterion / ContestRubric / JevScoreQuestion / QuestionSet / ContestCriterionResult / ContestScoreResult と定数）、`frontend/src/types/contest.ts`（同じ形）、`backend/tests/test_contest_models.py`（29テスト）。既存コードは変更なし
- 決めたこと: 観点の id は英数字・_・- の1〜40文字（Jev の questions の名前にそのまま使うため）。QuestionSet は「観点1つにつき Question 1つ」を型の段階で保証する（T04 で Claude の出力の抜け・余分を検出するのに使う）
- つまずき: テスト用の補助関数で `levels or 既定値` と書き、空のリスト（段階0個）が既定値にすり替わってテストが1件失敗した → `is None` で判定するよう直した
- `contest.ts` はまだどの画面からも使われていないが、型チェック（tsc）の対象に入っていることを確認した（build.log の末尾）
- 証拠: `evals/evidence/T03/`（pytest.log: 52 passed、build.log、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00b/00c/00d/05 すべて○）。評価役はリポジトリの外で型を直接試し、AC-05 の5ケースがそれぞれ正しい理由でエラーになることを確認した。backend と frontend の型が一致することも機械的に比較して確認
- 評価役の指摘のうち T05・T07 に関わるものは、引き継ぎメモの「後続タスクへの申し送り」に書いた。T03 自体の小さな改善は提案 P3 に書いた

### 2026-09-26 採用された提案の記録
- 人間「提案の2つを採用します」→ P2(b) は T05 の申し送りへ、P2(a)・P3 は新しいタスク T13 として tasks.json に追加（人間の決定による追加。基準タグの更新は人間待ち。それまで check_tasks は T13 について警告を出す）

### 2026-09-26 T04 観点 → Jev の Score Question を Claude で生成
- 追加: `backend/app/services/question_builder.py`（`generate_questions`）、`backend/tests/test_question_builder.py`（10テスト）
- 変更: `review_generator._call_claude` に `failure_detail` 引数を追加（既定値は今までと同じ文言なので、既存の審査機能の動きは変わらない）
- 決めたこと: Claude には単純な形（criterion_id / instructions / levels）で出力させ、T03 の `QuestionSet` で検査する。抜け・余分・重複・段階数の誤りは 502 と日本語のエラーにする（黙って直さない）
- 確認: Claude API の資料（claude-api スキル）で、structured outputs は文字数・範囲などの制約に対応しないことを確認した。SDK の実物（`anthropic.transform_schema`）で、出力の型が対応済みの機能だけのスキーマになることを確かめ、テストにした（`claude-output-schema.log`）
- モデルは既存設定の `claude-sonnet-5` のまま（資料の既定は claude-opus-5 だが、モデルを変えると費用と動きが変わるため、このタスクでは変えない）
- 証拠: `evals/evidence/T04/`（pytest.log: 62 passed、claude-output-schema.log、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00c/00d/06 すべて○）。評価役は SDK 1.8.0 のソースで「文字数・範囲などの制約はスキーマから外される」ことを確かめ、制約を付けた型ではスキーマのテストが落ちることも確認した
- 評価役の指摘のうち T07・T09 に関わるもの（Question の並び順、付け足した解釈の見せ方）は申し送りへ。小さな改善は提案 P4 へ

### 2026-09-26 T05 書き起こし＋Questions → Jev 採点 → 配点換算
- 追加: `backend/app/services/contest_scorer.py`（`score_transcript`・`to_points`・`build_jev_questions`）、`backend/tests/test_contest_scorer.py`（16テスト）
- 変更: `jev_scorer.py` から Jev の呼び出しと日本語エラーへの変換を `run_system_one` に切り出した（既存の `score_with_jev` はそれを使うだけ。既存テストはそのまま通る）
- 申し送りへの対応: `levels` を Jev の `criteria` に名前を変えて渡す／`low_confidence` は `confidence < 0.5` から計算（0.5 ちょうどは「低くない」）／`instructions` の先頭に「【観点】観点名」を入れた（採用された P2(b)）
- **つまずき**: 最初は Python の `round` で四捨五入したが、`round` は「ちょうど半分」を偶数の側に丸める（0.25 → 0.2）ため FR-6 の四捨五入と違った。ちょうど半分のテストを先に足して失敗を確かめてから、`Decimal` と `ROUND_HALF_UP` に直した。小数の誤差（0.3 ÷ 4 × 30 が 2.2499999… になる）も `Decimal(str(値))` で避けた
- テストの書き間違い: 「ちょうど半分」の例に 1.125 を使ったが、小数第1位で丸めるときは半分ではなかった（→ 1.1）。2.25 の例に差し替えた
- 結果は観点の順に並べる（Question が別の順でも）。Jev の答えが欠けた観点は 502、わずかな範囲外の score は範囲内に収める
- 証拠: `evals/evidence/T05/`（pytest.log: 78 passed、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00c/00d/07 すべて○）。評価役はリポジトリの外で `to_points` を229通り、合計を304通り、分数での正確な計算と比べて食い違い0件を確認。`run_system_one` の切り出し前後で `score_with_jev` の結果・エラーが10通りすべて同じことも確認
- 評価役の指摘: (1) 「モード不正かつキー無し」のときだけ 400 が ValueError に変わる（呼び出し元が先にモードを確かめるので、画面や API から見える動きは同じ）、(2) Jev の score が大きく範囲外でも黙って 0〜4 に収めてしまう（計画の「わずかなずれ」より広い）→ 提案 P5、(3) 証拠 pytest.log の1行目のコマンドに `PYTHONIOENCODING=utf-8` が抜けていた（実行したコマンドと違う。P1 違反）→ 学んだことへ、(4) `backend/tests/__pycache__/` に T02 で消した一時テストの .pyc が残っている（git 管理外・動作に影響なし）→ 人間の許可（2026-09-26「一時ファイルの残りかすを消してもよいです」）を得て削除した

### 2026-09-26 採用された提案 P4・P5 の記録と一時ファイルの削除
- 人間「提案2つを採用します」→ P4・P5 を新しいタスク T14 として tasks.json に追加（人間の決定による追加。基準タグの更新は人間待ち。それまで check_tasks は T14 について警告を出す）
- 人間「一時ファイルの残りかすを消してもよいです」→ `backend/tests/__pycache__/test_zz_tmp_unmocked.cpython-314-pytest-9.1.1.pyc`（T02 の一時テストの残り。対応する .py は無く、git 管理外）を削除した

### 2026-09-26 T06 音声 → 文字起こし → Jev の state
- 追加: `contest_scorer.score_audio`（Whisper の書き起こしを、そのまま `score_transcript` に渡す）、`backend/tests/test_contest_audio.py`（7テスト）
- 変更: `score_transcript` の入口で、空・空白だけの書き起こしを 400 と日本語のエラーにする（Jev は呼ばない）。音声からでも文字の直接入力からでも同じ検査がかかる
- 書き起こしの前後の空白も削らずにそのまま Jev に渡す（AC-08「そのまま入る」）。OPENAI_API_KEY が無いときは Whisper も Jev も呼ばずに止まる
- 証拠: `evals/evidence/T06/`（pytest.log: 85 passed、secret-scan.log、check_tasks.log）。ログの1行目は、実行するコマンドと同じ変数から書き出した
- 評価役の検品で **合格**（AC-00a/00c/00d/08 すべて○）。評価役はリポジトリの外のコピーでコードを7通り壊し（空判定を外す、Jev の前で strip する、transcribe を使わない など）、7通りとも既存のテストが失敗して検出することを確認した。1行目のコマンドも実際に使われたものと判断された（T05 の指摘は再発なし）
- 評価役の指摘のうち T07 に関わるもの（動画の拡張子、一時ファイルの後片付け）は申し送りへ。小さな指摘（空白付きのテストが結果の transcript までは見ていない）は記録のみ

### 2026-09-26 T07 API（観点→Questions、音声＋Questions→点数）
- 追加: `backend/app/routers/contest.py`（`POST /api/contest/questions`、`POST /api/contest/score`）、`backend/app/utils/validation_messages.py`（Pydantic の英語のエラーを「観点2の配点: 1以上にしてください」のような日本語に直す）、`backend/tests/test_contest_api.py`（19テスト）
- 変更: `main.py` に登録1行、`models/contest.py` の配点を strict に、`question_builder.py` で Question を観点の順に並べ直す
- 申し送りへの対応（決めたこと）:
  - 配点は厳密に整数だけ受け付ける（`"20"`・`20.0`・`true` は 400「整数で入力してください」）
  - Claude が別の順で返しても、Question は観点の順に並べ直して返す
  - 受け付ける拡張子は既存の審査と同じ（mp3/mp4/mpeg/mpga/m4a/wav/webm）。mp4 が Whisper まで届くテストあり
  - 一時フォルダは成功でもエラー（キー未設定・空の書き起こし）でも消える。テストあり
- 入力ミスは FastAPI 標準の 422（英語）ではなく、400 と日本語のエラーで返す。ファイルや Question が無いときも 400
- 証拠: `evals/evidence/T07/`（pytest.log: 104 passed、secret-scan.log、check_tasks.log）
- **評価役の判定: 不合格（AC-09 ×）**。記録: `evals/evidence/T07/review-1.md`。400 と日本語のエラーにならない経路が5つあった:
  1. /questions で配点に5000桁の整数 → 500（`json.loads` の `ValueError` を捕まえていない）
  2. /questions で20万段の入れ子の JSON → 500（`RecursionError`）
  3. /score の question_set で 2 と同じ → 500
  4. /score で media_file をファイルでなく文字列で送る → FastAPI 標準の 422（英語）
  5. /score で question_set をファイルのパートで送る（ブラウザで FormData に Blob を渡すと起きる）→ 422（英語。Starlette の内部オブジェクトの中身も入る）
- 修正方針: `parse_json` で `ValueError`・`RecursionError` も捕まえる／/score は `request.form()` から自分で取り出して検査する（文字列でもファイルのパートでも question_set を受け付ける。media_file が文字列・複数なら 400）／5つの経路と「早く止まる経路では一時フォルダを作らない」をテストに入れる
- 修正: 先に5つの経路のテストを書いて失敗を確かめてから直した（6件失敗 → 修正後すべて成功）。直している途中で、同じ種類の抜けをもう1つ自分で見つけた: 形の崩れた multipart を送ると 400 だが Starlette の英語の文（"Invalid multipart data."）が返る → 日本語に直してテストを追加
- 修正後: pytest 114 passed（`evals/evidence/T07/pytest.log` を作り直した）
- **再検品で合格**（AC-00a/00c/00d/09 すべて○）。評価役は修正前のコード（4451919）で新しいテスト8件が失敗することを確認し、さらに約50通りの異常な入力で英語のエラー・422・500 が0件であることを確かめた
- 再検品の小さな指摘（記録のみ。必要なら提案にする）: question_set を2つ送ると後ろが黙って使われる／終わりの区切りが無い multipart で案内の文言が原因と違う／question_set の上限超えの文言が送り方で違う／深い入れ子のテストが文言まで見ていない／`to_japanese` が知らない種類のエラーは「入力が正しくありません」だけになる

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
- T02（評価役の指摘）: 秘密情報チェックは、必ず `git add` した後に safety.md どおり `git diff --cached` で行う（`git diff` だけだと新規ファイルが漏れる）
- T03: テストの補助関数で `x or 既定値` と書くと、空のリストや 0 が既定値にすり替わる。「指定なし」は `is None` で判定する
- T07（評価役の指摘・不合格）: 「入力ミスは 400 と日本語」を作るときは、普通の入力ミスだけでなく、異常な入力（巨大な数、深い入れ子、ファイルの代わりに文字列、ブラウザ特有の送り方、壊れた multipart）も試す。FastAPI や Starlette が自動で返す英語のエラーの経路を1つずつ潰す
- T07: ヒアドキュメントの中の Python で `\r\n` を書くと、本物の改行になってファイルが壊れることがある。エスケープを含む行は Edit ツールで直接書く
- T05（評価役の指摘・P1 違反）: 証拠の1行目のコマンドから `PYTHONIOENCODING=utf-8` が抜けていた。証拠の1行目は、実行するコマンドと同じ文字列の変数から書き出す（手で書き写さない）
- T05: Python の `round()` は四捨五入ではない（ちょうど半分は偶数側へ: 0.25 → 0.2）。四捨五入が要件なら `Decimal` の `ROUND_HALF_UP` を使い、「ちょうど半分」のテストを入れる
- T02: Windows の非同期通信は `socket.connect` を通らない。通信を止めるときは名前解決（getaddrinfo）と asyncio の接続も止める
