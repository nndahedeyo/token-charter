"""DefiLlamaの公開データから、直近の収益を取り込む。参考表示のためだけで、点数は変えない。

取れなかった銘柄は前回の値を残す。どの銘柄も取れなくても失敗にはしない（サイトを止めないため）。
"""
import json
import time
import urllib.request
from datetime import datetime, timezone

from common import ROOT, load

API = "https://api.llama.fi/summary/fees/{slug}?dataType={kind}"
KINDS = {"revenue": "dailyRevenue", "holders": "dailyHoldersRevenue"}
OUT = ROOT / "data" / "metrics.json"


def get(slug, kind):
    req = urllib.request.Request(API.format(slug=slug, kind=kind), headers={"User-Agent": "token-charter"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)
    chart = j.get("totalDataChart") or []
    last30 = sum(v for _, v in chart[-30:]) if chart else None
    return {"d30": last30, "d7": j.get("total7d")}


def main():
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"tokens": {}}
    out = {"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "source": "DefiLlama", "tokens": dict(prev.get("tokens", {}))}
    ok = 0
    for t in load("tokens.json")["tokens"]:
        slug = t.get("defillama")
        if not slug:
            continue
        row = {"slug": slug, "date": out["fetched_at"]}
        for name, kind in KINDS.items():
            try:
                row[name] = get(slug, kind)
            except Exception as e:  # 取れない種類のデータは飛ばす
                print(f"skip {t['symbol']} {name}: {e}")
            time.sleep(1.5)
        if "revenue" in row or "holders" in row:
            out["tokens"][t["symbol"]] = row
            ok += 1
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"metrics: {ok} tokens updated")


if __name__ == "__main__":
    main()
