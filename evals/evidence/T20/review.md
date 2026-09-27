# T20 評価役の検品結果（2回目）

- 対象: コミット `b6bfa3b`（T20 の実装）＋ `8fca579`（1回目の差し戻し `review-1.md` への修正）
- 判定: **合格**（全 AC ○、task 文の要件もすべて ○）
- 外部API（Anthropic / OpenAI / TypeSafe）は一度も呼んでいない。Claude・Whisper・Jev はすべて偽物、キーはダミーで上書き、外部への通信は遮断して実行した。`backend/.env` は読んでいない。リポジトリのコードは変更していない。
- 実行役の説明は合格の理由にしていない。以下はすべて自分で再実行した結果と、証拠ファイルを見た結果。

## 1回目の指摘（AC-09 ×: 動画の一時フォルダが採点後に残る）は直ったか → **直った**

### 修正の中身（`git show 8fca579 -- backend/app`）
- `video_frames.extract_frames_base64` が `with av.open(video_path) as container:` になり、正常終了・途中の `return []`（映像ストリームなし／長さなし）・例外のどの経路でもファイルが閉じられる。
- `contest_scorer.describe_video` は Claude の答えが空白だけなら `None` を返す（→ `visual_included: false`）。
- `routers/*`・`review_generator.py`・フロントエンドは変更なし。

### 自分で確かめたこと（リポジトリの外の scratchpad のスクリプト。PyAV で本物の 32x32・3秒の mp4 を作成し、静止画の取り出しは本物）
ガベージコレクションを止めた（`gc.disable()`）状態で、「関数が自分で閉じている」ことを確かめた。

| 場面 | 今のコード | 修正前のコード（b6bfa3b の2ファイルに戻したコピー） |
|---|---|---|
| 関数を直接呼び、直後に `os.remove`: 本物の mp4 | 静止画4枚、削除できる | 静止画4枚、**PermissionError（使用中）** |
| 同: 音声だけの mp4（AAC のみ。途中の `return []` の経路） | 0枚、削除できる | **PermissionError** |
| 同: 壊れた mp4（ランダムなバイト。例外の経路） | 0枚、削除できる | 削除できる |
| 同: 後ろ半分を切った mp4（例外の経路） | 0枚、削除できる | 削除できる |
| `/api/contest/score` に本物の mp4 を5回連続 | 5回とも 200、Claude に静止画4枚で1回、`visual_included: true`、**一時フォルダは毎回消えた** | 5回とも**一時フォルダが残った** |
| 同: 本物の動画を .webm の名前で | 200、映像あり、一時フォルダ消えた | 残った |
| 同: 音声だけの mp4 | 200、Claude 0回、state は書き起こしそのもの、一時フォルダ消えた | **残った** |
| 同: 壊れた mp4 / 切れた mp4 | 200、Claude 0回、state は書き起こしそのもの、一時フォルダ消えた | 消えた |
| `/api/review`（ピッチ審査タブ）に本物の mp4 を3回 | 3回とも 200、静止画4枚がレビュー生成に渡る、一時フォルダ消えた | **残った** |
| 同: 音声だけの mp4 / 壊れた mp4 / 切れた mp4 / mp3 | 200、静止画0枚、一時フォルダ消えた | 音声だけの mp4 は**残った** |

（`/api/review` はレビュー生成と履歴保存だけ偽物にし、静止画の取り出しとルーターの一時フォルダ処理は本物。）
→ 修正前は残り、修正後は全場面で残らない。ピッチ審査タブ（T18 からの既存の問題）も同じ修正で直っている。音声だけの mp4 も修正前は残っていたが、今は閉じられる。

### 置き換えたテストは PyAV を本当に通っているか → **通っている**
- `test_frame_extraction_releases_the_video_file`: テスト内で PyAV で mp4 を作り、fixture の偽物ではなく本物の関数（モジュール読み込み時に取っておいた `real_extract_frames`）を呼んで4枚を確認 → すぐ `os.remove`。
- `test_api_real_mp4_is_analyzed_and_its_temp_dir_removed`: `contest_scorer.extract_frames_base64` を本物に戻してから API に送り、Claude（偽物）に届いた画像が4枚であること（= 本物の取り出しを通った証拠）と、`tempfile.mkdtemp` で記録した一時フォルダが消えていることを確認。
- 修正前のコードで失敗するか: `regression-before-fix.log`（3 failed）に加えて、自分でも HEAD の backend をリポジトリの外にコピーし、`video_frames.py` と `contest_scorer.py` だけ `b6bfa3b` に戻して `tests/test_contest_video.py` を実行 → **3 failed, 13 passed**（ログと一致）。失敗理由は PermissionError（WinError 32）、一時フォルダが存在、`visual_included` が True（空白の説明）で、それぞれテストの狙いどおり。

### テストの書き換えで中身が弱められていないか（`git show 8fca579 -- backend/tests`）→ **弱められていない**
- 変更は `test_contest_video.py` のみ。削除されたのは1回目で問題になった `test_api_mp4_upload_uses_video_and_cleans_up`（偽物を包んでいたテスト）だけで、その確認項目（200、`visual_included: true`、`visual_description`、Jev の state に説明が入る、一時フォルダが消える）は新しいテストにすべて残っている。旧テストの「取り出し時にファイルがある」は、新テストでは「本物の取り出しで4枚出た」ことで、より強く確かめられている。
- 他のテスト（音声だけ・失敗・キー無し・空の書き起こし・スライド上限超え・API mp3）は変更なし。追加は2件（ファイル解放、空白の説明）。

## 再実行の結果
| 内容 | 結果 |
|---|---|
| `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q -p no:cacheprovider` | **222 passed**（`pytest.log` の 222 passed と一致） |
| 修正前コードで `tests/test_contest_video.py` | 3 failed, 13 passed（`regression-before-fix.log` と一致） |
| `cd frontend && npm run build` | 成功。出力ファイル名のハッシュ `index-BEm3s3_m.js` / `index-B1btN5Cn.css` が `build.log` と一致（8fca579 はフロントを触っていない） |
| 秘密情報の検査（`docs/safety.md` 3章の正規表現を `git show 8fca579`・`git show b6bfa3b` に適用） | 一致は、証拠ファイルに書かれた検査コマンド自体の文字列（"sk-"）だけ。キーではない。`.env` は git 管理外 |
| `pytest` 実行前後の `%TEMP%` | テストでは `tmp*` フォルダは増えなかった |

## AC ごとの判定
| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | 再実行 222 passed、`pytest.log` と一致。既存テストの削除・弱体化なし（上記） |
| AC-00b フロントエンドがビルドできる | ○ | 再実行で成功、`build.log` と同じ出力 |
| AC-00c 秘密情報が含まれていない | ○ | `secret-scan.log`（一致なし）＋自分で両コミットを検査。一致は検査コマンドの文字列のみ |
| AC-00d tasks.json のルール違反がない | ○ | `check_tasks.py` エラー0件（末尾に出力） |
| AC-08 モック Whisper の出力が Jev の state にそのまま入る／空はエラー | ○ | `test_audio_only_is_unchanged_and_never_touches_video`（mp3/m4a/wav で state == 書き起こし）、`test_jev_state_is_the_transcript_itself_without_slides_or_video` が合格。自分の API 実行でも mp3・音声だけの mp4・壊れた mp4・Claude エラー・空白の説明・キー無しで state は書き起こしそのもの。空の書き起こしは 400「発表の文字起こしが空です。…」で Claude 0回・Jev 0回 |
| AC-09 API が仕様どおりに応答する | ○ | 成功200・不正な観点400・キー未設定の日本語エラーの既存テストが合格。1回目の × の原因（一時ファイルが残る）は上記のとおり解消し、それを確かめるテストが本物の PyAV を通っていて、修正前のコードで失敗することも自分で確認した |
| AC-12 画面で点数・合計・確信度の注意が表示される | ○ | `screenshot-02-result-with-video.png` を画像で確認: 観点別の点数（40/50、17.5/50）・合計 57.5/100・「この点数は参考値です」の注意・「スライド資料・発表の音声・映像（身振り・表情）で採点しました。」・「映像から読み取った様子」。`screenshot-01-form-video.png`: 動画を選んだときの注記。修正はフロントを触っていないので今も有効 |

## task 文の要件
| 要件 | 判定 | 根拠 |
|---|---|---|
| 動画（mp4/webm）→ 静止画 → Claude が説明 → スライド・書き起こしと一緒に Jev へ | ○ | テスト＋自分の API 実行（静止画4枚、state に説明が入る、`visual_included: true`）＋`jev-state-from-ui.log` |
| ピッチ審査タブと同じ仕組みを使う | ○ | `extract_frames_base64`・`describe_presentation_visuals` を共有。ピッチ審査タブの動きは自分の実行で確認（静止画4枚が渡る、音声だけ／壊れた動画は0枚で続行、一時フォルダは消える） |
| 音声だけのときは書き起こしをそのまま渡す | ○ | AC-08 のとおり。Claude は呼ばれない |
| 映像の分析に失敗・ANTHROPIC_API_KEY 無しでも映像なしで採点を続ける | ○ | 自分の実行: Claude エラー／壊れた・切れた・音声だけの mp4／キー空 → すべて 200、`visual_included: false` |
| 採点できないとき（書き起こし空など）は有料の映像分析をしない | ○ | 自分の実行: 空の書き起こしで 400、Claude 0回。スライド上限超えのテストも合格（Whisper も呼ばない） |
| 結果画面に映像を使ったかと読み取った様子を表示 | ○ | スクショ2 |
| （追加の修正）Claude が空の文章を返したら `visual_included: false` | ○ | 正しい。空白だけの答えで `visual_included: false`・`visual_description: null`・state は書き起こしそのもの（テスト＋自分の API 実行）。説明がない映像を「使った」と表示しないので、画面の表示とも矛盾しない。普通の答えは前後の空白が取られるだけで中身は同じ |
| （1回目の指摘）採点後に一時ファイルが消える | ○ | 上記 |

## 合否に影響しない指摘
- 例外の経路（壊れた動画・音声だけの動画）でファイルが閉じられることを確かめるテストはリポジトリには無い（成功の経路だけ）。`with` で閉じる作りなので今は問題なく、自分の実行でも確認済み。将来の変更に備えるなら、音声だけの mp4 で `os.remove` できるテストがあると安心。
- 1回目からの持ち越し: `extract_frames_base64` は同期処理なので、動画の読み込み中はサーバーが待たされる（ピッチ審査タブと同じ）。動画でスライドが無いとき、state に「発表音声の書き起こしのみで審査してください。」と映像の節が同居する。
- 1回目の検品で書かれていた、実行役が以前 `%TEMP%` に残した動画入りフォルダ（tmp60u01bap、tmpfutznkod、tmpt8cbhrn6、tmpu46p964_）は、この検品の途中（10:4x 台、最初の確認では存在）で無くなっていた。評価役は触っていない（削除したのは自分の実行で作ったフォルダだけで、作成時刻で確認してから消した）。人間か別のセッションが片付けたと思われるので、念のため確認してほしい。
- 検品の途中で、作業ツリーに T20 以外の未コミットの変更（`README.md`、`backend/.env.example`、`progress.md`）が現れた。評価役の変更ではない。別の作業が並行していると思われる。

## 片付け
- 自分で作った一時フォルダ（修正前コードでの確認で残った `%TEMP%\tmp*` 15個、pytest の作業フォルダ）はすべて削除した。スクリプトと動画は scratchpad の中だけ。

## check_tasks.py の出力（tasks.json を更新した後）
```
$ backend/.venv/Scripts/python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 20/21 タスク
```
