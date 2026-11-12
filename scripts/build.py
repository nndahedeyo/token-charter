"""data/ から公開ページを作る。日本語版を _site/index.html、英語版を _site/en/index.html に置く。"""
import json
import os
import re
import shutil
from urllib.parse import urlparse

from common import CATEGORIES, ROOT, grade, load, pct

CATEGORIES_EN = {"baseline": "Baseline", "l1": "Layer 1", "defi": "DeFi", "infra": "Infrastructure", "small": "Small"}
CONF = {"ja": {"high": "高", "medium": "中", "low": "低"}, "en": {"high": "High", "medium": "Medium", "low": "Low"}}


def js(value):
    """<script> の中に埋め込むJSON。「</script>」などで抜け出せないように < > & をエスケープする。"""
    return (json.dumps(value, ensure_ascii=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def tokens_for(lang, data, crit, metrics, icons):
    issuer_n = sum(1 for i in crit["items"] if i["group"] == "issuer")
    out = []
    for t in data["tokens"]:
        v = t["scores"]
        s = pct(v)
        m = metrics.get("tokens", {}).get(t["symbol"], {})
        if lang == "en":
            src = [[x.get("title_en") or urlparse(x["url"]).netloc.removeprefix("www."), x["url"]] for x in t["sources"]]
        else:
            src = [[x["title"], x["url"]] for x in t["sources"]]
        out.append({
            "s": t["symbol"], "n": t["name"],
            "c": (CATEGORIES_EN if lang == "en" else CATEGORIES)[t["category"]],
            "i": t["has_issuer"], "v": v, "t": s, "g": grade(s, crit["grades"]),
            "a": pct(v[:issuer_n]), "m": pct(v[issuer_n:]),
            "k": CONF[lang][t["confidence"]],
            "note": (t.get("note_en") or t["note"]) if lang == "en" else t["note"],
            "src": src, "rev": t["reviewed"],
            "met": {k: m[k].get("d30") for k in ("revenue", "holders") if isinstance(m.get(k), dict)} or None,
            "metAt": m.get("date"), "ic": t["symbol"] in icons,
        })
    return out


def items_for(lang, crit):
    e = lang == "en"
    return [{"no": i["no"],
             "grp": ("Issuer" if i["group"] == "issuer" else "Mechanism") if e else ("発行体" if i["group"] == "issuer" else "仕組み"),
             "name": i.get("name_en") if e else i["name"],
             "h": i.get("score2_en") if e else i["score2"],
             "m": i.get("score1_en") if e else i["score1"],
             "l": i.get("score0_en") if e else i["score0"],
             "eq": i.get("equity_analogue_en") if e else i["equity_analogue"]} for i in crit["items"]]


def grades_text(lang, g):
    if lang == "en":
        return f"A = {g['A']}+, B = {g['B']}–{g['A'] - 1}, C = {g['C']}–{g['B'] - 1}, D = {g['D']}–{g['C'] - 1}, E = {g['D'] - 1} or below"
    return f"A＝{g['A']}点以上、B＝{g['B']}〜{g['A'] - 1}、C＝{g['C']}〜{g['B'] - 1}、D＝{g['D']}〜{g['C'] - 1}、E＝{g['D'] - 1}以下"


def main():
    data, crit = load("tokens.json"), load("criteria.json")
    mpath = ROOT / "data" / "metrics.json"
    metrics = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {"tokens": {}}
    icon_dir = ROOT / "icons"
    icons = {p.stem for p in icon_dir.glob("*.png")} if icon_dir.exists() else set()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    repo_url = f"https://github.com/{repo}" if repo else ""
    out = ROOT / "_site"
    shutil.rmtree(out, ignore_errors=True)
    for lang, tpl, dest, base in (("ja", "template.html", out, ""), ("en", "template.en.html", out / "en", "../")):
        html = (ROOT / "site" / tpl).read_text(encoding="utf-8")
        values = {
            "__TOKENS__": js(tokens_for(lang, data, crit, metrics, icons)),
            "__ITEMS__": js(items_for(lang, crit)),
            "__REPO__": js(repo_url),
            "__BASE__": js(base),
            "__ASOF__": data["as_of"],
            "__COUNT__": str(len(data["tokens"])),
            "__GRADES__": grades_text(lang, crit["grades"]),
        }
        # 1回の置き換えで全部を埋める（データの中に「__BASE__」などの文字があっても、二重に置き換えない）
        html = re.sub("|".join(map(re.escape, values)), lambda m: values[m.group(0)], html)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(ROOT / "data", out / "data")  # 生データも公開して、誰でも検証できるようにする
    if icons:
        shutil.copytree(icon_dir, out / "icons")
    print(f"built {len(data['tokens'])} tokens (ja, en), {len(icons)} icons -> _site/")


if __name__ == "__main__":
    main()
