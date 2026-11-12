# 最初に一度だけ行う設定 / One-time setup

この設定のあとは、人が手を入れなくても動き続けます。所要時間は15分ほどです。

## 1. リポジトリを作る

GitHubで公開リポジトリ（例：`token-charter`）を作り、このフォルダの中身をすべてアップロードします。`.github` フォルダも忘れずに入れてください。

## 2. ページの公開を有効にする

「Settings」→「Pages」→「Build and deployment」の「Source」を **GitHub Actions** にします。

## 3. 自動反映を有効にする

「Settings」→「General」→「Pull Requests」で **Allow auto-merge** にチェックを入れます。

## 4. 反映のルールを設定する

「Settings」→「Rules」→「Rulesets」→「New branch ruleset」で、対象を `main` にして次を有効にします。「Bypass list」には誰も入れません。

| 設定 | 値 |
| --- | --- |
| Require a pull request before merging | オン。**Required approvals は 0**（承認は下の `approvals` で数えるため） |
| Require status checks to pass | オン。`validate` と `approvals` を追加 |
| Block force pushes | オン |
| Restrict deletions | オン |

GitHubの「Required approvals」は、書き込み権限を持つ人の承認しか数えません。そのため使わず、承認は `approvals` の検査が [APPROVERS.md](APPROVERS.md) の条件で数えます。

## 4b. 提案側の自動処理を動かさない設定

「Settings」→「Actions」→「General」→「Approval for running fork pull request workflows from contributors」で、**Require approval for all external contributors** を選びます。

提案に自動処理のファイルを紛れ込ませて、検査に合格したふりをさせる手口を防ぎます。トークン憲章の検査はすべて main の版で動くので、この設定にしても検査は止まりません。外部の人の提案で「Approve and run」のボタンが出ても、**押さないでください**。

## 5. 動作を確かめる

「Actions」→「Build and publish」→「Run workflow」で一度手動で動かし、ページが開けるか確かめます。以後は、main が更新されたときと、毎日1回自動で動きます。自動で反映された提案は、遅くとも翌日に公開されます。

## 止まらないための仕組み

- GitHubは、公開リポジトリで60日間動きがないと、定期実行を止めることがあります。毎日の収益データを `snapshots` ブランチに記録することで、動きを保つようにしています。それでも止まった場合は「Actions」から再開してください
- データが取れなかった週は、前回の値を表示したまま動き続けます

## 引き継ぎ

承認できる人は実績で自動的に増えるので、運営者がいなくなっても提案は反映され続けます。GitHubの設定が止まったとき（定期実行の停止など）に備えて、長く協力している人に管理権限（Maintain）を渡すかどうかは、ルールの変更と同じく4人の承認で決めることを勧めます。

---

## English

After this one-time setup (about 15 minutes), the project runs without anyone tending it.

1. Create a public repository and upload everything in this folder, including `.github`
2. Settings → Pages → Source: **GitHub Actions**
3. Settings → General → Pull Requests: check **Allow auto-merge**
4. Settings → Rules → Rulesets → New branch ruleset for `main`, with an empty bypass list: require a pull request with **0** required approvals (GitHub only counts approvals from people with write access, so the `approvals` check counts them instead, per APPROVERS.md), require the `validate` and `approvals` status checks, block force pushes, restrict deletions
4b. Settings → Actions → General → fork pull request workflows: **Require approval for all external contributors**. This stops a proposal from smuggling in its own workflow to fake a passing check. All of Token Charter's checks run from main, so they keep working. Never click "Approve and run" on an outside proposal
5. Actions → "Build and publish" → Run workflow once to confirm the site opens. After that it runs whenever main changes and once a day; auto-merged proposals go live by the next day

GitHub may pause scheduled workflows in public repositories after 60 days without activity. The daily job records revenue data to the `snapshots` branch to keep the repository active. If it still pauses, re-enable it from Actions. Approvers grow automatically from track record, so proposals keep merging even if the owner disappears.
