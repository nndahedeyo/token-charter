"""site/template.html（日本語）から site/template.en.html（英語）を作る。

日本語のひな形を直したら、このスクリプトを実行して英語版も作り直す。
対応する訳がない日本語が残ったら、失敗して知らせる。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAIRS = [
    ('<title>トークン憲章</title>', '<title>Token Charter</title>'),
    ('/* Layout: 公文書のような一段組。冒頭に憲章の主旨、中心に操作できる採点台帳、後ろに基準と計画 */', '/* Layout: single column like an official document: charter intro, interactive ledger, then criteria and plan */'),
    ('content:"段階 " counter(s)', 'content:"Stage " counter(s)'),
    ('TOKEN CHARTER · みんなで検証する台帳', 'TOKEN CHARTER · A LEDGER ANYONE CAN VERIFY'),
    ('<h1>トークン憲章</h1>', '<h1>Token Charter</h1>'),
    ('<p class="lead">暗号資産プロジェクトが<strong>約束を守っているか、守らせる仕組みがあるか</strong>を、同じ物差しで採点して公開します。株式市場で取引所や社債管理者が担っている「約束を守らせる役」を、公開データと、将来は担保と自動の罰則で代わりに担う試みです。</p>',
     '<p class="lead">We score whether crypto projects <strong>keep their promises, and whether anything makes them keep them</strong>, with one yardstick, in public. In stock markets, exchanges and bond trustees play the role of enforcer. Token Charter fills that role with public data now, and with collateral and automatic penalties later.</p>'),
    ('<span>採点時点：__ASOF__</span><span>対象：__COUNT__銘柄</span><span>10項目 × 0〜2点</span>', '<span>As of __ASOF__</span><span>__COUNT__ tokens</span><span>10 items × 0–2 points</span>'),
    ('<div>約束の<br>格付け<small>0–2 × 10</small></div>', '<div>Promise<br>rating<small>0–2 × 10</small></div>'),
    ('ランクの分布', 'Grade distribution'),
    ('<h2 id="t-h">採点台帳</h2>', '<h2 id="t-h">The ledger</h2>'),
    ('aria-label="区分で絞り込む"', 'aria-label="Filter by category"'),
    ('</span></span>2点', '</span></span>2 points'),
    ('</span></span>1点', '</span></span>1 point'),
    ('</span></span>0点', '</span></span>0 points'),
    ('対象外（発行体なし）', 'Not applicable (no issuer)'),
    ('<span>· 左の6つが発行体、右の4つが仕組み · 行を押すと根拠の要約とリンクを表示</span>', '<span>· Left 6 are issuer items, right 4 are mechanism items · Tap a row for the summary and sources</span>'),
    ('data-k="g">ランク<', 'data-k="g">Grade<'),
    ('data-k="s">銘柄<', 'data-k="s">Token<'),
    ('data-k="t">総合<', 'data-k="t">Score<'),
    ('<th>項目 1〜6 ／ 7〜10</th>', '<th>Items 1–6 / 7–10</th>'),
    ('data-k="a">発行体<', 'data-k="a">Issuer<'),
    ('data-k="m">仕組み<', 'data-k="m">Mechanism<'),
    ('data-k="c">区分<', 'data-k="c">Category<'),
    ('<th>確認度</th>', '<th>Confidence</th>'),
    ('<p class="note">BTC・ETH・SOL・ZECは発行体がないため「仕組み」の4項目だけで採点しています。発行体のある銘柄と点数を単純に比べることはできません。</p>',
     '<p class="note">BTC, ETH, SOL and ZEC have no issuer, so they are scored on the 4 mechanism items only. Their scores are not directly comparable with tokens that have an issuer.</p>'),
    ('10の採点項目', 'The 10 items'),
    ('ランク：__GRADES__（合計点を満点で割り、100点に換算）。', 'Grades: __GRADES__ (points divided by the maximum, on a 100-point scale).'),
    ('株式市場では誰が約束を守らせているか', 'Who enforces promises in stock markets'),
    ('<p>株式で約束が守られるのは、破ったときに罰する主体がいるからです。暗号資産にはその主体がいません。</p>', '<p>Companies keep their promises because someone penalizes them when they don\'t. Crypto has no one in that role.</p>'),
    ('<th>株式の仕組み</th><th>守らせる主体</th><th>トークン憲章での対応</th>', '<th>Stock market mechanism</th><th>Enforcer</th><th>Token Charter equivalent</th>'),
    ('<td>IPOのロックアップ（米国は通常180日）</td><td>引受証券会社との契約</td><td>内部関係者の売却ルール</td>', '<td>IPO lock-ups (usually 180 days in the US)</td><td>Underwriter contracts</td><td>Insider selling rules</td>'),
    ('<td>売却計画の事前届出（米国の10b5-1プラン）</td><td>証券当局</td><td>売却計画の事前公開</td>', '<td>Pre-filed trading plans (US 10b5-1)</td><td>Securities regulator</td><td>Published selling plans</td>'),
    ('<td>配当方針・自社株買いの決議</td><td>取締役会・株主総会</td><td>還元の約束と実行</td>', '<td>Dividend policy, buyback resolutions</td><td>Board, shareholder meeting</td><td>Holder-return commitments and delivery</td>'),
    ('<td>適時開示・四半期報告</td><td>取引所・証券当局</td><td>定期的な報告</td>', '<td>Timely disclosure, quarterly reports</td><td>Exchange, regulator</td><td>Regular reporting</td>'),
    ('<td>社債の財務制限条項</td><td>社債管理者・裁判所</td><td>担保と自動の罰則</td>', '<td>Bond covenants</td><td>Bond trustee, courts</td><td>Collateral and automatic penalties</td>'),
    ('<td>コーポレートガバナンス・コード</td><td>取引所（守るか、理由を説明するか）</td><td>説明責任</td>', '<td>Corporate governance codes</td><td>Exchange (comply or explain)</td><td>Accountability</td>'),
    ('<td>東証の「資本コストや株価を意識した経営」開示企業一覧</td><td>一覧の公表（罰則なし）</td><td>許可なしの格付け</td>', '<td>Tokyo Stock Exchange list of companies disclosing capital-efficiency plans</td><td>Public list (no penalty)</td><td>Permissionless rating</td>'),
    ('<h2 id="p-h">進め方</h2>', '<h2 id="p-h">Roadmap</h2>'),
    ('<b>許可なしの格付け</b><span>公開データから採点し、公開する。参加していないこと自体が判断材料になる。</span>', '<b>Permissionless rating</b><span>Score from public data and publish. Not taking part becomes information in itself.</span>'),
    ('<b>根拠の公開と異議の受付</b><span>点数ごとに根拠リンクを示し、誰からの訂正も、出典と2人の承認で受け付ける。いまはこの段階です。</span>', '<b>Sources and corrections</b><span>Every score links its sources. Anyone can correct it with a source and 2 approvals. We are here now.</span>'),
    ('<b>約束の登録</b><span>プロジェクトが還元・売却ルール・解除の約束を、決まった形式で登録する。</span>', '<b>Registered promises</b><span>Projects register their return, selling and unlock commitments in a fixed format.</span>'),
    ('<b>担保つきの約束</b><span>約束に担保を預け、破ればチェーン上の判定で保有者に渡す。</span>', '<b>Collateralized promises</b><span>Projects post collateral that goes to holders, by on-chain rules, if a promise is broken.</span>'),
    ('<p class="note">範囲外：ハッキングの防止、市場全体の上げ下げ、需要があるかどうか。トークン憲章が評価するのは「約束の信頼性」だけです。</p>', '<p class="note">Out of scope: hack prevention, market moves, and whether there is demand. Token Charter rates the reliability of promises only.</p>'),
    ('<footer>点数は公開情報にもとづき、出典つきの提案と2人の承認で更新されます。投資の推奨ではありません。', '<footer>Scores are based on public information and change only through sourced proposals with 2 approvals. Not investment advice.'),
    ('p.push("収益 "+usd(t.met.revenue))', 'p.push("Revenue "+usd(t.met.revenue))'),
    ('p.push("うち保有者へ "+usd(t.met.holders))', 'p.push("to holders "+usd(t.met.holders))'),
    ('直近30日（DefiLlamaの分類による、${esc(t.metAt||"")}取得・参考値で点数には反映しない）：${p.join("、")}', 'Last 30 days (DefiLlama categories, fetched ${esc(t.metAt||"")}; reference only, not used in scores): ${p.join(", ")}'),
    ('CATS=["すべて","基準","大型チェーン","DeFi・還元型","インフラ","小型見本"]', 'CATS=["All","Baseline","Layer 1","DeFi","Infrastructure","Small"]'),
    ('let cat="すべて"', 'let cat="All"'),
    ('<span>銘柄</span><span class="syms">', '<span>tokens</span><span class="syms">'),
    ("${x===null?'対象外':x+'点'}", "${x===null?'n/a':x+(x===1?' point':' points')}"),
    ('cat==="すべて"', 'cat==="All"'),
    ('<p class="src">根拠：', '<p class="src">Sources: '),
    ('.join("　")}</p>${metLine(t)}', '.join(" · ")}</p>${metLine(t)}'),
    ('<p class="src">確認日：${esc(t.rev)}', '<p class="src">Reviewed ${esc(t.rev)}'),
    ('encodeURIComponent("[訂正] "+t.s)', 'encodeURIComponent("[Correction] "+t.s)'),
    ('rel="noopener">この銘柄の訂正を提案する</a>', 'rel="noopener">Propose a correction</a>'),
    ('`　<a href="${REPO}/issues', '` · <a href="${REPO}/issues'),
    ('株式での対応：', 'Stock market analogue: '),
    ('`担保つきの約束をしている銘柄は、${T.length}銘柄のうち一つもありません（項目5で2点の銘柄はゼロ）。ここがトークン憲章の埋めたい空白です。`', '`None of the ${T.length} tokens backs its promises with collateral (no token scores 2 on item 5). That is the gap Token Charter wants to fill.`'),
    ('`担保つきの約束をしている銘柄は、${T.length}銘柄のうち${n}銘柄です（項目5で2点）。`', '`${n} of the ${T.length} tokens back their promises with collateral (2 points on item 5).`'),
    ('/blob/main/RULES.md" target="_blank" rel="noopener">編集ルール</a>', '/blob/main/RULES.en.md" target="_blank" rel="noopener">Editing rules</a>'),
    ('rel="noopener">生データ</a>', 'rel="noopener">Raw data</a>'),
    ('<a class="lang" href="en/">English</a>', '<a class="lang" href="../">日本語</a>'),
]


def main():
    ja = (ROOT / "site" / "template.html").read_text(encoding="utf-8")
    en = ja.replace('<html', '<html')
    missing = [a for a, _ in PAIRS if a not in en]
    if missing:
        print("見つからない文字列があります（日本語版が変わった可能性）:")
        for m in missing:
            print(" -", m[:80])
        sys.exit(1)
    for a, b in PAIRS:
        en = en.replace(a, b)
    allowed = {"日本語"}
    left = [ln for ln in en.splitlines() if re.search(r"[ぁ-んァ-ヶ一-龥]", ln) and not any(w in ln for w in allowed)]
    if left:
        print("訳のない日本語が残っています:")
        for ln in left:
            print(" -", ln.strip()[:100])
        sys.exit(1)
    (ROOT / "site" / "template.en.html").write_text(en, encoding="utf-8")
    print("wrote site/template.en.html")


if __name__ == "__main__":
    main()
