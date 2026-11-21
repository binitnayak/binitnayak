#!/usr/bin/env python3
"""Generates glass-style SVG stat cards for a GitHub profile README (stdlib only).
Usage:  GITHUB_TOKEN=xxx python generate_cards.py binitnayak
Without a token it still works (public API, low rate limit) and falls back to sample data."""
import json, os, sys, urllib.request, collections
from html import escape

USER = sys.argv[1] if len(sys.argv) > 1 else "binitnayak"
OUT = "assets"
os.makedirs(OUT, exist_ok=True)

FALLBACK = {  # used only if the GitHub API is unreachable / rate-limited
    "langs": {"HTML": 76, "Python": 12, "Jupyter Notebook": 6, "TypeScript": 3, "JavaScript": 2},
    "repos": 16, "stars": 16, "followers": 0, "following": 0,
}
COLORS = {"HTML": "#e34c26", "Python": "#4a8fd0", "Jupyter Notebook": "#f37726", "TypeScript": "#3b82d6",
          "JavaScript": "#f1e05a", "CSS": "#a78bfa", "Vue": "#41b883", "Java": "#e76f51", "C++": "#f34b7d",
          "C": "#8d8d8d", "PHP": "#8892bf", "Shell": "#89e051", "Markdown": "#2563eb"}
PALETTE = ["#e34c26", "#4a8fd0", "#f37726", "#3b82d6", "#f1e05a", "#41b883", "#a78bfa"]

def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "card-gen"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    return json.load(urllib.request.urlopen(req, timeout=25))

def load():
    try:
        u = api(f"https://api.github.com/users/{USER}")
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100")
        tot = collections.Counter()
        for r in repos:
            if not r["fork"]:
                tot.update(api(r["languages_url"]))
        s = sum(tot.values()) or 1
        langs = {k: 100 * v / s for k, v in tot.most_common(5)}
        return {"langs": langs, "repos": u["public_repos"], "followers": u["followers"],
                "following": u["following"], "stars": sum(r["stargazers_count"] for r in repos)}
    except Exception as e:
        print("API failed, using fallback data:", e)
        return FALLBACK

def kfmt(n):
    return f"{n/1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)

def shell(w, h, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs>
 <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#090d14"/></linearGradient>
 <radialGradient id="g1" cx="12%" cy="0%" r="55%"><stop offset="0" stop-color="#3b82f6" stop-opacity=".45"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/></radialGradient>
 <radialGradient id="g2" cx="85%" cy="15%" r="45%"><stop offset="0" stop-color="#22c55e" stop-opacity=".22"/><stop offset="1" stop-color="#22c55e" stop-opacity="0"/></radialGradient>
 <radialGradient id="g3" cx="55%" cy="105%" r="50%"><stop offset="0" stop-color="#a855f7" stop-opacity=".35"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/></radialGradient>
</defs>
<style>text{{font-family:'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif}}</style>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="url(#bg)" stroke="#3b6ea8" stroke-opacity=".8"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="url(#g1)"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="url(#g2)"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="22" fill="url(#g3)"/>
{body}
<text x="{w-14}" y="{h-10}" text-anchor="end" font-size="10" fill="#ffffff" fill-opacity=".25" font-weight="600">@{escape(USER)}</text>
</svg>'''

def language_card(d):
    items = list(d["langs"].items())[:5]
    b = ['<rect x="28" y="26" width="804" height="228" rx="18" fill="#05080f" fill-opacity=".55" stroke="#3b6ea8" stroke-opacity=".6"/>',
         '<text x="46" y="62" font-size="27" font-weight="800" fill="#e8eefc">Language Stack</text>',
         '<text x="46" y="84" font-size="13" font-weight="700" fill="#8b96ab">Repository-weighted technologies</text>',
         '<text x="766" y="62" text-anchor="end" font-size="13" font-weight="700" fill="#4f9cf9">&gt; stack.scan</text>',
         '<rect x="786" y="60" width="8" height="2" fill="#4f9cf9"><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></rect>']
    for i, (name, pct) in enumerate(items):
        y = 106 + i * 32
        c = COLORS.get(name, PALETTE[i % len(PALETTE)])
        w = max(8, 466 * pct / 100)
        b += [f'<circle cx="52" cy="{y}" r="5" fill="{c}"/>',
              f'<text x="72" y="{y+5}" font-size="13.5" font-weight="700" fill="#fff">{escape(name)}</text>',
              f'<text x="306" y="{y+5}" text-anchor="end" font-size="13.5" font-weight="800" fill="{c}">{round(pct)}%</text>',
              f'<rect x="330" y="{y-4}" width="466" height="9" rx="4.5" fill="#fff" fill-opacity=".13"/>',
              f'<rect x="330" y="{y-4}" width="{w:.1f}" height="9" rx="4.5" fill="{c}"><animate attributeName="width" from="0" to="{w:.1f}" dur="1s" fill="freeze"/></rect>']
    return shell(860, 280, "\n".join(b))

def highlights_card(d):
    tiles = [("Open Source", f'{d["repos"]} public repositories', "#4f9cf9"),
             ("Impact", f'{kfmt(d["stars"])} stars earned', "#22c55e"),
             ("Community", f'{kfmt(d["followers"])} followers', "#a855f7")]
    b = ['<text x="46" y="52" font-size="11" font-weight="800" letter-spacing="3" fill="#8b96ab">HIGHLIGHTS</text>']
    for i, (t, s, c) in enumerate(tiles):
        x = 36 + i * 270
        b += [f'<rect x="{x}" y="70" width="250" height="100" rx="16" fill="#05080f" fill-opacity=".55" stroke="#3b6ea8" stroke-opacity=".6"/>',
              f'<rect x="{x}" y="86" width="4" height="68" rx="2" fill="{c}"/>',
              f'<text x="{x+24}" y="114" font-size="17" font-weight="800" fill="#fff">{t}</text>',
              f'<text x="{x+24}" y="140" font-size="13" fill="#9aa5ba">{escape(s)}</text>']
    return shell(860, 200, "\n".join(b))

def signal_card(d):
    tiles = [("Stars", kfmt(d["stars"]), "#4f9cf9"), ("Repos", str(d["repos"]), "#a855f7"),
             ("Followers", kfmt(d["followers"]), "#22c55e"), ("Following", kfmt(d["following"]), "#22d3ee")]
    b = ['<text x="30" y="46" font-size="22" font-weight="800" fill="#fff">Profile Signal</text>',
         f'<text x="30" y="64" font-size="11" font-weight="700" fill="#8b96ab">Live GitHub stats · @{escape(USER)}</text>']
    for i, (t, v, c) in enumerate(tiles):
        x = 28 + i * 200
        b += [f'<rect x="{x}" y="84" width="184" height="88" rx="14" fill="#05080f" fill-opacity=".55" stroke="#3b6ea8" stroke-opacity=".6"/>',
              f'<text x="{x+16}" y="108" font-size="11" font-weight="700" fill="#9aa5ba">{t}</text>',
              f'<text x="{x+16}" y="145" font-size="30" font-weight="800" fill="{c}">{v}</text>',
              f'<rect x="{x+16}" y="158" width="152" height="4" rx="2" fill="#fff" fill-opacity=".12"/>',
              f'<rect x="{x+16}" y="158" width="{40+ (i*17)%90}" height="4" rx="2" fill="{c}"/>']
    return shell(840, 200, "\n".join(b))

if __name__ == "__main__":
    d = load()
    for name, fn in [("language-stack", language_card), ("highlights", highlights_card), ("profile-signal", signal_card)]:
        open(f"{OUT}/{name}.svg", "w", encoding="utf-8").write(fn(d))
        print("wrote", f"{OUT}/{name}.svg")
