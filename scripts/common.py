"""共通の計算。点数とランクは保存せず、毎回ここで計算する（データの書き換えで結果だけを変えられないように）。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = {"baseline": "基準", "l1": "大型チェーン", "defi": "DeFi・還元型", "infra": "インフラ", "small": "小型見本"}


def load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def pct(values):
    vals = [v for v in values if v is not None]
    return round(sum(vals) / (2 * len(vals)) * 100) if vals else None


def grade(score, cutoffs):
    for g in ("A", "B", "C", "D"):
        if score >= cutoffs[g]:
            return g
    return "E"
