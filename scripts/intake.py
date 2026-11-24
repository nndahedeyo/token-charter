"""評価の希望と訂正の窓口：Nostr に届いた「評価の希望」と「訂正」を、憲章の課題（Issue）にする。

点数は変えない。判断もしない。人が確かめるきっかけを作るだけ（RULES.md「評価の希望と訂正の窓口」）。
- 届いた文はデータとして扱い、決して実行しない。課題に書くときは、@ や # の働きを止め、引用として載せる
- 署名と、荒らしを防ぐ小さな計算（NIP-13、先頭の0が14ビット以上）を確かめる。満たさないものは捨てる
- 評価の希望：銘柄ごとに1つの課題にまとめ、送った人（使い捨てのかぎ）の数を「希望 n件」として書き直す
- 訂正：出典の URL がないものは捨てる。同じ銘柄・項目・出典は1つにまとめる
- 1回に新しく作る課題は MAX_NEW 件まで。閉じた課題と同じ題名は、新しく作らない（判断を尊重する）
"""
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import time

from common import load

KIND, TAG, POW = 7730, "token-charter", 14
RELAYS = ["wss://relay.damus.io", "wss://nos.lol", "wss://relay.primal.net", "wss://relay.nostr.band", "wss://offchain.pub", "wss://nostr.mom", "wss://relay.snort.social", "wss://nostr.wine"]
DAYS = 30           # 30日以内に届いたものを見る
MAX_NEW = 5         # 1回に新しく作る課題の上限
LABEL = "from-nostr"
COIN = re.compile(r"^[a-z0-9-]{1,64}$")
ITEMS = {str(i) for i in range(1, 11)} | {"summary"}

# ---- BIP340（Schnorr 署名）の確かめ。外部の部品を使わない ----
P = 2 ** 256 - 2 ** 32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)


def _add(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a[0] == b[0] and (a[1] + b[1]) % P == 0:
        return None
    if a == b:
        lam = 3 * a[0] * a[0] * pow(2 * a[1], P - 2, P) % P
    else:
        lam = (b[1] - a[1]) * pow(b[0] - a[0], P - 2, P) % P
    x = (lam * lam - a[0] - b[0]) % P
    return (x, (lam * (a[0] - x) - a[1]) % P)


def _mul(pt, k):
    r = None
    while k:
        if k & 1:
            r = _add(r, pt)
        pt = _add(pt, pt)
        k >>= 1
    return r


def _tagged(tag, msg):
    h = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(h + h + msg).digest()


def schnorr_verify(msg, pub, sig):
    if len(msg) != 32 or len(pub) != 32 or len(sig) != 64:
        return False
    x = int.from_bytes(pub, "big")
    if x >= P:
        return False
    y_sq = (pow(x, 3, P) + 7) % P
    y = pow(y_sq, (P + 1) // 4, P)
    if y * y % P != y_sq:
        return False
    pt = (x, y if y % 2 == 0 else P - y)
    r, s = int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big")
    if r >= P or s >= N:
        return False
    e = int.from_bytes(_tagged("BIP0340/challenge", sig[:32] + pub + msg), "big") % N
    R = _add(_mul(G, s), _mul(pt, N - e))
    return R is not None and R[1] % 2 == 0 and R[0] == r


def event_id(ev):
    s = json.dumps([0, ev["pubkey"], ev["created_at"], ev["kind"], ev["tags"], ev["content"]], separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode()).hexdigest()


def leading_zeros(hexid):
    n = 0
    for c in hexid:
        v = int(c, 16)
        if v == 0:
            n += 4
            continue
        return n + (4 - v.bit_length())
    return n


def valid(ev, now):
    """署名・番号・計算の量・時刻を確かめる。中身の形は parse で見る。"""
    try:
        if ev.get("kind") != KIND or not any(t[:2] == ["t", TAG] for t in ev.get("tags", [])):
            return False
        if not (now - DAYS * 86400 <= int(ev["created_at"]) <= now + 600):
            return False
        if event_id(ev) != ev["id"] or leading_zeros(ev["id"]) < POW:
            return False
        nonce = next((t for t in ev["tags"] if t and t[0] == "nonce"), None)
        if not nonce or len(nonce) < 3 or int(nonce[2]) < POW:   # 目標を自分で下げたものは数えない
            return False
        return schnorr_verify(bytes.fromhex(ev["id"]), bytes.fromhex(ev["pubkey"]), bytes.fromhex(ev["sig"]))
    except Exception:
        return False


def clean(s, n):
    """課題に載せる文：制御文字を消し、長さを切り、@ や # が人や課題を呼ばないようにする。"""
    s = re.sub(r"\s*[\r\n]+\s*", " / ", str(s or ""))   # 改行で引用の外に出ないように
    s = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", s)[:n]
    s = s.replace("@", "@\u200b").replace("#", "#\u200b").replace("`", "'").replace("<", "＜").replace(">", "＞")
    return s.strip()


def parse(ev, symbols, coins):
    try:
        c = json.loads(ev["content"])
    except Exception:
        return None
    if not isinstance(c, dict):
        return None
    if c.get("t") == "add":
        coin = str(c.get("coin", ""))
        if not COIN.match(coin) or coin in coins:
            return None
        return {"t": "add", "coin": coin, "why": clean(c.get("why"), 300), "who": ev["pubkey"], "at": ev["created_at"]}
    if c.get("t") == "fix":
        tok, item, src = str(c.get("token", "")), str(c.get("item", "")), str(c.get("source", ""))
        if tok not in symbols or item not in ITEMS or not re.match(r"^https://[^\s<>\"']{4,300}$", src):
            return None
        what = clean(c.get("what"), 600)
        if not what:
            return None
        return {"t": "fix", "token": tok, "item": item, "what": what, "source": src, "insider": c.get("interest") == "insider", "who": ev["pubkey"], "at": ev["created_at"]}
    return None


def group(entries):
    """評価の希望は銘柄ごと、訂正は銘柄・項目・出典ごとにまとめる。"""
    adds, fixes = {}, {}
    for e in entries:
        if e["t"] == "add":
            g = adds.setdefault(e["coin"], {"who": set(), "why": []})
            g["who"].add(e["who"])
            if e["why"] and e["why"] not in g["why"]:
                g["why"].append(e["why"])
        else:
            key = (e["token"], e["item"], e["source"])
            fixes.setdefault(key, e)
    return adds, fixes


def add_issue(coin, g):
    title = f"[追加の希望] {coin}"
    reasons = "\n".join(f"> {w}" for w in g["why"][:10]) or "> （理由の記入なし / no reason given）"
    body = (f"窓口（Nostr）に届いた、トークン憲章への追加の希望です。\n"
            f"A request to add this coin, received through the request window (Nostr).\n\n"
            f"- CoinGecko: https://www.coingecko.com/en/coins/{coin}\n"
            f"- 希望 / Requests: **{len(g['who'])}件**（送った人の数。使い捨てのかぎで数えるので目安 / counted by throwaway keys, so approximate）\n\n"
            f"届いた理由 / Reasons received:\n\n{reasons}\n\n"
            f"評価するには、出典つきで data/tokens.json に提案してください（CONTRIBUTING.md）。\n"
            f"To rate it, open a sourced proposal to data/tokens.json (see CONTRIBUTING.md).\n\n"
            f"<!-- intake:add:{coin} -->")
    return title, body


def fix_issue(key, e):
    tok, item, src = key
    h = hashlib.sha256(src.encode()).hexdigest()[:8]
    title = f"[訂正] {tok} 項目{item} ({h})" if item != "summary" else f"[訂正] {tok} 要約 ({h})"
    body = (f"窓口（Nostr）に届いた訂正です。点数は変わっていません。出典を確かめてから提案にしてください。\n"
            f"A correction received through the request window (Nostr). No score has changed. Check the source before turning it into a proposal.\n\n"
            f"- 銘柄 / Token: {tok}\n- 項目 / Item: {item}\n- 出典 / Source: {src}\n"
            f"- 利害の開示 / Disclosure: {'関係者または大口保有者 / team or large holder' if e['insider'] else '利害関係なし / no interest'}\n\n"
            f"何が違うか / What is wrong:\n\n> {e['what']}\n\n<!-- intake:fix:{tok}:{item}:{h} -->")
    return title, body


async def fetch_relay(url, since):
    import websockets
    out = []
    try:
        async with websockets.connect(url, open_timeout=15, close_timeout=5, max_size=2 ** 22) as ws:
            await ws.send(json.dumps(["REQ", "i", {"kinds": [KIND], "#t": [TAG], "since": since, "limit": 2000}]))
            while True:
                d = json.loads(await asyncio.wait_for(ws.recv(), 20))
                if d[0] == "EVENT" and d[1] == "i":
                    out.append(d[2])
                elif d[0] == "EOSE":
                    break
        print(f"{url}: ok {len(out)}")
    except Exception as x:
        print(f"{url}: {type(x).__name__}", file=sys.stderr)
    return out


def fetch(now):
    since = now - DAYS * 86400
    async def run():
        return await asyncio.gather(*(fetch_relay(u, since) for u in RELAYS))
    seen, out = set(), []
    for evs in asyncio.run(run()):
        for ev in evs:
            if isinstance(ev, dict) and ev.get("id") not in seen:
                seen.add(ev.get("id"))
                out.append(ev)
    return out


def gh(*args, input_text=None):
    return subprocess.run(["gh", *args], input=input_text, capture_output=True, text=True, check=True).stdout


def plan(events, data, now, existing):
    """作る・書き直す課題の一覧を返す（GitHub には触れない。試験できるように分けてある）。
    existing: 題名 → {"number", "state", "body"}"""
    symbols = {t["symbol"] for t in data["tokens"]}
    coins = {t.get("coingecko") for t in data["tokens"] if t.get("coingecko")}
    entries = [e for e in (parse(ev, symbols, coins) for ev in events if valid(ev, now)) if e]
    adds, fixes = group(entries)
    todo = []
    for coin, g in sorted(adds.items(), key=lambda x: -len(x[1]["who"])):
        todo.append(add_issue(coin, g))
    for key, e in sorted(fixes.items(), key=lambda x: x[1]["at"]):
        todo.append(fix_issue(key, e))
    new, edit = [], []
    for title, body in todo:
        ex = existing.get(title)
        if ex is None:
            if len(new) < MAX_NEW:
                new.append((title, body))
        elif ex["state"] == "OPEN" and ex["body"] != body:
            edit.append((ex["number"], body))
    return new, edit


def main():
    now = int(time.time())
    data = load("tokens.json")
    events = fetch(now)
    print(f"events: {len(events)}")
    subprocess.run(["gh", "label", "create", LABEL, "--color", "5B6676", "--description", "評価の希望と訂正の窓口（Nostr）から届いたもの"], capture_output=True)
    raw = json.loads(gh("issue", "list", "--label", LABEL, "--state", "all", "--limit", "500", "--json", "number,title,state,body"))
    existing = {i["title"]: i for i in raw}
    new, edit = plan(events, data, now, existing)
    for title, body in new:
        gh("issue", "create", "--title", title, "--label", LABEL, "--body-file", "-", input_text=body)
        print(f"created: {title}")
    for number, body in edit:
        gh("issue", "edit", str(number), "--body-file", "-", input_text=body)
        print(f"updated: #{number}")


if __name__ == "__main__":
    main()
