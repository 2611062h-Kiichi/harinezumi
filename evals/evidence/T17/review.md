# T17 評価役レビュー 2回目（採用された提案 P7 の反映・再検品）

- 評価日: 2026-09-27
- 対象コミット: `6b60d45`（本体）＋ `77652ce`（1回目の差し戻しへの修正）
- 評価役: Agent ツールで起動した新しいサブエージェント（実行役の説明・コミットメッセージは合格理由にしていない）
- 1回目の検品記録: `review-1.md`（(b) の回帰で不合格）
- **判定: 合格（全て○）→ status "done" / passes true**

## AC ごとの判定

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | 自分で `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q` を再実行 → **177 passed**（`pytest.log` の 177 passed と一致）。`git diff harness-baseline -- backend/tests`（基準タグ = `6b60d45`）は追加45行・削除1行で、削除1行は import に `client` を足した行の置き換えだけ。`git diff 6b60d45^ HEAD -- backend/tests`（T17 全体）も追加230行・削除0行。既存テストは弱められていない |
| AC-00b フロントエンドがビルドできる | ○ | 自分で `cd frontend && npm run build` を再実行 → `✓ built`（49 modules、`index-Dt203dL_.js 172.88 kB`。`build.log` と同じ） |
| AC-00c 秘密情報が含まれていない | ○ | safety.md 3章の grep を `git show 6b60d45` / `git show 77652ce` / 作業ツリーの `git diff` に実行。一致は検査コマンドの文字列そのもの（`secret-scan.log` と `review-1.md` 内）だけで、キーは無い。`backend/.env` は読んでいない |
| AC-00d tasks.json のルール違反がない | ○ | `check_tasks.py` を再実行 → エラー0件（末尾に出力を貼付） |
| AC-09 API が仕様どおりに応答する | ○ | TestClient のテスト（上限超え日本語400・Whisper 呼ばれない、書き起こし空＋スライドで案内付き400、形の指定が無い図形の PPTX でピッチ審査タブ・コンテストとも200 など）が再実行で成功。自分で作った PPTX（下記）でも `/api/slides/extract` 200、`/api/contest/score` 200（スライドのみ・スライド＋音声とも）。1回目の「誤った理由の400」は解消 |
| AC-12 画面で送ると観点別の点数・合計・確信度の注意が表示される | ○ | T17 のスクショ3枚を画像で確認: 01=注記「スピーカーノート・表・グループ化した図形の中の文字を含む…図や画像の中の文字は読み取れません」「60ページ・30,000文字（ノートを含む）まで」、02=「ページ数が多すぎます（61ページ、上限60ページ）」、03=「文字起こしが空です…スライド資料だけを選び直して採点すれば、スライドだけで採点することもできます。」。T17 のフロント変更は `AudioScoreForm.tsx` の注記6行だけ（`git diff 6b60d45^ HEAD --stat -- frontend`）で、77652ce はフロントを触っていない。結果画面は T15 から変わっていないため、T15 の `screenshot-02-result-both.png`（観点別 16/20・10.5/30、合計 26.5/50、「参考値です」の注意）を画像で確認し今も有効と判断。build も成功 |

## task 文 (a)(b)(c) の判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| (a) ページ数・文字数の上限、超えたら日本語400、書き起こしより前に確認 | ○ | 77652ce は `contest_scorer.py` を触っていない（1回目で○、今回もテスト再実行で成功）。`score_audio` で `check_slide_limits(slides)`（182行）が `transcribe(...)`（183行）より前にあることを再確認 |
| (b) PPTX の表・グループ図形の文字を読む、画面の注記 | ○ | **1回目の指摘は直っている**（下記）。表・結合セル・入れ子グループ・グループ内の形の指定が無い図形・プレースホルダー・グラフ・画像・コネクタ・自由形・セルの txBody なしを混ぜた PPTX で、抽出・ピッチ審査タブ・コンテストの3経路とも正常。T17 前の抽出処理で読めていた行はすべて今も読める（読める文字は増えるだけ）。注記はスクショ01で確認 |
| (c) 書き起こしが空のときの「スライドだけで採点」案内 | ○ | 77652ce は該当コードを触っていない。関連テスト（案内が付く／スライド無し・文字の無いスライドでは付かない／API 経由）が再実行で成功。スクショ03で画面表示も確認 |

## 1回目の指摘（形の指定が無い図形で NotImplementedError）は直ったか → 直っている

`_shape_texts` のグループ判定が `shape.shape_type == MSO_SHAPE_TYPE.GROUP` から `isinstance(shape, GroupShape)` に変わり、`shape_type` はどこからも呼ばれなくなった。

`_shape_texts` が各図形で呼ぶ属性と、T17 前には読めていた図形で新しく例外が出る経路が無いかの確認（python-pptx 1.0.2 のソースを読んで確認）:

| 呼ぶもの | 対象 | 例外の可能性 |
|---|---|---|
| `isinstance(shape, GroupShape)` | 全図形 | なし（属性を読まない） |
| `shape.has_table` | グループ以外の全図形 | `BaseShape`（p:sp・p:pic・p:cxnSp・プレースホルダー等）は常に False を返すだけ。`GraphicFrame` だけ `a:graphic/a:graphicData/@uri` を読む。この2つは OOXML の仕様で必須なので、正しいファイルでは例外は出ない（仕様違反のファイルは下の「合否に影響しない指摘1」） |
| `shape.table.rows` / `row.cells` / `cell.text` | 表だけ | `cell.text` は txBody が無いセルでも作って読む。セルの txBody を消した表でも正常だった |
| `shape.has_text_frame` / `text_frame.text` | 表以外 | T17 前と同じ呼び方 |
| `shape.shapes` | グループだけ | 入れ子3段でも正常 |

再現と確認（リポジトリ外の scratchpad に pytest ファイルを作り、`-p tests.conftest` でネットワーク遮断・偽の Whisper/Jev を使って実行。終了後に削除）:

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -p tests.conftest -p no:cacheprovider -q -s --rootdir=. <scratchpad>/test_review2.py
# 5枚の PPTX: 1=テキストボックス＋形の指定なし図形＋spPr が空の図形＋空の形なし図形
#            2=グループ＞形なし、グループ＞グループ＞形なし、3段目＞形なし、表
#            3=タイトル・本文プレースホルダー＋画像＋コネクタ
#            4=結合セルの表（txBody なしのセル含む）＋グラフ＋自由形（custGeom）
#            5=SmartArt 風の未知 uri の graphicFrame＋形なし図形＋ノート
新: ['本文テキスト\n形なし1\nspPr空の図形', 'グループ内形なし\n入れ子形なし\n3段目形なし\n表A\n表D',
     'タイトル\n本文プレースホルダー', '結合見出し\n縦結合 | b\n自由形', '最後の形なし']
T17前(6b60d45^): ['本文テキスト\n形なし1\nspPr空の図形', '', 'タイトル\n本文プレースホルダー', '自由形', '最後の形なし']
  → T17 前に読めた行はすべて新しい結果にも含まれる（テストで確認）。ノートも同じ
1回目の検品時点(6b60d45)の抽出処理: 同じ PPTX で NotImplementedError（このテスト資料で本当に不具合が再現することを確認）
ピッチ審査タブ POST /api/slides/extract → 200（上の「新」と同じ中身）
コンテスト POST /api/contest/score（スライドのみ）→ 200、Jev の state に 形なし1/3段目形なし/表A/表D/自由形/最後の形なし/ノート
コンテスト POST /api/contest/score（スライド＋音声）→ 200
形なし図形1つだけの PPTX → 抽出OK、/api/slides/extract 200、/api/contest/score 200
5 passed
```

リポジトリのテスト `test_shape_without_geometry_is_still_read`・`test_geometry_less_shape_reads_in_both_modes` も、抽出・ピッチ審査タブ・コンテストの3経路を確かめており、`regression-before-fix.log` で修正前は失敗していたことが記録されている。

## 合否に影響しない指摘

1. OOXML の仕様違反のファイル（`p:graphicFrame` に必須の `a:graphic` が無い）は、T17 前は読み飛ばせていたが、今は `has_table` で `InvalidXmlError` になる（ピッチ審査タブ 500、コンテストは「壊れています」の400）。ただし壊れたファイルでピッチ審査タブが500になるのは T17 前からの動き（ZIP でない .pptx でも500を確認）で、正しいファイルでは起きない。ピッチ審査タブの抽出の例外を400にするかは別の提案にしてよい。
2. `p:contentPart`（手書きインク）を含むスライドは python-pptx の中で `AttributeError` になる。T17 前の抽出処理でも同じく失敗するので回帰ではない。
3. 1回目の指摘2（画面の上限表示 `MAX_SLIDE_PAGES`/`MAX_SLIDE_CHARS` が config.py の手書きコピー）は未対応のまま（progress.md に明記あり）。
4. `secret-scan.log` は 6b60d45 のときのもので、77652ce の分は取り直していない（評価役が自分で検査し問題なし）。
5. リポジトリ直下に T17 と無関係の未追跡ファイル `Screenshot 2026-09-27 050107.png` と `pitch/` がある。コミットに混ぜないよう注意（評価役は触っていない）。

## 自分で再実行したコマンドと結果

```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
177 passed in 4.52s

$ cd frontend && npm run build
✓ 49 modules transformed.
dist/assets/index-Dt203dL_.js   172.88 kB │ gzip: 57.22 kB
✓ built in 554ms

$ git diff harness-baseline --stat -- backend/tests
 backend/tests/test_contest_slide_limits.py | 22 +++++++++++++++++++++-
 backend/tests/test_slide_extractor.py      | 24 ++++++++++++++++++++++++
 2 files changed, 45 insertions(+), 1 deletion(-)   # 削除1行は import 行の置き換え

$ git diff 6b60d45^ HEAD --stat -- backend/tests
 2 files changed, 230 insertions(+)                  # 削除0行

$ git show 77652ce | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
415, 467 行: review-1.md 内の検査コマンド文字列のみ
$ git show 6b60d45 | grep -nE ...   → 596 行: secret-scan.log 内の検査コマンド文字列のみ
$ git diff | grep -nE ...           → 一致なし
```

## check_tasks.py の出力

```
$ backend/.venv/Scripts/python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 16/18 タスク
```

（T17 を done / passes true にした後の出力）
