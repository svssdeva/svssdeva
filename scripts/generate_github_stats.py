import os
import json
import urllib.request
from collections import defaultdict

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "svssdeva"
ASSETS_DIR = "assets"

C = {
    "bg":     "#1a1b27",
    "bg2":    "#16161e",
    "border": "#70a5fd",
    "title":  "#70a5fd",
    "text":   "#c0caf5",
    "muted":  "#565f89",
    "green":  "#73daca",
    "orange": "#ff9e64",
    "red":    "#f7768e",
    "yellow": "#e0af68",
    "pink":   "#bb9af7",
    "teal":   "#7dcfff",
}

RANK_COLORS = {
    "SSS+": "#FFD700",
    "SS":   "#e0af68",
    "S":    "#73daca",
    "A":    "#7aa2f7",
    "B":    "#bb9af7",
    "C":    "#565f89",
    "F":    "#3b4261",
}

GQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        forkCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      restrictedContributionsCount
    }
    pullRequests(states: MERGED) { totalCount }
    issues { totalCount }
    followers { totalCount }
  }
}
"""


def gql(query, variables=None):
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "svssdeva-stats-bot",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_stats():
    data = gql(GQL_QUERY, {"login": USERNAME})
    user = data["data"]["user"]
    repos = user["repositories"]["nodes"]
    cc = user["contributionsCollection"]

    stars   = sum(r["stargazerCount"] for r in repos)
    forks   = sum(r["forkCount"] for r in repos)
    commits = cc["totalCommitContributions"] + cc.get("restrictedContributionsCount", 0)
    prs     = user["pullRequests"]["totalCount"]
    issues  = user["issues"]["totalCount"]
    followers = user["followers"]["totalCount"]
    repo_count = user["repositories"]["totalCount"]

    lang_bytes  = defaultdict(int)
    lang_colors = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            lang_bytes[name] += edge["size"]
            lang_colors[name] = edge["node"]["color"] or "#858585"

    total_bytes = sum(lang_bytes.values()) or 1
    top_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:6]
    langs = [
        {"name": n, "pct": round(b / total_bytes * 100, 1), "color": lang_colors[n]}
        for n, b in top_langs
    ]

    return {
        "stars": stars, "forks": forks, "commits": commits,
        "prs": prs, "issues": issues, "followers": followers,
        "repos": repo_count, "langs": langs,
    }


def x(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


# ── Stats Card ────────────────────────────────────────────────────────────────

def stats_svg(s):
    W, H = 495, 200
    items = [
        ("⭐", "Total Stars",    s["stars"],     C["yellow"]),
        ("🔀", "Total PRs",      s["prs"],        C["teal"]),
        ("💻", "Total Commits",  s["commits"],    C["green"]),
        ("🐛", "Total Issues",   s["issues"],     C["red"]),
        ("📦", "Total Repos",    s["repos"],      C["orange"]),
        ("👥", "Followers",      s["followers"],  C["pink"]),
    ]
    rows = ""
    for i, (icon, label, value, color) in enumerate(items):
        col, row = i % 2, i // 2
        tx, ty = 28 + col * 242, 76 + row * 42
        rows += (
            f'<text x="{tx}" y="{ty}" font-size="14">{icon}</text>'
            f'<text x="{tx+24}" y="{ty}" font-family="\'Segoe UI\',sans-serif"'
            f' font-size="13" fill="{C["text"]}">{x(label)}</text>'
            f'<text x="{tx+210}" y="{ty}" font-family="\'Segoe UI\',sans-serif"'
            f' font-size="13" fill="{color}" text-anchor="end" font-weight="600">{x(value)}</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<rect width="{W}" height="{H}" rx="10" fill="{C["bg"]}"/>'
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="9" fill="none"'
        f' stroke="{C["border"]}" stroke-width="1" opacity="0.35"/>'
        f'<text x="25" y="35" font-family="\'Segoe UI\',sans-serif" font-size="15"'
        f' font-weight="600" fill="{C["title"]}">svssdeva\'s GitHub Stats</text>'
        f'<line x1="25" y1="45" x2="{W-25}" y2="45"'
        f' stroke="{C["border"]}" stroke-width="0.5" opacity="0.25"/>'
        f'{rows}'
        f'<text x="{W-12}" y="{H-8}" font-family="\'Segoe UI\',sans-serif"'
        f' font-size="9" fill="{C["muted"]}" text-anchor="end">updated daily</text>'
        f'</svg>'
    )


# ── Top Languages Card ────────────────────────────────────────────────────────

def langs_svg(langs):
    W = 350
    H = 48 + len(langs) * 30 + 18
    bars = ""
    for i, lang in enumerate(langs):
        y     = 48 + i * 30
        bar_w = max(int(lang["pct"] / 100 * 270), 6)
        color = x(lang["color"])
        bars += (
            f'<rect x="25" y="{y-13}" width="{bar_w}" height="13" rx="3" fill="{color}"/>'
            f'<text x="{bar_w+32}" y="{y}" font-family="\'Segoe UI\',sans-serif"'
            f' font-size="12" fill="{C["text"]}">{x(lang["name"])}</text>'
            f'<text x="{W-14}" y="{y}" font-family="\'Segoe UI\',sans-serif"'
            f' font-size="11" fill="{C["muted"]}" text-anchor="end">{x(lang["pct"])}%</text>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<rect width="{W}" height="{H}" rx="10" fill="{C["bg"]}"/>'
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="9" fill="none"'
        f' stroke="{C["border"]}" stroke-width="1" opacity="0.35"/>'
        f'<text x="25" y="32" font-family="\'Segoe UI\',sans-serif" font-size="15"'
        f' font-weight="600" fill="{C["title"]}">Top Languages</text>'
        f'<line x1="25" y1="40" x2="{W-25}" y2="40"'
        f' stroke="{C["border"]}" stroke-width="0.5" opacity="0.25"/>'
        f'{bars}'
        f'<text x="{W-12}" y="{H-6}" font-family="\'Segoe UI\',sans-serif"'
        f' font-size="9" fill="{C["muted"]}" text-anchor="end">updated daily</text>'
        f'</svg>'
    )


# ── Trophies Card (BCK rank system) ───────────────────────────────────────────

def get_rank(value, thresholds):
    for min_val, label in sorted(thresholds, key=lambda t: t[0], reverse=True):
        if value >= min_val:
            return label
    return "F"


def trophies_svg(s):
    trophies = [
        ("⭐", "Stars",    s["stars"],     [(0,"F"),(10,"C"),(50,"B"),(100,"A"),(500,"S"),(1000,"SS"),(2000,"SSS+")]),
        ("💻", "Commits",  s["commits"],   [(0,"F"),(50,"C"),(200,"B"),(500,"A"),(1000,"S"),(2000,"SS"),(5000,"SSS+")]),
        ("🔀", "Pull Reqs",s["prs"],       [(0,"F"),(5,"C"),(20,"B"),(50,"A"),(100,"S"),(300,"SS"),(500,"SSS+")]),
        ("🐛", "Issues",   s["issues"],    [(0,"F"),(5,"C"),(20,"B"),(50,"A"),(100,"S"),(300,"SS"),(500,"SSS+")]),
        ("📦", "Repos",    s["repos"],     [(0,"F"),(5,"C"),(15,"B"),(30,"A"),(50,"S"),(75,"SS"),(100,"SSS+")]),
        ("👥", "Followers",s["followers"], [(0,"F"),(5,"C"),(20,"B"),(50,"A"),(100,"S"),(300,"SS"),(1000,"SSS+")]),
    ]
    cw, ch = 100, 112
    gap    = 10
    cols   = len(trophies)
    W      = cols * cw + (cols + 1) * gap
    H      = ch + 58

    cards = ""
    for i, (icon, name, value, thresh) in enumerate(trophies):
        rank  = get_rank(value, thresh)
        color = RANK_COLORS.get(rank, RANK_COLORS["F"])
        cx    = gap + i * (cw + gap)
        cy    = 44
        cards += (
            f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="8"'
            f' fill="{C["bg2"]}" stroke="{color}" stroke-width="1.2"/>'
            f'<text x="{cx+cw//2}" y="{cy+28}" font-size="20" text-anchor="middle">{icon}</text>'
            f'<text x="{cx+cw//2}" y="{cy+50}" font-family="\'Segoe UI\',sans-serif"'
            f' font-size="14" fill="{color}" text-anchor="middle" font-weight="700">{x(rank)}</text>'
            f'<text x="{cx+cw//2}" y="{cy+68}" font-family="\'Segoe UI\',sans-serif"'
            f' font-size="10" fill="{C["muted"]}" text-anchor="middle">{x(name)}</text>'
            f'<text x="{cx+cw//2}" y="{cy+87}" font-family="\'Segoe UI\',sans-serif"'
            f' font-size="12" fill="{C["text"]}" text-anchor="middle">{x(value)}</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<rect width="{W}" height="{H}" rx="10" fill="{C["bg"]}"/>'
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="9" fill="none"'
        f' stroke="{C["border"]}" stroke-width="1" opacity="0.35"/>'
        f'<text x="{W//2}" y="28" font-family="\'Segoe UI\',sans-serif" font-size="14"'
        f' font-weight="600" fill="{C["title"]}" text-anchor="middle">'
        f'GitHub Achievements \u2014 BCK Rank</text>'
        f'{cards}'
        f'</svg>'
    )


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)
    print("Fetching GitHub stats via GraphQL...")
    s = fetch_stats()
    print(f"  Stars={s['stars']}  Commits={s['commits']}  PRs={s['prs']}  "
          f"Issues={s['issues']}  Repos={s['repos']}  Followers={s['followers']}")

    for fname, content in [
        ("github-stats.svg",    stats_svg(s)),
        ("github-langs.svg",    langs_svg(s["langs"])),
        ("github-trophies.svg", trophies_svg(s)),
    ]:
        path = os.path.join(ASSETS_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Generated {fname}")
