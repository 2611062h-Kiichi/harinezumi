# progress.md — 途中経過と引き継ぎ

> AI はこのファイルに **追記** する（過去の記録は消さない）。
> セッションが切れても、別の AI に移っても、ここを読めば続きから再開できるように書く。

---

## 引き継ぎメモ（常に最新の状態に書き換える欄）
- **最終更新**: 2026-09-26
- **今の作業ブランチ**: `feature/contest-jev-questions`（土台: origin/feature/business-contest-rubric の b2dfe7f。upstream は未設定＝まだ push していない）
- **最後に終わったこと**: T04 合格（`evals/evidence/T04/review.md`）
- **次にやること**: T05（文字起こしテキストと Questions で Jev 採点・配点換算）
- **人間待ち**: T13 を追加したので、確認後に `git tag -f harness-baseline`
- **後続タスクへの申し送り**（T03 評価役の指摘より。該当タスクの作業計画に入れること）:
  - T05: Jev に渡す `Score` の `instructions` が観点名（または観点の内容）になっていることをテストで確かめる（採用された P2(b)）
  - T05: 型の `levels` を、Jev の `Score(criteria=...)` に名前を変えて渡す。`low_confidence` は必ず `confidence < LOW_CONFIDENCE_THRESHOLD` から計算する（型では確かめていない）
  - T07/T09: Claude が観点と違う順番で Question を返しても今はそのまま通る。API か画面で観点の順に並べ直すか決める（T04 評価役の指摘2）
  - T09: voice.md 2章「付け足した解釈は画面で人間に見せる」は、今の出力の型では解釈を区別できない。Question 確認画面（FR-3）で、観点の説明と Question を並べて見せるなどの方法を決める（T04 評価役の指摘1）
  - T07: API で観点を受け取るとき、配点に `"20"`・`20.0`・`true` が通らないよう strict にするか決める（今の型は Pydantic の標準の検査なので受け付ける）
- **止まっていること / 人間待ち**: なし（基準タグ `harness-baseline` = 86bd2d7）
- **注意**:
  - 依存関係は作業ブランチの内容で入れ直し済み（typesafe-sdk 0.7.1 の import、`npm run build` の成功を確認）
  - バックエンドのテスト: `cd backend && .venv/Scripts/python -m pytest -q`（開発用の道具は `pip install -r requirements-dev.txt`）
  - `npm install` を実行すると、npm のバージョン差で `frontend/package-lock.json` の `libc` 行が消える。機能には関係ないので `git checkout -- frontend/package-lock.json` で戻す
  - APIキーの有無（値は見ていない）: `TYPESAFE_API_KEY` は Windows の環境変数で設定済み。`ANTHROPIC_API_KEY` は未設定（`backend/.env` がダミー値のまま）。`backend/.env` には `TYPESAFE_API_KEY` の行が無い（main の .env.example から作ったため）

---

## 作業計画（計画役が書く・タスクごとに上書き）
### T04 観点 → Jev の Score Question を Claude で生成（AC-00a, AC-00c, AC-00d, AC-06）
1. `backend/app/services/question_builder.py` を新規作成: `generate_questions(rubric: ContestRubric) -> QuestionSet`
   - Claude の呼び出しは既存の `review_generator._call_claude`（`messages.parse` ＋ Pydantic、エラーを日本語に変換済み）を使う。失敗時の文言が「AIレビュー」固定なので、引数で差し替えられるようにする（既定値は今のまま＝既存の動きは変わらない）
   - モデルは既存の設定 `claude_model`（claude-sonnet-5）をそのまま使う
   - Claude に求める出力の型は単純な形（criterion_id / instructions / levels の一覧）にする。SDK は API が対応しない制約（文字数など）を自動で外すため、細かい検査は T03 の `QuestionSet` で行う
   - Claude の出力を `QuestionSet` に通し、抜け・余分・重複・段階数の誤りがあれば 502 と日本語のエラーにする（黙って直さない）
   - プロンプトは docs/voice.md 2章に従う（1つの観点だけを聞く、低い順、観察できる事実で書く、主催者の観点の意味を変えない）
   - ANTHROPIC_API_KEY が無ければ 400（Claude を呼ばない）
2. `backend/tests/test_question_builder.py`（Claude は偽物）: 成功、プロンプトに観点の id・名前・説明・配点が入る、Question の抜け→エラー、余分→エラー、段階が5個でない→エラー、Claude が形の合わない出力を返した（parsed_output が None）→エラー、キー無し→400 で呼び出しなし
3. 証拠: `evals/evidence/T04/` に pytest.log、secret-scan.log（`git add` 後に `--cached`）、check_tasks.log
- 変更予定ファイル: 新規 `question_builder.py`・テスト、`review_generator.py`（`_call_claude` に引数を1つ追加するだけ）
- 承認が必要な操作: なし（実 API は呼ばない）

---

## 要確認（人間に聞きたいこと）
- docs/requirements.md 5章の Q1〜Q6

---

## 提案（AI からの変更提案。人間が採用したら該当ファイルに反映する）
- **P4（2026-09-26、T04 評価役の指摘3〜5より）**: (a) Claude の呼び出し中に SDK が例外を出した場合も 502 になることをテストで確かめる。(b) 段階が空のときのエラーの括弧内が英語（Pydantic 標準の文）になるので、日本語にする（NFR-3）。(c) 段階数のテストの入力を別々の文にする。どれも小さな変更。（未採用）
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
- T02: Windows の非同期通信は `socket.connect` を通らない。通信を止めるときは名前解決（getaddrinfo）と asyncio の接続も止める
