# progress.md — 途中経過と引き継ぎ

> AI はこのファイルに **追記** する（過去の記録は消さない）。
> セッションが切れても、別の AI に移っても、ここを読めば続きから再開できるように書く。

---

## 引き継ぎメモ（常に最新の状態に書き換える欄）
- **最終更新**: 2026-09-27
- **今の作業ブランチ**: `feature/contest-jev-questions`（土台: origin/feature/business-contest-rubric の b2dfe7f。upstream は未設定＝まだ push していない）
- **最後に終わったこと**: T11（実APIで1回通しの動作確認・人間承認済み）合格（`evals/evidence/T11/review.md`）。push はしていない
- **次にやること**: T12（README に新機能の使い方と必要なキーを書く）。これが最後のタスク
- **開発サーバーの起動（学んだこと）**: バックエンドは `--reload` なしで起動する（`--reload` の子プロセスが止めた後もポートを握り続けることがある）。画面が真っ白でビルドは通るときは Vite の再起動を試す。**Vite も止めたあと子プロセス（node vite.js）がポート5173に残ることがある**。再起動したら「Local: http://localhost:5173」で起動したかを必ず確かめ、5174 などになったら残った子プロセスを止める
- **偽物サーバーで撮影するとき**: `.env` に本物のキーが入ったので、偽物サーバーでは ANTHROPIC / OPENAI / TYPESAFE のキーをすべてダミーで上書きし、使う外部呼び出しはすべて偽物に差し替える
- **人間待ち**: push・本番反映は、もう一人の開発者と相談するまで保留。`pitch/` と参考画像（`Screenshot 2026-09-27 050107.png`）をコミットするかは未定
- **後続タスクへの申し送り**（T03 評価役の指摘より。該当タスクの作業計画に入れること）:
  - T05: Jev に渡す `Score` の `instructions` が観点名（または観点の内容）になっていることをテストで確かめる（採用された P2(b)）
  - T05: 型の `levels` を、Jev の `Score(criteria=...)` に名前を変えて渡す。`low_confidence` は必ず `confidence < LOW_CONFIDENCE_THRESHOLD` から計算する（型では確かめていない）
  - T07/T09: Claude が観点と違う順番で Question を返しても今はそのまま通る。API か画面で観点の順に並べ直すか決める（T04 評価役の指摘2）
  - T09: voice.md 2章「付け足した解釈は画面で人間に見せる」は、今の出力の型では解釈を区別できない。Question 確認画面（FR-3）で、観点の説明と Question を並べて見せるなどの方法を決める（T04 評価役の指摘1）→ **T09 で対応**
  - T07: 受け付ける音声・動画の拡張子を決め、動画（mp4 など）でも Whisper に渡るかテストする（T06 評価役の指摘2）→ **T07 で対応済み**
  - T07: `score_audio` に渡す一時ファイルの作成と削除は API 側の責任。エラーのときも一時ファイルが消えることをテストで確かめる（T06 評価役の指摘3）→ **T07 で対応済み**
  - T07: API で観点を受け取るとき、配点に `"20"`・`20.0`・`true` が通らないよう strict にするか決める（今の型は Pydantic の標準の検査なので受け付ける）→ **T07 で対応済み（strict）**
- **注意**:
  - 依存関係は作業ブランチの内容で入れ直し済み（typesafe-sdk 0.7.1 の import、`npm run build` の成功を確認）
  - バックエンドのテスト: `cd backend && .venv/Scripts/python -m pytest -q`（開発用の道具は `pip install -r requirements-dev.txt`）
  - `npm install` を実行すると、npm のバージョン差で `frontend/package-lock.json` の `libc` 行が消える。機能には関係ないので `git checkout -- frontend/package-lock.json` で戻す
  - APIキーの有無（値は見ていない）: 2026-09-27 に人間が `backend/.env` に登録し、ANTHROPIC / OPENAI / TYPESAFE の3つとも設定済み（有無だけ確認）

---

## 作業計画（計画役が書く・タスクごとに上書き）
### T20 コンテスト観点モードにも映像の分析を入れる（AC-00a, AC-00b, AC-00c, AC-00d, AC-08, AC-09, AC-12）
- 人間の依頼（2026-09-27）:「コンテスト観点モードにも映像の分析を入れてください」
1. `contest_scorer.score_audio`: スライド上限の確認 → Whisper 書き起こし → **書き起こしが空でなく**、ファイルが動画（`video_frames.is_video_file`）で、`ANTHROPIC_API_KEY` があるときだけ、`video_frames.extract_frames_base64` で静止画4枚 → ピッチ審査タブと同じ `review_generator.describe_presentation_visuals`（Claude が非言語的な表現を説明。失敗したら None）→ `score_materials` に `visual_description` を渡す
2. `build_jev_state(slides, transcript, visual_description)`: スライドも映像も無ければ従来どおり書き起こしをそのまま（AC-08 を崩さない）。どちらかがあれば `build_user_prompt(slides, transcript, visual_description)`（ピッチ審査と同じ組み立て。「# 発表映像から読み取れる非言語的表現」の節が入る）
3. `ContestScoreResult` に `visual_included: bool = False` と `visual_description: str | None = None` を追加（既定値つきなので、既存の保存データやテストは影響なし）
4. 画面: 採点フォームの注記に「動画（mp4 / webm）なら表情・身振りも材料にする」、読み込み中の段階に「映像を分析しています」、結果画面に使った材料（スライド・音声・映像）と「映像から読み取った様子」の文章を表示
5. テスト（偽物のAI）: 動画＋書き起こし → Jev の state に映像の節が入る・結果に visual_included=True／音声のみ（mp3）→ 静止画を取り出さず state は書き起こしそのまま／映像の説明に失敗 → 映像なしで採点が続く／キーが無い → Claude を呼ばない／書き起こしが空 → 400 で Claude（映像）を呼ばない／スライド上限超え → Whisper も映像も呼ばない／API 経由で mp4 を送ると映像が使われる
6. 画面確認: 外部APIだけ偽物にして、動画で採点した結果画面をスクショ
7. 証拠: `evals/evidence/T20/`
- 実 API・push・削除は含まない（本物の動画での確認は、必要なら人間の承認を得て別途）

### T11 実APIで1回通しの動作確認（AC-00a, AC-00c, AC-00d, AC-13）
- **人間の承認（2026-09-27）**: 「.envにAPIkeyを登録しました テストしてください」→ 実 API（Anthropic / OpenAI / TypeSafe）を使う T11 の実行を承認。キーは3つとも設定済み（有無だけ確認。値は見ていない）
- サンプル音声（Q6）: 人間の用意が無いため、`pitch/harinezumi_pitch.pptx` のノートの「話すこと」（スライド1〜8＝本番で録音する最初の2分）を Windows の音声合成（Microsoft Haruka、日本語）で読み上げた WAV を作る。個人情報なし・費用なし。音声ファイルは scratchpad に置き、リポジトリには入れない（大きいため。ハッシュと長さを記録）
- 手順: バックエンドを再起動して .env のキーを読み込ませる → Playwright で画面から操作（コンテスト観点モード → 観点3つを入力 → Question生成（Claude 1回）→ スライド＋音声で採点（Whisper 1回・Jev 1回））→ 結果画面をスクショ。API の応答（観点ごとの点数・合計・確信度）と各段階の所要時間を `e2e.log` に記録。キーは記録しない
- 呼び出し回数を最小にする（通しは1回。失敗したら原因を調べてから、もう1回だけ試す）。見込み費用は数十円程度
- 証拠: `evals/evidence/T11/` に e2e.log、screenshot-*.png、pytest.log、secret-scan.log、check_tasks.log

### T19 採用された提案 P8 の反映（AC-00a, AC-00b, AC-00c, AC-00d, AC-09）
- 人間の決定（2026-09-27）:「提案8を受け入れます。実装してください。」
1. (a) `schemas.CriterionScore.levels` を省略可（既定は空のリスト）にする。画面の `CriterionCard` は空なら「審査基準を見る」を出さないので、古い履歴もそのまま表示できる。テスト: levels の無い古い形の JSON を履歴フォルダに置いて `/api/history` が 200 で読める
2. (b) `generate_rubric_from_names`: Claude が返した項目数が指定した数と違えば、日本語の 502（「評価項目N個分の判定基準を作れませんでした。もう一度お試しください。」）。Jev は呼ばない。テスト: 少ない・多いの両方
3. (c) `parse_custom_rubric`: Pydantic の生メッセージ（英語）の代わりに `to_japanese` を使い、何番目の項目かも書く。テスト: 段階が5個でない・名前が無い・項目が文字列、でいずれも日本語で英語が混ざらない
4. (d) `frontend/index.html` の Google Fonts（Space Grotesk / Inter）の読み込み3行を外す（CSS で使っていないことを確認済み）
5. 証拠: `evals/evidence/T19/` に pytest.log、before-fix.log、build.log、secret-scan.log、check_tasks.log
- 実 API・push・削除は含まない

### T18 他の開発者のブランチ（本番の機能）をマージで取り込む（AC-00a, AC-00b, AC-00c, AC-00d）
- 人間の依頼（2026-09-27）:「他の人がデプロイしている機能を確認することはできますか？その機能をここにも実装してください。」
- 人間の決定: 取り込み方は **マージ**（履歴ごと合流。push はしない）。見た目は **こちらの明るい背景＋オレンジを維持**
- 対象: `origin/feature/business-contest-rubric` の分岐点 b2dfe7f 以降の17コミット（最新 161f8d7、2026-09-26）
- 衝突の見込み（`git merge-tree` で確認）: `jev_scorer.py`、`review_generator.py`、`index.css` の3ファイル。App.tsx などは自動で合流
1. `git merge origin/feature/business-contest-rubric`（--no-ff）。衝突を解く:
   - `jev_scorer.py`: 相手の `score_with_jev(state_text, criteria)`（評価基準を引数で受け取る）と、こちらの `run_system_one`（コンテスト観点モードが使う）を両方残す
   - `review_generator.py`: 相手の機能（カスタム評価基準・プレビュー・動画分析）と、こちらの変更（`_call_claude` の `failure_detail`、`build_user_prompt` の公開）を両方残す
   - `index.css`: こちらのオレンジのデザインを土台にし、相手の新しい部品（評価基準のプレビュー、判定基準の表示、Powered by など）のクラスをオレンジのデザインで書き直す。暗いテーマの色は入れない
2. 依存関係 `av`（PyAV。動画から静止画を取り出す）を venv に入れる（requirements.txt に相手が追加済み）
3. テスト: 既存テスト全件＋相手の機能のテストを外部API偽物で追加（評価基準3方式の分岐、プレビューAPI、動画の静止画抽出が失敗しても審査が止まらないこと）。相手のブランチにはテストが無いため
4. 画面確認: 外部APIだけ偽物にして、ピッチ審査タブ（評価基準の選び方・プレビュー・結果の判定基準）とコンテスト観点モードをスクショ
5. 証拠: `evals/evidence/T18/`（merge.log、pytest.log、build.log、スクショ、secret-scan.log、check_tasks.log）
- 実 API 呼び出し・push は含まない。マージは人間の承認済み（上記の決定）

### T17 採用された提案 P7 の反映（AC-00a, AC-00b, AC-00c, AC-00d, AC-09, AC-12）
- 人間の決定（2026-09-27）:「提案P7を採用します。実装してください。」
1. (a) 上限: `config.py` に `max_contest_slide_pages`（60ページ）と `max_contest_slide_chars`（30,000文字。本文＋スピーカーノート）を追加（.env で変えられる）。5分前後のピッチには十分な余裕がある値。`contest_scorer.check_slide_limits()` で確かめ、超えたら「何ページ／何文字で、上限はいくつか」を含む日本語の400。`score_audio` では **Whisper で書き起こす前** に確かめる（上限超えのスライドのために書き起こし代を払わない）。ピッチ審査タブの動きは変えない
2. (b) 表・グループ図形: `slide_extractor.extract_from_pptx` を、グループ化した図形の中を順にたどり、表はセルの文字を行ごとに「 | 」でつないで読むように変更。ピッチ審査タブも同じ抽出処理を使うため、そちらでも読み取れる文字が増える（減ることはない）。画面の注記を「表やグループ化した図形の中の文字も読み取る。図や画像の中の文字は読み取れない」に合わせ、上限も書く
3. (c) 案内: 書き起こしが空の400で、読み取れる文字のあるスライドが一緒に送られていれば、「スライド資料だけを選び直して採点すれば、スライドだけで採点できる」ことを文言に足す（エラー後は選択欄が空に戻るため「選び直して」と書く）
4. テスト: 上限ちょうどは通り1つ超えると400（ページ・文字それぞれ）、上限超えのときWhisperが呼ばれない、API経由で日本語400、表・グループ（入れ子含む）の文字が読める、書き起こし空＋スライドありのときだけ案内が付く
5. 証拠: `evals/evidence/T17/` に pytest.log、build.log、secret-scan.log、check_tasks.log、画面のスクショ（注記と上限超えエラー、書き起こし空の案内。外部APIだけ偽物にして撮る）
- 実 API・push・削除は含まない（承認不要）

### T16 採用された提案 P6 の反映（AC-00a, AC-00c, AC-00d, AC-10）
- 人間の決定（2026-09-27）:「提案P6を受け入れます。実行してください。」
1. `question_set_storage.list_all()`: ファイルの更新時刻（`os.path.getmtime`）で並べるのをやめ、読み込んだ内容の `saved_at` で新しい順に並べる
2. `question_set_storage.save()`: 時計の細かさ（Windows では同じ時刻が続けて返ることがある。実測で20万回中4万通り程度）のため、続けて保存したときに `saved_at` が同じになりうる。直前の保存より必ず1マイクロ秒以上あとの時刻にする小さな仕組みを入れ、同じプロセス内では順序が必ず決まるようにする
3. テスト追加: (a) ファイルの更新時刻をわざと逆にしても `saved_at` の順になる、(b) 時計が同じ時刻を返し続けても、2つ目の `saved_at` が1つ目より新しく、一覧も新しい順になる
4. 既存テスト `test_list_returns_newest_first_with_summary_fields` は書き換えない
5. 証拠: `evals/evidence/T16/` に pytest.log（全体）、repeat.log（該当テストファイルを繰り返し実行し全て成功）、secret-scan.log、check_tasks.log
- 実 API・push・削除は含まない（承認不要）

### T15 コンテスト観点モードでスライドも使う（AC-00a, AC-00b, AC-00c, AC-00d, AC-08, AC-09, AC-12）
- 人間の依頼（2026-09-27）:「コンテスト観点モードでもスライドを使えるようにしてください」
1. `contest_scorer.py`: `score_materials(question_set, slides, transcript)` を追加。Jev の state は、スライドが無ければ書き起こしをそのまま（従来どおり＝AC-08 を崩さない）、スライドがあれば既存の `review_generator.build_user_prompt`（ピッチ審査と同じ組み立て）でスライドの文字＋スピーカーノート＋書き起こしをまとめた文章にする。`score_transcript`・`score_audio` はこの関数を使う形に整理
2. 空の判定: 音声を送ったのに書き起こしが空 → 400（従来どおり）。スライドだけで、どのスライドからも文字が読めない → 400（「画像だけのPDFなどは読めない」旨の日本語）
3. `ContestScoreResult` に `slides_included`・`transcript_included` を追加（何を材料に採点したかを画面に出すため）。frontend の型も同じく
4. `routers/contest.py` の `/score`: `slide_file`（任意、.pdf/.pptx、既存の上限 20MB）を受け付け、`media_file` を任意にする。どちらも無ければ 400。スライドが2つ以上・拡張子違い・壊れたファイル（pdfplumber / python-pptx が例外を出す）は 400 と日本語（T07 の反省: 異常な入力も 500 にしない）
5. 画面: `AudioScoreForm` にスライドの選択欄を追加し、どちらか一方があれば送れるようにする。`contestApi.scoreAudio` を `scorePitch(questionSet, mediaFile, slideFile)` に。結果画面に「スライドと音声で採点」などの表示
6. テスト（Whisper・Jev は偽物）: スライド＋音声で state にスライドの文字と書き起こしがそのまま入る／スライドのみで Whisper を呼ばない／音声のみは従来どおり state＝書き起こし／どちらも無い→400／文字の無いスライドのみ→400／壊れたPDF・PPTX→400／拡張子違い→400／スライド2つ→400／一時フォルダの後片付け
7. 証拠: `evals/evidence/T15/` に pytest.log、build.log、スクリーンショット、secret-scan.log、check_tasks.log
- 承認が必要な操作: なし（実 API は呼ばない。スクリーンショットは T10 と同じく一時的なスタブで撮影し、コミットしない）

### T14 採用された提案 P4・P5 の反映（AC-00a, AC-00c, AC-00d, AC-06, AC-07）
1. P4(a) Claude の SDK 例外 → 502: `test_question_builder.py` の `FakeAnthropic` に `error` を追加し、`anthropic.APIConnectionError` を送出するテストを足す（`review_generator._call_claude` の `except anthropic.APIConnectionError` / `except Exception` が既に502にしているので、テストの追加のみ）
2. P4(b) 段階が空のときのエラーを日本語に: `question_builder._format_validation_error`（Pydantic の生メッセージを英語のまま繋げていた）を、既に `contest.py` の入力チェックで使っている `app.utils.validation_messages.to_japanese` に差し替える（重複コードの統一でもある）。テストで、段階が空のQuestionをClaudeが返したときの502メッセージが日本語（「Question1の段階5: 入力してください」）になることを確認
3. P4(c) 段階数テストの入力を別々の文に: `test_wrong_level_count_is_rejected` の `LEVELS[:1] * count`（同じ文の繰り返し）を、`[f"段階{i}" for i in range(count)]`（別々の文）に変える
4. P5 Jev の score が大きく外れたら502: `contest_scorer.py` に許容誤差の定数（0.001。浮動小数点の誤差は吸収し、それを超えるずれは異常値として扱う）を追加。範囲外だが誤差の範囲内ならこれまで通り0〜4に収め、誤差を超えていたらログを残して502（観点名入りの日本語エラー）にする。テストで、既存の「わずかな誤差」ケース（0.0000001）は今まで通り成功し、「大きく外れた」ケース（5.0, -1.0）は502になることを確認
5. 証拠: `evals/evidence/T14/` に pytest.log、secret-scan.log、check_tasks.log
- 変更予定ファイル: `test_question_builder.py`（追記）、`question_builder.py`（`_format_validation_error` を `to_japanese` に置き換え）、`test_contest_scorer.py`（既存テスト1件の入力変更＋新規テスト追加）、`contest_scorer.py`（範囲外判定の追加）
- 承認が必要な操作: なし。実 API は呼ばない

### T13 採用された提案 P2(a)・P3 の反映（AC-00a, AC-00c, AC-00d, AC-03, AC-05）
- ユーザーの指示: サンプル音声の準備待ちの間に、T11（実API通し確認・要承認）を後回しにして、依存関係が満たされている T13 を先に進める（T14 は依頼にはあるが T13 を先に着手）
1. PDF のスライド抽出テスト（P2(a)）: `backend/requirements-dev.txt` に `reportlab` を追加（PDF書き出し用。テスト専用の道具なので docs/safety.md の「テスト用のpytestなど」の例外に該当し、承認なしで進める）。`test_slide_extractor.py` に、reportlab で作った2ページのPDFから `extract_from_pdf` がページ番号・本文を正しく取り出すテストと、文字の無いページが空文字になるテストを追加
2. AC-05 のテスト強化（P3(a)）: `test_contest_models.py` の「エラーになること」だけを見ているテストに、`ValidationError.errors()` の `loc`（どの項目か）や具体的な文言を確認する assert を足す（配点の範囲外・名前が空・観点16個/0個・段階が空・IDが不正・結果の範囲外の各テスト）
3. 採点結果の空文字禁止（P3(b)）: `app/models/contest.py` の `ContestCriterionResult.name` と `ContestScoreResult.contest_name` を `str` から `RequiredText`（既存の `ContestCriterion.name` と同じ制約）に変更。テストを追加
4. 証拠: `evals/evidence/T13/` に pytest.log、secret-scan.log、check_tasks.log
- 変更予定ファイル: `requirements-dev.txt`（追記）、`test_slide_extractor.py`（追記）、`app/models/contest.py`（型の変更2箇所）、`test_contest_models.py`（既存テストの強化＋追加）
- 承認が必要な操作: なし（reportlab はテスト専用。実 API は呼ばない）

### T10 画面: 音声アップロードと結果表示、保存済みQuestionsの選択（AC-00a, AC-00b, AC-00c, AC-00d, AC-12）
1. `frontend/src/api/contestApi.ts` に追記: `listQuestionSets()`（GET一覧）、`loadQuestionSet(id)`（GET読み込み）、`scoreAudio(questionSet, mediaFile)`（POST /api/contest/score、multipart。`media_file` と `question_set`＝JSON文字列）
2. `frontend/src/components/LoadingState.tsx` に任意の `stages` プロパティを追加（既定値は今のピッチ審査用の文言のままなので既存の動きは変わらない）。T09 で「Questionを生成中」の場面にピッチ審査用の文言（「スライドを解析中…」）が出ていた小さな不正確さも、ここで直す
3. `frontend/src/components/contest/SavedQuestionSetPicker.tsx`: `listQuestionSets` で一覧を取得し、名前・コンテスト名・観点数・保存日時を表示。選ぶと `onSelect(id)`
4. `frontend/src/components/contest/AudioScoreForm.tsx`: 音声/動画ファイルを選ぶ（既存の UploadForm と同じ拡張子・上限MB）。送信で `scoreAudio` を呼ぶ
5. `frontend/src/components/contest/ContestScoreResultView.tsx`: 合計点／満点、観点ごとの点数／配点、`low_confidence` が true の観点には voice.md 1章の文言（「発表の中に判断材料が少ないため、この点数は参考値です。」）を表示。「もう一度採点する」「最初からやり直す」ボタン
6. `ContestQuestionsPage.tsx` を拡張し、次の2つの入口をどちらも `QuestionSetReview` の「音声で採点する」ボタンに合流させる（1本の採点フローにする）
   - 新規生成: 入力フォーム → 生成 → 確認・編集（既存の T09 フロー）
   - 保存済みの再利用: `CriteriaForm` に「保存済みのQuestionsを使う」リンクを追加 → `SavedQuestionSetPicker` → 選択 → 読み込み → 確認・編集画面に表示（そのまま採点しても、直してから採点してもよい）
7. 証拠のスクリーンショット: T09 と同じやり方（question_builder のスタブに加えて、`contest_scorer.score_audio` を Whisper/Jev を呼ばずに固定の点数を返す関数に一時的に差し替える。コミットしない）で、音声アップロード画面と結果画面を撮影
8. 証拠: `evals/evidence/T10/` に build.log、pytest.log（既存機能への影響なし）、screenshot-*.png、secret-scan.log、check_tasks.log
- 変更予定ファイル: `api/contestApi.ts`（追記）、`LoadingState.tsx`（後方互換の拡張）、新規 `components/contest/SavedQuestionSetPicker.tsx`・`AudioScoreForm.tsx`・`ContestScoreResultView.tsx`、`ContestQuestionsPage.tsx`・`CriteriaForm.tsx`・`QuestionSetReview.tsx`（つなぎ込み）、`index.css`（追記）
- 承認が必要な操作: なし。実 API は呼ばない（スクリーンショット用の一時差し替えはコミットしない）

### T09 画面: コンテスト観点の入力フォームとQuestion確認・編集（AC-00a, AC-00b, AC-00c, AC-00d, AC-11）
1. `frontend/src/types/contest.ts` に `SavedQuestionSet`・`SavedQuestionSetSummary` を追加（T08 でバックエンドに追加した形をミラー）
2. `frontend/src/api/contestApi.ts` を新規作成: `ContestApiError`、`generateQuestions(rubric)`（POST /api/contest/questions）、`saveQuestionSet(name, questionSet)`（POST /api/contest/question-sets）。既存の `reviewApi.ts` と同じ作り（`detail` を日本語エラーとしてそのまま投げる）
3. 画面はピッチ審査と別モードとして追加する（既存の審査フローは変えない）。`App.tsx` に「ピッチ審査」「コンテスト観点モード」の切り替えを追加
4. `frontend/src/components/contest/CriteriaForm.tsx`: コンテスト名＋観点（名前・説明・配点）を1〜15個、追加・削除できる形で入力。観点の id はユーザーに見せず `c1, c2, …` を自動採番（Jev の id 形式の制約をユーザーに意識させない）。送信で `generateQuestions` を呼ぶ
5. `frontend/src/components/contest/QuestionEditor.tsx`: 1つの Question を表示・編集。**観点の名前・説明を Question の指示文・段階と並べて見せる**（申し送り: AIが付け足した解釈を人間が見比べられるように。T04 評価役の指摘1への対応）。instructions と5段階の levels を編集できる
6. `frontend/src/components/contest/QuestionSetReview.tsx`: `QuestionEditor` を並べる（**バックエンドが観点の順に並べ替え済みなので、画面側での並べ替えは不要** — T07 評価役の指摘2はサーバー側で解決済み、申し送りに追記して閉じる）。名前を付けて `saveQuestionSet` で保存するフォームを持つ
7. `frontend/src/components/contest/ContestQuestionsPage.tsx`: 状態遷移（入力→生成中→確認・編集→保存中→保存済み／エラー）をまとめる
8. スクリーンショット撮影（AC-11 の証拠）: 実際に Claude API を呼ぶとお金がかかり承認が必要なので、`backend/app/services/question_builder.generate_questions` を一時的に固定の QuestionSet を返す関数に差し替えて（コミットしない一時的な変更）バックエンドとフロントエンドを起動し、入力→生成結果→編集の3枚を撮る。撮影後は差し替えを元に戻す
9. 証拠: `evals/evidence/T09/` に build.log、screenshot-01-form.png、screenshot-02-generated.png、screenshot-03-edit.png、secret-scan.log、check_tasks.log
- 変更予定ファイル: `types/contest.ts`（追記）、新規 `api/contestApi.ts`・`components/contest/*`、`App.tsx`（モード切替の追記）、`index.css`（新しいクラスの追記）
- 承認が必要な操作: なし。実 API は呼ばない（スクリーンショット用の一時差し替えはコミットしない）

### T08 Questions セットの保存・一覧・読み込み（AC-00a, AC-00c, AC-00d, AC-10）
1. `backend/app/models/contest.py` に `SavedQuestionSet`（id・name・question_set・saved_at）と `SavedQuestionSetSummary`（id・name・contest_name・criteria_count・saved_at。一覧表示用の軽い形）を追加
2. `backend/app/services/question_set_storage.py` を新規作成（`history.py` と同じ作りに揃える）
   - `save(name, question_set) -> SavedQuestionSet`: `backend/data/question_sets/<uuid>.json` に保存。名前は必須（空白のみは拒否）
   - `list_all() -> list[SavedQuestionSetSummary]`: 保存日時の新しい順
   - `load(id) -> SavedQuestionSet`: 無ければ見つからない旨のエラー
   - ファイル名に使う id は保存側で作る UUID（ユーザー入力の name をそのままファイル名にしない）
3. `backend/app/routers/contest.py` に3つの窓口を追加。入力チェックは他の窓口と同じやり方（400・日本語）
   - `POST /api/contest/question-sets`（name・question_set を受け取り保存）
   - `GET /api/contest/question-sets`（一覧）
   - `GET /api/contest/question-sets/{id}`（読み込み。無ければ404）
4. `backend/tests/test_question_set_storage.py`：保存→一覧→読み込みで同じ内容に戻る（AC-10）、一覧が複数件で新しい順、無い id は分かるエラー、名前が空は拒否
5. `backend/tests/test_contest_api.py` に3つの窓口のテストを追記（成功・不正な入力400・存在しないid→404）
6. 証拠: `evals/evidence/T08/` に pytest.log、secret-scan.log、check_tasks.log（1行目は実行コマンドと同じ変数から）
- 変更予定ファイル: `models/contest.py`（追加のみ）、新規 `question_set_storage.py`・テスト、`routers/contest.py`（追記）
- 承認が必要な操作: なし（保存先はテストでは一時フォルダ。本番の保存先はコードに書くだけで、削除やアクセス権の変更は行わない）

---

## 要確認（人間に聞きたいこと）
- docs/requirements.md 5章の Q1〜Q6

---

## 提案（AI からの変更提案。人間が採用したら該当ファイルに反映する）
- **P8（2026-09-27、T18 のマージ作業中に気づいたこと。相手のコードなので勝手に直していない）**: (a) 審査結果の型に `levels`（判定基準）が必須で加わったため、それより前に保存された審査履歴（`backend/data/reviews/`）があると履歴の読み込みでエラーになる（今この PC には履歴が0件なので実害なし）→ 読めない古い履歴は飛ばす、または `levels` を省略可にする。(b) 項目名を指定したとき、Claude が返した項目数が足りないと、その項目の判定基準が空のまま Jev に送られる（エラーになる可能性）→ 数が合わなければ 502 にする。(c) 編集したプレビューの形式エラーの文言に英語（Pydantic の生メッセージ）が混ざる → `to_japanese` を使う。(d) `frontend/index.html` が相手の暗いデザイン用の Google Fonts を読み込んでいるが、オレンジのデザインでは使っていない → 外すと表示が少し速くなる。いずれも相手の開発者と相談のうえ決めるのがよい。→ **採用（2026-09-27、人間「提案8を受け入れます。実装してください。」）。T19 として tasks.json に追加**
- **P7（2026-09-27、T15 評価役の指摘2〜4より）**: (a) スライドのページ数（または抽出文字数）に上限を設け、超えたら日本語で知らせる、(b) 採点画面の注記に「表やグループ化した図形の中の文字は読み取れない」を追記するか、抽出処理を表・グループ図形に対応させる、(c) 書き起こしが空で400になったとき、スライドがあれば「スライドだけで採点し直す」案内を出す。→ **採用（2026-09-27、人間「提案P7を採用します。実装してください。」）。T17 として tasks.json に追加**
- **P6（2026-09-27、T14 の全体テスト実行中に発見）**: `question_set_storage.list_all()` の並び順が `os.path.getmtime`（ファイルの更新時刻）に頼っているため、2件を続けて保存すると順序が入れ替わることがある（`test_list_returns_newest_first_with_summary_fields` が失敗する）。当初「数百回に1回」と見積もったが、**T15 評価役の実測では全体実行13回中3回・単体8回中1回失敗**しており、評価役の誤判定の原因になりうる。`saved_at`（保存内容に持たせている日時）で比べるように直せば確実。**採用を推奨**。→ **採用（2026-09-27、人間「提案P6を受け入れます。実行してください。」）。T16 として tasks.json に追加**
- **P5（2026-09-26、T05 評価役の指摘2より）**: Jev の score が 0〜4 から大きく外れた（例: 0.001 より大きくずれた）ときは、黙って収めずにログを残して 502 にする。わずかな誤差だけ収める。→ **採用（2026-09-26、人間「提案2つを採用します」）。T14 として tasks.json に追加**
- **P4（2026-09-26、T04 評価役の指摘3〜5より）**: (a) Claude の呼び出し中に SDK が例外を出した場合も 502 になることをテストで確かめる。(b) 段階が空のときのエラーの括弧内が英語（Pydantic 標準の文）になるので、日本語にする（NFR-3）。(c) 段階数のテストの入力を別々の文にする。どれも小さな変更。→ **採用（2026-09-26、人間「提案2つを採用します」）。T14 として tasks.json に追加**
- **P3（2026-09-26、T03 評価役の指摘1・5より）**: (a) AC-05 のテストを「エラーになるか」だけでなく「どの項目のエラーか」まで確かめるようにする（将来ほかの制約を足したとき、別の理由で通ってしまうのを防ぐ）。(b) 採点結果の `name` と `contest_name` も空文字を禁止する。どちらも小さな変更。→ **採用（2026-09-26、人間「提案の2つを採用します」）。T13 として tasks.json に追加**
- **P2（2026-09-26、T02 評価役の指摘3より）**: 今あるテストの抜けを、関係するタスクで補ってはどうか。(a) スライド抽出の PDF 経路のテスト、(b) Jev に渡す `Score` の `instructions` が観点名になっているかの確認。(b) は T05（Jev 採点）の作業計画に含めるのが自然。→ **採用（2026-09-26、人間「提案の2つを採用します」）。(a) は T13 に、(b) は T05 の申し送りに入れた**
- **P1（2026-09-26）**: 「証拠に、実行したコマンドを書いていない」という指摘が T00・T01 の2回続いた。`docs/roles.md` 2章の「証拠の保存例」に「ログの1行目に `$ 実行したコマンド` を書く」を追加してはどうか。→ **採用（2026-09-26、人間）。docs/roles.md 2章に反映済み**

---

## 作業ログ（新しいものを下に追記）
### 2026-09-26 ハーネス作成
- 既存コード（main と origin/feature/business-contest-rubric）を調査し、docs/requirements.md 1〜2章にまとめた
- typesafe-sdk 0.7.1 のソースで Jev の入出力の型を確認した
- 作成: AGENTS.md, CLAUDE.md, docs/*, tasks.json, progress.md, evals/*, .claude/skills/next-task/SKILL.md, .claude/settings.json
- 証拠: `python evals/check_tasks.py` の結果（エラー0件）

### 2026-09-26 T00 作業ブランチ作成（ユーザーの許可を得て AI が実行）
- `git switch -c feature/contest-jev-questions origin/feature/business-contest-rubric` → ハーネスをコミット（2472589）→ `harness-baseline` タグを付けた
- 新しいブランチが origin/feature/business-contest-rubric を upstream として追跡していたため、`git branch --unset-upstream` で外した（そのままだと `git push` が別のブランチに入ってしまう）
- 依存関係を入れ直し、バックエンドの import とフロントエンドのビルドが通ることを確認
- 証拠: `evals/evidence/T00/`（git.log, secret-scan.log, check_tasks.log, review.md）。評価役サブエージェントが5条件すべて○と判定

### 2026-09-26 T01 未確定事項への回答記録
- 人間の回答（原文）: 「Q1、良いです」「Q2、そうです」「Q3、僕のキーです」→ docs/requirements.md 5章に記録（54ef02b）。人間が `git tag -f harness-baseline` で基準を更新
- **評価役の判定: 不合格（AC-02 ×）**。理由: 3章の見出しに `[確定・Q2]` を付けたため、Q2 で聞いていない「TypeSafe = TypeSafe AI 社」の項目まで確定に見えた（AIの推測を確定扱い）
- 修正: 確定の印を「Questions」の項目だけに付け、「TypeSafe」の項目は `[仮定・人間に未確認]` に戻した。証拠を作り直した（実行コマンドを記録、secret-scan.log を追加）
- 人間の追加回答（原文）: TypeSafe の解釈について「あっています」、提案 P1 について「採用してください」→ requirements.md 3章を確定に、roles.md 2章に P1 を反映
- 人間が基準タグを付け直し（86bd2d7）→ 評価役の再検品で **合格**（AC-02/AC-00c/AC-00d すべて○）。証拠: `evals/evidence/T01/review.md`

### 2026-09-26 T02 pytest 導入と既存機能の回帰テスト
- 追加: `backend/requirements-dev.txt`（pytest）、`backend/pytest.ini`、`backend/tests/`（23テスト）、`backend/.gitignore` に `.pytest_cache/`。アプリ本体のコードは変更なし
- テスト対象: 配点計算・ルーブリック構造、PPTX 抽出、/api/health、jev_scorer（Jev に渡す内容・点数変換・エラー）、transcription（Whisper の結果・エラー）
- `tests/conftest.py` が全テストで、APIキーをダミー値に差し替え、外部への通信を遮断する
- **発見と修正**: 最初の通信遮断は `socket.connect` しか止めておらず、確認のためにモック無しで Jev を呼んだところ、**ダミーキー `test-typesafe-key` を付けた1回分のリクエストが api.typesafe.ai に届いた**（認証エラーで拒否。本物のキーは送られておらず、料金も発生していない）。原因は、非同期の通信がホスト名の解決（getaddrinfo）と Windows 専用の接続方式（ConnectEx）を使い、`socket.connect` を通らないこと。名前解決と asyncio の接続も遮断するよう直し、`test_network_guard.py` に再発防止テストを入れた（モック無しの Jev 呼び出しが「認証エラー」ではなく「接続失敗」になることを確認）
- 証拠: `evals/evidence/T02/`（pytest.log: 23 passed、secret-scan.log: 一致なし、check_tasks.log）
- 計画からの変更: 計画にあった `pytest-offline.log` は作らなかった。遮断の確認テスト（test_network_guard.py）が通常の pytest.log に含まれるため（評価役の指摘2を受けて記録）
- 評価役の検品で **合格**（AC-00a/00c/00d/03/04 すべて○）。証拠: `evals/evidence/T02/review.md`。評価役はリポジトリの外で追加の遮断テスト8件（IP直指定、別のイベントループ、同期クライアント、モック無しの Whisper と Anthropic など）も実行し、すべて止まることを確認した
- 評価役の指摘1への対応: 秘密情報チェックが safety.md の手順（`--cached`）と違い、まだ追加していない新規ファイルが検査対象外だった可能性があった → コミット全体を safety.md のパターンで検査し直した（`secret-scan-commit.log`。一致は検索コマンド自身の1行だけ）

### 2026-09-26 T03 観点・Question・採点結果の型定義
- 追加: `backend/app/models/contest.py`（ContestCriterion / ContestRubric / JevScoreQuestion / QuestionSet / ContestCriterionResult / ContestScoreResult と定数）、`frontend/src/types/contest.ts`（同じ形）、`backend/tests/test_contest_models.py`（29テスト）。既存コードは変更なし
- 決めたこと: 観点の id は英数字・_・- の1〜40文字（Jev の questions の名前にそのまま使うため）。QuestionSet は「観点1つにつき Question 1つ」を型の段階で保証する（T04 で Claude の出力の抜け・余分を検出するのに使う）
- つまずき: テスト用の補助関数で `levels or 既定値` と書き、空のリスト（段階0個）が既定値にすり替わってテストが1件失敗した → `is None` で判定するよう直した
- `contest.ts` はまだどの画面からも使われていないが、型チェック（tsc）の対象に入っていることを確認した（build.log の末尾）
- 証拠: `evals/evidence/T03/`（pytest.log: 52 passed、build.log、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00b/00c/00d/05 すべて○）。評価役はリポジトリの外で型を直接試し、AC-05 の5ケースがそれぞれ正しい理由でエラーになることを確認した。backend と frontend の型が一致することも機械的に比較して確認
- 評価役の指摘のうち T05・T07 に関わるものは、引き継ぎメモの「後続タスクへの申し送り」に書いた。T03 自体の小さな改善は提案 P3 に書いた

### 2026-09-26 採用された提案の記録
- 人間「提案の2つを採用します」→ P2(b) は T05 の申し送りへ、P2(a)・P3 は新しいタスク T13 として tasks.json に追加（人間の決定による追加。基準タグの更新は人間待ち。それまで check_tasks は T13 について警告を出す）

### 2026-09-26 T04 観点 → Jev の Score Question を Claude で生成
- 追加: `backend/app/services/question_builder.py`（`generate_questions`）、`backend/tests/test_question_builder.py`（10テスト）
- 変更: `review_generator._call_claude` に `failure_detail` 引数を追加（既定値は今までと同じ文言なので、既存の審査機能の動きは変わらない）
- 決めたこと: Claude には単純な形（criterion_id / instructions / levels）で出力させ、T03 の `QuestionSet` で検査する。抜け・余分・重複・段階数の誤りは 502 と日本語のエラーにする（黙って直さない）
- 確認: Claude API の資料（claude-api スキル）で、structured outputs は文字数・範囲などの制約に対応しないことを確認した。SDK の実物（`anthropic.transform_schema`）で、出力の型が対応済みの機能だけのスキーマになることを確かめ、テストにした（`claude-output-schema.log`）
- モデルは既存設定の `claude-sonnet-5` のまま（資料の既定は claude-opus-5 だが、モデルを変えると費用と動きが変わるため、このタスクでは変えない）
- 証拠: `evals/evidence/T04/`（pytest.log: 62 passed、claude-output-schema.log、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00c/00d/06 すべて○）。評価役は SDK 1.8.0 のソースで「文字数・範囲などの制約はスキーマから外される」ことを確かめ、制約を付けた型ではスキーマのテストが落ちることも確認した
- 評価役の指摘のうち T07・T09 に関わるもの（Question の並び順、付け足した解釈の見せ方）は申し送りへ。小さな改善は提案 P4 へ

### 2026-09-26 T05 書き起こし＋Questions → Jev 採点 → 配点換算
- 追加: `backend/app/services/contest_scorer.py`（`score_transcript`・`to_points`・`build_jev_questions`）、`backend/tests/test_contest_scorer.py`（16テスト）
- 変更: `jev_scorer.py` から Jev の呼び出しと日本語エラーへの変換を `run_system_one` に切り出した（既存の `score_with_jev` はそれを使うだけ。既存テストはそのまま通る）
- 申し送りへの対応: `levels` を Jev の `criteria` に名前を変えて渡す／`low_confidence` は `confidence < 0.5` から計算（0.5 ちょうどは「低くない」）／`instructions` の先頭に「【観点】観点名」を入れた（採用された P2(b)）
- **つまずき**: 最初は Python の `round` で四捨五入したが、`round` は「ちょうど半分」を偶数の側に丸める（0.25 → 0.2）ため FR-6 の四捨五入と違った。ちょうど半分のテストを先に足して失敗を確かめてから、`Decimal` と `ROUND_HALF_UP` に直した。小数の誤差（0.3 ÷ 4 × 30 が 2.2499999… になる）も `Decimal(str(値))` で避けた
- テストの書き間違い: 「ちょうど半分」の例に 1.125 を使ったが、小数第1位で丸めるときは半分ではなかった（→ 1.1）。2.25 の例に差し替えた
- 結果は観点の順に並べる（Question が別の順でも）。Jev の答えが欠けた観点は 502、わずかな範囲外の score は範囲内に収める
- 証拠: `evals/evidence/T05/`（pytest.log: 78 passed、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00c/00d/07 すべて○）。評価役はリポジトリの外で `to_points` を229通り、合計を304通り、分数での正確な計算と比べて食い違い0件を確認。`run_system_one` の切り出し前後で `score_with_jev` の結果・エラーが10通りすべて同じことも確認
- 評価役の指摘: (1) 「モード不正かつキー無し」のときだけ 400 が ValueError に変わる（呼び出し元が先にモードを確かめるので、画面や API から見える動きは同じ）、(2) Jev の score が大きく範囲外でも黙って 0〜4 に収めてしまう（計画の「わずかなずれ」より広い）→ 提案 P5、(3) 証拠 pytest.log の1行目のコマンドに `PYTHONIOENCODING=utf-8` が抜けていた（実行したコマンドと違う。P1 違反）→ 学んだことへ、(4) `backend/tests/__pycache__/` に T02 で消した一時テストの .pyc が残っている（git 管理外・動作に影響なし）→ 人間の許可（2026-09-26「一時ファイルの残りかすを消してもよいです」）を得て削除した

### 2026-09-26 採用された提案 P4・P5 の記録と一時ファイルの削除
- 人間「提案2つを採用します」→ P4・P5 を新しいタスク T14 として tasks.json に追加（人間の決定による追加。基準タグの更新は人間待ち。それまで check_tasks は T14 について警告を出す）
- 人間「一時ファイルの残りかすを消してもよいです」→ `backend/tests/__pycache__/test_zz_tmp_unmocked.cpython-314-pytest-9.1.1.pyc`（T02 の一時テストの残り。対応する .py は無く、git 管理外）を削除した

### 2026-09-26 T06 音声 → 文字起こし → Jev の state
- 追加: `contest_scorer.score_audio`（Whisper の書き起こしを、そのまま `score_transcript` に渡す）、`backend/tests/test_contest_audio.py`（7テスト）
- 変更: `score_transcript` の入口で、空・空白だけの書き起こしを 400 と日本語のエラーにする（Jev は呼ばない）。音声からでも文字の直接入力からでも同じ検査がかかる
- 書き起こしの前後の空白も削らずにそのまま Jev に渡す（AC-08「そのまま入る」）。OPENAI_API_KEY が無いときは Whisper も Jev も呼ばずに止まる
- 証拠: `evals/evidence/T06/`（pytest.log: 85 passed、secret-scan.log、check_tasks.log）。ログの1行目は、実行するコマンドと同じ変数から書き出した
- 評価役の検品で **合格**（AC-00a/00c/00d/08 すべて○）。評価役はリポジトリの外のコピーでコードを7通り壊し（空判定を外す、Jev の前で strip する、transcribe を使わない など）、7通りとも既存のテストが失敗して検出することを確認した。1行目のコマンドも実際に使われたものと判断された（T05 の指摘は再発なし）
- 評価役の指摘のうち T07 に関わるもの（動画の拡張子、一時ファイルの後片付け）は申し送りへ。小さな指摘（空白付きのテストが結果の transcript までは見ていない）は記録のみ

### 2026-09-26 T07 API（観点→Questions、音声＋Questions→点数）
- 追加: `backend/app/routers/contest.py`（`POST /api/contest/questions`、`POST /api/contest/score`）、`backend/app/utils/validation_messages.py`（Pydantic の英語のエラーを「観点2の配点: 1以上にしてください」のような日本語に直す）、`backend/tests/test_contest_api.py`（19テスト）
- 変更: `main.py` に登録1行、`models/contest.py` の配点を strict に、`question_builder.py` で Question を観点の順に並べ直す
- 申し送りへの対応（決めたこと）:
  - 配点は厳密に整数だけ受け付ける（`"20"`・`20.0`・`true` は 400「整数で入力してください」）
  - Claude が別の順で返しても、Question は観点の順に並べ直して返す
  - 受け付ける拡張子は既存の審査と同じ（mp3/mp4/mpeg/mpga/m4a/wav/webm）。mp4 が Whisper まで届くテストあり
  - 一時フォルダは成功でもエラー（キー未設定・空の書き起こし）でも消える。テストあり
- 入力ミスは FastAPI 標準の 422（英語）ではなく、400 と日本語のエラーで返す。ファイルや Question が無いときも 400
- 証拠: `evals/evidence/T07/`（pytest.log: 104 passed、secret-scan.log、check_tasks.log）
- **評価役の判定: 不合格（AC-09 ×）**。記録: `evals/evidence/T07/review-1.md`。400 と日本語のエラーにならない経路が5つあった:
  1. /questions で配点に5000桁の整数 → 500（`json.loads` の `ValueError` を捕まえていない）
  2. /questions で20万段の入れ子の JSON → 500（`RecursionError`）
  3. /score の question_set で 2 と同じ → 500
  4. /score で media_file をファイルでなく文字列で送る → FastAPI 標準の 422（英語）
  5. /score で question_set をファイルのパートで送る（ブラウザで FormData に Blob を渡すと起きる）→ 422（英語。Starlette の内部オブジェクトの中身も入る）
- 修正方針: `parse_json` で `ValueError`・`RecursionError` も捕まえる／/score は `request.form()` から自分で取り出して検査する（文字列でもファイルのパートでも question_set を受け付ける。media_file が文字列・複数なら 400）／5つの経路と「早く止まる経路では一時フォルダを作らない」をテストに入れる
- 修正: 先に5つの経路のテストを書いて失敗を確かめてから直した（6件失敗 → 修正後すべて成功）。直している途中で、同じ種類の抜けをもう1つ自分で見つけた: 形の崩れた multipart を送ると 400 だが Starlette の英語の文（"Invalid multipart data."）が返る → 日本語に直してテストを追加
- 修正後: pytest 114 passed（`evals/evidence/T07/pytest.log` を作り直した）
- **再検品で合格**（AC-00a/00c/00d/09 すべて○）。評価役は修正前のコード（4451919）で新しいテスト8件が失敗することを確認し、さらに約50通りの異常な入力で英語のエラー・422・500 が0件であることを確かめた
- 再検品の小さな指摘（記録のみ。必要なら提案にする）: question_set を2つ送ると後ろが黙って使われる／終わりの区切りが無い multipart で案内の文言が原因と違う／question_set の上限超えの文言が送り方で違う／深い入れ子のテストが文言まで見ていない／`to_japanese` が知らない種類のエラーは「入力が正しくありません」だけになる

### 2026-09-26 T08 Questions セットの保存・一覧・読み込み
- 追加: `SavedQuestionSet`・`SavedQuestionSetSummary`（models/contest.py）、`question_set_storage.py`（save/list_all/load。`history.py` と同じ作り）、窓口3つ（`POST/GET /api/contest/question-sets`、`GET /api/contest/question-sets/{id}`）、`test_question_set_storage.py`（8テスト）とAPIテスト追記（7件）
- ファイルは `backend/data/question_sets/<uuid>.json`。ファイル名は保存側が作る UUID で、ユーザーが入力した名前をそのままファイル名にしない
- T07 の反省を踏まえ、読み込みの id をそのままファイルパスに使わず、UUID の形だけを受け付けるようにした（`../../etc/passwd` などは 404）。実際に試すと、一部はルーティングの側で先に弾かれ、残りは自作の検査で弾かれる。どちらの経路でも 404 になることをテストで確認
- 証拠: `evals/evidence/T08/`（pytest.log: 132 passed、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00c/00d/10 すべて○）。評価役は id を使った読み込みの安全性を重点的に確認し、パス操作のような id が2つの異なる経路（ルーティング自体・自作の検査）でどちらも404になることを再現した。name が空、question_set が壊れているときに保存前で400になり、ファイルが作られないことも確認
- 評価役の指摘: (1) `backend/.gitignore` が `data/reviews/*.json` は除外しているが `data/question_sets/*.json` を除外していなかった（history.py と同じ作りに揃えるべき。今回のコミットに実データの混入はない）→ このタイミングで直した。(2) `SaveQuestionSetRequest.name` が他の型の書き方（RequiredText）と不統一（動作に問題はない）→ 記録のみ

### 2026-09-26 T09 画面: コンテスト観点の入力フォームとQuestion確認・編集
- 追加: `frontend/src/api/contestApi.ts`（generateQuestions・saveQuestionSet。一覧・読み込みは T10 で使うので今回は追加しない）、`frontend/src/components/contest/`（CriteriaForm・QuestionEditor・QuestionSetReview・ContestQuestionsPage）、`types/contest.ts` に `SavedQuestionSet`・`SavedQuestionSetSummary` を追記（T08 の型のミラー）
- 既存の「ピッチ審査」画面は変えず、`App.tsx` にタブ切り替えで「コンテスト観点モード」を追加した
- 観点の id（Jev の Score の名前に使う英数字IDで、Jev の questions のキーとして使われる）はユーザーに見せず `c1, c2, …` を自動採番。ユーザーは名前・説明・配点だけを入力する
- 申し送りへの対応:
  - Question の並び順（T07/T09 の申し送り）: バックエンド（T07）が既に観点順に並べ替え済みなので、画面側は受け取った順に表示するだけでよい。申し送りをクローズした
  - 付け足した解釈の見せ方（T09 の申し送り）: `QuestionEditor` で、主催者が入力した観点の説明を Question の質問文・段階のすぐ上に表示し、見比べて編集できるようにした
- スクリーンショット（AC-11 の証拠）: 実際に Claude API を呼ぶと料金と承認が必要なため、scratchpad の一時スクリプトで `question_builder.generate_questions` を固定の QuestionSet を返す関数に差し替えて起動した（コミットしない）。Playwright（scratchpad に一時インストール。chromium-cli が環境に無かったため `run` スキルの代替手順に従った）でブラウザを操作し、入力フォーム→生成結果→編集後の3枚を撮影。console エラーは0件。撮影後はサーバーを停止し、`git status` でリポジトリに一時ファイルが残っていないことを確認した
- 証拠: `evals/evidence/T09/`（build.log、pytest.log: 132 passed（既存機能への影響なし）、screenshot-01/02/03、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00b/00c/00d/11 すべて○）。評価役は3枚のスクショを実際に画像として開き、同じコンテスト名・観点が3枚を通して一貫していることと、コードの文言・クラス名との一致から本物の画面と判断した。id の自動採番がバックエンドの正規表現を満たすこと、既存のピッチ審査フローがロジック変更なしで移されていることもコードで確認。合否に影響しない指摘はなし

### 2026-09-26 T10 画面: 音声アップロードと結果表示、保存済みQuestionsの選択
- 追加: `contestApi.ts` に `listQuestionSets`・`loadQuestionSet`・`scoreAudio`（multipart）を追記、`components/contest/`（SavedQuestionSetPicker・AudioScoreForm・ContestScoreResultView）、`ContestQuestionsPage.tsx` の状態遷移を拡張
- 新規生成のフローと保存済み再利用のフローを、`QuestionSetReview`（確認・編集画面）の「この内容で音声を採点する」ボタンに合流させた。保存済みを選んでも編集画面に入るので、そのまま採点しても直してから採点してもよい
- `low_confidence` の観点には voice.md 1章の文言そのまま「発表の中に判断材料が少ないため、この点数は参考値です。」を表示
- 小さな改善: `LoadingState.tsx` に任意の `stages` プロパティを追加（既定値は今までどおりなので既存の動きは変わらない）。T09 で「Questionを生成中」の場面にピッチ審査用の文言（「スライドを解析中…」）が出ていた不正確さも、ここで直した
- スクリーンショット（AC-12 の証拠）: T09 と同じやり方で、今回は `question_builder.generate_questions` に加えて `contest_scorer.score_audio` も固定の点数（うち1つは確信度0.35で low_confidence）を返す関数に一時的に差し替えて撮影（コミットしない）。音声アップロード画面・採点結果画面（合計点・観点別点数・確信度の注意）・保存済み一覧画面の3枚。撮影中に保存した Question セットのファイル（`backend/data/question_sets/`。gitignore 済み）は撮影後に削除した。console エラーは0件
- 証拠: `evals/evidence/T10/`（build.log、pytest.log: 132 passed（既存機能への影響なし）、screenshot-01/02/03、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00b/00c/00d/12 すべて○）。評価役は確信度が低い観点にだけ注意書きが出て、そうでない観点には出ていないことをスクショとコードの両方で確認。画面側が合計・観点別点数を独自に計算し直さず API の値をそのまま表示していること、保存済み選択→編集→採点の流れがコード上つながっていることも確認。合否に影響しない指摘はなし

### 2026-09-27 T13 採用された提案 P2(a)・P3 の反映
- 人間の指示: サンプル音声待ちの間、T11（要承認）より先に依存関係の満たされた T13 を進める
- P2(a): `backend/requirements-dev.txt` に `reportlab`（テスト専用。PDF書き出しはpdfplumberにはできないため）を追加。`test_slide_extractor.py` に PDF（2ページ・英語テキスト。base14フォントは日本語非対応なので英語にした。日本語の抽出はPPTXのテストで確認済み）からの抽出テストと、文字の無いページが空文字になるテストを追加
- P3(a): `test_contest_models.py` の「ValidationErrorになること」だけを見ていたテストに、`errors()` の `loc`（どの項目のエラーか）や具体的な文言の assert を追加。段階数0個のテストで「ちょうど5個」の文言確認を全ケースに広げた（元は0個のときだけ確認を飛ばしていたが、実際は0個でも同じ文言が出ることを確認したので統一した）
- P3(b): `ContestCriterionResult.name` と `ContestScoreResult.contest_name` を `str` から `RequiredText`（`ContestCriterion.name` と同じ制約）に変更し、空文字・空白のみを拒否するテストを追加
- 証拠: `evals/evidence/T13/`（pytest.log: 138 passed（既存132＋新規6）、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00c/00d/03/05 すべて○）。評価役はリポジトリの外で PDF テストを直接実行してファイルが実在しテキストが読めることを確認し、AC-05 の強化されたテストを3パターン意図的に緩めて（誤った項目でエラーにする／型変更を戻す／段階0個のメッセージを変える）すべて検出されることを確認した。合否に影響しない指摘はなし

### 2026-09-27 T14 採用された提案 P4・P5 の反映
- P4(a): `test_question_builder.py` の `FakeAnthropic` に例外を投げられるようにし、2種類のテストを追加。(1) `anthropic.APIConnectionError`（既存の専用 except 節）→ 502＋「接続に失敗」を含む日本語文言。(2) 型の無い `RuntimeError`（generic な except Exception 節）→ 502＋`FAILURE_DETAIL`。最初 (1) だけを実装し `FAILURE_DETAIL` と一致するはずと書いたが、`_call_claude` の専用 except 節はより具体的な別の日本語文言を返すことが分かり、2つに分けて書き直した
- P4(b): `question_builder.py` の `_format_validation_error`（Pydantic の生メッセージを英語のまま繋げていた）を削除し、`contest.py` の入力チェックで既に使っている `app.utils.validation_messages.to_japanese` に統一。段階が空のQuestionをClaudeが返したときのエラーが「Question1の段階5: 入力してください」のような日本語になることをテストで確認
- P4(c): `test_wrong_level_count_is_rejected` の入力を、同じ文の繰り返し（`LEVELS[:1] * count`）から段階ごとに別々の文（`f"段階{i}の説明文"`）に変更
- P5: `contest_scorer.py` に許容誤差 `JEV_SCORE_DRIFT_TOLERANCE = 0.001` を追加。範囲外だが誤差の範囲内ならこれまで通り0〜4に収め、それを超えたらログを残して502（観点名入りの日本語エラー）にする。既存の「わずかな誤差」テスト（0.0000001）は許容範囲内なので変更なし、「大きく外れた」ケース（5.0, -1.0, 4.5, -0.5）が502になるテストを追加
- 気づいたこと（このタスクの範囲外・今回は直していない）: バックエンドの全テストを複数回流したところ、1回だけ `test_question_set_storage.py::test_list_returns_newest_first_with_summary_fields` が失敗した。2件を連続保存したときの一覧の並び順を `os.path.getmtime`（ファイルの更新時刻）で決めているため、同じミリ秒に保存されるとまれに順序が入れ替わる。3回連続で単体実行、3回連続で全体実行するとすべて成功したので頻度は低いが、直すなら保存時刻を保存内容（`saved_at`）で比べる方が確実。提案 P6 として記録
- 証拠: `evals/evidence/T14/`（pytest.log: 145 passed、secret-scan.log、check_tasks.log）
- 評価役の検品で **合格**（AC-00a/00c/00d/06/07 すべて○）。評価役は T14 対象のテストだけを5回連続・mtimeフレークのテストを単体で20回連続実行してどちらも安定して成功することを確認し、P6（mtimeフレーク）が今回の変更と無関係であると裏付けた。許容誤差0.001の境界（±0.0005は成功、±0.002は502）もリポジトリの外で実測して確認。合否に影響しない指摘はP6のみ（対応済みで記録済み）

### 2026-09-27 UI改善のためデザインSKILLを導入（人間の指示・T番号なし）
- ローカルで実際に動かして画面を確認したいという人間の依頼を受け、バックエンド（uvicorn）とフロントエンド（vite dev）を起動して確認してもらった
- 人間が https://www.tasteskill.dev/ の導入を依頼。中身を WebFetch で調査（無料・オープンソース・MITライセンス・アカウント/APIキー不要）してから `npx skills add Leonxlnx/taste-skill` を実行
- このコマンドは同じリポジトリにまとめられていた13個のスキルすべて（`.claude/skills/` にシンボリックリンク、`.agents/skills/` に実体、`skills-lock.json`）を入れてしまった。中身（SKILL.md）はすべて目視で確認し、外部通信や秘密情報を扱うような危険な指示は無かった
- 13個のうち、このプロジェクト（React + 素のCSS）に関係あるのは `design-taste-frontend`（tasteskill.dev 本体）と `redesign-existing-projects`（既存コードの診断・底上げ）の2つだけと判断し、人間に確認のうえ残り11個（ロゴ/モックアップ画像生成、Google Stitch専用、Codex専用、競合する作風の強制など）を削除し、`skills-lock.json` も2件だけに揃えた
- Windows では `core.symlinks=false` のため、Git はシンボリックリンクではなく実体ファイルとしてコミットした（`.agents/skills/` と `.claude/skills/` の両方に同じ内容が入るが、Git 上は同じ blob なので二重には保存されない）
- まだ実際のUI改善（redesign-existing-projects スキルを使った作業）は行っていない。次にやるかは人間の指示待ち

### 2026-09-27 UI改善（redesign-existing-projects 中心・design-taste-frontend は一部のみ）
- 気づいたこと: `design-taste-frontend`（tasteskill.dev 本体）は「ランディングページ・ポートフォリオ向け」で、スキル自身が「ダッシュボード・複数ステップのフォーム・製品的なUIには向かない」と明記している。harinezumi は入力フォーム→生成→確認→採点という多段階のフォームアプリなので、対象外と判断。ヒーローセクション・マーケティング的な要素・GSAP等の新規ライブラリは使わず、`redesign-existing-projects`（どんなアプリにも使える汎用の監査リスト）を中心に、`design-taste-frontend` からはフォント/配色/ホバー・フォーカス反応など汎用的な部分だけを採用した
- 診断（redesign-existing-projects の監査チェックリストと照合）: 配色・フォント・角丸・カード構造は既に無難（AI にありがちな紫グラデーションや過度な角丸は無い）。一方で、ボタンに hover/active の反応が一切無い、フォーカスリングがブラウザ既定のまま、input/textarea/select に明示的な枠線が無くブラウザごとの見た目に依存、要素の遷移（transition）が皆無、キーボード操作用の「メインコンテンツへスキップ」リンクが無い、という具体的な抜けを確認
- 直したこと（`frontend/src/index.css`、`frontend/src/App.tsx`。新しい npm パッケージは追加していない）:
  - 角丸を `--radius-sm/md/lg` の3段階に統一
  - ボタン・タブ・入力欄に hover / active / focus-visible の反応と 150ms の transition を追加
  - input/select/textarea に明示的な枠線・角丸・フォーカス時のアクセントカラーの縁取りを追加
  - 見出し（h1/h2）の太さ・字間・行間を調整して視覚的な重みを出した
  - カード（.upload-form 等の大枠）に、背景色と同系色（テラコッタ）を薄く乗せた影を追加（真っ黒の影ではなく色味を合わせる、というredesignスキルの指針に沿った）
  - 観点別スコアのバーに、値が変わるときのアニメーション（width の transition）を追加
  - キーボード操作向けに「メインコンテンツへスキップ」リンクを追加
- 確認: `npm run build` 成功、バックエンドの既存テスト145件がそのまま合格（今回はフロントエンドのみの変更）。ローカルの開発サーバー（起動済み）に Playwright（scratchpad）でアクセスし、before/after のスクリーンショットを撮影。console エラー0件
- 証拠: `evals/evidence/ui-redesign/`（after-01-pitch-review.png、after-02-button-hover.png、after-03-contest-form-focus.png）。T番号は無いので `evals/acceptance.md` の対象外だが、変更前後の見た目を記録する目的で残す
- 評価役による検品は行っていない（tasks.json のタスクではないため）。人間が実際に画面で確認する想定

### 2026-09-27 UI改善の不具合修正: 「保存済みのQuestionsを使う」がホバー時に文字が見えなくなる
- 人間の報告: コンテスト観点モードの「保存済みのQuestionsを使う」にカーソルを合わせると、オレンジ色のベタ塗りになって文字が見えなくなる
- 原因: 前回追加した `.link-button:hover { background: none; ... }` は、汎用の `button:hover:not(:disabled) { background: var(--accent-dark); }` とCSSの詳細度（specificity）が同点になり、**あとに書かれた汎用ルールの方が勝っていた**。結果、背景がテキストと同じ色（accent-dark）に塗られ、文字が読めなくなっていた。詳細度の計算を誤っていたのが原因（この2つのCSSは「クラス1つ＋疑似クラス1つ」と「要素1つ＋疑似クラス2つ」で、疑似クラスの数は同じでも要素セレクタの分だけ後者が勝つ）
- 直し方: 詳細度で競わせる代わりに、汎用ルールの側に `:not(.link-button)` を追記し、「文字だけのボタン（.link-button）には、そもそも塗りつぶしの背景色を適用しない」と明示した。あわせて、不要になった `.link-button:hover` 側の `background: none` は削除して簡潔にした
- 確認: `npm run build` 成功、バックエンド既存テスト145件はそのまま合格。ローカルの開発サーバーで実際にホバーさせたスクリーンショットを撮り、文字が読めることを確認
- 学んだこと: CSSの詳細度を「クラス+疑似クラスの数」だけで比較して「要素セレクタの有無」を見落とした。同点になりそうな場合は、詳細度で競わせるより `:not()` で明示的に対象を除外する方が、あとから見ても意図が分かりやすく安全
- 証拠: `evals/evidence/ui-redesign/fix-link-button-hover.png`

### 2026-09-27 本番反映の相談 → 保留、および contestApi.ts のタイムアウト・本番URL対応
- 人間から「mainにマージして本番反映したい」と依頼を受けたが、調査の結果 (1) Vercel用の設定ファイル `vercel.json` は `main` ではなく `feature/business-contest-rubric` にしかない、(2) その `feature/business-contest-rubric` は私たちが枝分かれした後に、もう一人の開発者が18コミット（別のUIリデザインを含む）を追加していたことが判明。CSSファイルの衝突・見た目の混在のリスクがあるため、人間の判断で **マージ・pushは保留し、もう一人の開発者に確認してから** 進めることになった。push は一切していない
- 人間から「3分のピッチを送ったらどのくらいで分析できるか」と聞かれ、実測値が無いため処理の流れ（アップロード→Whisper文字起こし→Jev採点）から目安（30秒〜1分半程度）を回答し、実測にはT11（要承認）が必要と伝えた
- その過程で、`frontend/src/api/contestApi.ts` の `scoreAudio`（音声で採点するAPI呼び出し）に、既存の `reviewApi.ts` にはあるタイムアウト（5分でAbortし、日本語のエラーを出す）が無いことに気づき、人間の依頼で修正
- 修正中にもう1つ気づいた抜け: `contestApi.ts` の全関数が `reviewApi.ts` にある `API_BASE_URL`（本番でフロントエンドとバックエンドが別オリジンの場合に使う設定）に対応しておらず、相対パスに固定されていた。本番反映時に動かなくなる可能性があったため、依頼された範囲を超えるが同じ種類の抜けとして一緒に直した
- 直し方: `getJson`・`postJson`・`scoreAudio` が共通で使う `fetchWithTimeout` ヘルパーを作り、`API_BASE_URL` 付与とタイムアウト処理を一本化（reviewApi.ts と同じパターン）
- 確認: `npm run build` 成功、バックエンド既存テスト145件はそのまま合格、ローカルの開発サーバーで実際に一覧取得APIが動くことを確認（`VITE_API_BASE_URL` 未設定時は相対パスのまま＝今までと同じ動き）

### 2026-09-27 ピッチ資料（pptx）と台本の作成（人間の依頼・T番号なし）
- ハッカソン用の5分ピッチ資料を `pitch/harinezumi_pitch.pptx` に作成（15枚：本編14＋デモ失敗時の予備1）。人間の参考画像（`Screenshot 2026-09-27 050107.png`：オレンジ主体・重要度に青・角丸・游ゴシック）に合わせた。各スライドのノートに台本（時間・話すこと・動き）を記入
- 生成スクリプトは scratchpad（pptxgenjs）。PowerPoint COM で全ページを画像化して目視確認し、読点の孤立・スクショの読みにくさ・余白の偏りを修正。validate.py は合格
- `pitch/` と参考画像はまだコミットしていない

### 2026-09-27 T15 コンテスト観点モードでスライドも使う
- 人間の質問「スライド資料を入力した場合どう使われるか」に、ピッチ審査タブのみで使われ、コンテスト観点モードでは使われないと回答。その後、人間の依頼でT15を追加（基準タグの更新は人間待ち）
- 変更: `contest_scorer.score_materials`（スライドのみ・音声のみ・両方）、`build_jev_state`（音声のみなら書き起こしをそのまま＝従来どおり、スライドがあればピッチ審査と同じ `build_user_prompt` で組み立て）、`ContestScoreResult` に `slides_included`・`transcript_included`、`/api/contest/score` に `slide_file`（任意）を追加し `media_file` も任意に。画面にスライドの選択欄と「何で採点したか」の表示
- T07 の反省を適用: 壊れたPDF/PPTX（pdfplumber・python-pptx の例外）、文字の無いスライドのみ、拡張子違い、スライド2つ、スライド欄に文字列、はすべて日本語の400。どちらも無いときも400
- 意図した挙動変更: 「ファイルが無い」ときの文言が「スライド資料、または発表の音声・動画ファイルを指定してください。」に変わったため、既存テスト1件（test_missing_media_file_is_400）を新しい意味（両方無い）に合わせて書き換えた
- テスト: 161件合格（新規 `test_contest_slides.py` 16件、既存1件の更新）
- 画面確認: 外部API（Claude・Whisper・Jev）だけを偽物にし、スライド抽出と Jev に渡す文章の組み立ては本物のコードで動かして撮影。Jev が受け取った文章（スライド本文・スピーカーノート・書き起こし）をログとして証拠に保存（`jev-state-from-ui.log`）
- つまずき: (1) 前回 `--reload` 付きで起動したバックエンドを止めても、子プロセスがポート8000を握ったまま残り、スタブが起動できなかった → 子プロセスを特定して停止。以後は `--reload` なしで起動。(2) Vite の開発サーバーが、OneDrive 上のファイルの連続した書き換えの最後の1回を取りこぼし、古いコードを配信していた（ビルドは成功しているのに画面が真っ白）→ 開発サーバーを再起動。(3) 結果画面のボタン「別の音声でもう一度採点する」がスライドのみの採点では不正確なので「もう一度採点する」に変更
- 証拠: `evals/evidence/T15/`
- 評価役の検品で **合格**（AC-00a/00b/00c/00d/08/09/12 と task 文の要件すべて○）。評価役は異常な入力を32通り＋500ページのPDFで試し（0バイト、中身と拡張子の不一致、パスワード付きPDF、途中で切れたPDF、ファイル名 `../../x.pdf`、21MB超など）、500・英語のエラー・一時フォルダの残り・外部通信がいずれも0件であることを確認。書き換えた既存テストは「仕様変更に伴う正当な書き換えで、むしろ厳しくなった」と判断
- 評価役の合否に影響しない指摘: (1) P6 の不安定テストが実測で全体実行13回中3回・単体8回中1回失敗（見積もりの「数百回に1回」より大幅に多い）→ P6 の記述を更新し採用を推奨、(2) PDFのページ数・文字数に上限が無い（500ページで0.37秒だが Jev に渡る文章が長くなりうる）、(3) PPTX の表・グループ化した図形の文字は読まれない（ピッチ審査と共通の既存処理）が、画面の注記では伝わりにくい、(4) 書き起こしが空で400になったとき「スライドだけで採点し直す」案内が無い → (2)〜(4) は提案 P7 として記録

### 2026-09-27 T16 採用された提案 P6 の反映
- 人間「提案P6を受け入れます。実行してください。」→ T16 として tasks.json に追加（人間の決定による追加。基準タグの更新は人間待ち）
- 変更: `question_set_storage.list_all()` をファイルの更新時刻ではなく保存内容の `saved_at` で並べるように。`save()` に `_next_saved_at()` を追加し、時計が同じ時刻を返しても直前の保存より1マイクロ秒以上あとになるようにした
- テスト: 新規2件（ファイルの更新時刻を逆にしても saved_at 順／時計を止めても新しい順）。既存テストは書き換えていない。全体 163 件合格
- 修正前のコードに戻して新しいテストを実行すると失敗することを確認（`before-fix.log`）。修正後は該当ファイルを30回・全体を10回繰り返し実行してすべて成功（`repeat.log`、`repeat-full.log`）
- 証拠: `evals/evidence/T16/`
- 人間が基準タグを更新（T16 を受け入れ）
- 評価役の検品で **合格**（AC-00a/00c/00d/10 と task 文の要件すべて○）。評価役は不安定だったテストを単体で50回連続（50/50成功）、該当ファイルを30回連続で再実行。使い捨ての作業コピーで保存処理だけを修正前に戻し、新しいテスト2件が失敗することを確かめた。既存テストは追加のみで弱められていないことも確認
- 評価役の合否に影響しない指摘: `_last_saved_at` は鍵（ロック）なしの共有変数なので、同時に2件保存すると理論上同じ時刻になりうる（1人で使うローカルアプリなので実害はほぼ無い）。再起動をまたぐ順番はパソコンの時計に頼る

### 2026-09-27 T17 採用された提案 P7 の反映
- 人間「提案P7を採用します。実装してください。」→ T17 として tasks.json に追加（人間の決定による追加。基準タグの更新は人間待ち）
- (a) `config.py` に `max_contest_slide_pages`=60・`max_contest_slide_chars`=30000 を追加。`contest_scorer.check_slide_limits()` を `score_materials` と、`score_audio` の **Whisper 呼び出しより前** で実行。超えたら「61ページ、上限60ページ」のように数字入りの日本語400。ピッチ審査タブには上限をかけていない
- (b) `slide_extractor.extract_from_pptx` がグループ図形の中（入れ子も）と表のセル（行ごとに「 | 」区切り、空セルは飛ばす）も読むように。ピッチ審査タブも同じ処理なので、そちらも読める文字が増える。画面の注記を更新し上限も表示
- (c) 書き起こしが空の400で、文字のあるスライドが一緒なら「スライド資料だけを選び直して採点すれば…」を付け足す。エラー後は選択欄が空に戻ることをスクショで確認したので「選び直して」とした
- テスト: 新規 `test_contest_slide_limits.py` 11件・`test_slide_extractor.py` に2件。全体175件合格。修正前のアプリのコードに戻すと新しいテストが失敗することを確認（`before-fix.log`）
- 画面確認: T15 と同じく外部API（Claude・Whisper・Jev）だけ偽物にしたサーバーで撮影（61ページのPPTX→上限エラー、無音の音声＋スライド→案内）
- つまずき: スクショ保存先のパスを bash のヒアドキュメントで書いたら `\\` が `\` 1つになり、JS のテンプレート文字列で `\s` が消えて `evals/evidence/T17screenshot-…png` という名前で保存された → 自分が直前に作ったファイルなので削除し、区切りを `/` にして撮り直した
- 証拠: `evals/evidence/T17/`
- **評価役の判定: 不合格（in_progress に差し戻し）**（`evals/evidence/T17/review.md`）。AC-00a/00b/00c/00d/09/12 と (a)(c) は○、(b) が×。理由: `_shape_texts` が全図形で `shape.shape_type` を呼ぶが、python-pptx は形の指定（prstGeom/custGeom）もテキストボックス印も無い図形で `NotImplementedError` を投げる。T17 前は読めていたそのような PPTX が、ピッチ審査タブ `/api/slides/extract` で **500**、コンテストでは「壊れています」の誤った400になる（回帰）。直し方の例: グループ判定を `isinstance(shape, GroupShape)` にする／`shape_type` の例外を捕まえて従来の読み方に戻す。その図形を含む PPTX のテスト（抽出・ピッチ審査タブ・コンテスト）を足す
- 差し戻しへの対応: 評価役の指摘を自分でも再現（形の指定を消した図形で `NotImplementedError`）。グループの判定を `isinstance(shape, GroupShape)` に変更し、`shape_type` を使わないようにした。テスト2件追加（抽出処理、ピッチ審査タブ `/api/slides/extract` とコンテスト採点の両API）。差し戻し前の抽出処理ではこの2件が失敗し（`regression-before-fix.log`）、修正後は全体177件合格。1回目の検品記録は `review-1.md` に名前を変えて残した
- 評価役の合否に影響しない指摘のうち、「画面の上限表示（60ページ・30,000文字）は config.py の値を手で写している」は未対応（.env で上限を変えたときは AudioScoreForm.tsx の数字も直す必要がある）
- 人間が基準タグを更新（T17 を受け入れ）
- 評価役の再検品で **合格**（`review.md`。AC-00a/00b/00c/00d/09/12 と (a)(b)(c) すべて○）。評価役は形の指定が無い図形（外側・グループ内・3段の入れ子）、spPr が空の図形、結合セル、画像・コネクタ・グラフ・自由形・未知の図などを含む PPTX を作り、抽出処理・ピッチ審査タブ・コンテスト採点の3経路すべてで正常なことを確認。T17 前に読めていた文字はすべて今も読めることも確認
- 評価役の合否に影響しない指摘: (1) 仕様違反の壊れた PPTX（graphicFrame に必須の要素が無い）は T17 前は読み飛ばされていたが、今は例外になる（ピッチ審査タブでは500。ただし壊れたファイルで500になるのは T17 前から）、(2) 手書きインクを含むスライドは python-pptx 内部で例外（T17 前から同じ）、(3) 画面の上限表示の手書き写し（上記）、(4) secret-scan.log が `6b60d45` 時点のまま → 実際は `77652ce` の前に取り直したが、内容が同じだったため git 上は変更なしに見えている
- 学んだこと: ライブラリの便利な属性（今回は python-pptx の `shape_type`）は、正しいファイルでも例外を出すことがある。読み取り処理を変えるときは「前は読めていたファイルが今も読めるか」をテストで確かめる

### 2026-09-27 T18 他の開発者のブランチ（本番の機能）をマージで取り込む
- 人間の依頼「他の人がデプロイしている機能を確認することはできますか？その機能をここにも実装してください。」→ `git fetch` で確認（取得のみ・push なし）。`origin/feature/business-contest-rubric` の17コミット（最新 161f8d7）。T18 として tasks.json に追加（人間の依頼による追加。基準タグの更新は人間待ち）
- 人間の決定: マージで取り込む／見た目はこちらのオレンジを維持
- 衝突3ファイルを解消（`merge.log`）: `jev_scorer.py` は両方の関数を残し、`score_with_jev` は相手の新しい形（評価基準を引数で受け取る）に。`review_generator.py` の `_call_claude` は相手の `tools` とこちらの `failure_detail` を両方。`index.css` はこちらを採用し、相手の新しい部品（評価基準プレビュー・判定基準の表示・Powered by）のスタイルをオレンジで書き直して追加
- 既存テストの書き換え: 相手が `score_with_jev(text, mode)` → `(text, criteria)`、`compute_overall_score(scores, mode)` → `(scores)` に変えたため、T02 で書いたテスト9件の呼び出し方だけを新しい形に合わせた（確かめている中身は同じ）。評価基準の数が7以外でも総合点が正しいテストを1件追加
- 相手のブランチにはテストが無かったため `test_merged_review_features.py`（22件）を追加: 評価基準の3方式（既定・イベント内容からAIが設計＝web検索ツール付き・項目名指定＝ユーザーの名前と順番を守る）と優先順位、プレビューAPIの入力チェック（日本語400・Claudeを呼ばない）、結果に判定基準が入る、動画の静止画の説明がJevに渡る・説明に失敗しても審査は止まらない、本物の小さな動画から静止画4枚をJPEGで取り出せる
- 依存関係 `av`（PyAV）を venv にインストール（相手が requirements.txt に追加済み）
- 画面確認（外部APIだけ偽物）: 評価基準プレビュー、結果カードの判定基準、コンテスト観点モードがオレンジのまま。途中で、プレビューの「1点」と説明が別の行に分かれる不具合を見つけた（既存の `.field span` が block にしていた）→ プレビュー内だけ inline に直した
- テスト200件合格、ビルド成功
- 証拠: `evals/evidence/T18/`
- 評価役の検品で **合格**（`review.md`。AC-00a/00b/00c/00d ○、相手の機能・こちらの機能ともに○）。評価役は、相手のブランチで変わったファイルが衝突した4ファイル以外まったく同じであること、コンテスト観点モードのファイルがマージ前と同じであること、`index.css` のマージ前の部分が1行も変わらず暗いテーマの名残が0件であることを確認。使い捨てのコピーで相手の実装を9通り壊し、追加テストが9通りすべてで失敗することも確かめた
- 評価役の合否に影響しない指摘: (1) `index.html` の Google Fonts が未使用（P8(d) と同じ）、(2) `.powered-by-sep` にスタイルなし（見た目の問題なし）、(3) コンテスト画面の「観点を追加する」と「Questionを生成する」のボタンの間に隙間がない（マージ前から）、(4) Jev キーが無いとき（Claude だけで採点）に判定基準が返るかはテストされていない（コード上は入れている）

### 2026-09-27 T19 採用された提案 P8 の反映
- 人間「提案8を受け入れます。実装してください。」→ T19 として tasks.json に追加（人間の決定による追加。基準タグの更新は人間待ち）
- (a) `CriterionScore.levels` を省略可（既定は空リスト）に。判定基準の無い古い形の履歴 JSON を置いても `/api/reviews/history` が 200 で読める（画面は空なら「審査基準を見る」を出さない既存の作り）
- (b) `generate_rubric_from_names`: Claude が返した項目数が指定と違えば、判定基準を空のまま使わず日本語の 502（Jev は呼ばない）
- (c) `parse_custom_rubric`: 項目ごとに確かめ、英語の生メッセージの代わりに「評価基準の2番目の項目の形式が正しくありません（段階: 5個以上にしてください）」のような日本語に
- (d) `index.html` から使っていない Google Fonts の読み込みを削除（CSS に Space Grotesk / Inter の指定が無いことを確認）
- テスト6件追加。修正前のコードでは6件とも失敗（`before-fix.log`）、修正後は全体206件合格。ビルド成功
- 証拠: `evals/evidence/T19/`
- 評価役の検品で **合格**（`review.md`。AC-00a/00b/00c/00d/09 と (a)(b)(c)(d) すべて○）。評価役は壊れた評価基準を24通り送って500・英語のエラーが0件、項目数の不一致（1・2・4・10個）ではJevも審査本体のClaudeも呼ばれないこと、新しい審査結果には4通りの評価基準すべてで判定基準が5個入ることを確認
- 評価役の合否に影響しない指摘: (1) 編集した評価基準の name が空文字でも通る（T18以前からの挙動）、(2) (b) のテストは審査本体のClaudeが呼ばれないことまでは見ていない（評価役がAPI経由で確認済み）、(3) `/api/review` のキー未設定エラーのテストが無い、(4) `backend/data/reviews/` に履歴が2件ある → **T18 の画面確認（偽物のAIを使った撮影）で私が作ったもので、中身は偽物の審査結果**。git の管理外（.gitignore 済み）。削除は人間の承認が必要なので確認待ち
- 人間「偽物の審査記録2件は消してください」（2026-09-27）→ 2件とも撮影用の固定文言を含むことを確かめてから削除。`backend/data/reviews/` は0件

### 2026-09-27 T11 実APIで1回通しの動作確認
- 人間の承認: 「.envにAPIkeyを登録しました テストしてください」。キー3つとも設定済みを有無だけで確認
- サンプル音声: ピッチ台本（スライド1〜8の「話すこと」、605文字）を Windows 音声合成（Haruka）で読み上げた WAV（約113秒）。スライドは `pitch/harinezumi_pitch.pptx`。本番のデモ（最初の2分を録音して採点）と同じ組み合わせ
- バックエンドを再起動して .env のキーを読み込ませ、画面から1回だけ通しで実行（Claude 1回・Whisper 1回・Jev 1回）。**1回目で成功**、やり直しなし
- 結果: Question生成 13.6秒、採点（書き起こし＋Jev）7.9秒。3観点すべてに点数（22.8/30、30.9/40、29.9/30）、合計 83.6/100。確信度 0.78〜0.99 で「参考値」扱いは無し。換算を検算し一致
- 実測で分かったこと: 2分弱の音声なら採点は約8秒（以前の目安「30秒〜1分半」より速い）。Whisper は固有名詞を聞き違えた（起業部→企業部、配点→拝点、Claude→クローダーを、Jev→jf）。スライドの文字も一緒に Jev に渡るので、スライドを添えると聞き違いの影響を減らせる
- 証拠: `evals/evidence/T11/`（e2e.log にキーや個人情報は無いことを確認）
- 評価役の検品で **合格**（`review.md`。実APIは呼ばずに証拠で判定）。指摘を受けて、引き継ぎメモを最新にし、生の応答・実行スクリプト・読み上げ台本を証拠フォルダに保存した

### 2026-09-27 T20 コンテスト観点モードにも映像の分析を入れる
- 人間の質問「映像から身振り手振りを採点する機能はついていますか？」→ ピッチ審査タブだけにある（T18 で取り込み済み）と回答。人間の依頼「コンテスト観点モードにも映像の分析を入れてください」→ T20 として追加（基準タグの更新は人間待ち）
- 変更: `contest_scorer.score_audio` で、書き起こしが空でなく・動画（mp4/webm）で・Claude のキーがあるときだけ、静止画4枚 → ピッチ審査タブと同じ `describe_presentation_visuals` で説明 → Jev の state に「# 発表映像から読み取れる非言語的表現」の節を追加。失敗・キー無し・静止画なしなら映像なしで採点を続ける。音声だけのときの state は書き起こしそのまま（AC-08 を維持）。`ContestScoreResult` に `visual_included`・`visual_description`（既定値つき）
- 画面: 注記、読み込み段階「映像から身振り・表情を分析中…」、結果画面に使った材料と「映像から読み取った様子」
- テスト: `test_contest_video.py` 14件（動画→映像の節が Jev へ／音声のみは変化なし・静止画も取らない／説明失敗・静止画なし・キー無しでも採点継続／書き起こし空やスライド上限超えでは映像分析（有料）をしない／API経由のmp4）。全体220件合格
- 画面確認: 外部APIだけ偽物（**今回は .env に本物の ANTHROPIC キーがあるため、偽物サーバーでは ANTHROPIC キーもダミーで上書きし、映像のClaude呼び出しも偽物にした**）。静止画の取り出しは本物のコードで、64x64・5秒の本物の動画から4枚取れた（`jev-state-from-ui.log`）
- つまずき: Vite を止めても子プロセスがポート5173を握ったまま残り、新しい Vite が5174で起動 → 5173の古い Vite が途中の状態のコードを配っていて「isVideoFile is not defined」。子プロセス（自分が起動した vite.js）を特定して止め、5173で起動し直した
- 証拠: `evals/evidence/T20/`
- 評価役の検品で **不合格**（1回目の記録は `evals/evidence/T20/review-1.md` に名前を変えて残した）。理由: アップロードした動画の一時ファイルが採点後に消えない（Windows）。`video_frames.extract_frames_base64` が `av.open` した動画を閉じないため、直後の `shutil.rmtree(tmp_dir, ignore_errors=True)` が黙って失敗し、`%TEMP%\tmpXXXX\tmpYYYY.mp4` が残る（偽物のAIで実物の mp4 を API に送り、7回中7回で残るのを確認。実行役の画面確認で残ったと思われる 10:30 / 10:32 の2つも `%TEMP%` に残っている）。`test_api_mp4_upload_uses_video_and_cleans_up` は、fixture で差し替え済みの偽物の静止画取り出しを「本物」として包んでいるため、PyAV を通らず、この問題を見逃している。直し方の例: `with av.open(...) as container:` で必ず閉じる＋本物の動画で「採点後に一時フォルダが消える」テストを足す（ピッチ審査タブ `routers/review.py` も同じ関数を使うので同じ問題あり）
- 差し戻しへの対応: 自分でも再現（静止画を取り出したあと一時フォルダを消せず残る）。`video_frames.extract_frames_base64` を `with av.open(...) as container:` にして必ず閉じるように修正（ピッチ審査タブも同じ関数なので両方直る）。見逃したテストは、fixture で偽物にした関数を包んでいて PyAV を通っていなかった → 本物の小さな mp4 を API に送り、本物の静止画取り出しを通したうえで一時フォルダが消えることを確かめるテストと、取り出し後にファイルを削除できるテストに置き換えた。合否に影響しない指摘のうち「Claude が空の文章を返すと visual_included が true になる」も直し、テストを追加
- 差し戻し前のコード（b6bfa3b）では新しいテスト3件が失敗（`regression-before-fix.log`）、修正後は全体222件合格
- 一時フォルダ `%TEMP%` に残っている動画入りのフォルダ4つ（10:30・10:32 は自分の画面確認、10:44 は再現、10:45 は修正前コードでのテスト実行で作ったもの。中身はすべて合成したテスト用動画）は、削除に人間の承認が必要なので確認待ち
- 評価役の合否に影響しない指摘のうち未対応: 静止画の取り出しが同期処理で、長い動画ではサーバー全体が待たされる（ピッチ審査タブも同じ）／スライドなしで動画を送ると state に「書き起こしのみで審査」の文と映像の節が並ぶ（ピッチ審査タブと同じ文言）

---

## 学んだこと（改善の蓄積）
> 失敗やつまずきを1行で書く。同じ内容が **2回** 出たら、ルール化の提案を「提案」欄に書く。
> 人間が採用したら、AGENTS.md / docs/safety.md / SKILL.md のどこかに反映し、ここに「→反映済み（ファイル名）」と書く。

- （例）Windows では `python` が別の環境を指すことがある → `backend/.venv/Scripts/python` を明示する
- T00: `git switch -c <新> origin/<別ブランチ>` を使うと、新しいブランチがその別ブランチを追跡する設定になる。作ったらすぐ `git branch --unset-upstream` で外す
- T00: 複数のコマンドを `&&` でつなぐと、途中のコマンドがわざと失敗させるもの（例: upstream が無いことの確認）でも、そこで後ろが止まる。証拠を取るコマンドはつなげずに1つずつ実行する
- T00（評価役の指摘）: 秘密情報チェックの証拠に、実際に使ったコマンドと違う書き方を残していた。証拠には、実行したコマンドをそのまま記録する
- T01（評価役の指摘・不合格）: 見出しに「確定」の印を付けると、その下の項目すべてが確定に見える。確定・仮定の印は、項目ごとに付ける
- T01: `check_tasks.log` にも実行したコマンド行を入れる（T00 と同じ種類の指摘が2回目 → P1 として docs/roles.md に反映済み）
- T02: 「テストが全部通った」だけでは安全装置が効いている証明にならない。わざと失敗するはずの状況（モック無しの呼び出し）を作って、本当に止まるか確かめる。今回それで遮断の抜け穴が見つかった
- T02（評価役の指摘）: 秘密情報チェックは、必ず `git add` した後に safety.md どおり `git diff --cached` で行う（`git diff` だけだと新規ファイルが漏れる）
- T03: テストの補助関数で `x or 既定値` と書くと、空のリストや 0 が既定値にすり替わる。「指定なし」は `is None` で判定する
- T07（評価役の指摘・不合格）: 「入力ミスは 400 と日本語」を作るときは、普通の入力ミスだけでなく、異常な入力（巨大な数、深い入れ子、ファイルの代わりに文字列、ブラウザ特有の送り方、壊れた multipart）も試す。FastAPI や Starlette が自動で返す英語のエラーの経路を1つずつ潰す
- T07: ヒアドキュメントの中の Python で `\r\n` を書くと、本物の改行になってファイルが壊れることがある。エスケープを含む行は Edit ツールで直接書く
- T05（評価役の指摘・P1 違反）: 証拠の1行目のコマンドから `PYTHONIOENCODING=utf-8` が抜けていた。証拠の1行目は、実行するコマンドと同じ文字列の変数から書き出す（手で書き写さない）
- T05: Python の `round()` は四捨五入ではない（ちょうど半分は偶数側へ: 0.25 → 0.2）。四捨五入が要件なら `Decimal` の `ROUND_HALF_UP` を使い、「ちょうど半分」のテストを入れる
- T02: Windows の非同期通信は `socket.connect` を通らない。通信を止めるときは名前解決（getaddrinfo）と asyncio の接続も止める
