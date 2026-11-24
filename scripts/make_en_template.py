"""site/template.html（日本語）から site/template.en.html（英語）を作る。

日本語のひな形を直したら、このスクリプトを実行して英語版も作り直す。
対応する訳がない日本語が残ったら、失敗して知らせる。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAIRS = [
    ('<html lang="ja">', '<html lang="en">'),
    ('<title>トークン憲章</title>', '<title>Token Charter</title>'),
    ('TOKEN CHARTER · みんなで検証する台帳', 'TOKEN CHARTER · A LEDGER ANYONE CAN VERIFY'),
    ('<h1>トークン憲章</h1>', '<h1>Token Charter</h1>'),
    ('<p>暗号資産プロジェクトが<strong>約束を守っているか、守らせる仕組みがあるか</strong>を、10項目で採点した台帳です。<a href="#about">くわしく</a></p>',
     '<p>A ledger scoring whether crypto projects <strong>keep their promises, and whether anything makes them keep them</strong>, on 10 items. <a href="#about">More</a></p>'),
    ('<span>採点時点：__ASOF__</span><span>対象：__COUNT__銘柄</span><span>10項目 × 0〜2点</span><a class="lang" href="en/">English</a>',
     '<span>As of __ASOF__</span><span>__COUNT__ tokens</span><span>10 items × 0–2 points</span><a class="lang" href="../">日本語</a>'),
    ('<h2 id="t-h">採点台帳</h2>', '<h2 id="t-h">The ledger</h2>'),
    ('点数が違うと思ったら、誰でも送れます。', 'Think a score is wrong? Anyone can send a fix. '),
    ('>✎ 訂正する</a>', '>✎ Correct</a>'),
    ('>＋ 評価を頼む</a>', '>＋ Request a rating</a>'),
    ('<a href="#send">しくみ</a>', '<a href="#send">How it works</a>'),
    ('aria-label="ランクで絞り込む"', 'aria-label="Filter by grade"'),
    ('aria-label="区分で絞り込む"', 'aria-label="Filter by category"'),
    ('placeholder="銘柄・役割で探す" aria-label="銘柄・役割で探す"', 'placeholder="Search tokens or roles" aria-label="Search tokens or roles"'),
    ('aria-label="並べ方"', 'aria-label="Sort"'),
    ('</i>2点</span>', '</i>2 points</span>'),
    ('</i>1点</span>', '</i>1 point</span>'),
    ('</i>0点</span>', '</i>0 points</span>'),
    ('</i>対象外</span>', '</i>Not applicable</span>'),
    ('<span>数字は項目の番号。押すと理由と役割が開きます</span>', '<span>Numbers are item numbers. Tap a token for reasons and its role</span>'),
    ('ここにない銘柄は ', 'Token not listed? '),
    ('BTC・ETH・SOL・ZECは発行体がないため「仕組み」の4項目だけで採点しています。発行体のある銘柄と点数を単純に比べることはできません。',
     'BTC, ETH, SOL and ZEC have no issuer, so they are scored on the 4 mechanism items only. Their scores are not directly comparable with tokens that have an issuer.'),
    ('<h2 id="dist-h">ランクの分布</h2>', '<h2 id="dist-h">Grade distribution</h2>'),
    ('<h2 id="about-h">この憲章について</h2>', '<h2 id="about-h">About the charter</h2>'),
    ('<p>暗号資産プロジェクトが<strong>約束を守っているか、守らせる仕組みがあるか</strong>を、同じ物差しで採点して公開します。株式市場で取引所や社債管理者が担っている「約束を守らせる役」を、公開データと、将来は担保と自動の罰則で代わりに担う試みです。</p>',
     '<p>We score whether crypto projects <strong>keep their promises, and whether anything makes them keep them</strong>, with one yardstick, in public. In stock markets, exchanges and bond trustees play the role of enforcer. Token Charter fills that role with public data now, and with collateral and automatic penalties later.</p>'),
    ('<h2 id="send-h">訂正と評価の依頼</h2>', '<h2 id="send-h">Corrections and rating requests</h2>'),
    ('<p>この台帳は、みんなの訂正で育ちます。出典のURLを1つ添えるだけで、名前はいりません。送った内容は1日以内に憲章の課題になり、人が出典を確かめて、正しければ点数に反映します。</p>',
     '<p>This ledger grows through everyone\'s corrections. Add one source URL; no name needed. What you send becomes a charter issue within a day, and people check the source and update the score if it holds up.</p>'),
    ('<p class="small muted">台帳で銘柄を開くと、項目ごとに「訂正する」があります。ここにない銘柄は、CoinGecko の銘柄ページのURLを送るだけです。頼んだ人の数も課題に表示されます。</p>',
     '<p class="small muted">Open a token in the ledger to find "Correct" on each item. For a token not listed, just send its CoinGecko page URL. The issue shows how many people asked.</p>'),
    ('<h2 id="c-h">10の採点項目</h2>', '<h2 id="c-h">The 10 items</h2>'),
    ('ランク：__GRADES__（合計点を満点で割り、100点に換算）。', 'Grades: __GRADES__ (points divided by the maximum, on a 100-point scale).'),
    ('株式市場では誰が約束を守らせているか', 'Who enforces promises in stock markets'),
    ('<p>株式で約束が守られるのは、破ったときに罰する主体がいるからです。暗号資産にはその主体がいません。</p>', '<p>Companies keep their promises because someone penalizes them when they don\'t. Crypto has no one in that role.</p>'),
    ('<span class="k">株式の仕組み</span>', '<span class="k">Stock market mechanism</span>'),
    ('守らせる主体：証券当局</span>', 'Enforcer: Securities regulator</span>'),
    ('守らせる主体：', 'Enforcer: '),
    ('<b>IPOのロックアップ（米国は通常180日）</b>', '<b>IPO lock-ups (usually 180 days in the US)</b>'),
    ('引受証券会社との契約', 'Underwriter contracts'),
    ('→ 内部関係者の売却ルール', '→ Insider selling rules'),
    ('<b>売却計画の事前届出（米国の10b5-1プラン）</b>', '<b>Pre-filed trading plans (US 10b5-1)</b>'),
    ('→ 売却計画の事前公開', '→ Published selling plans'),
    ('<b>配当方針・自社株買いの決議</b>', '<b>Dividend policy, buyback resolutions</b>'),
    ('取締役会・株主総会', 'Board, shareholder meeting'),
    ('→ 還元の約束と実行', '→ Holder-return commitments and delivery'),
    ('<b>適時開示・四半期報告</b>', '<b>Timely disclosure, quarterly reports</b>'),
    ('取引所・証券当局', 'Exchange, regulator'),
    ('→ 定期的な報告', '→ Regular reporting'),
    ('<b>社債の財務制限条項</b>', '<b>Bond covenants</b>'),
    ('社債管理者・裁判所', 'Bond trustee, courts'),
    ('→ 担保と自動の罰則', '→ Collateral and automatic penalties'),
    ('<b>コーポレートガバナンス・コード</b>', '<b>Corporate governance codes</b>'),
    ('取引所（守るか、理由を説明するか）', 'Exchange (comply or explain)'),
    ('→ 説明責任', '→ Accountability'),
    ('<b>東証の「資本コストや株価を意識した経営」開示企業一覧</b>', '<b>Tokyo Stock Exchange list of companies disclosing capital-efficiency plans</b>'),
    ('一覧の公表（罰則なし）', 'Public list (no penalty)'),
    ('→ 許可なしの格付け', '→ Permissionless rating'),
    ('<h2 id="p-h">進め方</h2>', '<h2 id="p-h">Roadmap</h2>'),
    ('<b>許可なしの格付け</b><span>公開データから採点し、公開する。参加していないこと自体が判断材料になる。</span>', '<b>Permissionless rating</b><span>Score from public data and publish. Not taking part becomes information in itself.</span>'),
    ('<b>根拠の公開と異議の受付 <span class="now-tag">いまここ</span></b><span>点数ごとに根拠リンクを示し、誰からの訂正も、出典と2人の承認で受け付ける。いまはこの段階です。</span>', '<b>Sources and corrections <span class="now-tag">We are here</span></b><span>Every score links its sources. Anyone can correct it with a source and 2 approvals. We are at this stage now.</span>'),
    ('<b>約束の登録</b><span>プロジェクトが還元・売却ルール・解除の約束を、決まった形式で登録する。</span>', '<b>Registered promises</b><span>Projects register their return, selling and unlock commitments in a fixed format.</span>'),
    ('<b>担保つきの約束</b><span>約束に担保を預け、破ればチェーン上の判定で保有者に渡す。</span>', '<b>Collateralized promises</b><span>Projects post collateral that goes to holders, by on-chain rules, if a promise is broken.</span>'),
    ('範囲外：ハッキングの防止、市場全体の上げ下げ、需要があるかどうか。トークン憲章が評価するのは「約束の信頼性」だけです。', 'Out of scope: hack prevention, market moves, and whether there is demand. Token Charter rates the reliability of promises only.'),
    ('<p>点数は公開情報にもとづき、出典つきの提案と2人の承認で更新されます。投資の推奨ではありません。</p>', '<p>Scores are based on public information and change only through sourced proposals with 2 approvals. Not investment advice.</p>'),
    ('const LQ="";   // 窓口へ渡す言語（英語版では lang=en）', 'const LQ="lang=en";   // language for the request window'),
    ('const W={all:"すべて",grade:g=>`ランク${g}`,gradeN:(g,n)=>`ランク${g}（${n}銘柄）`,none:"当てはまる銘柄がありません",of:"/ 100",conf:"確認度",noIssuer:"発行体がないので、左の6項目は対象外",',
     'const W={all:"All",grade:g=>`Grade ${g}`,gradeN:(g,n)=>`Grade ${g} (${n} tokens)`,none:"No matching tokens",of:"/ 100",conf:"Confidence",noIssuer:"No issuer, so the left 6 items do not apply",'),
    ('issuer:"発行体",mech:"仕組み",issuerH:"発行体（項目1〜6）",mechH:"仕組み（項目7〜10）",pts:v=>v+"点",what:"何のトークン？",na:"対象外（発行体がありません）",fix:"✎ 訂正する",fixA:(s,n)=>`${s} の項目${n}を訂正する`,fixAll:s=>`${s} の訂正を送る`,',
     'issuer:"Issuer",mech:"Mechanism",issuerH:"Issuer (items 1–6)",mechH:"Mechanism (items 7–10)",pts:v=>v+" pts",what:"What is this token for?",na:"Not applicable (no issuer)",fix:"✎ Correct",fixA:(s,n)=>`Correct item ${n} of ${s}`,fixAll:s=>`Send a correction for ${s}`,'),
    ('src:"根拠",rev:"確認日：",met:(d,p)=>`直近30日（DefiLlamaの分類による、${d}取得・参考値で点数には反映しない）：${p}`,rev1:"収益 ",hold:"うち保有者へ ",sep:"、",',
     'src:"Sources",rev:"Reviewed ",met:(d,p)=>`Last 30 days (DefiLlama categories, fetched ${d}; reference only, not used in scores): ${p}`,rev1:"Revenue ",hold:"to holders ",sep:", ",'),
    ('sorts:[["t","総合点の高い順"],["a","発行体の点の高い順"],["m","仕組みの点の高い順"],["s","銘柄名の順"],["c","区分の順"]],sortI:(no,n)=>`項目${no}「${n}」の高い順`,',
     'sorts:[["t","Highest score"],["a","Highest issuer score"],["m","Highest mechanism score"],["s","Token name"],["c","Category"]],sortI:(no,n)=>`Item ${no}: ${n}`,'),
    ('eq:"株式での対応：",sortby:"この項目の点で台帳を並べる",', 'eq:"Stock market analogue: ",sortby:"Sort the ledger by this item",'),
    ('gap0:n=>`担保つきの約束をしている銘柄は、${n}銘柄のうち一つもありません（項目5で2点の銘柄はゼロ）。ここがトークン憲章の埋めたい空白です。`,gapN:(k,n)=>`担保つきの約束をしている銘柄は、${n}銘柄のうち${k}銘柄です（項目5で2点）。`,',
     'gap0:n=>`None of the ${n} tokens backs its promises with collateral (no token scores 2 on item 5). That is the gap Token Charter wants to fill.`,gapN:(k,n)=>`${k} of the ${n} tokens back their promises with collateral (2 points on item 5).`,'),
    ('rules:"編集ルール",rulesF:"RULES.md",raw:"生データ",req:"評価を頼む・訂正を送る"};', 'rules:"Editing rules",rulesF:"RULES.en.md",raw:"Raw data",req:"Request a rating or send a correction"};'),
    ('// ランクの分布：上は絞り込み、下は読むだけ', '// Grade distribution: the top one filters, the bottom one is read-only'),
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
