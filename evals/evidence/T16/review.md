# T16 検品記録（評価役）

- 対象コミット: `765011a`（T16: order saved question sets by saved_at instead of file mtime (P6)）
- 検品日: 2026-09-27
- 判定: **合格**（全 AC ○）

## AC ごとの判定

| AC | 判定 | 根拠ファイル | 評価役による再実行の結果 |
|---|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | `pytest.log`（163 passed） | `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q -p no:cacheprovider` → **163 passed in 4.31s**（証拠と同じ件数・失敗0） |
| AC-00c 秘密情報が含まれていない | ○ | `secret-scan.log` | `git show 765011a` と作業ツリーの `git diff` に safety.md 3章のパターンで grep。`git show` の一致は1件のみで、`secret-scan.log` に書かれた grep コマンド文字列そのもの（キーではない）。作業ツリー側は一致なし。`.env` は追跡されていない |
| AC-00d tasks.json のルール違反がない | ○ | `check_tasks.log` | 本ファイル末尾の `check_tasks.py` 出力のとおりエラー0件 |
| AC-10 Questions を保存・一覧・読み込みできる | ○ | `backend/tests/test_question_set_storage.py`, `pytest.log` | `test_save_then_load_returns_the_same_content`（保存→読み込みで同内容・saved_at も一致）と `tests/test_contest_api.py::test_save_list_and_load_question_set_round_trip`（API 経由の保存→一覧→読み込み）が再実行で合格 |

## task 文の要件の確認

| 要件 | 判定 | 確認方法 |
|---|---|---|
| 並び順が saved_at で決まる（ファイル更新時刻ではない） | ○ | コード: `list_all()` が全ファイルを読み込み `saved_at` で降順ソート（`os.path.getmtime` は使われなくなった）。テスト `test_list_orders_by_saved_at_not_file_mtime` は古い方のファイルの mtime を1時間未来にしても保存順どおりに並ぶことを確かめている |
| 続けて保存しても新しい順が守られる | ○ | コード: `_next_saved_at()` が前回保存時刻以下なら +1マイクロ秒して、プロセス内で必ず単調増加させる。テスト `test_saves_within_the_same_clock_tick_still_list_newest_first` は時計を固定して同時刻の2回保存でも新しい順になることを確かめている |
| 不安定だったテストが安定して通る | ○ | `test_list_returns_newest_first_with_summary_fields` を単体で **50回連続** 再実行 → 50/50 passed。`test_question_set_storage.py` 全体を **30回連続** 再実行 → 30/30 で「13 passed」（証拠 `repeat.log` と一致） |
| 新テストが本当に修正を確かめているか | ○ | 評価役が一時 worktree（scratchpad、終了後に削除）で `question_set_storage.py` だけを修正前（`f8582cf`）に戻して新テストを実行 → 新テスト2件が FAILED（2 failed, 11 passed）。`before-fix.log` と同じ結果 |

## 既存テストが弱められていないか

- `git show 765011a -- backend/tests` : `test_question_set_storage.py` への **追加のみ**（import 3行と新テスト2件）。既存テストの書き換え・削除なし。不安定だったテスト `test_list_returns_newest_first_with_summary_fields` の中身も変更なし。
- `git diff harness-baseline --stat -- backend/tests` : `test_question_set_storage.py | 35 +++` のみ（削除行0）。

## 合否に影響しない指摘

1. `_last_saved_at` はプロセス内のグローバル変数で、ロックがない。FastAPI の同期エンドポイントがスレッドプールで同時に呼ばれると、理論上は同じ時刻が2回出る可能性がある（ローカル1人利用なので実害はほぼない）。
2. 別プロセス・再起動をまたいだ単調性は時計任せ（OS の時計が戻った場合など）。一覧の並び順の用途では問題にならない。
3. `list_all()` は並べ替えのために全ファイルを読むようになった（以前も要約を作るために全ファイルを読んでいたので、実質的な負荷増はない）。

## check_tasks.py の出力（tasks.json の T16 を done / passes true に更新し、本 review.md 作成後）

```
$ backend/.venv/Scripts/python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 15/17 タスク
```

終了コードは 0。実行役の時点で出ていた「T16: 基準に無い新しいタスク」の警告は、今回は出なかった。検品の途中で基準タグ `harness-baseline` が `765011a`（T16 のコミット）を指すように更新されたためで、この基準の tasks.json には T16 が入っている。上の「既存テストが弱められていないか」の `git diff harness-baseline` は、タグが動く前（T16 より前の基準）で実行したもの。
