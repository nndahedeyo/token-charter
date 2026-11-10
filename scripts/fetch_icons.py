"""CoinGeckoから銘柄のアイコンを取り込み、icons/ に保存する（公開ページの表示用）。

取れなかった銘柄はアイコンなしで表示されるだけで、失敗にはしない。
"""
import json
import time
import urllib.parse
import urllib.request

from common import ROOT, load

OUT = ROOT / "icons"
API = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&ids="


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "token-charter"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    OUT.mkdir(exist_ok=True)
    toks = [t for t in load("tokens.json")["tokens"] if t.get("coingecko")]
    ids = {t["coingecko"]: t["symbol"] for t in toks}
    try:
        markets = json.loads(get(API + urllib.parse.quote(",".join(ids))))
    except Exception as e:
        print("icons: skipped,", e)
        return
    ok = 0
    for m in markets:
        sym, url = ids.get(m.get("id")), str(m.get("image") or "")
        if not sym or not url.startswith("https://"):
            continue
        url = url.replace("/large/", "/small/")
        try:
            data = get(url)
            if len(data) < 200_000:
                (OUT / f"{sym}.png").write_bytes(data)
                ok += 1
        except Exception as e:
            print(f"icon skip {sym}: {e}")
        time.sleep(0.3)
    print(f"icons: {ok}/{len(toks)}")


if __name__ == "__main__":
    main()
