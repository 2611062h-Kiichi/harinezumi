# T06 評価役の検品記録

- 対象: T06「音声/動画 → 既存 transcribe() → Jev の state へ渡す流れを作り、空の書き起こしをエラーにする。モック Whisper でテストする」
- 変更: コミット 7f7aa60（`backend/app/services/contest_scorer.py` +13行、`backend/tests/test_contest_audio.py` 新規、証拠3件、progress.md、tasks.json）
- 手順: `docs/roles.md` 3章。`evals/acceptance.md` → `tasks.json` の T06 → `evals/evidence/T06/` → `git show 7f7aa60` の順に確認
- 要件: `docs/requirements.md` FR-4（既存の transcribe() で文字起こし、空の結果はエラー）、NFR-3（日本語で次にすることが分かるエラー）
- 実行環境: Windows 11、Git Bash。実 API は呼んでいない。`backend/.env` は読んでいない。環境変数の値は表示していない

## 判定: 合格（全条件 ○）

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | 証拠1行目のコマンドをそのまま再実行して 85 passed、失敗0件。証拠と比べて、1行目以外で違うのは所要時間（3.68s → 3.84s）だけ。`pytest -q` でも 85 passed |
| AC-00c 秘密情報が含まれていない | ○ | safety.md 3章のコマンドで一致なし（`--cached` は今は空なので、コミット 7f7aa60 全体でも検査。一致は secret-scan.log に書かれた検索コマンド自身の1行だけ） |
| AC-00d tasks.json のルール違反がない | ○ | `python evals/check_tasks.py` がエラー0件。警告1件は T14（人間の決定で追加し、基準タグの更新待ち）の既知のもの |
| AC-08 音声 → 文字起こし → Jev 入力 がつながっている。空の書き起こしはエラー | ○ | 下の「AC-08 の確認」のとおり。モック Whisper の出力が Jev の `state` に加工なしで入ることを確かめるテストがあり、判定や受け渡しを壊すとテストが実際に落ちることを、リポジトリの外で確認した |

## 自分で再実行したコマンドと結果

### 1. 証拠 pytest.log の1行目のコマンド（そのまま）
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -v
```
結果: `85 passed in 3.84s`（exit 0）。うち `tests/test_contest_audio.py` の7件はすべて PASSED。

出力をスクラッチ用フォルダに保存し、証拠と比べた:
```
$ diff <(tail -n +2 evals/evidence/T06/pytest.log) "$S/rerun.log"
96c96
< ============================= 85 passed in 3.68s ==============================
---
> ============================= 85 passed in 3.84s ==============================
```
（`$S` はスクラッチ用フォルダ）テスト名・順番・結果は証拠とすべて同じ。
1行目のコマンドについて: 実行時の設定 `PYTHONIOENCODING=utf-8` が入っており、そのコマンドで再実行すると証拠と所要時間以外まったく同じ出力になった。T05 で指摘された「1行目に実行時の設定が抜けている」問題は再発していないと判断した。

### 2. `pytest -q`（acceptance.md の確かめ方）
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
85 passed in 3.93s
```

### 3. 秘密情報チェック（safety.md 3章）
```
$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（出力なし。exit=1）
$ git show 7f7aa60 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
272:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
```
一致は secret-scan.log に書かれた検索コマンド自身の1行だけ。

## AC-08 の確認

### コードを読んで確かめたこと
- `score_audio`（contest_scorer.py）は既存の `app.services.transcription.transcribe()` を呼び、`transcription.text` を **そのまま** `score_transcript` に渡す。`transcription.py` はこのコミットで変更されていない
- `score_transcript` の空判定は `if not transcript.strip():` で、判定にだけ `strip()` を使っている。削った文字列を変数に入れ直しておらず、Jev には `run_system_one(transcript, questions)` で元の文字列が渡る。`run_system_one` は `client.system_one(state, questions)` にそのまま渡す（jev_scorer.py 20〜28行目）
- 空・空白だけのときは、`build_jev_questions` と `run_system_one` より前で 400 にしている。エラー文は「発表の文字起こしが空です。音声に話し声が入っているか確認して、もう一度お試しください。」で、日本語で次にすることが分かる（NFR-3）
- テストでは Whisper（`transcription.AsyncOpenAI`）と Jev（`jev_scorer.AsyncTypeSafeClient`）を偽物に差し替えている。本物の `transcribe()` と `run_system_one()` はそのまま動く。conftest.py がダミーキーと外部通信の遮断を全テストにかけている
- テストが確かめていること: Whisper に音声ファイルの中身と `whisper-1` が渡る／Jev の `state` が Whisper の出力と完全に同じ（前後の空白と改行付きのときも同じ）／結果の transcript と合計点／`""`・`"   "`・`"\n\t "` で 400、エラー文に「文字起こしが空」、Jev は一度も呼ばれない／文字を直接入れた場合も同じ／OPENAI_API_KEY が無いと Whisper も Jev も呼ばれない

### テストが意味を持つかの確認（リポジトリの外で実施）
`backend` の `app`・`tests`・`pytest.ini` だけをスクラッチ用フォルダにコピーし（`.venv`・`.env`・`__pycache__` は除外）、コピー側の `contest_scorer.py` を1か所ずつ書き換えて、リポジトリの `.venv` の Python で全テストを実行した。リポジトリのコードは変更していない。
```
$ cd "$S/mut" && PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 "$PY" -m pytest -q -p no:cacheprovider
```
（`$PY` はリポジトリの `backend/.venv/Scripts/python`）

| 書き換え | 結果 | 落ちたテスト |
|---|---|---|
| M1 空判定を外す（`if False:`） | 4 failed, 81 passed | 空の3件、文字の直接入力1件 |
| M2 `strip()` なしの判定（`if not transcript:`） | 3 failed, 82 passed | 空白だけの2件、文字の直接入力1件 |
| M3 `score_audio` で `transcription.text.strip()` を渡す | 1 failed, 84 passed | `test_surrounding_whitespace_is_passed_through_as_is` |
| M4 `score_transcript` で Jev の前に `transcript = transcript.strip()` | 1 failed, 84 passed | 同上 |
| M5 空判定を Jev 呼び出しの後ろに移す | 4 failed, 81 passed | 空の3件、文字の直接入力1件（Jev が呼ばれたことを検出） |
| M6 `transcribe()` を使わず固定の文にする | 6 failed, 79 passed | 受け渡し・空白・空・キー無しのテスト |
| M7 エラー文を英語にする | 3 failed, 82 passed | 空の3件 |

どの書き換えもテストで検出された。空・空白だけで Jev が呼ばれないこと、Whisper の出力が加工されずに state に入ることを、テストが実際に確かめていると判断した。確認用のコピーは実行後に削除した。

### T05 までの動きへの影響
- アプリ本体の変更は `contest_scorer.py` の13行の追加だけ（`git diff 4f03472 7f7aa60 --stat -- backend/app`）
- `test_contest_scorer.py`（換算・四捨五入・並び順・欠けた観点など）を含む既存の78件はすべてそのまま通る
- 動きが変わるのは「空・空白だけの書き起こしを `score_transcript` に渡したとき」だけで、これは FR-4 で求められた変更

## 合否に影響しない指摘
1. `test_surrounding_whitespace_is_passed_through_as_is` は Jev の `state` だけを確かめていて、結果の `transcript` が空白付きのままかは確かめていない（今のコードはそのまま返している）
2. 「音声/動画」のうち動画（mp4 など）の拡張子でのテストは無い。`transcribe()` はファイルの中身をそのまま Whisper に渡すので、動画の扱いは Whisper 側と既存の `transcribe()` に任されている。画面・API 側（T07 以降）で受け付ける拡張子を決めるときに確かめるとよい
3. `score_audio` の `transcribe()` に渡す一時ファイルの作成・削除は呼び出し側（T07 の API）の責任になる。T07 で後片付けを確かめるとよい

## 後片付け
- スクラッチ用フォルダだけを使い、リポジトリ内に確認用ファイルは作っていない
- 再実行の前後で `backend` 配下（`.venv` を除く）の `.pyc` の一覧が同じことを確認した（33件、差分なし）
- 変更したのは `tasks.json` の T06 の `status`（review → done）と `passes`（false → true）、およびこの `review.md` の新規作成だけ。コミット・push・タグ・ブランチ操作はしていない

## `python evals/check_tasks.py` の出力（tasks.json 更新と review.md 作成の後）
```
$ python evals/check_tasks.py
WARN : T14: 基準に無い新しいタスクです。人間が追加したなら基準タグを更新してください。
結果: エラー 0 件 / 警告 1 件 / 完了 7/15 タスク
(exit=0)
```
