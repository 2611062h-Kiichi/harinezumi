# T05 評価役の検品記録

- 検品日: 2026-09-26
- 対象: コミット 496293c「Score transcripts with Jev and convert to contest points (T05)」（ブランチ `feature/contest-jev-questions`）
- 評価役: 実行役とは別のサブエージェント（`docs/roles.md` 3章）
- 読んだもの: `evals/acceptance.md`、`tasks.json` の T05、`evals/evidence/T05/`（pytest.log・secret-scan.log・check_tasks.log）、`git show 496293c`、`progress.md`（引き継ぎメモ・作業計画・作業ログ T05）、`docs/requirements.md` 4章 FR-5/6/7/9、`docs/safety.md` 3章
- 読んでいないもの: `backend/.env`（指示どおり読んでいない）。環境変数の値も表示していない

## 判定: 合格（全条件 ○）

| 条件 | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | 再実行で 78 passed / 失敗0件。証拠 `pytest.log` と各テストの結果（78件すべて PASSED）が一致 |
| AC-00c 秘密情報が含まれていない | ○ | `docs/safety.md` 3章の検査式でコミット 496293c の差分を検査し、一致は証拠ファイル `secret-scan.log` 自身に書かれた検査コマンドの行だけ（キーではない）。それを除くと一致なし。未コミットのステージ済み差分も一致なし |
| AC-00d tasks.json のルール違反がない | ○ | `python evals/check_tasks.py` がエラー0件（末尾に出力を貼付） |
| AC-07 Jev 採点が正しい形で呼ばれ、配点換算がサーバーで計算される | ○ | 下の「AC-07 の詳細」 |

## AC-07 の詳細

### Jev の呼び方（FR-5）
- `contest_scorer.score_transcript` は `run_system_one(transcript, questions)` を1回だけ呼び、その中で `client.system_one(state, questions)` を1回呼ぶ（`backend/app/services/contest_scorer.py`, `backend/app/services/jev_scorer.py`）。
- テスト `test_sends_transcript_and_score_questions_to_jev`: 偽物の Jev への呼び出しが1回、`state == TRANSCRIPT`、`questions` の各値が `typesafe_sdk.Score` のインスタンス、`criteria` が型の `levels` と同じ、`instructions` が `【観点】観点名\n` で始まることを確認している。
- 実 SDK（typesafe-sdk）の `AsyncTypeSafeClient.system_one(self, state, questions, ...)` の引数の順番と、`Score` のフィールドが `type / instructions / criteria` であることを、通信なしで `inspect` して確かめた。呼び方は SDK の形と合っている。

### 配点換算（FR-6）
- 換算例 score 3.0・5段階・配点20 → 15.0 は `test_converts_jev_score_to_contest_points` と `test_points_use_round_half_up` の両方にある。
- 計算は `Decimal(str(score)) / (段階数-1) * 配点` を `ROUND_HALF_UP` で小数第1位に丸める。Python の `round` は使っていない。
- **リポジトリ外の確認スクリプト**（スクラッチ用フォルダの `check_rounding.py`。リポジトリには置いていない）で、分数（`fractions.Fraction`）による正確な四捨五入の参照値と比べた:
  - `to_points` 229通り（ちょうど半分: 0.05×20=0.25, 0.3×30/4=2.25, 0.02×100/4=0.5, 0.1×1/4=0.025→0.0 など／段階の端 0・4／配点の端 1・100／誤差が出やすい 0.1, 0.3, 0.7, 1.1, 3.95, 2.45 などと配点 1,3,7,9,11,13,33,99,100 の組み合わせ）→ **不一致 0件**
  - Python の `round(0.25, 1)` は 0.2、`to_points(0.05, 5, 20)` は 0.3（ちょうど半分が切り上がっている）
  - 端: `to_points(0,5,1)=0.0`、`to_points(4,5,1)=1.0`、`to_points(0,5,100)=0.0`、`to_points(4,5,100)=100.0`、`to_points(3.0,5,20)=15.0`
  - 実 Jev が返しうる、短い小数で書けない値（`0.30000000000000004`, `2.3499999999999996`, `1/3`, `2/3`, `3.0000000000000004`）も参照値と一致
- 合計: 同じスクリプトで偽物の Jev を使い `score_transcript` を 304通り（観点1〜15個、配点1〜100、score を小数1〜3桁でランダム＋配点1の観点15個に 0.1 点ずつ等）実行し、`total_points` が「丸めた各観点の点数を分数で正確に足した値」と一致、`max_total_points` が配点の合計と一致 → **不一致 0件**。合計は `Decimal(str(点数))` で足してから丸めているので、float の足し算の誤差は出ない。
- 結果は観点の順に並ぶ（`test_results_follow_rubric_order`、Question を逆順にしたデータで確認）。

### 申し送り3項目（引き継ぎメモ）
| 項目 | 判定 | 根拠 |
|---|---|---|
| P2(b): `instructions` に観点名 | ○ | `build_jev_questions` が `【観点】{観点名}\n{instructions}` を作る。テストで観点ごとに `startswith` を確認 |
| `levels` → `Score(criteria=...)` への名前変換 | ○ | `Score(instructions=..., criteria=q.levels)`。テストで `list(question.criteria) == LEVELS` を確認 |
| `low_confidence` を `confidence < LOW_CONFIDENCE_THRESHOLD` から計算 | ○ | `low_confidence=answer.confidence < LOW_CONFIDENCE_THRESHOLD`（しきい値 0.5 は `app/models/contest.py`）。テストで 0.49→True、0.5→False、0.9→False（FR-7） |

### キーが無いとき（FR-9）
- `test_missing_typesafe_key_is_a_clear_error`: キーを空にすると 400・`TYPESAFE_API_KEY` を含む日本語メッセージ、偽物の Jev は一度も呼ばれない（黙って別方式にしていない）。

### `jev_scorer.py` の切り出しで既存の動きが変わっていないか
- `git show 496293c -- backend/app/services/jev_scorer.py` を確認。エラー処理（例外の種類・ステータス・日本語メッセージ）は差分の文脈行で、変更されていない。
- さらにリポジトリ外のスクリプト（`check_jev_equiv.py`）で、コミット前の `jev_scorer.py`（`git show 496293c^:...` をスクラッチ用フォルダに保存）と今の `jev_scorer.py` の `score_with_jev` を、同じ偽物の Jev で並べて実行した。成功・認証エラー・利用上限・接続エラー・その他のエラー × キーあり/キー無し の10通りすべてで、戻り値（または HTTP ステータスとメッセージ）と Jev に渡した state・questions が **完全に同じ**:
  - 認証エラー → 400「TYPESAFE_API_KEYが正しくありません。」
  - 利用上限 → 502「Jev(TypeSafe API)の利用上限に達しました。しばらく待ってから再度お試しください。」
  - 接続エラー → 502「Jev(TypeSafe API)への接続に失敗しました。ネットワークを確認してください。」
  - その他 → 502「Jev(TypeSafe API)エラー: …」
  - キー無し → 400「TYPESAFE_API_KEYが設定されていません。」
- 既存の `tests/test_jev_scorer.py` も再実行で全件 PASSED。

### 実際の Jev を呼んでいないこと
- テストは `monkeypatch.setattr(jev_scorer, "AsyncTypeSafeClient", FakeTypeSafeClient)` で偽物に差し替えている（`run_system_one` はモジュール内の名前 `AsyncTypeSafeClient` を使うので、差し替えが効く）。
- `backend/tests/conftest.py` の自動 fixture が、名前解決・`socket.connect`・asyncio の `sock_connect` を localhost 以外で止め、キーはダミー値に置き換えている。
- 評価役も実 API を呼ぶ実験はしていない（確認スクリプトは偽物の Jev のみ、名前解決も止めて実行）。

## 自分で再実行したコマンドと結果

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
============================= 78 passed in 3.87s ==============================
```
- 証拠 `evals/evidence/T05/pytest.log`（78 passed in 3.49s）と、テスト名ごとの PASSED/FAILED を突き合わせて差分なし（`test_contest_scorer.py` 16件を含む）。

```
$ git show 496293c -- . ':!evals/evidence/T05/secret-scan.log' | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（一致なし、exit=1）
$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（一致なし、exit=1）
```

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python <スクラッチ用フォルダ>/check_rounding.py
to_points cases: 229 mismatches: 0
python round(0.25,1)= 0.2  to_points(0.05,5,20)= 0.3
to_points(3.0,5,20)= 15.0
to_points(0,5,1)= 0.0  to_points(4,5,1)= 1.0  to_points(4,5,100)= 100.0  to_points(0,5,100)= 0.0
total trials: 304 mismatches: 0

$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python <スクラッチ用フォルダ>/check_jev_equiv.py <スクラッチ用フォルダ>
（成功・4種類のエラー × キーあり/無し の10通りすべて SAME）
```
（確認用スクリプトはリポジトリの外のスクラッチ用フォルダにだけ置いた）

## 合否に影響しない指摘
1. `score_with_jev` の中で、キーの確認より先に `get_rubric_criteria(mode)` が動くようになった。「モードが不正」かつ「キー無し」のときだけ、出るエラーが 400（キー無し）から `ValueError` に変わる。ただし呼び出し元の `review_generator.py` はその前に `get_rubric_criteria(mode)` を呼んでいるので、今の画面・API から見える動きは変わらない。
2. Jev の score が範囲外のとき、わずかなずれでなくても（例: 5.0 や -1.0）黙って 0〜4 に収めてしまう。「わずかな誤差を収める」という計画の意図より広い。大きく外れたときはログを出すか 502 にするかを、後続タスクで検討するとよい。
3. 証拠 `pytest.log` の1行目は `$ cd backend && .venv/Scripts/python -m pytest -v` で、実際には `PYTHONIOENCODING=utf-8` を付けて実行したかどうかがログから分からない（結果には影響なし）。
4. `backend/tests/__pycache__/` に、対応する `.py` が無い `test_zz_tmp_unmocked.cpython-314-pytest-9.1.1.pyc` が残っている（git の管理外。T05 の差分ではない。以前の一時テストの残りと思われる）。

## check_tasks の出力（tasks.json の T05 を done / passes: true にした後）

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 6/14 タスク
```
