# T08 検品結果（評価役）

対象コミット: `7406c0e`「Add save/list/load for named Question sets (T08)」
参照: `progress.md` 作業計画（T08）／作業ログ（T08）、`tasks.json` T08、`evals/acceptance.md`、`docs/requirements.md` 4章 FR-8

## 総合判定: 合格（○）

## AC ごとの判定

### AC-00a（既存のテストがすべて通る）: ○
- 証拠 `evals/evidence/T08/pytest.log` の1行目のコマンドをそのまま再実行した。

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
============================= 132 passed in 3.85s =============================
```

- 証拠ログと同じ「132 passed」で一致。失敗0件。

### AC-00c（秘密情報が含まれていない）: ○
- `docs/safety.md` 3章のコマンドをコミット全体に対して再実行した。

```
$ git show 7406c0e | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
490:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
```

- ヒットしたのは `evals/evidence/T08/secret-scan.log` に記録された「実行したコマンド自体の行」のみ（T07 で確立した記法どおり）。実際の秘密情報（キーなど）は無し。
- 追加確認: 保存された JSON ファイルと API 応答に `sk-` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `TYPESAFE_API_KEY` / `-----BEGIN` のいずれも含まれないことを、隔離したテスト用ディレクトリに実際に保存させたうえで確認した（下記「追加の再現テスト」参照）。

### AC-00d（tasks.json のルール違反がない）: ○
- 自分で再実行。

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 8/15 タスク
```

- 証拠 `evals/evidence/T08/check_tasks.log` と同じ「エラー 0 件」。

### AC-10（Questions セットの保存・一覧・読み込み。保存→一覧→読み込みで同じ内容に戻る）: ○
- `backend/tests/test_question_set_storage.py`（8件）と `backend/tests/test_contest_api.py` の追記分（7件）が pytest で全通過（上記 132 passed に含まれる）。
- さらに、リポジトリ外のスクラッチフォルダに作った検証スクリプト（`probe_t08.py`。TestClient のみ使用、実 API 呼び出し無し、保存先は `tempfile.mkdtemp()` で完全に隔離）で、以下を自分で再現した。全27チェックが成功（fail=0）。

```
$ PYTHONIOENCODING=utf-8 .venv/Scripts/python <scratch>/probe_t08.py
（抜粋）
[OK] malicious id via HTTP: ../../../backend/.env :: status=404, len=22
[OK] malicious id via HTTP: ..%2F..%2F..%2Fbackend%2F.env :: status=404, len=22
[OK] malicious id via HTTP: ..\..\..\backend\.env :: status=404, len=38
[OK] malicious id via HTTP: %2e%2e%2f%2e%2e%2fbackend%2f.env :: status=404, len=22
[OK] malicious id via HTTP: aaaa...(5000文字) :: status=404, len=38
[OK] null-byte id via service function :: HTTPException: 404
[OK] very long id via service function :: HTTPException: 404
[OK] service function bad id: /etc/passwd :: HTTPException: 404
[OK] service function bad id: C:\Windows\win.ini :: HTTPException: 404
[OK] service function bad id: ....//....//backend/.env :: HTTPException: 404
[OK] service function bad id: ..;/..;/backend/.env :: HTTPException: 404
[OK] blank name '' -> 400
[OK] blank name '   ' -> 400
[OK] blank name '\t\n' -> 400
[OK] blank name did not create files
[OK] mismatched criteria/questions -> 400 :: detail=保存内容に誤りがあります。観点とQuestionが1対1になっていません。Questionが無い観点: problem
[OK] malformed question_set did not create files
[OK] duplicate criterion id -> 400
[OK] wrong level count -> 400
[OK] list ordering newest first
[OK] round trip content identical (raw JSON compare)
[OK] loaded question_set == original QUESTION_SET (pydantic ==)
[OK] no secret markers in API response
[OK] no secret markers in saved json files
[OK] list endpoint still 200 with existing data

=== SUMMARY ===
total=27 fail=0
```

- 確認できたこと（roles.md「T07 で異常な入力を試さないと発見できない不合格が一度あった」を踏まえた重点確認）:
  1. **id を使った読み込みの安全性**: `GET /api/contest/question-sets/{saved_id}` は、`saved_id` を `_ID_PATTERN`（UUID4 形式の正規表現）にまず通し、一致しなければファイルシステムに触れずに404を返す（`backend/app/services/question_set_storage.py` の `load()`）。
     - `../../../backend/.env`、`..%2F..%2F..%2Fbackend%2F.env`（URLエンコード）、`..\..\..\backend\.env`（バックスラッシュ）、5000文字の巨大id、`00000000-...`（形は正しいが存在しない）、null バイトを含むid（サービス関数を直接呼んで確認。HTTP層ではNULバイトはURLとして送れないため）— すべて404。中身が漏れたケースは無い。
     - 実際に、`../../../backend/.env` や `%2e%2e%2f...` のように「/」を含む・デコードするとスラッシュになる id は **FastAPI/Starlette のルーティング自体**が404にしていた（応答本文長22＝Starlette標準の `{"detail":"Not Found"}`）。一方、`..\..\..\backend\.env`（バックスラッシュ、スラッシュを含まないので1セグメントとしてルーティングを通過）や `not-a-uuid`、5000文字のidは**アプリ自作の `_ID_PATTERN` 検査**で404（応答本文長38＝日本語メッセージ「指定されたQuestionセットが見つかりません。」）。作業ログの説明「一部はルーティングの側で先に弾かれ、残りは自作の検査で弾かれる」を自分で再現し、確認した。
     - `backend/.env` の中身は一度も読んでいない（読む・表示するのは禁止事項のため）。全チェックは応答本文の長さ・ステータスコード・秘密情報マーカーの有無のみで判定した。
  2. **保存の入力検査**:
     - `name` が `""`・`"   "`・`"\t\n"` のとき400で、かつファイルが1件も作られないことを確認（保存前にサービス層で検査している）。
     - `question_set` が壊れている場合（観点とQuestionが1対1でない、観点IDが重複、段階数が5でない）はいずれも400になり、ファイルが作られないことを確認。これは pydantic の `model_validator`（`QuestionSet._one_question_per_criterion` 等）が `parse_json()` の中で発火し、`question_set_storage.save()` に到達する前に弾かれているため。
  3. **一覧・読み込みの一致**: 保存→一覧→読み込みを実施し、(a) 生JSONの完全一致、(b) `SavedQuestionSet.model_validate()` した結果の `question_set` が元の `QUESTION_SET`（pydanticの`==`）と一致、の両方を確認。`saved_at` を含め往復で値が変わらないことも確認。
  4. **複数保存時の並び順**: 2件保存し、一覧が新しい順（後に保存した方が先頭）になることを確認（保存順のUUIDではなく `os.path.getmtime` でソートしているため）。
  5. **既存機能への影響**: `pytest -v` で `/questions`・`/score`・`history.py` 関連の既存テストを含む132件がすべて通過。ルーター差分（`git show 7406c0e -- backend/app/routers/contest.py`）は追記のみで、既存エンドポイントのコードは変更されていないことをdiffで目視確認した。

## 合否に影響しない指摘（今後の申し送り候補）
- `backend/.gitignore` は `data/reviews/*.json` は除外しているが、`data/question_sets/*.json`（本タスクの保存先）は除外リストに入っていない。history.py と「同じ作り」を謳っているなら、`.gitignore` も揃えるべき。現状は本番保存先 `backend/data/question_sets/` 自体がまだ存在せず（テストはすべて `tmp_path` で隔離しているため）、今回のコミットに秘密情報や実データの混入は無い（AC-00cは○）。ただし今後実際にこのディレクトリへ保存が発生した場合、`git add -A` 等で誤ってコミットされうる。ブロッカーではないが、次のタスクか改善提案として `.gitignore` に `data/question_sets/*.json` を追加することを推奨する。
- `routers/contest.py` の `SaveQuestionSetRequest.name` はプレーンな `str`（`RequiredText` 制約なし）で、空白のみの名前を拒否しているのは `question_set_storage.save()` 内の `name.strip()` チェックのみ。動作上は問題ない（400になる）が、他のモデル（`ContestRubric.contest_name` 等）はモデル層で `RequiredText` を使っており、書き方が一貫していない。合否には影響しない。

## check_tasks.py の実行結果（末尾貼り付け）

判定前（T08 が status: review のままの状態での再実行）:

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 8/15 タスク
```

tasks.json の T08 を `status: "done"`, `passes: true` に更新した後の再実行:

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 9/15 タスク
```
