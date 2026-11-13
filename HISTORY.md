# ルールの手続きを通さなかった変更の記録 / Changes made outside the rules

リポジトリの持ち主（@nndahedeyo）が、GitHubの設定（Ruleset）を一時的に外して、承認の手続きを通さずに反映した変更を、すべてここに書きます（[RULES.md](RULES.md)「この仕組みの限界」）。このファイルの変更にも、4人の承認が必要です。

Every change the repository owner pushed by temporarily disabling the ruleset, skipping approval, is listed here. Changing this file also takes 4 approvals.

立ち上げ期間は、承認できる人がまだいないため、仕組みそのものを整えるのに持ち主が直接変更しました。承認できる人が4人そろってからは、この方法を使わないことを目指します。

During launch there were no approvers yet, so the owner set up the system directly. The aim is to stop doing this once there are 4 approvers.

| 日付 / Date (UTC) | 変更 / Change | 理由 / Why |
| --- | --- | --- |
| 2026-11-09 | 収益データが0のときは表示しない、DefiLlamaの分類であることを明記（40ab547） | 誤解を招く表示の修正 / Fix a misleading display |
| 2026-11-10 | 英語版ページとコインのアイコンを追加、HYPEの要約を更新（8d2935d） | 立ち上げの準備 / Launch preparation |
| 2026-11-12 | 承認できる人を実績で自動的に決める仕組みに変更、検査を提案側から書き換えられないように（1a32482） | GitHubの承認設定では、持ち主しか承認できず、提案が反映されなかったため / GitHub's approval setting only counted the owner, so nothing could merge |
| 2026-11-13 | AIエージェントの決まり、自動の見張り役、この記録を追加（e5aa8e9 と、その日の後続の修正）| 承認できる人が4人そろう前に、AIで承認者を水増しする手口を防ぐため / To block AI-driven approver inflation before 4 approvers exist |
| 2026-11-13 | 開けなくなった出典5件（TRX・AVAX・XLM・CAKE・CC のDEVの記事）を、公式資料や報道に差し替え。見張り役が閉じたIssueを立て直さないように修正。点数と要約は変更なし | 記事が削除されて根拠が確かめられなくなったため。承認できる人が持ち主だけで、持ち主名義の提案は承認できないため / The articles were deleted; the only approver is the owner, who can't approve own proposals |
