import json, os, time, urllib.parse, urllib.request
ids = json.load(open("ids.json"))
def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": "token-charter"})
    with urllib.request.urlopen(r, timeout=30) as f: return f.read()
m = json.loads(get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&ids=" + urllib.parse.quote(",".join(ids))))
os.makedirs("icons", exist_ok=True)
for x in m:
    s, u = ids.get(x.get("id")), str(x.get("image") or "")
    if s and u.startswith("https://"):
        try: open(f"icons/{s}.png", "wb").write(get(u)); print("ok", s)
        except Exception as e: print("skip", s, e)
        time.sleep(0.3)
