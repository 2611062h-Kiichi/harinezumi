# progress.md — 途中経過と引き継ぎ

> AI はこのファイルに **追記** する（過去の記録は消さない）。
> セッションが切れても、別の AI に移っても、ここを読めば続きから再開できるように書く。

---

## 引き継ぎメモ（常に最新の状態に書き換える欄）
- **最終更新**: 2026-09-26
- **今の作業ブランチ**: `feature/contest-jev-questions`（土台: origin/feature/business-contest-rubric の b2dfe7f。upstream は未設定＝まだ push していない）
- **最後に終わったこと**: T03 合格（`evals/evidence/T03/review.md`）
- **次にやること**: T04（観点 → Jev の Score Question を Claude で生成）
- **後続タスクへの申し送り**（T03 評価役の指摘より。該当タスクの作業計画に入れること）:
  - T05: Jev に渡す `Score` の `instructions` が観点名（または観点の内容）になっていることをテストで確かめる（採用された P2(b)）
  - T05: 型の `levels` を、Jev の `Score(criteria=...)` に名前を変えて渡す。`low_confidence` は必ず `confidence < LOW_CONFIDENCE_THRESHOLD` から計算する（型では確かめていない）
  - T07: API で観点を受け取るとき、配点に `"20"`・`20.0`・`true` が通らないよう strict にするか決める（今の型は Pydantic の標準の検査なので受け付ける）
- **止まっていること / 人間待ち**: なし（基準タグ `harness-baseline` = 86bd2d7）
- **注意**:
  - 依存関係は作業ブランチの内容で入れ直し済み（typesafe-sdk 0.7.1 の import、`npm run build` の成功を確認）
  - バックエンドのテスト: `cd backend && .venv/Scripts/python -m pytest -q`（開発用の道具は `pip install -r requirements-dev.txt`）
  - `npm install` を実行すると、npm のバージョン差で `frontend/package-lock.json` の `libc` 行が消える。機能には関係ないので `git checkout -- frontend/package-lock.json` で戻す
  - APIキーの有無（値は見ていない）: `TYPESAFE_API_KEY` は Windows の環境変数で設定済み。`ANTHROPIC_API_KEY` は未設定（`backend/.env` がダミー値のまま）。`backend/.env` には `TYPESAFE_API_KEY` の行が無い（main の .env.example から作ったため）

---

## 作業計画（計画役が書く・タスクごとに上書き）
### T03 観点・Question・採点結果の型定義（AC-00a, AC-00b, AC-00c, AC-00d, AC-05）
1. `backend/app/models/contest.py` を新規作成（既存の schemas.py は触らない）。Pydantic の型:
   - `ContestCriterion`: id（英数字・_・- の1〜40文字）、name（必須・前後の空白は除去・1〜100文字）、description（任意・〜1000文字）、max_points（1〜100 の整数）
   - `ContestRubric`: contest_name（1〜100文字）、criteria（1〜15個、id の重複禁止）
   - `JevScoreQuestion`: criterion_id、instructions（必須）、levels（ちょうど5個・低い順・空の段階は禁止）
   - `QuestionSet`: rubric + questions。観点1つにつき Question 1つ（抜け・余分・重複・知らない id を禁止）
   - `ContestCriterionResult`: criterion_id、name、max_points、jev_score（0〜4）、points（0〜配点）、confidence（0〜1）、low_confidence
   - `ContestScoreResult`: contest_name、results、total_points、max_total_points、transcript、generated_at
   - 定数: 段階数 5、観点の上限 15、確信度のしきい値 0.5（requirements.md FR-1/2/7 の値）
   - 自作の検査のエラーメッセージは日本語にする
2. `frontend/src/types/contest.ts` に同じ形の TypeScript の型を書く
3. `backend/tests/test_contest_models.py`: 正しい入力が通ること＋AC-05 の各ケース（配点0、名前が空、観点16個、段階が5個でない、ID重複）と Question の抜け・余分がエラーになること
4. 証拠: `evals/evidence/T03/` に pytest.log、build.log、secret-scan.log（`git add` 後に `git diff --cached`）、check_tasks.log（すべて1行目に実行コマンド）
- 変更予定ファイル: 上の2つの新規ファイルとテスト（既存コードは変えない）
- 承認が必要な操作: なし

---

## 要確認（人間に聞きたいこと）
- docs/requirements.md 5章の Q1〜Q6

---

## 提案（AI からの変更提案。人間が採用したら該当ファイルに反映する）
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
