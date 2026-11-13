"""見張り役：約束に関わる変化を機械的に見つけて、訂正の依頼（Issue）を立てる。

点数は変えない。判断もしない。人が確かめるきっかけを作るだけ（RULES.md「AIと自動の見張り」）。
見つけるもの：
1. 収益の大きな減少：直近30日の収益が、30日前の30日間より半分以下になった銘柄。
   市場全体の動きか、その銘柄だけの動きかを分けるため、全銘柄の中央値も書く
2. 開けなくなった出典：ページが消えた（404・410）か、サイトが見つからない出典
同じ題名のIssueが開いていれば、新しく立てない。
"""
import json
import os
import statistics
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from common import ROOT, load

DROP = 0.5          # 半分以下になったら知らせる
MIN_REVENUE = 100_000  # 30日で10万ドル未満の銘柄は、ぶれが大きいので見ない
LABEL = "watch"


def revenue_change(history_dir, today):
    """銘柄ごとの、直近30日の収益と、30日前の30日間の収益の比。"""
    now_f = history_dir / f"{today.isoformat()}.json"
    files = sorted(history_dir.glob("*.json"))
    if not files:
        return {}, None
    now = json.loads((now_f if now_f.exists() else files[-1]).read_text(encoding="utf-8"))
    target = today - timedelta(days=30)
    old_f = [f for f in files if abs((date.fromisoformat(f.stem) - target).days) <= 3]
    if not old_f:
        return {}, None   # 30日前の記録がまだない
    old = json.loads(old_f[0].read_text(encoding="utf-8"))
    out = {}
    for sym, row in now.get("tokens", {}).items():
        a = (row.get("revenue") or {}).get("d30")
        b = (old.get("tokens", {}).get(sym, {}).get("revenue") or {}).get("d30")
        if a is not None and b and b >= MIN_REVENUE:
            out[sym] = (a / b, a, b)
    return out, old_f[0].stem


def dead(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (token-charter link check)"})
    try:
        with urllib.request.urlopen(req, timeout=20):
            return None
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}" if e.code in (404, 410) else None   # 403などはボット除けのことが多いので無視
    except urllib.error.URLError as e:
        reason = str(e.reason)
        return "サイトが見つからない" if "Name or service not known" in reason or "nodename" in reason else None
    except Exception:
        return None


def findings(today, history_dir, check_links=True):
    out = []
    changes, since = revenue_change(history_dir, today)
    if changes:
        med = statistics.median(r for r, _, _ in changes.values())
        for sym, (r, a, b) in sorted(changes.items()):
            if r <= DROP:
                market = "市場全体も同じくらい減っています" if med <= DROP + 0.15 else "市場全体（中央値）より大きく減っています"
                out.append((f"[自動検知] {sym}：直近30日の収益が{(1 - r) * 100:.0f}%減少",
                            f"DefiLlamaの収益（直近30日）が、{since}時点の30日間の **{b:,.0f}ドル** から **{a:,.0f}ドル** に減りました（{r * 100:.0f}%）。\n\n"
                            f"同じ期間の全銘柄の中央値は {med * 100:.0f}% です。{market}。\n\n"
                            "点数は自動では変わりません。還元の約束（項目1）や約束の実行（項目2）に関わる変化か、出典を確かめてください。"))
    if check_links:
        for t in load("tokens.json")["tokens"]:
            for s in t["sources"]:
                why = dead(s["url"])
                if why:
                    out.append((f"[自動検知] {t['symbol']}：出典「{s['title']}」が開けません",
                                f"出典「{s['title']}」（{s['url']}）が開けません（{why}）。\n\n"
                                "移転先か、代わりになる出典を探して提案してください。点数は自動では変わりません。\n\n"
                                "ボット除けで誤って検知することもあります。ブラウザで開けた場合は、このIssueを閉じてください。"))
    return out


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def main():
    dry = "--dry-run" in sys.argv
    history_dir = Path(os.environ.get("HISTORY_DIR", ROOT / "history"))
    today = date.fromisoformat(os.environ["TODAY"]) if os.environ.get("TODAY") else date.today()
    items = findings(today, history_dir, check_links="--no-links" not in sys.argv)
    if dry:
        for title, body in items:
            print(title, "\n", body, "\n")
        return
    subprocess.run(["gh", "label", "create", LABEL, "--color", "7FCBCB",
                    "--description", "見張り役が自動で見つけた変化（点数は自動では変わりません）"], capture_output=True)
    listed = json.loads(gh("issue", "list", "--state", "open", "--label", LABEL, "--limit", "200", "--json", "title"))
    open_titles = {i["title"] for i in listed}
    made = 0
    for title, body in items:
        if title in open_titles or made >= 10:   # 同じものは立てない。一度に多く立てすぎない
            continue
        gh("issue", "create", "--title", title, "--body", body + "\n\n---\n見張り役（scripts/watch.py）が自動で立てました。",
           "--label", LABEL)
        made += 1
    print(f"watch: {len(items)} found, {made} issues opened")


if __name__ == "__main__":
    main()
