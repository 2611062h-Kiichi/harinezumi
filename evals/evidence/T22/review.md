# T22 評価（評価役・別サブエージェント）

- 対象コミット: `a0c5add`（T22: redesign the UI）
- 読んだもの: `evals/acceptance.md`、`tasks.json` の T22、`progress.md` の作業計画 T22、`evals/evidence/T22/` 一式（before/after の PNG 18枚を画像として開いて比較）、`git show a0c5add -- frontend/`、`frontend/src/index.css` 全体、`backend/app/services/contest_scorer.py`
- 外部 API（Anthropic / OpenAI / TypeSafe）は呼んでいない。`backend/.env` は読んでいない。リポジトリのコードは変えていない

## 判定

| AC | 判定 | 根拠 |
|---|---|---|
| AC-00a | ○ | 評価役が `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q` を再実行 → **234 passed**。`pytest.log`（234 passed）と一致 |
| AC-00b | ○ | 評価役が `cd frontend && npm run build` を再実行 → 成功。出力ファイル名とサイズ（`index-C8fcDHTb.css` 22.52 kB、`index-DThxBFyz.js` 178.89 kB）まで `build.log` と一致 |
| AC-00c | ○ | `git show a0c5add \| grep -nE "sk-\|ts-[A-Za-z0-9]{8,}\|api_key\s*=\s*['\"][^'\"]+"` → 一致は `secret-scan.log` の中に書かれたコマンド文字列そのもの（453行目）だけで、秘密情報は無し。偽物サーバー `stub_t22.py` のキーはダミー（`screenshot-dummy`）|
| AC-00d | ○ | `check_tasks.py` がエラー0件（下に出力を貼付。T22 の「基準に無い新しいタスク」警告は想定内）|
| AC-11 | ○ | `after-04-contest-form(.png/-mobile.png)` に観点の入力欄（コンテスト名・名前・説明・配点）、`after-05-contest-questions.png` に生成結果（Jevへの質問文・段階1〜5）と編集欄（テキストエリア・保存名）が写っている。評価役の再現でも質問文テキストエリアに入力 → 値が反映されることを確認 |
| AC-12 | ○ | `after-07-contest-result.png` に観点別の点数（32/40、21/60）・合計（53/100 のゲージ＋「合計 53 点（100 点満点）」）・確信度の注意（「発表の中に判断材料が少ないため、この点数は参考値です。」）が表示されている。ピッチ審査側も `after-03-review-result.png` に点数・合計・AI確信度 |

**総合: 合格（全 AC ○）**

## 見た目の評価（before と after の比較）
- 良くなっている。灰色一色の平らな画面から、暖かいクリーム色の背景（淡いグラデーション＋紙のざらつき）、角の丸い白いカード、ハリネズミのロゴつきヘッダー、切り替えスイッチ風タブになり、まとまりが出た
- 方向性は保たれている。背景は明るいまま、アクセントは以前と同じオレンジ系（`#b8543a`）1色。暗いテーマや紫・青の「AIっぽいグラデーション」は無い（CSS の色はすべて暖色系の変数。`color-scheme: light` 固定）
- 点数: 総合点が円形ゲージになり一目で分かる。良かった点はチェック印、改善提案は番号つきのカードで読みやすくなった
- 読み込み中: 回るだけ → 「今どの手順か」が分かる一覧（済み=チェック、現在=強調）
- 崩れ: 証拠のスクショと評価役の再撮影（1100px / 375px）の両方で、文字の切れ・重なり・はみ出しは見当たらない。375px 幅で全画面（両タブの入力→結果）の `scrollWidth` = `clientWidth`（横はみ出し無し）

## 機能を変えていないか（`git show a0c5add -- frontend/src`）
- API 呼び出し・状態遷移・ボタンの onClick は変更なし。変わったのはマークアップと className、style の指定方法のみ
  - `App.tsx`: タブを `<header>` 内へ移動し、ロゴとキャッチコピー（「ピッチを、本番の審査基準で採点する」）を追加。タブの文言・onClick は同じ。`aria-label`・`aria-current` を追加
  - `CriterionCard.tsx` / `ContestScoreResultView.tsx`: 棒の幅を `width: X%` → CSS 変数 `--fill` と `transform: scaleX()` に。再現で `matrix(0.8,…)`（4/5 = 0.8）になることを確認
  - `ReviewResult.tsx`: 総合点の数字 → `ScoreGauge`（同じ `animatedScore` を表示）。一言講評・要約・注記はそのまま
  - `LoadingState.tsx`: 現在の段階の文言はそのまま表示し、その下に手順一覧を追加。`role="status" aria-live="polite"` を追加
  - `StrengthsList.tsx`: `ul` に className を追加しただけ
- 既存の文言・操作は消えていない（両タブの流れを再現し、使われているボタン名・見出しがすべて見つかった）
- コンテスト観点モードの結果画面で増えた文言の事実確認:
  - 「合計 {total_points} 点（{max_total_points} 点満点）」: 以前ゲージの無い「53 / 100」で出していた値と同じ2つの値
  - 「観点ごとの点数は、Jev の判定を配点に合わせて換算したものです。」: `contest_scorer.to_points()` が `jev_score / (段階数-1) × 配点` を四捨五入して観点の点を出し、合計はその和（`score_materials`）なので **事実として正しい**。偽物の Jev の値でも 3.2/4×40=32、1.4/4×60=21 と画面の値が一致

## アクセシビリティ
- フォーカスの輪: 全体に `:focus-visible { outline: 2px solid accent; outline-offset: 3px }`。入力欄は輪の代わりに枠の色＋4px の影。再現で Tab 移動するとタブボタンに 2px の輪、select に影の輪が出ることを確認。旧 CSS の `summary:focus-visible` 専用ルールは消えたが、全体ルールで同じ見た目が出る
- スキップリンク: 最初の Tab で表示され、Enter で `#main-content` に移動（再現で確認。動きを減らす設定でも同じ）
- 動きを減らす設定: `prefers-reduced-motion: reduce` で全アニメーション・トランジションを 1ms・1回に。再現（Playwright の reducedMotion）でゲージのアニメーション時間が 0.001s、棒とゲージは最終の値で表示されることを確認
- ゲージの読み上げ: `role="img"` と `aria-label="68 / 100"`（コンテストは「53 / 100」）。中の数字も文字として残っている
- 文字のコントラスト（WCAG の計算式で評価役が計算）: 本文 16:1、補足文（`--text-muted`）背景により 4.8〜5.4:1、白文字×オレンジのボタン 4.8:1、確信度の注意 5.7:1 → いずれも基準 4.5:1 以上

## クラス名の抜け落ち
- `src` の `className` で使われているクラスと `index.css` で定義されているクラスを照合。使われているのに定義が無いのは `criterion-name` だけで、これは **変更前の CSS にも無かった**（親の `.criterion-header` の太字で表示されている）ので T22 による抜け落ちではない
- 変更前にあって今は無いクラスは `overall-score` のみで、コンポーネント側でも使われなくなっている（ゲージに置き換え）

## 外部から読み込むもの（Google Fonts）
- `index.html` に Google Fonts（Zen Kaku Gothic New / Outfit、`display=swap`）の読み込みを追加。スクリプトではなく CSS とフォントファイルだけで、利用者のデータは送られない（送られるのは閲覧者の IP とブラウザ情報のみ）
- 読み込めない環境（オフライン等）でも `display=swap` と代わりのフォント（Hiragino / Yu Gothic / system-ui）指定があるので、文字が消えることは無く表示が崩れるだけで済む
- 問題なしと判断（下の「指摘」に、気にする場合の代案を記載）

## 評価役が自分で行った画面確認
- scratchpad に作った一時フォルダで、`stub_t22.py` をポートだけ 8765 に変えた偽物サーバー（外部AIはすべて偽物・キーはダミー・履歴保存なし）と、リポジトリ外の起動スクリプトで Vite を 5180 番（`/api` を 8765 へ転送）に立てた。8000 / 5173 の開発サーバーには触れていない
- 1100px・375px・1100px＋動きを減らす設定 の3通りで、両タブの流れ（入力 → 評価基準の確認 → 審査 → 結果、観点入力 → Question 生成 → 編集 → 採点 → 結果）を実行。ブラウザのエラー 0 件、横はみ出し 0 件
- `backend/data/reviews` は 0 件のまま（増えていない）。終わったあと一時フォルダとサーバーは片付けた

## 合否に影響しない指摘（改善のアイデア）
1. **薄い文字色 `--text-faint`（#a39487）のコントラストが 2.9:1** と低い。使われているのは「観点1」の番号、審査基準の「1点」〜「5点」、ゲージの「/ 100」、読み込み中のまだの手順、入力欄の見本文字など。**「観点1」と「1点」は変更前は `--text-muted`（約 5:1）だった**ので、少し読みにくくなった。補足的な文字なので合否は○としたが、`question-editor-index` と `criterion-level-num` は `--text-muted` に戻すのがおすすめ
2. タブの `aria-current="page"` は「ページの場所」を表す属性で、切り替えボタンには `aria-pressed` のほうが意味として合う（読み上げの実害は小さい）
3. `LoadingState` は一覧ごと `aria-live` の中にあるため、段階が進むたびに一覧全体が読み上げられる可能性がある。現在の段階の `<p>` だけを live にするとすっきりする
4. `.overall-score-max` の CSS は使われなくなったので消してよい
5. フォームの横並びボタン（「採点する」と「Questionの編集に戻る」、「観点を追加する」と「Questionを生成する」）が隙間なくくっついている。変更前からの状態だが、`.upload-form button` などにも `margin-right` を足すと良い
6. Google Fonts を避けたい場合（オフライン発表会場・プライバシー重視）は、フォントファイルを `frontend/public` に置いて自前で配信する方法がある
7. 説明文（`.lead`）に `max-width: 60ch` が付き、1100px 幅でカードの右側に大きな空きが出る。好みの範囲

## check_tasks.py の出力
```
$ backend/.venv/Scripts/python evals/check_tasks.py
WARN : T22: 基準に無い新しいタスクです。人間が追加したなら基準タグを更新してください。
結果: エラー 0 件 / 警告 1 件 / 完了 23/23 タスク
```
