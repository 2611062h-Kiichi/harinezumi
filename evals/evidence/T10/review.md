# T10 検品結果（評価役）

対象コミット: 6b9781c16f19de894ae061b77c592d512740172a
「画面: 音声アップロードと、観点別の点数・合計・確信度の注意を表示する結果画面を作る（保存済み Questions の選択も含む）」

## 総合判定: 合格（すべて○）

## AC ごとの判定

### AC-00a（既存のテストが全部通る） ○
自分で再実行した:
```
$ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
........................................................................ [ 54%]
............................................................             [100%]
132 passed in 3.67s
```
`evals/evidence/T10/pytest.log`（132 passed）と一致。T10 は backend を変更していないため件数も変わっていない。

### AC-00b（フロントエンドがビルドできる） ○
自分で再実行した:
```
$ cd frontend && npm run build
> tsc -b && vite build
✓ 49 modules transformed.
✓ built in 595ms
```
`evals/evidence/T10/build.log` の内容（モジュール数・成功メッセージ）と一致。再実行後 `git status --porcelain` は空で、`package-lock.json` に差分は発生しなかった（元に戻す操作は不要だった）。

### AC-00c（秘密情報なし） ○
自分で再実行した（証拠と同じコマンド）:
```
$ git add -A && git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（一致なし。grep終了コード1）
$ git status --porcelain
（差分をステージしただけの状態を git reset で戻し、以後クリーン）
```
`evals/evidence/T10/secret-scan.log` の「一致なし」と一致。`backend/.env` は開いていない・値も見ていない。

### AC-00d（check_tasks エラー0件） ○
自分で再実行した:
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 10/15 タスク
```
`evals/evidence/T10/check_tasks.log` と一致。

### AC-12（画面で音声を送ると、観点別の点数・合計・確信度の注意が表示される） ○

**スクリーンショット3枚を実際に画像として開いて確認**:
- `screenshot-01-audio-upload.png`: 「発表を採点する」画面。ファイル選択欄（fake-pitch.mp3 選択済み）、「採点する」「Questionの編集に戻る」ボタンあり。コンテスト名「学生ビジネスプランコンテスト2026」、Question 2件と表示。
- `screenshot-02-score-result.png`: 「学生ビジネスプランコンテスト2026 の採点結果」。合計 26.3 / 50。観点別に「課題の明確さ 15 / 20」（注意書きなし）、「市場規模・成長性 11.3 / 30」（注意書きあり: 「発表の中に判断材料が少ないため、この点数は参考値です。」）。
- `screenshot-03-saved-list.png`: 「保存済みのQuestionsを選ぶ」画面。「学生ビジネスプランコンテスト2026」・観点2件・2026/9/26 23:55:22 の1件が一覧表示され、「選ぶ」「戻る」ボタンあり。

**一貫性**: 3枚を通してコンテスト名「学生ビジネスプランコンテスト2026」、観点数2件（課題の明確さ／市場規模・成長性）が一致しており、上部の「ピッチ審査／コンテスト観点モード」タブも共通。日本語UIとして不自然な点はなし。本物の画面（コード上のクラス名・文言と一致）と判断した。

**確信度が低い観点にのみ注意書きが出るか**: スクショでは「課題の明確さ」（低confidenceでない）に注意書きなし、「市場規模・成長性」（progress.mdの記述どおり confidence 0.35 で low_confidence=true）にのみ注意書きあり。コード `frontend/src/components/contest/ContestScoreResultView.tsx` でも
```tsx
{r.low_confidence && (
  <p className="note criterion-confidence">
    発表の中に判断材料が少ないため、この点数は参考値です。
  </p>
)}
```
と、`results` 配列を map するループの中で観点ごとに `low_confidence` を判定しており、該当する観点だけに表示される作りになっている。文言は `docs/voice.md` 1章の「発表の中に判断材料が少ないため、この点数は参考値です。」と一言一句一致（スクショの文字列も同一）。

**計算がサーバー側で行われているか**: `ContestScoreResultView.tsx` は `result.total_points`／`result.max_total_points`／`r.points`／`r.max_points` をそのまま表示しているだけで、フロントエンドで独自に配点換算や合計を計算し直している箇所はない（`(r.points / r.max_points) * 100` はバー表示用の割合計算のみで、点数そのものの計算ではない）。サーバー側の計算は `backend/app/services/contest_scorer.py`（`score_transcript`／`round_half_up`／`LOW_CONFIDENCE_THRESHOLD`）にあり、T05 で実装済み・T10 では変更されていないことを `git show 6b9781c --stat` で確認済み（`backend/app/services/contest_scorer.py` は差分に含まれない）。

**保存済みQuestionsを選ぶ→読み込み→編集画面→音声で採点、の流れがコード上つながっているか**: `frontend/src/components/contest/ContestQuestionsPage.tsx` の状態遷移を確認。
- `CriteriaForm` の「保存済みのQuestionsを使う」→ `onUseSaved` → `status="saved-list"` → `SavedQuestionSetPicker`
- 選択 → `handleSelectSaved(id)` → `loadQuestionSet(id)` → `setQuestionSet(saved.question_set)` → `status="review"`（＝`QuestionSetReview` 編集画面）
- 新規生成のパス（`handleGenerate`→`status="review"`）とここで合流し、どちらも同じ `QuestionSetReview` の「この内容で音声を採点する」ボタン（`onProceedToScoring`）→ `status="audio-upload"` → `AudioScoreForm` → `handleScoreAudio` → `scoreAudio()` → `status="score-result"` → `ContestScoreResultView`
に一本道でつながっている。コード上分岐が途切れている箇所はない。

**LoadingStateの変更がピッチ審査画面を壊していないか**: `frontend/src/components/LoadingState.tsx` は `stages` を任意プロパティとし、デフォルト値 `DEFAULT_STAGES`（「スライドを解析中…」「音声を文字起こし中…」「AIが審査中…（1分ほどかかる場合があります）」）は変更前と同じ文言。`frontend/src/App.tsx:67` の呼び出し `<LoadingState />` は引数なしのため既定値が使われ、ピッチ審査画面の表示は変わらないことを確認した。

**スタブ・撮影中データが残っていないか**:
```
$ git show 6b9781c --stat
```
の18ファイルに scratchpad やデータファイルは含まれておらず（フロントエンドのソース・型・CSS・テスト証拠・progress.md・tasks.json のみ）、backend 側のコード（`contest_scorer.py` など）も含まれていない。
```
$ git status --porcelain
（出力なし＝クリーン）
```
現在のワーキングツリーもクリーンで、`backend/data/question_sets/`（`.gitignore` の `data/question_sets/*.json` で無視設定済み。行が存在することを確認）にも撮影時のファイルは残っていない（`ls backend/data/question_sets` は存在しないディレクトリとして返る）。progress.md の「撮影中に保存したQuestionセットのファイルは削除した」という記述と矛盾しない。

## 合否に影響しない指摘
- 特になし。T09評価時の指摘（Question並び順、解釈の見せ方）はすでにクローズ済みで、T10のコードもそれを踏襲している。
- 観点別点数の合計（15 + 11.3 = 26.3）は表示上の整合が取れている。個々の配点換算ロジック自体（サーバー側の四捨五入等）はT05で検証済みのためT10の対象外。

## 判定
tasks.json の T10 を `"status": "done"`, `"passes": true` に更新した。

## python evals/check_tasks.py の出力（最終確認）
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 11/15 タスク
```
