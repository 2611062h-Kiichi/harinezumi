# T20 評価役の検品結果

- 対象: コミット `b6bfa3b`（T20: コンテスト観点モードでも動画なら映像を分析する）
- 判定: **不合格**（AC-09 が ×。アップロードした動画の一時ファイルが採点後に消えない）
- 外部API（Anthropic / OpenAI / TypeSafe）は一度も呼んでいない。`backend/.env` は読んでいない。

## 再実行の結果
| 内容 | 結果 |
|---|---|
| `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q -p no:cacheprovider` | 220 passed（`pytest.log` と一致） |
| `pytest tests/test_contest_video.py` | 14 passed |
| `cd frontend && npm run build` | 成功。出力ファイル名のハッシュも `build.log` と一致（index-BEm3s3_m.js / index-B1btN5Cn.css） |
| `git show b6bfa3b \| grep -nE "sk-\|ts-[A-Za-z0-9]{8,}\|api_key\s*=\s*['\"][^'\"]+"` | 1件だけ一致するが、`secret-scan.log` に書かれた検査コマンド自体の文字列（"sk-"）で、秘密情報ではない |
| `git show b6bfa3b -- backend/tests` | 追加は新規ファイル `test_contest_video.py` のみ。既存テストの削除・変更なし |
| scratchpad のスクリプトでアプリを動かす（Whisper・Jev・Claude は偽物、キーはダミーで上書き、外部通信は遮断、静止画の取り出しは本物の PyAV） | 下の「自分で確かめたこと」参照 |

## 自分で確かめたこと（偽物のAI＋本物の 64x64・5秒の mp4 を API `/api/contest/score` に送信）
| 場面 | 結果 |
|---|---|
| mp4 | 200。Claude（偽物）に静止画4枚で1回だけ依頼、Jev の state に映像の節が入り、`visual_included: true` |
| mp3 | 200。Claude 呼び出し0回、state は書き起こしそのもの、`visual_included: false` / `visual_description: null` |
| 壊れた webm（静止画が取れない） | 200。Claude 呼び出し0回、state は書き起こしそのもの |
| Claude がエラー | 200。映像なしで採点が続く |
| 書き起こしが空 | 400（日本語）。Claude 呼び出し0回、Jev 呼び出し0回 |
| ANTHROPIC_API_KEY が空 | 200。Claude 呼び出し0回 |
| **一時ファイル** | **mp4 で静止画を取り出せたとき、アップロードした動画が `%TEMP%\tmpXXXX\tmpYYYY.mp4` に残る（連続7回中7回）** |

原因: `backend/app/services/video_frames.py` の `extract_frames_base64` が `av.open()` した動画を閉じない。Windows では開いたままのファイルは消せないので、`routers/contest.py` の `shutil.rmtree(tmp_dir, ignore_errors=True)` が黙って失敗する。直接確かめた結果: 取り出し直後の `os.remove` は PermissionError、`gc.collect()` の後なら消せる（= ガベージコレクション待ちで開きっぱなし）。実行役の画面確認のときのものと思われる動画（4868バイト、10:30 と 10:32）も `%TEMP%\tmpfutznkod`・`%TEMP%\tmpu46p964_` に残っている（評価役が作ったものではないので消していない）。

`test_api_mp4_upload_uses_video_and_cleans_up` が見逃した理由: `real_extract = contest_scorer.extract_frames_base64` を読んだ時点で、fixture がすでに偽物（`["AAAA","BBBB"]` を返すだけ）に差し替えているため、PyAV を一度も通らない。テストの名前どおりのこと（本物の取り出し後に一時ファイルが消える）を確かめていない。

## AC ごとの判定
| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存テストがすべて通る | ○ | 再実行 220 passed。`pytest.log` と一致。既存テストは弱められていない |
| AC-00b フロントエンドがビルドできる | ○ | 再実行で成功、`build.log` と同じ出力 |
| AC-00c 秘密情報が含まれていない | ○ | コミットの差分を検査。一致はログ内の検査コマンド文字列のみ。`.env` はコミットに無い |
| AC-00d tasks.json のルール違反がない | ○ | `check_tasks.py` エラー0件（末尾に出力） |
| AC-08 モック Whisper の出力が Jev の state にそのまま入る | ○ | `test_audio_only_is_unchanged_and_never_touches_video`（mp3/m4a/wav で state == 書き起こし）、`test_jev_state_is_the_transcript_itself_without_slides_or_video`、既存の test_contest_audio も合格。自分の API 実行でも mp3 の state は書き起こしそのもの。空の書き起こしは 400 |
| AC-09 API が仕様どおりに応答する | **×** | 成功200・不正な観点400・キー未設定の日本語エラーは既存テストを含め合格。ただし動画を送ると一時ファイル（ユーザーの発表動画）が採点後も残り、証拠のテスト `test_api_mp4_upload_uses_video_and_cleans_up` は本物の処理を通らないため「消える」ことを確かめていない（roles.md の不合格の例「テストが AC の中身を確かめていない」に当たる） |
| AC-12 画面で点数・合計・確信度の注意が表示される | ○ | `screenshot-02-result-with-video.png`: 観点別点数・合計 57.5/100・「参考値です」の注意、「スライド資料・発表の音声・映像（身振り・表情）で採点しました。」、「映像から読み取った様子」が表示。`screenshot-01-form-video.png`: 動画の注記が表示 |

## task 文の要件
| 要件 | 判定 | 根拠 |
|---|---|---|
| 動画（mp4/webm）→ 静止画 → Claude が説明 → スライド・書き起こしと一緒に Jev へ | ○ | テスト2種＋`jev-state-from-ui.log`＋自分の実行 |
| ピッチ審査タブと同じ仕組みを使う | ○ | `describe_presentation_visuals`・`build_user_prompt`・`extract_frames_base64` を共有。`review_generator.py`・`routers/review.py` は差分なし → ピッチ審査タブの動きは変わっていない |
| 音声だけのときは書き起こしをそのまま渡す | ○ | 上記 AC-08 |
| 映像の分析失敗・キー無しでも映像なしで採点を続ける | ○ | テスト＋自分の実行（Claude エラー・静止画なし・キー空） |
| 採点できないとき（書き起こし空・スライド上限超え）は有料の分析をしない | ○ | テスト＋自分の実行。スライド上限超えは Whisper も呼ばない |
| 結果画面に映像を使ったかと読み取った様子を表示 | ○ | スクショ2 |
| （依頼の確認項目）`ContestScoreResult` の追加項目が既存を壊さない | ○ | 既定値つき。コンテストの採点結果は保存されていない（保存は Question セットのみ）。フロントは値が無くても表示が崩れない |
| （依頼の確認項目）一時ファイルが採点後に消える | **×** | 上記。動画が `%TEMP%` に残る |

## 差し戻し内容（直し方の例）
1. `video_frames.extract_frames_base64` で `with av.open(video_path) as container:` を使い、必ず閉じる。
2. 本物の小さな動画（テスト内で PyAV で作れる）を API に送り、採点後に一時フォルダが消えていることを確かめるテストを足す（fixture の偽物を包まない）。
3. 修正前のコードでそのテストが落ちることを `before-fix.log` に残す。

## 合否に影響しない指摘
- ピッチ審査タブ（`routers/review.py`）も同じ関数を使うので、同じ一時ファイルの残りがある（T18 からの既存の問題）。上の修正1で両方直る。
- `extract_frames_base64` は同期処理で、async の中から呼ばれるので、動画の読み込み中はサーバー全体が待たされる（ピッチ審査タブと同じ。長い動画だと気になるかもしれない）。
- Claude が空の文章を返すと `visual_description` が `""` で `visual_included: true` になり、state が書き起こしそのものでなくなる（映像の節は付かない）。まれな場面。
- 動画でスライドが無いとき、state に「発表音声の書き起こしのみで審査してください。」と映像の節が同居する（ピッチ審査タブと同じ文言で、少し矛盾して読める）。
- `jev-state-from-ui.log` の「vision call」が2回なのは、画面で2回採点したため（`%TEMP%` の2つの残りと時刻が合う）。state は最後の1回分だけ。

## check_tasks.py の出力（tasks.json を更新した後）
```
$ backend/.venv/Scripts/python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 19/21 タスク
```
（「基準に無い新しいタスク」の警告が出ないのは、基準タグ `harness-baseline` が今は `b6bfa3b`（T20 の実装コミット）を指していて、基準に T20 が入っているため。実行役の `check_tasks.log` の時点では警告が出ていたので、コミット後にタグが動かされている。人間が更新したのなら問題なし。AI が動かしたのなら「基準タグの更新は人間待ち」という progress.md の記述と食い違うので、人間に確認してほしい）
