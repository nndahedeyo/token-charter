"""提案ごとに承認を数え、結果を「approvals」という検査結果として提案に付ける（RULES.md「承認」）。

GitHubの「承認が必要」の設定は、書き込み権限を持つ人の承認しか数えないため使わない。
代わりにこのスクリプトが、APPROVERS.md と実績から承認できる人を決めて数える。
このスクリプトは常に main の版が動く（提案の中身のコードは実行しない）。
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"

NEED_NORMAL = 2          # ふつうの変更に必要な承認
NEED_RULES = 4           # ルール・仕組みの変更に必要な承認
MERIT = 3                # 承認できる人になるのに必要な、反映された提案の数
MIN_ACCOUNT_DAYS = 90    # 承認できる人のアカウントの古さ
QUIET_DAYS = 14          # 承認1人のまま反対がなければ反映するまでの日数

# ここに触れる変更は「ルール・仕組みの変更」として4人の承認が要る
PROTECTED = re.compile(
    r"^(RULES(\.en)?\.md|CONTRIBUTING(\.en)?\.md|APPROVERS\.md|LICENSE|data/criteria\.json|scripts/|site/|\.github/)")


def parse_approvers(text):
    """APPROVERS.md から、立ち上げの承認者と、外された人を読む。"""
    founders, removed, sec = set(), set(), None
    for line in text.splitlines():
        if line.startswith("## "):
            sec = "f" if "Founding" in line else "r" if "Removed" in line else None
            continue
        m = re.match(r"^\s*-\s*@([A-Za-z0-9-]{1,39})\b", line)
        if m and sec:
            (founders if sec == "f" else removed).add(m.group(1).lower())
    return founders, removed


def latest_reviews(reviews):
    """人ごとの最後の意思表示（承認・反対・取り下げ）。コメントだけのレビューは数えない。"""
    last = {}
    for r in sorted(reviews, key=lambda r: r["submitted_at"] or ""):
        if r["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            last[r["login"].lower()] = r
    return last


def decide(*, protected, head_sha, reviews, insiders, eligible, now):
    """承認の判定。戻り値は (反映してよいか, 説明)。

    reviews: [{login, state, commit_id, submitted_at}]
    insiders: 提案者と、提案にコミットした人（承認は数えない）
    eligible: login -> 承認できる人か
    """
    need = NEED_RULES if protected else NEED_NORMAL
    ok_approve, objections = [], []
    for login, r in latest_reviews(reviews).items():
        if login in insiders or not eligible(login):
            continue
        if r["state"] == "APPROVED" and r["commit_id"] == head_sha:
            ok_approve.append(r)
        elif r["state"] == "CHANGES_REQUESTED":
            objections.append(r)   # 反対は、本人が承認に変えるか取り下げるまで残る
    a, o = len(ok_approve), len(objections)
    kind = "ルールの変更" if protected else "通常の変更"
    if a - o >= need:
        return True, f"{kind}：承認{a}・反対{o}。条件を満たしました"
    if not protected and a >= 1 and o == 0:
        first = min(dt.datetime.fromisoformat(r["submitted_at"].replace("Z", "+00:00")) for r in ok_approve)
        left = first + dt.timedelta(days=QUIET_DAYS) - now
        if left <= dt.timedelta(0):
            return True, f"{kind}：承認{a}、{QUIET_DAYS}日間反対なし。条件を満たしました"
        return False, f"{kind}：承認{a}/{need}・反対0。反対がなければ残り{left.days + 1}日で反映"
    return False, f"{kind}：承認{a}・反対{o}。承認が反対より{need}多くなると反映"


def symbols(text):
    try:
        return {t.get("symbol") for t in json.loads(text)["tokens"]}
    except Exception:
        return None


class GitHub:
    def __init__(self, repo, token):
        self.repo, self.token, self.cache = repo, token, {}

    def req(self, path, method="GET", body=None, raw=False):
        url = path if path.startswith("http") else API + path
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}", "User-Agent": "token-charter",
            "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json"})
        with urllib.request.urlopen(r, timeout=30) as f:
            out = f.read()
        return out.decode() if raw else json.loads(out or b"null")

    def pages(self, path):
        out, page = [], 1
        while True:
            sep = "&" if "?" in path else "?"
            got = self.req(f"{path}{sep}per_page=100&page={page}")
            out += got
            if len(got) < 100:
                return out
            page += 1

    def file_at(self, path, ref):
        try:
            return self.req(f"/repos/{self.repo}/contents/{path}?ref={ref}", raw=True)
        except Exception:
            return None

    def eligible_fn(self, founders, removed, now):
        def eligible(login):
            if login in self.cache:
                return self.cache[login]
            ok = False
            if login in removed or login.endswith("[bot]"):
                ok = False
            elif login in founders:
                ok = True   # 名簿の人は、外されるまで承認できる（アカウントの古さは問わない）
            else:
                u = self.req(f"/users/{urllib.parse.quote(login)}")
                age = now - dt.datetime.fromisoformat(u["created_at"].replace("Z", "+00:00"))
                if age >= dt.timedelta(days=MIN_ACCOUNT_DAYS) and u.get("type") == "User":
                    q = urllib.parse.quote(f"repo:{self.repo} is:pr is:merged author:{login}")
                    ok = self.req(f"/search/issues?q={q}&per_page=1")["total_count"] >= MERIT
            self.cache[login] = ok
            return ok
        return eligible


def evaluate(gh, pr, founders, removed, now):
    n, head = pr["number"], pr["head"]["sha"]
    files = [f["filename"] for f in gh.pages(f"/repos/{gh.repo}/pulls/{n}/files")]
    protected = any(PROTECTED.match(f) for f in files)
    if "data/tokens.json" in files and not protected:
        before = symbols(gh.file_at("data/tokens.json", pr["base"]["sha"]) or "")
        after = symbols(gh.file_at("data/tokens.json", head) or "")
        if before is None or after is None or not before <= after:
            protected = True   # 銘柄を消す・名前を変える変更は、ルールの変更と同じ扱い
    insiders = {pr["user"]["login"].lower()}
    for c in gh.pages(f"/repos/{gh.repo}/pulls/{n}/commits"):
        for k in ("author", "committer"):
            if c.get(k) and c[k].get("login") and c[k]["login"] != "web-flow":
                insiders.add(c[k]["login"].lower())
    reviews = [{"login": r["user"]["login"], "state": r["state"], "commit_id": r.get("commit_id"),
                "submitted_at": r.get("submitted_at")}
               for r in gh.pages(f"/repos/{gh.repo}/pulls/{n}/reviews") if r.get("user")]
    ok, why = decide(protected=protected, head_sha=head, reviews=reviews, insiders=insiders,
                     eligible=gh.eligible_fn(founders, removed, now), now=now)
    return head, ok, why


def main():
    repo, token = os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"]
    only = os.environ.get("PR_NUMBER")
    dry = "--dry-run" in sys.argv
    gh = GitHub(repo, token)
    founders, removed = parse_approvers((ROOT / "APPROVERS.md").read_text(encoding="utf-8"))
    now = dt.datetime.now(dt.timezone.utc)
    prs = [gh.req(f"/repos/{repo}/pulls/{only}")] if only else gh.pages(f"/repos/{repo}/pulls?state=open")
    for pr in prs:
        if pr["state"] != "open" or pr.get("draft"):
            continue
        head, ok, why = evaluate(gh, pr, founders, removed, now)
        print(f"#{pr['number']}: {'OK' if ok else '待ち'}  {why}")
        if not dry:
            gh.req(f"/repos/{repo}/statuses/{head}", "POST", {
                "state": "success" if ok else "pending", "context": "approvals",
                "description": why[:140], "target_url": f"https://github.com/{repo}/blob/main/RULES.md"})


if __name__ == "__main__":
    main()
