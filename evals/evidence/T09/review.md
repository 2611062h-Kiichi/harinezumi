# T09 評価役レビュー

対象コミット: `4948437`（Add contest-mode UI: criteria input and Question review/edit (T09)）
評価日: 2026-09-26
評価役: 新規サブエージェント（実行役とは別セッション）

## 変更内容の確認（`git show 4948437 --stat`）
- 新規: `frontend/src/api/contestApi.ts`、`frontend/src/components/contest/{ContestQuestionsPage,CriteriaForm,QuestionEditor,QuestionSetReview}.tsx`、`evals/evidence/T09/*`
- 追記: `frontend/src/App.tsx`（モード切替タブ）、`frontend/src/index.css`（新規クラス追加のみ、既存クラスは変更なし）、`frontend/src/types/contest.ts`（`SavedQuestionSet` 系の型追加）、`progress.md`、`tasks.json`
- backend 側の変更ファイルは無し（`git show 4948437 --stat` に `backend/` の行なし）

## 条件ごとの判定

### AC-00a（既存のテストがすべて通る） — ○
- 自分で再実行:
  ```
  $ cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python -m pytest -q
  ........................................................................ [ 54%]
  ............................................................            [100%]
  132 passed in 3.64s
  ```
- 証拠 `evals/evidence/T09/pytest.log`（132 passed）と完全一致。T08 終了時点と同じ132件のまま（backend を変更していないタスクなので妥当）。

### AC-00b（フロントエンドがビルドできる） — ○
- 自分で再実行:
  ```
  $ cd frontend && npm run build
  ...
  ✓ built in 568ms
  ```
  終了コード0、`tsc -b && vite build` 成功。証拠 `evals/evidence/T09/build.log` と一致（ビルド時間の数値以外は同一）。
- 実行後 `git status --porcelain` で差分なし（`package-lock.json` の変化も無かったため `git checkout` は不要だった）。

### AC-00c（秘密情報なし） — ○
- 自分で再実行:
  ```
  $ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
  （何も出力されない。git diff --cached は現在ステージ無しのため空）
  $ git show 4948437 | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
  79:+$ git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
  ```
  唯一のヒットは `evals/evidence/T09/secret-scan.log` に記録された「実行したコマンド文字列そのもの」であり、実際の秘密情報ではない（T02 評価役が確認した誤検知パターンと同じ）。
- 3枚のスクリーンショットを目視したが、APIキーや個人情報の類は写っていない（コンテスト名・観点名・ダミーの評価文言のみ）。
- backend/.env は読んでいない。

### AC-00d（check_tasks エラー0件） — ○
- 自分で再実行:
  ```
  $ python evals/check_tasks.py
  結果: エラー 0 件 / 警告 0 件 / 完了 9/15 タスク
  ```
  証拠 `evals/evidence/T09/check_tasks.log` と一致。

### AC-11（画面で観点を入力し、生成された Questions を確認・編集できる） — ○
- `screenshot-01-form.png`: 「コンテスト観点モード」タブが選択された状態で、コンテスト名（学生ビジネスプランコンテスト2026）、観点1「課題の明確さ」（説明・配点20）、観点2「市場規模・成長性」（説明・配点30）の入力欄、「観点を追加する（2/15）」「Questionを生成する」ボタンが写っている。入力欄が実際に写っている。
- `screenshot-02-generated.png`: 「Questionの確認・編集」画面で、観点1・観点2それぞれについて「主催者の説明: …」（ピンク色の帯）とその下に「Jevへの質問文」、5段階（段階1〜5、最も低い〜最も高いのラベル付き）がすべて表示されている。生成結果が確認できる。
- `screenshot-03-edit.png`: 観点1の「Jevへの質問文」がフォーカスされた入力欄になっており、文言が「課題の明確さ（誰のどんな課題か）をどの程度満たしているか【編集済み】」に書き換えられている。編集欄が実際に機能していることが分かる。
- 3枚を通してコンテスト名・観点名・配点（20/30）・段階の文言が一貫しており、同じセッションで連続して撮られた本物の画面と判断できる。ボタンやカードのレイアウトも `CriteriaForm.tsx`・`QuestionEditor.tsx`・`QuestionSetReview.tsx`・`index.css` のコードと一致しており、作り物の画像や別画面の使い回しではない。
- `build.log` は AC-00b の証拠と兼用で、ビルドが成功していることを確認済み。

## 特に厳しく見た点への回答

1. **スクリーンショットが本物か・3枚の一貫性**: 上記の通り、同じコンテスト名・同じ2観点・同じ配点が3枚を通して現れており、コードのクラス名・文言（「主催者の説明:」「AIが観点の説明を元に作った段階評価です。…」「段階1（最も低い）」等）とも完全一致。本物の画面と判断した。

2. **`CriteriaForm.tsx` の入力チェックとバックエンド制約の整合**:
   - 観点数: `MAX_CRITERIA = 15`（`frontend/src/types/contest.ts` と `backend/app/models/contest.py` で同じ値。初期状態が1件で、`removeCriterion` は1件未満にできないため下限1件も満たす）→ FR-1 の「1〜15個」と一致。
   - 名前必須: `if (!c.name.trim())` でチェック → backend の `RequiredText`（`strip_whitespace=True, min_length=1`）と整合。
   - 配点: `MIN_POINTS=1, MAX_POINTS=100` で `Number.isInteger` チェック → backend の `max_points: int = Field(ge=1, le=100, strict=True)` と整合。
   - 観点の自動採番 `id: c${i+1}`（例: `c1`, `c2`, …）は backend の `CriterionId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,40}$")]` を満たす（英数字のみ、1〜40文字以内）。ユーザーに id を意識させない設計は要件通り機能する。

3. **`QuestionEditor.tsx` が観点の説明とQuestionを並べて見せているか**:
   - `criterion.description` があれば `<p className="question-editor-original">主催者の説明: {criterion.description}</p>` を Jev への質問文・5段階のすぐ上に表示している。スクリーンショットでも実際に確認できた（申し送り「T04評価役の指摘1」への対応）。
   - 5段階（`question.levels.map`）はすべて `<textarea>` で個別に編集可能。`updateLevel` が該当インデックスだけを更新する実装で、5つとも編集できることをコードとスクリーンショットの両方で確認した。

4. **既存の「ピッチ審査」画面が壊れていないか**: `App.tsx` の差分を確認したところ、`status` に基づく分岐（`UploadForm`／`LoadingState`／エラー表示／`ReviewResult`）はロジックを変えずに `appMode === "review"` の分岐の中にそのまま移しているだけで、`handleSubmit`・`handleReset` などの関数やその中身も変更なし。新しいタブ切り替え UI を外側に追加しただけであり、既存フローへの影響はない。

5. **Playwright / scratchpad の一時ファイルが残っていないか**:
   - `git show 4948437 --stat` に Playwright や scratchpad 関連のファイルは含まれていない（フロントエンドのソース・evidence・progress.md・tasks.json のみ）。
   - `git status --porcelain` はクリーン（作業ツリーに未追跡ファイルなし）。
   - リポジトリ全体を `scratchpad` で検索した結果、ヒットは `progress.md` の説明文と `evals/evidence/T07/review*.md` の過去の記述のみで、実体ファイルは見つからなかった。progress.md の記載（一時インストール・撮影後の削除確認）は裏付けが取れた。

6. **秘密情報の混入**: AC-00c の通り、スクリーンショット・新規ファイルともに秘密情報の混入なし。

## 結論
全ての合格条件（AC-00a, AC-00b, AC-00c, AC-00d, AC-11）が ○。

- `status`: `done`
- `passes`: `true`

## `python evals/check_tasks.py` の実行結果（再掲）
```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 9/15 タスク
```
