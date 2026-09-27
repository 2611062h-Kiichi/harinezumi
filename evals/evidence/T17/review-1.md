# T17 評価役レビュー（採用された提案 P7 の反映）

- 評価日: 2026-09-27
- 対象コミット: `6b60d45`（T17: slide limits, PPTX tables/groups, slides-only hint）
- 評価役: Agent ツールで起動した新しいサブエージェント（実行役の説明・コミットメッセージは合格理由にしていない）
- **判定: 不合格（×あり）→ status "in_progress" / passes false**

## AC ごとの判定

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存テストがすべて通る | ○ | 自分で `PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q` を再実行 → **175 passed**（`pytest.log` の 175 passed と一致）。`git diff harness-baseline -- backend/tests` は `test_contest_slide_limits.py`（新規150行）と `test_slide_extractor.py`（36行追記）の**追加のみ**で、削除・書き換えられた既存テストは0行 |
| AC-00b フロントエンドがビルドできる | ○ | 自分で `npm run build` を再実行 → `✓ built`（49 modules、`index-Dt203dL_.js 172.88 kB`。`build.log` と同じ出力） |
| AC-00c 秘密情報が含まれていない | ○ | `git show 6b60d45 \| grep -nE "sk-\|ts-[A-Za-z0-9]{8,}\|api_key\s*=\s*['\"][^'\"]+"` → 一致は1行だけで、`secret-scan.log` に書かれた**検査コマンドの文字列そのもの**（キーではない）。作業ツリーの `git diff` にも一致なし。`backend/.env` は読んでいない |
| AC-00d tasks.json のルール違反がない | ○ | `check_tasks.py` を再実行 → エラー0件（末尾に出力を貼付）。警告「T17 が基準に無い新しいタスク」は想定内 |
| AC-09 API が仕様どおりに応答する | ○ | TestClient のテスト（`test_api_oversized_pptx_is_japanese_400_without_whisper`、`test_api_silent_audio_with_slides_suggests_slides_only` ほか既存の contest API テスト）が再実行で成功。自分の追加確認（下記）でも、上限超え・ちょうど・PDF のページ超えは日本語の400/200。ただし下記「指摘1」の入力では、コンテスト API は 500 にはならないが「壊れています」という**誤った理由の**日本語400を返す（以前は読めていたファイル） |
| AC-12 画面で送ると観点別の点数・合計・確信度の注意が表示される | ○ | T17 のスクショ3枚を画像で確認: 01=注記「スピーカーノート・表・グループ化した図形の中の文字を含む…図や画像の中の文字は読み取れません」「60ページ・30,000文字（ノートを含む）まで」／02=「ページ数が多すぎます（61ページ、上限60ページ）」の日本語エラー／03=「文字起こしが空です…スライド資料だけを選び直して採点すれば、スライドだけで採点することもできます。」。結果画面そのものは T17 のスクショに無いが、`git diff a53b628 HEAD -- frontend` の変更は `AudioScoreForm.tsx` の注記だけで、結果画面のコードは T15 から変わっていないため、T15 の `screenshot-02-result-both.png`（観点別の点数・合計26.5/50・「参考値です」の注意）を画像で確認し、今も有効と判断。build も成功 |

## task 文 (a)(b)(c) の判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| (a) ページ数・文字数の上限、超えたら日本語400、書き起こしより前に確認 | ○ | `contest_scorer.check_slide_limits`（`>` で判定＝ちょうどは通る）。`score_audio` で `transcribe` の前に呼ばれる。テスト: 60ページ通過／61ページ400、上限3で3通過・4で400、文字100通過・102で400（ノート込み）、上限超えで `FakeOpenAI.calls == []`・Jev 呼び出し0。自分の追加確認: ノートだけの長いスライド（51文字/上限50）＋音声 → 日本語400で Whisper・Jev とも0回、ちょうど50文字＋音声 → 200で Whisper 1回、PDF 3ページ/上限2 → 日本語400 |
| (b) PPTX の表・グループ図形の文字を読む、画面の注記 | **×** | 表（結合セル・空セル・複数行セル）、空のグループ、入れ子グループ、グループ内の表、表とテキストの混在、グラフ（読まないが落ちない）はすべて正常に読めた（下記）。注記もスクショ01で確認。**しかし「指摘1」の回帰がある**: ピッチ審査タブで以前は読めていた PPTX が 500 になる |
| (c) 書き起こしが空のときの「スライドだけで採点」案内 | ○ | 空の書き起こし＋文字のあるスライドのときだけ文言が付く（`test_blank_transcript_with_readable_slides_suggests_slides_only`）、スライド無し・文字の無いスライドでは付かない（parametrize 2件）、API 経由でも付き Jev は呼ばれない。スクショ03で画面表示も確認 |

## 指摘1（不合格の理由）: 形の種類が決まっていない図形があると、以前は読めた PPTX が読めなくなる

`slide_extractor._shape_texts` が全ての図形で `shape.shape_type` を呼ぶようになった。python-pptx 1.0.2 の `Shape.shape_type` は、プレースホルダーでも、定義済みの形（`a:prstGeom`）・自由形（`a:custGeom`）・テキストボックス（`txBox="1"`）のどれでもない `p:sp` に対して **`NotImplementedError("Shape instance of unrecognized shape type")` を投げる**（OOXML では形の指定は省略可能なので、PowerPoint 以外のツールが書き出したファイルなどで起こりうる）。

再現（リポジトリ外の一時フォルダで、テキストボックス「本文テキスト」＋ `a:prstGeom` を取り除いた図形「図形の文字」の1枚スライドを作成）:

| 呼び出し | T17 前（`6b60d45^` の抽出処理） | T17 後 |
|---|---|---|
| `extract_from_pptx` | `['本文テキスト\n図形の文字']`（正常に読める） | `NotImplementedError` |
| ピッチ審査タブ `POST /api/slides/extract` | 200 | **500 Internal Server Error**（`review.py` は抽出の例外を捕まえていない） |
| コンテスト `POST /api/contest/score`（スライドのみ） | 読めて採点へ進む | 400「スライド資料を読み込めませんでした。ファイルが壊れていないか…」（壊れていないのに壊れていると案内され、表の文字どころか全部読めなくなる） |

ピッチ審査タブの既存の動き（読める文字は「増える（減ることはない）」という計画 2. の約束）を壊しているため、(b) を × とする。
直し方の例（評価役は直さない）: グループの判定を `shape.shape_type` ではなく `isinstance(shape, GroupShape)`（`pptx.shapes.group.GroupShape`）にする、または `shape_type` の例外を捕まえて従来どおり `has_text_frame` で読む。あわせて、この形の図形を含む PPTX のテスト（抽出・ピッチ審査タブ・コンテスト）を足すこと。

## 合否に影響しない指摘

2. 画面の上限表示（`AudioScoreForm.tsx` の `MAX_SLIDE_PAGES = 60` / `MAX_SLIDE_CHARS = 30000`）は `config.py` の値の手書きコピー。`.env` で上限を変えると画面の案内だけ古い値のままになる（既存の `MAX_MEDIA_MB` と同じやり方なので今回は許容）。
3. 文字数には、表のセルをつなぐ「 | 」やテキスト間の改行も数えられる（上限30,000に対して影響は小さい）。
4. `score_audio` と `score_materials` の両方で `check_slide_limits` が呼ばれる（2回目は無害な重複）。
5. グラフ（chart）の中の文字は読まない。画面の注記「図や画像の中の文字は読み取れません」の範囲内と判断。
6. リポジトリ直下に T17 と無関係の未追跡ファイル `Screenshot 2026-09-27 050107.png` と `pitch/` がある。コミットに混ぜないよう注意（評価役は触っていない）。

## 自分で再実行したコマンドと結果

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
175 passed in 4.60s

$ cd frontend && npm run build
✓ 49 modules transformed.
dist/assets/index-Dt203dL_.js   172.88 kB │ gzip: 57.22 kB
✓ built in 552ms

$ git diff harness-baseline --stat -- backend/tests
 backend/tests/test_contest_slide_limits.py | 150 +++++
 backend/tests/test_slide_extractor.py      |  36 +++
 2 files changed, 186 insertions(+)        # 削除行 0

$ git show 6b60d45 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
596:+$ git diff --cached | grep -nE ...     # secret-scan.log 内の検査コマンド文字列のみ
```

### 想定外の入力の確認（リポジトリ外の一時フォルダで pytest。Whisper・Jev は既存テストの偽物、ネットワークは conftest で遮断。終了後に削除）

```
抽出結果（1スライド目から順に）:
1 '結合見出し\n縦結合 | b\nc'                 # 横・縦の結合セル。重複なし
2 ''                                          # 空のグループ、空グループの入れ子
3 '見出し\nx | y\nグループ文字\nグループ内の表'  # テキスト＋表＋グループ内の表
4 'グラフ横'                                   # グラフ（読まない・落ちない）
5 '一行目\n二行目'                              # 全部空の表は無視、複数行セル
6 ''  (notes 60文字)                          # ノートだけのスライド
コンテスト API（上のPPTXのみ）            → 200、state に 結合見出し/グループ内の表/グラフ横/ノート
ノートだけ51文字（上限50）＋音声          → 400「文字数が多すぎます（51文字、上限50文字。…」Whisper 0回・Jev 0回
ノートだけ50文字（上限50）＋音声          → 200、Whisper 1回
PDF 3ページ（上限2）                      → 400「ページ数が多すぎます（3ページ、上限2ページ）…」
ピッチ審査タブ /api/slides/extract（上のPPTX） → 200
形の指定が無い図形を含むPPTX:
  contest  → 400「スライド資料を読み込めませんでした。ファイルが壊れていないか…」
  review /api/slides/extract → 500 Internal Server Error
  T17前の抽出処理: ['本文テキスト\n図形の文字'] / T17後: NotImplementedError
```

## check_tasks.py の出力


```
$ backend/.venv/Scripts/python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 15/18 タスク
```

（T17 を in_progress にした後の出力。今回は「基準に無い新しいタスク」の警告は出なかった）
