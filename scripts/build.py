"""data/ から公開ページ（_site/）を作る。"""
import json
import os
import shutil

from common import CATEGORIES, ROOT, grade, load, pct

CONF = {"high": "高", "medium": "中", "low": "低"}


def main():
    data, crit = load("tokens.json"), load("criteria.json")
    mpath = ROOT / "data" / "metrics.json"
    metrics = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {"tokens": {}}
    issuer_n = sum(1 for i in crit["items"] if i["group"] == "issuer")
    toks = []
    for t in data["tokens"]:
        v = t["scores"]
        s = pct(v)
        m = metrics.get("tokens", {}).get(t["symbol"], {})
        toks.append({
            "s": t["symbol"], "n": t["name"], "c": CATEGORIES[t["category"]], "i": t["has_issuer"], "v": v,
            "t": s, "g": grade(s, crit["grades"]), "a": pct(v[:issuer_n]), "m": pct(v[issuer_n:]),
            "k": CONF[t["confidence"]], "note": t["note"], "src": [[x["title"], x["url"]] for x in t["sources"]],
            "rev": t["reviewed"],
            "met": {k: m[k].get("d30") for k in ("revenue", "holders") if isinstance(m.get(k), dict)} or None,
            "metAt": m.get("date"),
        })
    items = [{"no": i["no"], "grp": "発行体" if i["group"] == "issuer" else "仕組み", "name": i["name"],
              "h": i["score2"], "m": i["score1"], "l": i["score0"], "eq": i["equity_analogue"]} for i in crit["items"]]
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    repo_url = f"https://github.com/{repo}" if repo else ""
    g = crit["grades"]
    html = (ROOT / "site" / "template.html").read_text(encoding="utf-8")
    html = (html.replace("__TOKENS__", json.dumps(toks, ensure_ascii=False))
                .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
                .replace("__REPO__", json.dumps(repo_url))
                .replace("__ASOF__", data["as_of"])
                .replace("__COUNT__", str(len(toks)))
                .replace("__GRADES__", f"A＝{g['A']}点以上、B＝{g['B']}〜{g['A'] - 1}、C＝{g['C']}〜{g['B'] - 1}、D＝{g['D']}〜{g['C'] - 1}、E＝{g['D'] - 1}以下"))
    out = ROOT / "_site"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    (out / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(ROOT / "data", out / "data")  # 生データも公開して、誰でも検証できるようにする
    print(f"built {len(toks)} tokens -> _site/index.html")


if __name__ == "__main__":
    main()
