"""評価の希望と訂正の窓口（scripts/intake.py）を、あらゆる送られ方で確かめる。python tests/test_intake.py"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import intake as I  # noqa: E402

NOW = 1_800_000_000
DATA = {"tokens": [{"symbol": "BTC", "coingecko": "bitcoin"}, {"symbol": "HYPE", "coingecko": "hyperliquid"}]}


def sign(msg, sk):
    d = int.from_bytes(sk, "big")
    Pt = I._mul(I.G, d)
    if Pt[1] % 2:
        d = I.N - d
    px = Pt[0].to_bytes(32, "big")
    t = (d ^ int.from_bytes(I._tagged("BIP0340/aux", bytes(32)), "big")).to_bytes(32, "big")
    k0 = int.from_bytes(I._tagged("BIP0340/nonce", t + px + msg), "big") % I.N
    R = I._mul(I.G, k0)
    k = k0 if R[1] % 2 == 0 else I.N - k0
    e = int.from_bytes(I._tagged("BIP0340/challenge", R[0].to_bytes(32, "big") + px + msg), "big") % I.N
    return R[0].to_bytes(32, "big") + ((k + e * d) % I.N).to_bytes(32, "big"), px


def make(content, n=1, at=NOW - 100, pow_bits=14, claim=None, kind=7730, tag="token-charter", tamper=False):
    sk = hashlib.sha256(f"key{n}".encode()).digest()
    _, px = sign(bytes(32), sk)
    ev = {"kind": kind, "created_at": at, "tags": [["nonce", "0", str(claim or pow_bits)], ["t", tag]], "content": json.dumps(content, ensure_ascii=False), "pubkey": px.hex()}
    i = 0
    while True:
        ev["tags"][0][1] = str(i)
        if I.leading_zeros(I.event_id(ev)) >= pow_bits:
            break
        i += 1
    ev["id"] = I.event_id(ev)
    ev["sig"] = sign(bytes.fromhex(ev["id"]), sk)[0].hex()
    if tamper:
        ev["content"] = ev["content"].replace("a", "b")
    return ev


ok = fail = 0


def check(label, cond):
    global ok, fail
    print(("OK  " if cond else "NG  ") + label)
    ok, fail = ok + bool(cond), fail + (not cond)


add = lambda coin, why="", n=1, **k: make({"t": "add", "coin": coin, "why": why}, n=n, **k)
fix = lambda tok="BTC", item="8", src="https://example.com/a", what="違う", n=1, **k: make({"t": "fix", "token": tok, "item": item, "what": what, "source": src, "interest": "none"}, n=n, **k)

# 公式の試験ベクトル（BIP340 の 0 番）で、署名の確かめが正しいこと
check("BIP340 の試験ベクトルを正しく確かめる", I.schnorr_verify(bytes(32), bytes.fromhex("F9308A019258C31049344F85F89D5229B531C845836F99B08601F113BCE036F9"),
      bytes.fromhex("E907831F80848D1069A5371B402410364BDF1C5F8307B0084C55F1CE2DCA821525F66A4A85EA8B71E482A74F382D2CE5EBEEE8FDB2172F477DF4900D310536C0")))
e = add("pepe")
check("正しい希望は受け付ける", I.valid(e, NOW))
check("書き換えた希望は捨てる", not I.valid(add("pepe", tamper=True), NOW))
check("計算の量が足りないものは捨てる", not I.valid(add("pepe", pow_bits=4, claim=14), NOW) or I.leading_zeros(add("pepe", pow_bits=4, claim=14)["id"]) >= 14)
check("目標を自分で下げたものは捨てる", not I.valid(add("pepe", pow_bits=14, claim=8), NOW))
check("古すぎるものは捨てる", not I.valid(add("pepe", at=NOW - 40 * 86400), NOW))
check("違う種類・違う目印は捨てる", not I.valid(add("pepe", kind=1), NOW) and not I.valid(add("pepe", tag="x"), NOW))

new, edit = I.plan([add("pepe", "使っている人が多い", 1), add("pepe", "", 2), add("pepe", "使っている人が多い", 3)], DATA, NOW, {})
check("同じ銘柄の希望は1つの課題にまとめ、人数を書く", len(new) == 1 and "**3件**" in new[0][1] and new[0][1].count("使っている人が多い") == 1)
check("すでに憲章にある銘柄の希望は課題にしない", I.plan([add("bitcoin")], DATA, NOW, {}) == ([], []))
check("銘柄の名前の形が違うものは捨てる", I.plan([add("Bad Coin!")], DATA, NOW, {}) == ([], []))
new, _ = I.plan([fix(), fix(n=2), fix(src="https://example.com/b")], DATA, NOW, {})
check("訂正は、銘柄・項目・出典ごとに1つ", len(new) == 2)
check("出典のない訂正は捨てる", I.plan([fix(src="")], DATA, NOW, {}) == ([], []) and I.plan([fix(src="http://x.com/a")], DATA, NOW, {}) == ([], []))
check("憲章にない銘柄・ない項目の訂正は捨てる", I.plan([fix(tok="XXX")], DATA, NOW, {}) == ([], []) and I.plan([fix(item="11")], DATA, NOW, {}) == ([], []))
new, _ = I.plan([fix(what="@nndahedeyo #1 <script>alert(1)</script> `x`")], DATA, NOW, {})
b = new[0][1]
check("@ と # は人や課題を呼ばない形にし、タグや ` は無害にする", "@nndahedeyo" not in b and "#1 " not in b and "<script>" not in b and "`" not in b)
many = [add(f"coin-{i}", n=i) for i in range(12)]
new, _ = I.plan(many, DATA, NOW, {})
check("1回に新しく作る課題は5件まで", len(new) == 5)
t0, b0 = I.plan([add("pepe")], DATA, NOW, {})[0][0]
ex = {t0: {"number": 7, "state": "OPEN", "body": b0}}
check("同じ中身なら書き直さない", I.plan([add("pepe")], DATA, NOW, ex) == ([], []))
new, edit = I.plan([add("pepe", n=1), add("pepe", n=2)], DATA, NOW, ex)
check("人数が増えたら、開いている課題を書き直す", new == [] and edit and edit[0][0] == 7 and "**2件**" in edit[0][1])
ex[t0]["state"] = "CLOSED"
check("閉じた課題は作り直さず、書き直しもしない", I.plan([add("pepe", n=1), add("pepe", n=2)], DATA, NOW, ex) == ([], []))
check("中身が壊れたものは捨てる", I.plan([make("not an object"), make({"t": "zzz"})], DATA, NOW, {}) == ([], []))

# 送る側と受け取る側で、中継と出典の条件がそろっていること
import pathlib, re as _re
_page = (pathlib.Path(__file__).resolve().parent.parent / "site" / "request.html").read_text(encoding="utf-8")
check("送る画面と同じ中継を読む", _re.findall(r'"(wss://[^"]+)"', _re.search(r"const RELAYS = \[[^\]]*\]", _page).group(0)) == I.RELAYS)
check("送る画面も同じ出典の条件で確かめる", "[^\\s<>\"']{4,300}" in _page)

print(f"{ok} OK, {fail} NG")
sys.exit(1 if fail else 0)
