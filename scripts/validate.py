"""提案の自動検査。RULES.md の「自動検査」と「意見が割れたとき」を機械で確かめる。

使い方:
  python scripts/validate.py                 # 形式だけを検査
  python scripts/validate.py --base origin/main  # 変更点と、30日以内の変更回数も検査
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys

from common import CATEGORIES, ROOT, load

URL = re.compile(r"^https://[^\s]+$")
errors = []


def err(msg):
    errors.append(msg)


def check_format(data, crit):
    n = len(crit["items"])
    issuer_items = sum(1 for i in crit["items"] if i["group"] == "issuer")
    seen = set()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(data.get("as_of", ""))):
        err("as_of は YYYY-MM-DD の形式にしてください")
    for t in data.get("tokens", []):
        sym = t.get("symbol", "?")
        if not re.match(r"^[A-Z0-9]{1,12}$", str(sym)):
            err(f"{sym}: symbol は英大文字と数字だけ、12文字以内にしてください")
        if sym in seen:
            err(f"{sym}: 同じ銘柄が2回あります")
        seen.add(sym)
        for k in ("symbol", "name", "category", "has_issuer", "scores", "confidence", "note", "sources", "reviewed"):
            if k not in t:
                err(f"{sym}: {k} がありません")
        if t.get("category") not in CATEGORIES:
            err(f"{sym}: category は {', '.join(CATEGORIES)} のどれかにしてください")
        sc = t.get("scores", [])
        if len(sc) != n:
            err(f"{sym}: scores は{n}個必要です（いま{len(sc)}個）")
        for i, v in enumerate(sc):
            if v is None:
                if t.get("has_issuer") or i >= issuer_items:
                    err(f"{sym}: 項目{i + 1}が空です。発行体のない銘柄の1〜{issuer_items}番目だけ null にできます")
            elif v not in (0, 1, 2):
                err(f"{sym}: 項目{i + 1}の点数 {v} は 0、1、2 のどれかにしてください")
        if not t.get("has_issuer") and any(v is not None for v in sc[:issuer_items]):
            err(f"{sym}: 発行体のない銘柄は、1〜{issuer_items}番目を null にしてください")
        srcs = t.get("sources", [])
        if not srcs:
            err(f"{sym}: 出典が1つもありません（原則1：検証可能性）")
        for s in srcs:
            if not s.get("title") or not URL.match(str(s.get("url", ""))):
                err(f"{sym}: 出典には title と https で始まる url が必要です")
        if t.get("confidence") not in ("high", "medium", "low"):
            err(f"{sym}: confidence は high、medium、low のどれかにしてください")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(t.get("reviewed", ""))):
            err(f"{sym}: reviewed は YYYY-MM-DD の形式にしてください")
        for k in ("coingecko", "defillama"):
            if t.get(k) is not None and not re.match(r"^[a-z0-9][a-z0-9.-]{0,80}$", str(t[k])):
                err(f"{sym}: {k} は英小文字・数字・ハイフン・ドットだけにしてください")
        if len(t.get("note", "")) > 300:
            err(f"{sym}: note は300文字以内にしてください")
        if len(t.get("note_en", "")) > 600:
            err(f"{sym}: note_en は600文字以内にしてください")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def tokens_at(rev):
    try:
        return {t["symbol"]: t for t in json.loads(git("show", f"{rev}:data/tokens.json"))["tokens"]}
    except subprocess.CalledProcessError:
        return {}


def changed_items(old, new):
    out = set()
    for sym, t in new.items():
        o = old.get(sym)
        if o is None:
            continue
        for i, (a, b) in enumerate(zip(o.get("scores", []), t.get("scores", []))):
            if a != b:
                out.add((sym, i))
    return out


def check_changes(base, data):
    old = tokens_at(base)
    new = {t["symbol"]: t for t in data["tokens"]}
    changes = changed_items(old, new)
    for sym in new:
        if sym in old and new[sym]["scores"] != old[sym]["scores"]:
            added = {s["url"] for s in new[sym]["sources"]} - {s["url"] for s in old[sym]["sources"]}
            if not added:
                err(f"{sym}: 点数を変えるときは、根拠になる出典を新しく1つ以上追加してください（原則1）")
    if not changes:
        return
    since = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    commits = git("log", f"--since={since}", "--format=%H", base, "--", "data/tokens.json").split()
    counts = {}
    for c in commits:
        for key in changed_items(tokens_at(f"{c}^"), tokens_at(c)):
            counts[key] = counts.get(key, 0) + 1
    for sym, i in sorted(changes):
        if counts.get((sym, i), 0) >= 3:
            err(f"{sym} の項目{i + 1}は30日以内にすでに{counts[(sym, i)]}回変わっています。"
                "議論のページ（Issue）で合意してから提案してください（RULES.md「意見が割れたとき」）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    a = ap.parse_args()
    data, crit = load("tokens.json"), load("criteria.json")
    check_format(data, crit)
    if a.base and not errors:
        check_changes(a.base, data)
    if errors:
        print("検査で問題が見つかりました:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"OK: {len(data['tokens'])}銘柄")


if __name__ == "__main__":
    main()
