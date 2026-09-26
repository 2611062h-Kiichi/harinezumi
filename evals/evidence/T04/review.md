# T04 検品記録（評価役）

- 対象: T04「観点から Jev の Score Question を Claude で生成するサービス（question_builder.py）を作り、モック Claude でテストする」
- 対象の変更: コミット 34853f8（`question_builder.py` 新規、`test_question_builder.py` 新規、`review_generator.py` の `_call_claude` に引数追加、証拠4点、progress.md、tasks.json）
- 読んだもの: `docs/roles.md` 3章、`evals/acceptance.md`、`tasks.json` の T04、`evals/evidence/T04/` の全ログ、`git show 34853f8`、`backend/tests/conftest.py`、`backend/app/models/contest.py`、`docs/requirements.md` 4章 FR-2、`docs/voice.md` 2章、SDK の `anthropic.transform_schema` のソース
- 実 API（Anthropic / OpenAI / TypeSafe）は呼んでいない。確認用スクリプトはリポジトリ外のスクラッチ用フォルダに置いた。`backend/.env` は読んでいない

## 判定: 合格（全条件 ○）

| 条件 | 判定 | 根拠 |
|---|---|---|
| AC-00a テストが全部通る | ○ | 自分で再実行して 62 passed。証拠 `pytest.log` とテスト名・結果が完全に一致 |
| AC-00c 秘密情報なし | ○ | コミット全体に safety.md 3章の検索をかけ、一致は証拠ログに書かれた検索コマンド自身の1行だけ。`.env` 等のファイルは含まれない |
| AC-00d check_tasks エラー0件 | ○ | 末尾の出力のとおりエラー 0 件。警告は T13（人間の決定で追加、基準タグ更新待ち）の既知のもののみ |
| AC-06 観点→Question 生成 | ○ | 下記のとおり。抜け・余分・重複・段階数の誤り・形に合わない出力がそれぞれ正しい理由で 502 になることを、テストの中身と独自の確認の両方で確かめた |

---

## 再実行したコマンドと結果

### 1. pytest（AC-00a, AC-06）
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
...
tests/test_question_builder.py::test_returns_one_question_per_criterion PASSED
tests/test_question_builder.py::test_sends_every_criterion_to_claude PASSED
tests/test_question_builder.py::test_missing_question_is_rejected PASSED
tests/test_question_builder.py::test_extra_question_is_rejected PASSED
tests/test_question_builder.py::test_duplicate_question_is_rejected PASSED
tests/test_question_builder.py::test_wrong_level_count_is_rejected[4] PASSED
tests/test_question_builder.py::test_wrong_level_count_is_rejected[6] PASSED
tests/test_question_builder.py::test_unparseable_claude_output_is_rejected PASSED
tests/test_question_builder.py::test_missing_anthropic_key_is_a_clear_error PASSED
tests/test_question_builder.py::test_output_schema_uses_only_supported_json_schema_features PASSED
...
============================= 62 passed in 3.49s ==============================
```
- 出力をスクラッチ用フォルダに保存し、`evals/evidence/T04/pytest.log` と「テスト名＋PASSED/FAILED」の一覧を並べ替えて `diff` → 差分なし。件数も 62 passed で一致（証拠は古くない）。

### 2. claude-output-schema.log の1行目のコマンド
```
$ cd backend && .venv/Scripts/python -c "import json, anthropic; from app.services.question_builder import GeneratedQuestions; print(json.dumps(anthropic.transform_schema(GeneratedQuestions), ensure_ascii=False, indent=1))"
```
- 出力を証拠ログの2行目以降と `diff` → 差分なし（anthropic SDK 1.8.0）。

### 3. 秘密情報の検索（AC-00c）
```
$ git show 34853f8 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
459:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
$ git show 34853f8 --name-only --format= | grep -iE "\.env|secret|key"
evals/evidence/T04/secret-scan.log
```
- 1つ目の一致は `secret-scan.log` に書かれた検索コマンド自身（`sk-` を含む）で、秘密情報ではない。ファイル名の一致もこのログのみ。テスト用のキーは conftest のダミー値（`test-anthropic-key`）。

### 4. check_tasks（AC-00d）
- 末尾に貼付。

---

## AC-06 の詳細確認

### テストの中身（正しい理由で弾いているか）
- 各異常系テストは `expect_502` で「502 であること」に加え、**原因ごとのメッセージ** を確かめている（抜け→「Questionが無い観点: market」、余分→「存在しない観点へのQuestion: team」、重複→「Questionが重複している観点: problem」、段階数→「ちょうど5個」）。単に「何かのエラーが出た」ではなく、狙った検査で弾かれていることがテストで分かる。
- 異常系の入力は、狙った1点以外は正しい（例: 抜けのテストは problem の Question が正しい5段階で、market だけが無い）。
- 段階数のテストは4個・6個の両方（parametrize）。
- 形に合わない出力: `parsed_output=None` のとき 502＋`FAILURE_DETAIL`（Question 用の日本語文言）になることを確認。
- 成功系: 観点1つにつき1つ、`criterion_id` が一致、5段階がそのまま入る `QuestionSet` が返る。プロンプトに観点の id・名前・説明（無い場合は「（説明なし）」）・配点が JSON として全部入ることを、JSON を取り出して比較して確認している。
- キー無し: 400 で、偽 Claude が一度も呼ばれない（`calls == []`）。

### 独自の確認（リポジトリ外のスクリプト、偽の Claude と通信遮断つき）
| 入力（偽 Claude の出力） | 結果 |
|---|---|
| 正しい2問 | 成功 `['problem', 'market']` |
| market が無い | 502「…Questionが無い観点: market」 |
| team が余分 | 502「…存在しない観点へのQuestion: team」 |
| problem が重複 | 502「…Questionが重複している観点: problem」 |
| 段階が4個／6個（中身がすべて別の文） | 502「観点 problem の段階の数が4個／6個です。段階はちょうど5個にしてください。」 |
| 段階が4個（同じ文の繰り返し＝テストと同じ形） | 同上（段階数の検査で弾かれている） |
| 段階の1つが空文字 | 502（空の段階は T03 の型で禁止） |
| `parsed_output=None` | 502「Questionの生成に失敗しました。もう一度お試しください。」 |
| 偽物を使わず本物の `AsyncAnthropic`（ダミーキー、通信遮断） | 502「Anthropic APIへの接続に失敗しました…」＝通信が遮断されれば外に出られない |

→ 各ケースが、テストの想定どおりの検査で弾かれている。黙って直す処理（並べ替え・補完）は無い。

### 実際の API を呼んでいないこと
- テストは `monkeypatch.setattr(question_builder, "AsyncAnthropic", FakeAnthropic)` で Claude のクライアントを差し替え、`messages.parse` に渡った引数を記録して確かめている（`api_key` が conftest のダミー値 `test-anthropic-key` であることもテストで確認）。
- `conftest.py` の autouse フィクスチャで、名前解決・`socket.connect`・asyncio の `sock_connect` がすべて localhost 以外は拒否される。差し替えを忘れても有料 API には届かない。上の最終行で、本物のクライアントでも接続エラーで止まることを確認した。
- `test_output_schema_uses_only_supported_json_schema_features` はネットワークを使わない（SDK のローカル関数 `transform_schema` のみ）。

### `review_generator._call_claude` の変更（既存の審査機能への影響）
- `git show 34853f8 -- backend/app/services/review_generator.py` で確認。追加されたのは末尾のキーワード引数 `failure_detail` のみで、既定値 `DEFAULT_FAILURE_DETAIL = "AIレビューの生成に失敗しました。もう一度お試しください。"` は、置き換えられた2か所の元の文言と1文字も違わない。
- 既存の呼び出し2か所（`review_generator.py` 200行・219行付近）は `failure_detail` を渡していないので既定値が使われ、動きは変わらない。他の例外処理（認証 400、BadRequest・レート制限・接続 502）は変更なし。既存テストも全部通っている。

### 「structured outputs は文字数・範囲などの制約に対応しないので型を単純にした」という判断
実行役の説明ではなく、SDK の実物とテストで確かめた。
- SDK 1.8.0 の `anthropic.transform_schema`（`anthropic/lib/_parse/_transform.py`）のソースを読んだ。`messages.parse` は `output_format` をこの関数で変換してから API に送る（`resources/messages/messages.py`）。この関数は `type`・`enum`・`description`・`title`・object の `properties`/`required`（`additionalProperties` は必ず false）・string の対応済み `format`・array の `items` と `minItems`（0 か 1 のときだけ）しか残さず、それ以外（`minLength`/`maxLength`/`maxItems`/`minimum`/`maximum`/`pattern`、2以上の `minItems` など）は **スキーマから外して description の文字列に移す**。つまり API のスキーマとしては強制されない。SDK の実装がこの判断を裏付けている。
- `claude-output-schema.log`（再実行して一致）では、`GeneratedQuestions` の変換結果は type/title/properties/items/required/additionalProperties=false だけで、description への書き出しも無い。
- テストの効き目を確かめるため、リポジトリ外で「`criterion_id` に文字数、`levels` に個数(5〜5)の制約を付けた同じ形の型」を変換したところ、description に `{maxLength: 40, minLength: 1}`・`{maxItems: 5, minItems: 5}` が書き出され、テストの禁止語リストの `minLength`・`maxLength`・`minItems`・`maxItems` に引っかかった。→ 誰かが生成用の型に制約を足すとこのテストは失敗する（意味のあるテスト）。
- 細かい検査（5段階・空の段階禁止・1対1）は、Claude の出力を受けた後に T03 の `QuestionSet` で行っており、上の独自確認のとおり実際に弾かれる。FR-2「出力は Pydantic の型で検証し、形が違えばエラーにする」を満たす。

### プロンプトが要件に沿っているか（FR-2・voice.md 2章）
| 要件 | プロンプト（`SYSTEM_PROMPT`） |
|---|---|
| 1観点につき1つ、`criterion_id` を必ず持つ（FR-2） | 「各観点につき、ちょうど1つの質問」「入力された観点の id をそのまま書く（変更・追加・省略しない）」 |
| 5段階・低い順（FR-2、voice 2章） | 「ちょうど{JEV_LEVEL_COUNT}個（=5）の段階の説明を、低い段階から高い段階の順に」 |
| 具体的で観察できる内容、感想語だけにしない（FR-2、voice 2章） | 「発表を聞いた人が確認できる事実で書く（「すごい」「弱い」のような感想語だけにしない）」 |
| 「〜をどの程度満たしているか」の形で1つの観点だけ（voice 2章） | 「その観点だけを「〜をどの程度満たしているか」の形で聞く1文。複数の観点を混ぜない」 |
| 主催者の観点の意味を変えない（voice 2章） | 「主催者の観点の意味を変えないでください。…主催者の意図から外れないように」 |
| 日本語 | 「出力はすべて日本語で」 |

---

## 合否に影響しない指摘（今後のタスクへの申し送り候補）
1. voice.md 2章の「付け足した解釈があれば、画面で人間に見せる」は、今のプロンプト／出力の型では「どこが付け足した解釈か」を Claude に分けて書かせていない。画面で確認・編集する T07 以降（FR-3）で、どう人間に見せるかを決めておくとよい。
2. Claude が観点と違う順番で Question を返した場合、そのまま（Claude の順番で）通る（独自確認で `['market', 'problem']` のまま成功）。1対1の検査は満たすので誤りではないが、画面表示や採点結果の並びを観点の順にそろえたいなら、後続タスクで並べ直すかどうか決めるとよい。
3. 「形に合わない出力」のテストは `parsed_output=None` の場合だけ。実際の SDK で JSON が型に合わないときは `messages.parse` の中で例外になり、`_call_claude` の最後の `except Exception` で同じ 502＋`FAILURE_DETAIL` になる（コードで確認）が、その経路のテストは無い。
4. 段階の1つが空文字のとき、エラーの括弧内が Pydantic 標準の英語（「String should have at least 1 character」）になる（T03 の型の標準メッセージ。NFR-3 の日本語メッセージの観点では小さな改善余地）。
5. 段階数のテストは同じ文を4個／6個並べた入力を使っている。段階数の検査で弾かれていることはメッセージで確かめているので問題はないが、別々の文にすると意図がより明確になる。

---

## check_tasks の出力（tasks.json の T04 を done/passes:true にし、本ファイル作成後に実行）
```
$ python evals/check_tasks.py
WARN : T13: 基準に無い新しいタスクです。人間が追加したなら基準タグを更新してください。
結果: エラー 0 件 / 警告 1 件 / 完了 5/14 タスク
```
