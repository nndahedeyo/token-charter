# 最初に一度だけ行う設定 / One-time setup

この設定のあとは、人が手を入れなくても動き続けます。所要時間は15分ほどです。

## 1. リポジトリを作る

GitHubで公開リポジトリ（例：`token-charter`）を作り、このフォルダの中身をすべてアップロードします。`.github` フォルダも忘れずに入れてください。

## 2. ページの公開を有効にする

「Settings」→「Pages」→「Build and deployment」の「Source」を **GitHub Actions** にします。

## 3. 自動反映を有効にする

「Settings」→「General」→「Pull Requests」で **Allow auto-merge** にチェックを入れます。

## 4. 反映のルールを設定する

「Settings」→「Rules」→「Rulesets」→「New branch ruleset」で、対象を `main` にして次を有効にします。

| 設定 | 値 |
| --- | --- |
| Require a pull request before merging | オン |
| Required approvals | **2** |
| Dismiss stale pull request approvals when new commits are pushed | オン |
| Require status checks to pass | オン、`validate` と `rules-guard` を追加 |
| Block force pushes | オン |

これで、RULES.mdの「検査と2人の承認がそろったら反映」と「ルールの変更は4人の承認」が、GitHubの仕組みとして強制されます。

## 5. 動作を確かめる

「Actions」→「Build and publish」→「Run workflow」で一度手動で動かし、ページが開けるか確かめます。以後は、main が更新されたときと、毎日1回自動で動きます。自動で反映された提案は、遅くとも翌日に公開されます。

## 止まらないための仕組み

- GitHubは、公開リポジトリで60日間動きがないと、定期実行を止めることがあります。毎日の収益データを `snapshots` ブランチに記録することで、動きを保つようにしています。それでも止まった場合は「Actions」から再開してください
- データが取れなかった週は、前回の値を表示したまま動き続けます

## 引き継ぎ

運営者がいなくなっても続くように、協力者のうち信頼できる2〜3人に、リポジトリの管理権限（Maintain）を渡しておくことを勧めます。

---

## English

After this one-time setup (about 15 minutes), the project runs without anyone tending it.

1. Create a public repository and upload everything in this folder, including `.github`
2. Settings → Pages → Source: **GitHub Actions**
3. Settings → General → Pull Requests: check **Allow auto-merge**
4. Settings → Rules → Rulesets → New branch ruleset for `main`: require a pull request, **2** approvals, dismiss stale approvals, require the `validate` and `rules-guard` status checks, block force pushes
5. Actions → "Build and publish" → Run workflow once to confirm the site opens. After that it runs whenever main changes and once a day; auto-merged proposals go live by the next day

GitHub may pause scheduled workflows in public repositories after 60 days without activity. The daily job records revenue data to the `snapshots` branch to keep the repository active. If it still pauses, re-enable it from Actions. Give 2–3 trusted contributors the Maintain role so the project outlives any one person.
