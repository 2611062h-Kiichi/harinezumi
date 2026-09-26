# T00 評価（評価役）

- 評価日: 2026-09-26
- 評価役: 実行役とは別のサブエージェント（docs/roles.md 3章に従う）
- 対象: tasks.json T00 / 合格条件 AC-01
- 読んだ証拠: `evals/evidence/T00/git.log`, `secret-scan.log`, `check_tasks.log`
- 注意: backend/.env は読んでいない。コード・ファイルの修正、push、ブランチ操作はしていない。

## 判定: 合格（全条件 ○）

| # | 条件 | 判定 | 根拠 |
|---|---|---|---|
| 1 | AC-01: 作業ブランチがあり、ハーネス一式がコミットされている | ○ | 再実行で現在ブランチ `feature/contest-jev-questions`、HEAD `2472589 Add AI harness for contest-question (Jev) feature`。git.log と一致 |
| 2 | 作業ブランチの親が origin/feature/business-contest-rubric の先頭（b2dfe7f） | ○ | `git rev-list --parents -n1 HEAD` → 親は `b2dfe7fd…` のみ（1親）。`origin/feature/business-contest-rubric` も `b2dfe7fd…` |
| 3 | `harness-baseline` タグがハーネスのコミットを指す | ○ | `harness-baseline^{commit}` = `24725895…` = HEAD。`git tag --points-at HEAD` → `harness-baseline` |
| 4 | ハーネスのファイルがすべてコミットに含まれる | ○ | `git show --name-status HEAD` で AGENTS.md, CLAUDE.md, docs/{mission,requirements,roles,safety,voice}.md, tasks.json, progress.md, evals/{acceptance.md,check_tasks.py,evidence/.gitkeep}, .claude/{settings.json,skills/next-task/SKILL.md} の14件すべて A。作業ツリー上の docs/ evals/ .claude/ のファイル一覧（find）と突き合わせ、未コミットは T00 の証拠（後から作るもの）のみ |
| 5 | コミットに秘密情報・backend/.env が含まれない | ○ | コミットの変更ファイルは上記14件のみで .env 系なし。`git ls-files` に backend/.env は無い（追跡は既存の `backend/.env.example`, `frontend/.env.example` のみで、このコミットでは未変更）。`git check-ignore -v backend/.env` → `backend/.gitignore:1:.env`。safety.md 3章のパターンで `git show HEAD` を検索すると1件ヒットするが、docs/safety.md に書かれた検索コマンドそのもの（パターン文字列の自己一致）で、キーではない |

### 証拠との差分・気づき（合否には影響しない）
- `secret-scan.log` は検索パターンを「(APIキーらしき文字列)」とぼかしており、結果「(一致なし)」となっている。safety.md 3章の正確なパターンで再実行すると上記の自己一致1件が出る。今後の証拠では実際に使ったコマンドをそのまま記録するのが望ましい。
- `secret-scan.log` の「.env は追跡されていない」は、`.env.example`（見本ファイル、土台ブランチから存在）を除いた意味として正しい。
- 作業ツリーの `tasks.json` は T00 の status/evidence のみ変更（`git diff tasks.json` で確認）。コミット済みのハーネスとの差分はこれだけ。
- 作業ブランチには upstream が未設定（push していない）。T00 の条件に push は含まれないので問題なし。

## 自分で再実行したコマンドと結果

```
$ git branch --show-current
feature/contest-jev-questions
$ git log --oneline -3
2472589 Add AI harness for contest-question (Jev) feature
b2dfe7f Fall back to Claude-only scoring when TYPESAFE_API_KEY is unset
0447308 Remove ffmpeg dependency and prep for Vercel deployment
$ git rev-parse HEAD HEAD^ harness-baseline^{commit} origin/feature/business-contest-rubric
24725895cf50f03f630b26a4c59200b7ec4a2c4f
b2dfe7fd3db4b8a73c7916a4282429ea151df5ef
24725895cf50f03f630b26a4c59200b7ec4a2c4f
b2dfe7fd3db4b8a73c7916a4282429ea151df5ef
$ git rev-list --parents -n1 HEAD
24725895cf50f03f630b26a4c59200b7ec4a2c4f b2dfe7fd3db4b8a73c7916a4282429ea151df5ef
$ git merge-base --is-ancestor origin/feature/business-contest-rubric HEAD && echo ancestor-ok
ancestor-ok
$ git tag --points-at HEAD
harness-baseline
$ git cat-file -t harness-baseline
commit
$ git show --name-status --format= HEAD
A	.claude/settings.json
A	.claude/skills/next-task/SKILL.md
A	AGENTS.md
A	CLAUDE.md
A	docs/mission.md
A	docs/requirements.md
A	docs/roles.md
A	docs/safety.md
A	docs/voice.md
A	evals/acceptance.md
A	evals/check_tasks.py
A	evals/evidence/.gitkeep
A	progress.md
A	tasks.json
$ git status --short
 M tasks.json
?? evals/evidence/T00/
$ git ls-files | grep -n '\.env'
6:backend/.env.example
35:frontend/.env.example
$ git show HEAD --name-only --format= | grep -i env
(出力なし)
$ git show HEAD | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
407:+- コミット前に確認: `git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"` で何も出ないこと。
  （docs/safety.md のパターン文字列の自己一致のみ。キーではない）
$ git check-ignore -v backend/.env
backend/.gitignore:1:.env	backend/.env
$ git rev-parse --abbrev-ref @{upstream}
fatal: no upstream configured for branch 'feature/contest-jev-questions'
```

## tasks.json の更新
T00 を `"status": "done"`, `"passes": true` に変更（他の項目・他のタスクは変更なし）。

## python evals/check_tasks.py の出力

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 1/13 タスク
```
