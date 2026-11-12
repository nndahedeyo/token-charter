"""承認の判定と、公開ページの安全性を、あらゆる立場から確かめる。python tests/test_rules.py"""
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import approvals as A  # noqa: E402

NOW = dt.datetime(2026, 12, 1, tzinfo=dt.timezone.utc)
HEAD = "h2"


def rv(login, state, commit=HEAD, days_ago=1):
    return {"login": login, "state": state, "commit_id": commit,
            "submitted_at": (NOW - dt.timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")}


ELIG = {"alice", "bob", "carol", "dave", "erin", "owner"}


def run(reviews, protected=False, insiders=("author",)):
    return A.decide(protected=protected, head_sha=HEAD, reviews=reviews, insiders=set(insiders),
                    eligible=lambda u: u in ELIG, now=NOW)[0]


CASES = [
    # (説明, 期待, 結果)
    ("承認者2人で反映", True, run([rv("alice", "APPROVED"), rv("bob", "APPROVED")])),
    ("承認1人だけ、まだ1日", False, run([rv("alice", "APPROVED")])),
    ("承認1人、14日たって反対なし → 反映", True, run([rv("alice", "APPROVED", days_ago=15)])),
    ("承認1人、14日たったが反対1 → 止まる", False, run([rv("alice", "APPROVED", days_ago=15), rv("bob", "CHANGES_REQUESTED")])),
    ("承認2・反対1 → 足りない（承認が反対より2多く必要）", False,
     run([rv("alice", "APPROVED"), rv("bob", "APPROVED"), rv("carol", "CHANGES_REQUESTED")])),
    ("承認3・反対1 → 反映", True,
     run([rv("alice", "APPROVED"), rv("bob", "APPROVED"), rv("dave", "APPROVED"), rv("carol", "CHANGES_REQUESTED")])),
    ("提案者の自己承認は数えない", False, run([rv("alice", "APPROVED"), rv("author", "APPROVED")])),
    ("提案にコミットした人の承認は数えない", False,
     run([rv("alice", "APPROVED"), rv("bob", "APPROVED")], insiders=("author", "bob"))),
    ("資格のない人（捨てアカウント）の承認は数えない", False, run([rv("alice", "APPROVED"), rv("sock1", "APPROVED")])),
    ("資格のない人の反対も数えない（嫌がらせで止められない）", True,
     run([rv("alice", "APPROVED"), rv("bob", "APPROVED"), rv("sock1", "CHANGES_REQUESTED")])),
    ("古い版への承認は数えない（承認後に中身をすり替え）", False,
     run([rv("alice", "APPROVED", commit="h1"), rv("bob", "APPROVED")])),
    ("古い版への承認は14日ルールにも使えない", False, run([rv("alice", "APPROVED", commit="h1", days_ago=20)])),
    ("反対した人が承認に変えたら反対は消える", True,
     run([rv("bob", "CHANGES_REQUESTED", days_ago=3), rv("bob", "APPROVED", days_ago=1), rv("alice", "APPROVED")])),
    ("承認を取り下げたら数えない", False,
     run([rv("alice", "APPROVED", days_ago=3), rv("alice", "DISMISSED", days_ago=1), rv("bob", "APPROVED")])),
    ("コメントだけのレビューは承認を消さない", True,
     run([rv("alice", "APPROVED", days_ago=3), rv("alice", "COMMENTED", days_ago=1), rv("bob", "APPROVED")])),
    ("ルールの変更：承認3では足りない", False,
     run([rv(u, "APPROVED") for u in ("alice", "bob", "carol")], protected=True)),
    ("ルールの変更：承認4で反映", True,
     run([rv(u, "APPROVED") for u in ("alice", "bob", "carol", "dave")], protected=True)),
    ("ルールの変更：14日ルールは使えない", False, run([rv("alice", "APPROVED", days_ago=60)], protected=True)),
    ("立ち上げた人1人だけでも、14日待てば通常の訂正は進む", True, run([rv("owner", "APPROVED", days_ago=14)])),
]

bad = [d for d, want, got in CASES if want != got]
for d, want, got in CASES:
    print(("OK  " if want == got else "NG  ") + d)

f, r = A.parse_approvers((ROOT / "APPROVERS.md").read_text(encoding="utf-8"))
print("OK  名簿の読み取り" if f == {"nndahedeyo"} and r == set() else f"NG  名簿の読み取り {f} {r}")
bad += [] if f == {"nndahedeyo"} and r == set() else ["名簿"]
for path in ("RULES.md", "APPROVERS.md", "scripts/x.py", ".github/workflows/a.yml", "data/criteria.json", "site/template.html"):
    if not A.PROTECTED.match(path):
        bad.append(f"保護されていない: {path}")
if A.PROTECTED.match("data/tokens.json"):
    bad.append("tokens.json が保護扱い")
print("OK  守るファイルの判定" if not [b for b in bad if b.startswith("保護") or "tokens.json" in b] else "NG  守るファイルの判定")

# 公開ページへの埋め込み攻撃：要約に </script> や __BASE__ を入れても、ページが壊れず実行もされない
import tempfile, shutil, os  # noqa: E401,E402
tmp = Path(tempfile.mkdtemp())
shutil.copytree(ROOT, tmp / "r", ignore=shutil.ignore_patterns("_site", ".git", "icons"))
d = json.loads((tmp / "r/data/tokens.json").read_text(encoding="utf-8"))
evil = '</script><script>alert(1)</script> __BASE__ __REPO__ __TOKENS__ & <img src=x onerror=alert(2)>'
d["tokens"][0]["note"] = evil[:300]
(tmp / "r/data/tokens.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
subprocess.run([sys.executable, "-E", "-s", "scripts/build.py"], cwd=tmp / "r", check=True, capture_output=True)
html = (tmp / "r/_site/index.html").read_text(encoding="utf-8")
leaks = html.count("<script>alert(1)") + html.count("<img src=x")
ok = leaks == 0 and "\\u003c/script\\u003e" in html and " __BASE__ " in html
print("OK  要約に仕込んだスクリプトは無害化される" if ok else "NG  要約からスクリプトが漏れる")
bad += [] if ok else ["XSS"]
d["tokens"][0]["symbol"] = "<b>X"
(tmp / "r/data/tokens.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
v = subprocess.run([sys.executable, "-E", "-s", "scripts/validate.py"], cwd=tmp / "r", capture_output=True, text=True)
ok = v.returncode != 0 and "symbol" in v.stdout
print("OK  銘柄名にHTMLを入れると検査で落ちる" if ok else "NG  銘柄名の検査")
bad += [] if ok else ["symbol"]
d["tokens"][0]["symbol"] = "../../x"
(tmp / "r/data/tokens.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
v = subprocess.run([sys.executable, "-E", "-s", "scripts/validate.py"], cwd=tmp / "r", capture_output=True, text=True)
print("OK  銘柄名でファイルの場所を書き換える手口は落ちる" if v.returncode else "NG  パス")
bad += [] if v.returncode else ["path"]
shutil.rmtree(tmp)
print("\n全部OK" if not bad else f"\n問題: {bad}")
sys.exit(1 if bad else 0)
