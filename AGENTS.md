# AGENTS.md — このリポジトリで働くAIのための地図

> ここは「百科事典」ではなく「地図」です。詳しいことは各リンク先に書いてあります。
> どのAI（Claude / 他社AI / 新しいセッション）でも、まずこのファイルから読んでください。

## 1. このプロジェクトは何か（1行）
ピッチ（発表）を AI が審査するローカル Web アプリ「harinezumi」。
今回の追加機能は **「コンテストの採点観点を入力 → Jev 用の Questions を自動生成 → 発表音声の書き起こしを Jev で採点」**。

## 2. 最初に読む順番（毎セッション必ず）
1. `progress.md` の「引き継ぎメモ」 … 前回どこまで進んだか
2. `tasks.json` … 次にやるタスク（status と dependencies を見る）
3. `docs/roles.md` … 自分が今どの役（計画役・実行役・評価役）か
4. 役ごとに指定された資料（`docs/roles.md` に書いてある）

## 3. 資料の場所（正しい情報源 = Source of Truth）
| 知りたいこと | 読むファイル | 誰が書き換えてよいか |
|---|---|---|
| 何を作るか・誰のためか | `docs/mission.md` | 人間のみ |
| 機能の細かい要件・Jev の仕様 | `docs/requirements.md` | 人間のみ（AIは提案まで） |
| 文章の口調 | `docs/voice.md` | 人間のみ |
| やってはいけないこと・承認が必要なこと | `docs/safety.md` | 人間のみ |
| 役割分担 | `docs/roles.md` | 人間のみ |
| 合格条件 | `evals/acceptance.md` | 人間のみ |
| タスク一覧 | `tasks.json` | AIは `status` / `passes` / `evidence` のみ |
| 途中経過・引き継ぎ | `progress.md` | AIが追記する |
| 証拠（ログ・スクショ） | `evals/evidence/<タスクID>/` | AIが追加する |
| 実際の動き | ソースコード（`backend/`, `frontend/`） | 実行役 |

資料とコードが食い違ったら、**勝手に片方を直さず** `progress.md` の「要確認」に書いて人間に聞くこと。

## 4. よく使うコマンド
```bash
# バックエンドのテスト
cd backend && .venv/Scripts/python -m pytest -q
# フロントエンドの型チェック＋ビルド
cd frontend && npm run build
# tasks.json のルール違反チェック（削除・改ざん・証拠なし合格を検出）
python evals/check_tasks.py
```

## 5. 絶対ルール（詳しくは `docs/safety.md`）
- タスクを消さない。`task` / `dependencies` / `acceptance` と `evals/acceptance.md` を書き換えない。
- 「完成しました」という発言は合格の理由にならない。**証拠ファイル**が必要。
- APIキー・パスワードをファイルやログに書かない。`backend/.env` を読まない・表示しない。
- 1回の作業で進めるタスクは1つだけ。終わったら `progress.md` を更新してコミット。
