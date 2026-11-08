# 提案のしかた / How to contribute

## 点数や要約を直す

1. `data/tokens.json` の該当する銘柄を編集する（GitHubの画面上で鉛筆マークから編集できます）
2. 変えるもの
   - `scores`：10項目の点数（0、1、2）。発行体のない銘柄の1〜6番目は `null`
   - `note`：要約（出典に書かれていることだけ）
   - `sources`：出典。変更の根拠になる出典を**必ず1つ以上**追加する
   - `reviewed`：確認した日付（例：`2026-11-20`）
3. 「Propose changes」で提案を出し、テンプレートに沿って、何をなぜ変えたかを書く
4. 採点されるプロジェクトと利害がある場合は、そのことを書く

コードが分からなくても、「訂正の提案」（Issue）から出典を添えて知らせるだけでも構いません。誰かが提案の形にします。

## 銘柄を追加する

`data/tokens.json` の `tokens` に、同じ形式で1件追加します。10項目すべてに出典が必要です。

## Fixing a score or summary

1. Edit the token in `data/tokens.json` (use the pencil icon on GitHub)
2. Change `scores` (0, 1 or 2; items 1–6 are `null` for tokens with no issuer), `note` (summarize sources only), `sources` (**add at least one** source for your change) and `reviewed` (the date you checked)
3. Click "Propose changes" and fill in the template: what you changed and why
4. Disclose any interest in the rated project

If you don't write code, open a "Correction" Issue with your source. Someone will turn it into a proposal.
