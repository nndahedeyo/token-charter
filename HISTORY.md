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
| 2026-11-24 | GitHubなしの窓口を追加：評価の希望と訂正を Nostr で受け付け、1日1回、自動で課題（目印「from-nostr」）にする（ページ request/、scripts/intake.py、tests/test_intake.py、.github/workflows/intake.yml、RULES.md）。点数と要約は変更なし / Added the no-GitHub window: rating requests and corrections arrive via Nostr and become issues daily. No scores or summaries changed | 承認できる人がほとんどおらず、GitHub を使わない人も評価や訂正に加われるようにするため。持ち主の判断で、承認の手続きを通さずに反映 / Almost no approvers yet; lets people without GitHub take part. Pushed directly by the owner's decision |
| 2026-11-24 | 公開ページをスマホ向けに作り直す（site/template.html、英語版も）：銘柄ごとに10項目の点を番号つきのマスで表示し、開くと項目ごとに点数の理由と「訂正する」を表示。ランク・区分・検索・項目ごとの並べ替え。スマホの幅で表示する設定（viewport）を追加。各銘柄に「役割」（何のためのトークンか）と細かい区分を追加（data/tokens.json の role・role_tag・role_en・role_tag_en、検査も追加）。点数・要約・出典は変更なし / Rebuilt the public page for phones (ja and en): per-token 10-item score cells, per-item reasons and "Correct" links, filters, search and per-item sorting, viewport meta. Added each token's role and sub-category (role fields in data/tokens.json, validated). No scores, notes or sources changed | 点数の基準が銘柄ごとにどう評価されているか、下の採点項目を見ないと分からず、スマホで見づらかったため。訂正を送りやすくするため。持ち主の判断で、承認の手続きを通さずに反映 / The per-item evaluation was hard to read without the criteria section, and the page was hard to use on phones. Pushed directly by the owner's decision |
| 2026-11-24 | 毎日の窓口の処理：新しい課題の枠を訂正から先に使う。CoinGecko に見つからない名前の評価の希望は印を付けて後ろに回す。憲章に入った銘柄の評価の希望は自動で閉じる（RULES.md に追記）。点数と要約は変更なし / Daily intake: corrections first; unknown CoinGecko ids flagged and placed last; fulfilled rating requests closed automatically. No scores or summaries changed | 訂正が評価の希望に埋もれないように、また見る人が少なくても課題がたまらないようにするため。持ち主の判断で、承認の手続きを通さずに反映 / Keeps corrections from being crowded out and stops fulfilled requests piling up. Pushed directly by the owner's decision |
| 2026-11-24 | 訂正の画面を ?item= で項目を選んだ状態で開けるようにする（項目ごとの「違う？」から開くため）。点数と要約は変更なし / The correction form can open with an item preselected (?item=). No scores or summaries changed | 訂正を送りやすくするため。持ち主の判断で、承認の手続きを通さずに反映 / Makes corrections easier. Pushed directly by the owner's decision |
| 2026-11-24 | 窓口の不備を直す：出典の URL を送る画面でも受け取る側と同じ条件で確かめる（空白・' " < > を含むもの、300文字を超えるものはその場で断る。切って送らない）。憲章のデータを読み込めないときは送れないようにする。応答しなくなった中継 relay.nostr.band を外し、offchain.pub と nostr.mom を足して5か所にする。点数と要約は変更なし / Fixed the request window: the form now checks source URLs with the same rules as the receiver, blocks sending when charter data fails to load, and uses 5 relays (dropped unresponsive relay.nostr.band). No scores or summaries changed | 「送りました」と出るのに課題にならないことがあったため。持ち主の判断で、承認の手続きを通さずに反映 / Some sends showed success but were silently dropped. Pushed directly by the owner's decision |
| 2026-11-24 | 窓口の説明から「GitHubなし」の言い方を外し、名前を「評価の希望と訂正の窓口」に。銘柄ごとの「訂正を提案する（GitHub）」リンクを「この銘柄の訂正を送る」1つにまとめた。点数と要約は変更なし / Dropped "no GitHub" wording; renamed to "Requests and corrections"; one "Send a correction" link per token. No scores or summaries changed | 誰でも送れるので、GitHubの有無を説明する必要がないため。持ち主の判断で、承認の手続きを通さずに反映 / Anyone can send, so GitHub need not be mentioned. Pushed directly by the owner's decision |
| 2026-11-13 | 開けなくなった出典5件（TRX・AVAX・XLM・CAKE・CC のDEVの記事）を、公式資料や報道に差し替え。見張り役が閉じたIssueを立て直さないように修正。点数と要約は変更なし | 記事が削除されて根拠が確かめられなくなったため。承認できる人が持ち主だけで、持ち主名義の提案は承認できないため / The articles were deleted; the only approver is the owner, who can't approve own proposals |
