# roles.md — AI の役割分担（3役）

> 書き換えてよいのは人間だけ。
> 1つのセッションで役を兼ねてもよいが、**評価役だけは必ず別の頭（新しいサブエージェントか新しいセッション）** で行う。
> 自分で作ったものを自分で合格にすると、見落としに気づけないため。

---

## 1. 計画役（Planner）
| 項目 | 内容 |
|---|---|
| 担当する | 次のタスクを1つ選ぶ／そのタスクの作業手順・変更するファイル・書くテストを決める／前提（依存タスク）が満たされているか確認する |
| 担当しない | コードを書く、合格判定をする、要件やタスクを書き換える |
| 最初に読む | `progress.md` → `tasks.json` → `docs/mission.md` → `docs/requirements.md` → `evals/acceptance.md` の該当 AC |
| 使える道具 | ファイルを読む・検索する、`git log` / `git diff`、`progress.md` への追記 |
| 返す成果物 | `progress.md` の「作業計画」欄（タスクID、手順3〜7個、変更予定ファイル、確認方法、承認が必要な操作の有無） |
| 完了条件 | 計画が該当 AC をすべてカバーしている／承認が必要な操作があればユーザーの返事をもらっている |

**タスクの選び方**: `status` が `todo` で、`dependencies` のタスクがすべて `done` のもののうち、ID が一番小さいもの。
該当が無ければ、止まっている理由（blocked / 人間待ち）をユーザーに報告する。

---

## 2. 実行役（Builder）
| 項目 | 内容 |
|---|---|
| 担当する | 計画どおりにコードとテストを書く／テストとビルドを実行する／証拠を `evals/evidence/<タスクID>/` に保存する／`status` を `review` にする |
| 担当しない | 計画にないタスクへの手出し、`passes` を `true` にすること、合格条件の変更、承認が必要な操作の独断実行 |
| 最初に読む | `progress.md` の作業計画 → 変更予定のファイル → `docs/voice.md` → `docs/safety.md` |
| 使える道具 | ファイルの読み書き、`pytest`、`npm run build`、`git add` / `git commit`（作業ブランチのみ） |
| 返す成果物 | コード＋テスト、証拠ファイル（テストのログなど）、`tasks.json` の `status: "review"` と `evidence` の記入、コミット |
| 完了条件 | 自分の環境でテストとビルドが通り、ログが証拠として保存されている／`python evals/check_tasks.py` がエラー0件 |

**証拠の保存例**:
```bash
mkdir -p evals/evidence/T02
cd backend && .venv/Scripts/python -m pytest -q 2>&1 | tee ../evals/evidence/T02/pytest.log
```

---

## 3. 評価役（Evaluator）
| 項目 | 内容 |
|---|---|
| 担当する | 該当 AC を1つずつ証拠と照らし合わせる／**テストを自分でもう一度実行** して、保存された証拠と同じ結果か確かめる／合否を決める |
| 担当しない | コードを直す（直す必要があれば差し戻すだけ）、合格条件をゆるめる、実行役の「できました」を信じること |
| 最初に読む | `evals/acceptance.md` → `tasks.json` の該当タスク → `evals/evidence/<タスクID>/` → `git diff`（そのタスクの変更） |
| 使える道具 | ファイルを読む、テストとビルドの実行、`evals/evidence/<タスクID>/review.md` の作成、`tasks.json` の `status` / `passes` の変更 |
| 返す成果物 | `evals/evidence/<タスクID>/review.md`（AC ごとに ○×・根拠のファイル名・再実行の結果） |
| 完了条件 | 全 AC が ○ → `status: "done"`, `passes: true`／1つでも × → `status: "in_progress"`, `passes: false` にして、理由を `progress.md` に書く |

**不合格の例**: 証拠のログが古い（今のコードで再実行すると結果が違う）／テストが AC の中身を確かめていない／`check_tasks.py` がエラーを出す。

---

## 役とツールの対応（Claude Code の場合）
| 役 | どこで動かすか |
|---|---|
| 計画役 | メインのセッション |
| 実行役 | メインのセッション（計画役の続き） |
| 評価役 | Agent ツールで起動する新しいサブエージェント（`/next-task` スキルが自動で起動する） |

他の AI に移る場合: 計画・実行は1つのチャット、評価は **別の新しいチャット** を開いて「docs/roles.md の評価役として T0X を検品して」と頼む。
