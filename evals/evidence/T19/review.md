# T19 検品記録（評価役）

- 対象: コミット `9e7705b`（親 `2941051`）。HEAD = `9e7705b`（`git diff 9e7705b HEAD -- backend/app frontend/index.html` は空）
- 検品日: 2026-09-27
- 判定: **合格（全 AC ○、task 文の (a)(b)(c)(d) もすべて満たす）**
- 外部API（Anthropic / OpenAI / TypeSafe）は呼んでいない（すべて偽物）。`backend/.env` は読んでいない。リポジトリ内のコードは変更していない。

## 共通 AC

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a 既存のテストがすべて通る | ○ | `pytest.log`（206 passed）。評価役が `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q -p no:cacheprovider` を再実行 → **206 passed in 4.53s**（証拠と同じ件数・失敗0）。`git show 9e7705b -- backend/tests` は追加のみ（`-` で始まる削除行0件）で、既存テストは弱められていない |
| AC-00b フロントエンドがビルドできる | ○ | `build.log`。評価役が `cd frontend && npm run build` を再実行 → `tsc -b && vite build` 成功、出力（index.html 0.41kB / index-BQsVL9te.css 9.08kB / index-vEwb3NHC.js 176.65kB）が証拠と一致 |
| AC-00c 秘密情報が含まれていない | ○ | `secret-scan.log`（一致なし）。評価役が `git show 9e7705b \| grep -nE "sk-\|ts-[A-Za-z0-9]{8,}\|api_key\s*=\s*['\"][^'\"]+"` を実行 → 一致は1行のみで、`secret-scan.log` に書かれた検査コマンドの文字列そのもの（キーではない） |
| AC-00d tasks.json のルール違反がない | ○ | `check_tasks.log`。評価役の再実行結果は末尾に記載（エラー0件。警告1件は想定内の「T19 が基準に無い新しいタスク」） |
| AC-09 API が仕様どおりに応答する | ○ | `pytest.log`（TestClient 使用の追加テスト: 履歴 200、項目数不一致 502、形式エラー 400 日本語）。評価役も下記の使い捨てスクリプト（TestClient＋偽物）で `/api/review`・`/api/rubric/preview`・`/api/reviews/history` を実際に叩いて確認。キー未設定時の日本語エラー（`ANTHROPIC_API_KEYが設定されていません。`）は T19 で変更されていない経路で、`test_contest_api.py` で確認済み・全体テスト通過 |

## 修正前に失敗するテストか（テストが中身を確かめているか）

`before-fix.log` の再現: `git archive HEAD backend` を scratchpad に展開し、`schemas.py`・`routers/review.py`・`review_generator.py` だけを `9e7705b^` の版に戻して `tests/test_merged_review_features.py` を実行 → **6 failed, 22 passed**（追加6件がすべて失敗）。証拠と一致。展開したコピーは削除済み。

## task 文の要件

### (a) levels の無い古い履歴が読めるか — ○
- `CriterionScore.levels` を `Field(default_factory=list)` に変更（schemas.py）。
- 評価役の確認: levels の無い古い形の履歴（confidence も無い形も含む2件）を一時フォルダに置き `/api/reviews/history` → **200**、`levels == []`。
- 弱くなった所が無いか:
  - `review_generator.generate_review` は Jev あり・なしの両経路で `CriterionScore(..., levels=c["levels"])` を必ず渡している（`c["levels"]` はキー参照なので、無ければ KeyError で気づける）。基準の出どころ4通り（汎用の既定・ビジネス・項目名指定・編集済み JSON）すべてで、新しい審査結果の各項目に **levels が5個入る** ことを TestClient で確認。保存した新しい結果を履歴から読み直しても5個のまま。
  - 静的ルーブリックは `test_every_criterion_has_unique_id_and_five_levels` で5段階が保証されている。
  - `CriterionCard.tsx` は `criterion.levels.length > 0 &&` のときだけ「審査基準を見る」を出す。API は既定値で必ず `[]` を返すので、空のときも壊れない（`types/review.ts` の `levels: string[]` と整合）。

### (b) 項目数不一致 → Jev も審査本体の Claude も呼ばずに日本語 502 — ○
- `generate_rubric_from_names` で `len(result.criteria) != len(names)` なら 502「評価項目3個分の判定基準を作れませんでした。もう一度お試しください。」。
- 評価役の確認（3項目指定、Claude の返答 1・2・4・10 個）: `/api/review` はすべて **502・上記の日本語**、Jev 呼び出し **0回**、Claude 呼び出しは判定基準作成の1回（`GeneratedLevelsOutput`）だけで、審査本体（`PitchReviewLLMOutput`）は **呼ばれない**。`/api/rubric/preview` も同じ 502。
- 数が合うとき: 「チーム／課題／市場」の順で指定し、Claude が別名を返しても、結果の名前と順番はユーザー指定のまま、判定基準は位置で対応（`0-L1, 1-L1, 2-L1`）、Jev に渡る instructions もユーザーの名前。プレビューも同じ。既存テスト `test_user_named_criteria_keep_the_users_names_and_order` も通過。

### (c) 編集プレビューの形式エラーが日本語だけ — ○
`/api/review` に `custom_rubric_json` を24通り送った結果（英字3文字以上の並びが detail に無いことを機械的に確認）:

| 入力 | 結果 |
|---|---|
| levels 4個 / 6個 / 空 / 無し / 文字列 / 数字の配列 / null の配列 | 400「評価基準の1番目の項目の形式が正しくありません（段階: 5個以上にしてください）」等、すべて日本語 |
| name が数字 / null / 無し | 400「（名前: 入力の形が正しくありません）」「（名前: 入力してください）」 |
| 項目が null / 文字列 / 数字 / 配列 | 400「（入力の形が正しくありません）」 |
| 2番目の項目だけ不正 | 400「評価基準の2番目の項目の…」 |
| 空配列 / 11項目 / オブジェクト / JSON文字列 / JSON null | 400「評価基準は1〜10項目で指定してください。」 |
| JSONとして壊れている | 400「評価基準の形式が正しくありません。」 |
| name が空文字 / 空白だけ、余計なキー付き | 200 で受け付け（エラーにはならない。下の指摘1） |

500 や英語の生メッセージは1件も出なかった。スクリプトは scratchpad で実行し、削除済み（履歴の保存先も一時フォルダに差し替え、リポジトリ内には何も書いていない）。

### (d) 使っていないフォントの読み込み削除 — ○
- `index.html` から preconnect 2行と Space Grotesk / Inter の stylesheet を削除。
- `frontend/`（node_modules・dist を除く）を `grotesk|googleapis|gstatic|\bInter\b` で検索 → **0件**。`font-family` は `index.css` の「Hiragino Kaku Gothic ProN, Yu Gothic, system-ui」と `inherit` のみ。コンポーネントに `fontFamily` の指定なし。

## 合否に影響しない指摘
1. 編集した評価基準の **name が空文字・空白だけ** でも受け付けられ、名前の無い項目で審査が進む（`GeneratedCriterion.name` に最小文字数の制約が無い。T18 のマージ以前からの挙動で、T19 の範囲外）。levels の各文が空文字でも同様に通ると考えられる。必要なら、空白を除いて1文字以上を必須にする提案を検討。余計なキーは無視されるだけで問題なし。
2. (b) の追加テストは `resolve_rubric` を直接呼ぶ形で、「審査本体の Claude も呼ばれない」ことまでは確かめていない（評価役が `/api/review` 経由で確認済み。コード上も `resolve_rubric` で例外が出るので、審査本体に届かない）。
3. `/api/review` のキー未設定時の日本語エラーを確かめるテストは無い（コンテスト API 側にはある）。T19 では変更していない経路。
4. P8 の時点では「履歴0件」だったが、今 `backend/data/reviews/` に 2026-09-27 09:21 作成の履歴が2件ある（どちらも levels 付きの新しい形。評価役の作業より前に作られたもの。T18 の画面確認で作られたと思われる）。読み込みに問題はない。

## check_tasks.py の再実行結果
```
$ backend/.venv/Scripts/python evals/check_tasks.py
WARN : T19: 基準に無い新しいタスクです。人間が追加したなら基準タグを更新してください。
結果: エラー 0 件 / 警告 1 件 / 完了 18/20 タスク
```
