# T21 評価役の検品結果（2回目）

- 対象: コミット `6e49f80`（並列化）＋ `f8704aa`（1回目の差し戻しへの修正）
- 判定: **合格**（AC-00a / 00b / 00c / 00d / 08 / 09 と task 文の要件はすべて ○）
- 外部API（Anthropic / OpenAI / TypeSafe）は一度も呼んでいない。Claude・Whisper・Jev・URL のダウンロードはすべて偽物、キーはダミー（環境変数で上書きし、読み込み後に `dummy-` で始まることを確認）、名前解決と外への接続は遮断。自作の確認は scratchpad に `git archive` で取り出したコード（`.env` の無い場所）で行った。`backend/.env` は読んでいない。リポジトリのコードは変更していない。実際のネットワークからのダウンロードはしていない。
- 実行役の説明（progress.md の作業ログ、実行役からのメッセージ）は合格の理由にしていない。以下は自分で再実行した結果。

## AC ごとの判定

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存テストがすべて通る | ○ | `pytest -q` を再実行: **234 passed**（`pytest.log` の 234 passed と一致） |
| AC-00b フロントがビルドできる | ○ | `npm run build` 再実行で成功（`✓ built`）。T21 の2コミットは `frontend/` を変更していない（`git diff --stat 90011ea f8704aa -- frontend` が空） |
| AC-00c 秘密情報なし | ○ | `git show f8704aa` と `git show 6e49f80` に safety.md 3章の正規表現をかけ、一致は検査コマンドの文字列そのもの（secret-scan.log・review-1.md に書かれた行）だけ。キーは無い。作業ツリーの差分にも一致なし |
| AC-00d tasks.json のルール違反なし | ○ | `check_tasks.py` エラー0件（末尾に出力） |
| AC-08 書き起こし → Jev 入力・空ならエラー | ○ | 既存テスト（`test_contest_video.py` ほか）が通る。f8704aa はコンテスト側（`contest_scorer.py`・`routers/contest.py`）を変更していない（`git diff --stat 6e49f80 f8704aa -- backend/app` は `routers/review.py` だけ）。URL 経路でも偽 Whisper の文字列が Jev まで届き 200・`transcript_included: true`（下の U1） |
| AC-09 API が仕様どおり応答 | ○ | 自作確認: 成功 200（U1・P1）、Claude キー無し → 400「ANTHROPIC_API_KEYが設定されていません。」（U3・P3）、ダウンロード失敗 → 400「URLから音声を取得できませんでした。」（U4）、Whisper 接続エラー → 502「OpenAI APIへの接続に失敗しました。ネットワークを確認してください。」（U6）。いずれも日本語で、変更前と同じ文言。入力ミスの 400 は既存テストで通る |

## 1回目の指摘（×）が直ったか → **直った**

`routers/review.py` は、ダウンロードを `stage.in_thread(download_audio_from_url, ...)`（打ち切らない）、書き起こしを `stage.call(transcribe_download(download_task))`（打ち切れる）に分け、書き起こし側は `await asyncio.shield(download)` でダウンロードの終わりを待つ形になった。

コードを読んで確かめたこと:
- 失敗時、`Stage._abort` は書き起こしの Task だけを取り消す。取り消しは `shield` の外側で止まり、ダウンロードの Task 自体は取り消されない。ダウンロードの Task も `Stage` に登録されているので、`gather(return_exceptions=True)` がその終わりを待ってから例外が上がる → その後に `finally` で一時フォルダを消す。
- 書き起こしの Task がまだ一度も動いていないうちに取り消された場合も、ダウンロードの Task は別に登録されているので待たれる。
- ダウンロードが失敗したときは、ダウンロードの Task と書き起こしの Task の両方が同じ例外で終わるが、`Stage.wait` は「始めた順で最初」を返すので、ダウンロードの例外（400 の文言）がそのまま出る（U4 で確認）。
- 要求そのものが取り消されたとき（ブラウザが通信を切った等）も `Stage.wait` の `except CancelledError` で同じ後片付けが走る（U8・U9 で確認）。

偽物で確かめた結果（ダウンロード = 別スレッドで 1.5秒待ってから一時フォルダに書き込み、ファイルを 0.2秒開いたまま。Whisper 0.3秒。スライドは本物の読み取り処理の前に 0.5秒ファイルを開いたまま待つ包み。`shutil.rmtree` の呼ばれた時刻を記録）:

| 場面 | 修正後（f8704aa） | 修正前（6e49f80 の review.py） |
|---|---|---|
| U1 URL 正常 | 200。ダウンロード（0.02秒開始）はスライド・評価基準と同時、Whisper はダウンロード終了（1.72）の後 1.73 開始、Jev・コメントはその後。一時フォルダ消えた | 同じ |
| U2 壊れた pptx ＋ URL | スライド失敗 0.51 → ダウンロード終了 1.70 → 一時フォルダ削除 1.70 → 500。**Whisper は始まらない**。ダウンロードは一時フォルダが残っているうちに書き込めた | Whisper を 1.71 に開始してから 500 |
| U3 Claude キー無し ＋ URL | 400（日本語）。**Whisper は始まらない**。削除はダウンロード終了の後 | Whisper を呼んでから 400 |
| U4 ダウンロード失敗（評価基準の生成 3秒） | 1.5秒で 400（文言同じ）。評価基準の生成（Claude）は打ち切り、Whisper は始まらない | 同じ |
| U5 ダウンロード後に Whisper（3秒）が動いている最中にスライドが失敗（2.0秒） | Whisper を 2.01 で打ち切り、2.01 で片付け・応答 | Whisper の終わり（4.71）まで待った |
| U6 URL で Whisper が接続エラー（評価基準 3秒） | 502（文言同じ）。評価基準の生成を打ち切り | 同じ |
| U7 評価基準の生成がダウンロード中に失敗 | 502。Whisper は始まらない。削除はダウンロード終了の後 | Whisper を呼んでから 502 |
| U8 ダウンロード中に要求が取り消された（`create_review` を直接呼んで 0.4秒で cancel） | 取り消しが呼び出し元に伝わる。Whisper は始まらない。**削除（1.70）はダウンロード終了（1.70）の後** | Whisper を呼んだ |
| U9 Whisper（3秒）の最中に要求が取り消された | Whisper を即打ち切り、片付け | Whisper の終わりまで待った |
| U10 対照実験: `transcribe_download` から `shield` を外した版に差し替え | スライド失敗 0.51 で **一時フォルダを先に消し**、1.51 にダウンロードが消えたフォルダへ書こうとした（`tmp_exists=False`） | — |

U10 で、`shield` が無いと「ダウンロード中に一時フォルダを消す」問題が起き、自分の確認方法がそれを見分けられることを確かめた。つまり今のコードの `shield` は必要で、正しく効いている。

## 修正で、1回目に ○ だった項目が崩れていないか

| 項目 | 判定 | 根拠 |
|---|---|---|
| ピッチ審査タブ: 第1段（スライド・書き起こし・静止画・評価基準）が同時 | ○ | P1（本物の小さな mp4 と本物の pptx）: 4つとも 0.02秒に開始し、最初の終了は 0.33秒 |
| 第2段は第1段の後、映像分析 → Jev → コメントの順（T20 維持） | ○ | P1: 第1段の最後（静止画 1.05）→ visual → jev → comments。テスト `test_review_runs_stage_one_in_parallel_then_stage_two` も映像の説明が Jev の state に入ることを確認して通る |
| コンテスト: スライド確認の後に書き起こし、静止画は最初から同時 | ○ | コンテスト側のコードは f8704aa で変更なし。`test_contest_extracts_frames_alongside_slides_and_transcription`・`test_contest_bad_slides_never_start_whisper_and_wait_for_frames` が通る（下の繰り返し実行を含む） |
| 書き起こしが空なら映像分析なし | ○ | コンテスト側は変更なし。`test_contest_video.py` の該当テストが通る |
| 一時フォルダが残らない | ○ | U1〜U9・P1〜P4 のすべてで応答時に消えていた。`%TEMP%` の実行前後の比較で、自分の実行による新しい残りは無し（増えた1件 `wctF6E3.tmp` は日付が 2026-09-25 の他のプログラムのもの） |
| 日本語のエラー文言 | ○ | 上の AC-09 のとおり、変更前と同じ文言 |
| アップロード経路の失敗時 | ○ | P2 壊れた pptx（Whisper 3秒）: Whisper を 0.51 で打ち切り、静止画の終了（1.02）を待ってから削除。P3 キー無し: Whisper を即打ち切り、静止画を待って削除 |
| 指摘4（保存失敗時の片付けの隙間）への対応 | ○ | P4: 動画の保存で例外を起こすと、どの処理も始まらないまま片付け（削除）→ エラー応答。保存をすべて済ませてから処理を始める形になっている |

## テストの変更が確かめる中身を弱めていないか（`git show f8704aa -- backend/tests`）
- 外したのは、壁時計の所要時間の上限2つ（`< STEP * 2.5`、`< STEP * 3`）だけ。同時に動いていることは、どちらのテストにも元からある `overlapped(...)`（全部が始まってから最初の1つが終わる）で確かめており、これは所要時間の上限より厳密に「同時性」を見ている。第2段の順序、T20 の映像→Jev、一時フォルダの確認はそのまま残っている。→ 弱まっていない。
- 追加された URL 経路のテスト4件は、「ダウンロードがスライド・評価基準と同時」「Whisper はダウンロードの後」「スライドが壊れていると Whisper を始めない・ダウンロードは最後まで待つ・一時フォルダが消える」「キー無しで Whisper を始めない」「ダウンロードのエラー文言がそのまま出る」を確かめている。「削除がダウンロードの後」は直接の時刻比較ではないが、先に消えるとダウンロードの偽物の書き込みが失敗して `"download" in end` が成り立たなくなるので、間接的に確かめられている（U10 で同じ仕組みを確認）。
- 失敗時のテストに残っている `< 5` 秒の上限は「Whisper の 10秒を待たなかった」ことを見るためのもので、目的が違う（下の指摘1）。

## regression-before-fix.log の再現
scratchpad に f8704aa を取り出し、`routers/review.py` だけを 6e49f80 のものに戻して `tests/test_parallel_pipeline.py` を実行:
```
FAILED tests/test_parallel_pipeline.py::test_review_url_failure_elsewhere_never_starts_whisper
FAILED tests/test_parallel_pipeline.py::test_review_url_without_claude_key_never_starts_whisper
2 failed, 10 passed
```
`regression-before-fix.log` と同じ。修正後のコードでは 12 passed。

## テストの安定性（繰り返し実行）
- 普通の状態: `test_parallel_pipeline.py`＋`test_contest_video.py` を10回連続 → 10回とも 28 passed。
- 高負荷（CPU 16個に対して、使い切る処理を24個裏で動かす。1回目の検品と同じ条件）: `test_parallel_pipeline.py` 単独 6回すべて 12 passed。2ファイル合わせて 3＋5＋8 = 16回のうち **15回 28 passed、1回だけ「1 failed, 27 passed」**（このときは失敗したテスト名を記録していなかった。そのあと `-rf` を付けて繰り返した 13回はすべて合格で、再現できなかった）。負荷で所要時間が普段の約14倍（7秒 → 約100秒）になっており、失敗時のテストに残る `< 5` 秒の上限、または時刻の重なりの確認が極端な過負荷で外れたものと思われる。1回目（高負荷で 3回に1回以上失敗）より大きく安定したので、合否には影響させない。
- 実行役からの依頼で、PC への負荷を減らすため、途中（9回目の途中）で負荷試験を止めた。負荷用のプロセスが残っていないことは確認した。

## 合否に影響しない指摘
1. 極端な過負荷で1回だけ失敗があった（上記。テスト名は未特定）。失敗時のテストの `< 5` 秒の上限は、「10秒の Whisper を待たなかった」ことを所要時間ではなく `cancelled` の記録で見ている部分もあるので、上限を 9秒程度に広げても確かめる中身は変わらない。
2. URL 経路では、他が失敗・取り消されても、ダウンロード（別スレッド、止められない）が終わるまで応答を返さない（U2・U3・U7・U8）。人間の決定（ファイルを扱う処理は終わるのを待ってから一時フォルダを消す）どおりで、お金はかからないが、実際の YouTube などではダウンロードに時間がかかるとエラーの表示まで待たされる。Claude キーが無いことは最初に分かるので、キーの確認をダウンロードを始める前に行えば待たずに済む（別タスク向けの提案）。
3. `secret-scan.log` は 1コミット目のときのもので、修正コミット `f8704aa` の分は記録が足されていない。今回自分で `git show f8704aa` を検査して問題が無いことを確かめた。
4. 1回目の指摘2・3・5・6（例外の優先順位が時間で決まる／ピッチ審査タブの壊れた pptx が 500「Internal Server Error」／コンテストの〔スライド→書き起こし〕は要求の取り消しで止まらない／評価基準の生成代）は今回の修正の範囲外で、変わっていない。U2・U5 でも壊れた pptx は 500 だった（変更前と同じ）。

## 再実行したコマンド
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
234 passed in 9.85s
$ cd frontend && npm run build
✓ built in 12.93s
$ git show f8704aa | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
670:+$ git show 6e49f80 | grep -nE ...   ← review-1.md に書かれた検査コマンドの行
671:+1020:+$ git diff --cached | grep -nE ...   ← 同上
$ git show 6e49f80 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
1020:+$ git diff --cached | grep -nE ...   ← secret-scan.log のコマンド行そのもの
$ (scratchpad の f8704aa＋6e49f80 の review.py) PYTHONIOENCODING=utf-8 <repo>/backend/.venv/Scripts/python -m pytest -q -p no:cacheprovider -rf tests/test_parallel_pipeline.py
2 failed, 10 passed   （上の2件）
$ (scratchpad の f8704aa) 同じコマンド
12 passed
$ (scratchpad の f8704aa の backend/) PYTHONIOENCODING=utf-8 <repo>/backend/.venv/Scripts/python failsafe2.py   # U1〜U10（評価役が作った確認用。scratchpad に置き、終了後に削除）
ALL OK
$ (同) failsafe3.py   # P1〜P4
ALL OK
$ for i in 1..10: pytest -q tests/test_parallel_pipeline.py tests/test_contest_video.py
28 passed ×10
```
作ったもの（コードのコピー、確認用スクリプト、負荷用スクリプト、ログ、コピーの中にできた reviews/*.json）は scratchpad から削除済み。

## check_tasks.py の出力（tasks.json の T21 を status "done"・passes true にした後）
```
$ backend/.venv/Scripts/python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 22/22 タスク
```
