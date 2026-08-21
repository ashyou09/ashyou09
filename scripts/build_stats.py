#!/usr/bin/env python3
"""
Render assets/stats.svg from live GitHub data.

Third-party README stat services (github-readme-stats, streak-stats) were both
returning 503 when this profile was built, which is exactly the broken-widget
look this page is trying to avoid. Generating the panel here and committing the
result means the profile renders from this repo alone and cannot go down; the
workflow in .github/workflows/stats.yml keeps the numbers fresh.

Language share is counted by *primary language per repository*, not by bytes.
Byte counts are dominated by whichever repo happens to vendor the most code and
misrepresent what the work actually is.
"""

import collections
import json
import os
import urllib.request

USER = "ashyou09"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "stats.svg")

BG, LINE, FG, FG_2, FG_3, ACCENT = (
    "#0a0b0d", "#ffffff", "#e9eaec", "#9ca2ac", "#6a707a", "#f0a22e",
)

# GitHub linguist colours, so the bar matches what people see on repo pages.
LANG_COLOUR = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#663399",
    "Rust": "#dea584",
    "Jupyter Notebook": "#DA5B0B",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "Shell": "#89e051",
}


def api(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "profile-stats",
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
               if os.environ.get("GITHUB_TOKEN") else {}),
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def collect():
    user = api(f"https://api.github.com/users/{USER}")
    repos = [r for r in api(f"https://api.github.com/users/{USER}/repos?per_page=100")
             if not r.get("fork")]
    langs = collections.Counter(r["language"] for r in repos if r["language"])
    return {
        "repos": len(repos),
        "stars": sum(r["stargazers_count"] for r in repos),
        "followers": user["followers"],
        "langs": langs.most_common(6),
    }


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(d):
    W, H = 1200, 190
    mono = "ui-monospace, 'SF Mono', 'DejaVu Sans Mono', Menlo, monospace"
    sans = "'Helvetica Neue', Helvetica, Arial, sans-serif"
    p = []

    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="GitHub statistics">'
    )
    p.append(
        '<defs><pattern id="g" width="30" height="30" patternUnits="userSpaceOnUse">'
        f'<circle cx="1" cy="1" r="1" fill="{LINE}" fill-opacity="0.045"/></pattern>'
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath></defs>'
    )
    p.append(f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{BG}"/>')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#g)"/>')

    p.append(
        f'<text x="72" y="46" font-family="{mono}" font-size="12" letter-spacing="4.4" '
        f'fill="{ACCENT}">AT A GLANCE</text>'
    )

    # ── left: headline numbers ──
    for i, (value, label) in enumerate(
        [(d["repos"], "public repos"), (d["stars"], "stars earned"), (d["followers"], "followers")]
    ):
        x = 72 + i * 168
        p.append(
            f'<text x="{x}" y="118" font-family="{sans}" font-size="44" font-weight="600" '
            f'letter-spacing="-1.6" fill="{FG}">{value}</text>'
        )
        p.append(
            f'<text x="{x}" y="144" font-family="{mono}" font-size="11.5" '
            f'fill="{FG_3}">{esc(label)}</text>'
        )

    # ── right: language share, by primary language per repo ──
    bx, bw, by = 640, 488, 84
    p.append(
        f'<text x="{bx}" y="46" font-family="{mono}" font-size="12" letter-spacing="4.4" '
        f'fill="{ACCENT}">LANGUAGES</text>'
    )

    total = sum(n for _, n in d["langs"]) or 1
    x = bx
    for name, n in d["langs"]:
        seg = bw * n / total
        p.append(
            f'<rect x="{x:.1f}" y="{by}" width="{max(seg - 2, 1):.1f}" height="12" rx="6" '
            f'fill="{LANG_COLOUR.get(name, ACCENT)}" fill-opacity="0.92"/>'
        )
        x += seg

    for i, (name, n) in enumerate(d["langs"]):
        col, row = i % 3, i // 3
        lx, ly = bx + col * 166, 126 + row * 24
        p.append(f'<circle cx="{lx + 4}" cy="{ly - 4}" r="4" fill="{LANG_COLOUR.get(name, ACCENT)}"/>')
        p.append(
            f'<text x="{lx + 16}" y="{ly}" font-family="{mono}" font-size="11.5" fill="{FG_2}">'
            f'{esc(name)} <tspan fill="{FG_3}">{100 * n / total:.0f}%</tspan></text>'
        )

    p.append(f'<rect width="{W}" height="{H}" rx="16" fill="none" stroke="{LINE}" stroke-opacity="0.09"/>')
    p.append("</g></svg>")
    return "\n".join(p)


if __name__ == "__main__":
    data = collect()
    with open(OUT, "w") as fh:
        fh.write(render(data) + "\n")
    print("wrote", os.path.normpath(OUT), data)
