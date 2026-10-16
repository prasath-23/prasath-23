#!/usr/bin/env python3
"""Generate the SVG cards used by README.md.

    python tools/build_cards.py        # writes assets/*.svg

Everything shown on the cards lives in the DATA section below: edit it, re-run.

GitHub serves repo SVGs with `Content-Security-Policy: default-src 'none';
style-src 'unsafe-inline'`, so the cards are built around three rules:
  * inline <style> and SMIL only - no scripts and no web fonts (embedded or
    linked), so text uses the same system font stacks GitHub itself uses;
  * no layout depends on exact text width - widths are estimated from Arial
    metrics with headroom, and every cursor is a trailing <tspan> that follows
    its text in whatever font the viewer has;
  * every card still reads with animation off (prefers-reduced-motion).
"""

import argparse
import os
from xml.sax.saxutils import escape

# --------------------------------------------------------------------------
# DATA
# --------------------------------------------------------------------------

NAME = "PRASATH KUMAR"
STATUS = "BUILDING AI AGENTS"
HERO_FILE = "Profile.cs"
HERO_LABEL = "var developer ="
ROLES = [
    "Backend & AI-agent engineer",
    "Prompts · retrieval · MCP · agent evaluation",
    "C# / .NET and Java backends on SQL Server + AWS",
    "After hours: an identity provider in Go",
]
SUBTITLE = "Associate Engineer, Agent Engineering @ Aptean · Coimbatore, India"
HERO_CHIPS = ["C# / .NET", "Java", "Kotlin", "Go", "SQL Server", "AWS", "AI Agents", "MCP"]

# (kind, text[, right-hand note]) - rendered as a terminal session
ABOUT = [
    ("cmd", "whoami"),
    ("out", "prasath — backend & AI-agent engineer, Coimbatore, India"),
    ("gap",),
    ("cmd", "cat now.md"),
    ("out", "Associate Engineer, Agent Engineering @ Aptean"),
    ("dim", "Building AI agents for ERP products: prompts, retrieval, MCP integrations, evals"),
    ("gap",),
    ("cmd", "cat shipped.md"),
    ("item", "ARS / Paragon routing integration, built end to end", "SQL Server → .NET API → Vue"),
    ("note", "two enterprise clients adopted the platform to use it"),
    ("item", "ShipsGo v1.2 → v2 migration, analyzed and shipped", "AWS Lambda · EventBridge"),
    ("item", "Zero-trust secrets: Parameter Store → AWS KMS", "no cleartext, fleet-wide"),
    ("item", "Account deactivation sync + forced logout", "across 5 services"),
    ("item", "240+ pull requests authored", "Azure DevOps · GitHub"),
    ("gap",),
    ("prompt",),
]

PROJECTS = {
    "alora-auth": dict(
        repo="prasath-23/Alora-Auth", lang="Go", lang_color="#00ADD8",
        title="Alora Auth",
        tagline="multi-tenant identity provider & SSO for B2B products",
        lines=[
            "Sign in once with a password, Google or company SSO, then open each product",
            "with a short-lived token of its own. Services and AI agents get tokens too.",
        ],
        detail="refresh-token rotation with reuse detection · append-only audit log · tenant isolation",
        chips=["Go", "Gin", "PostgreSQL 16", "gRPC", "OAuth2 + PKCE", "RS256 · JWKS", "Argon2id"],
    ),
    "krypt": dict(
        repo="prasath-23/Krypt", lang="Kotlin", lang_color="#A97BFF",
        title="Krypt",
        tagline="offline app locker for Android",
        lines=[
            "Locked apps open only when a trusted second",
            "person, the Guardian, approves. No internet",
            "permission: requests travel as deep links.",
        ],
        chips=["Kotlin", "Jetpack Compose", "Hilt", "Room", "Deep links"],
    ),
    "sleep-apnea": dict(
        repo="prasath-23/Sleep-apnea-detection", lang="Python", lang_color="#3572A5",
        title="Sleep Apnea Detection",
        tagline="apnea, minute by minute, from one ECG lead",
        stats=[("83.4%", "accuracy"), ("88.6%", "sensitivity"), ("16,945", "test minutes")],
        note="modified 1D LeNet-5 · after Wang et al. (PeerJ 2019)",
        chips=["Python", "TensorFlow"],
    ),
}

P, S = "production", "side"   # stack chips: used at work vs. in personal projects
STACK = [
    ("languages", [("C#", P), ("Java", P), ("Kotlin", P), ("SQL / T-SQL", P), ("JavaScript", P),
                   ("Go", S), ("Python", S)]),
    ("backend", [(".NET Core", P), ("ASP.NET", P), ("Entity Framework", P), ("Gin", S), ("gRPC", S)]),
    ("ai agents", [("Prompt engineering", P), ("Retrieval", P), ("MCP", P), ("Agent evaluation", P),
                   ("Claude Code", S)]),
    ("aws", [("Lambda", P), ("EventBridge", P), ("KMS", P), ("S3", P), ("EC2", P), ("ECR", P)]),
    ("devops", [("Terraform", P), ("Docker", P), ("Nginx", P), ("Linux", P), ("Azure DevOps", P)]),
    ("data", [("SQL Server", P), ("PostgreSQL", P), ("Redis", P)]),
    ("security", [("Zero-trust secrets", P), ("OAuth2 / OIDC", S), ("PKCE", S), ("JWT · JWKS", S),
                  ("Argon2id", S)]),
    ("observability", [("OpenTelemetry", P), ("Grafana LGTM", P), ("SonarQube", P)]),
    ("frontend", [("Vue.js", P), ("Quasar", P), ("React", S)]),
]

# --------------------------------------------------------------------------
# Look
# --------------------------------------------------------------------------

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

BG = ("#0b0f19", "#0d1117", "#070a11")
SURFACE, BORDER, HAIR = "#161b22", "#30363d", "#21262d"
TEXT, TEXT2, MUTED, FAINT = "#e6edf3", "#c9d1d9", "#8b949e", "#6e7681"
CYAN, VIOLET, PILL = "#00f2fe", "#9b51e0", "#38bdf8"
LIGHTS = ("#ff5f56", "#ffbd2e", "#27c93f")

# Arial advance widths for ASCII 32..126 in 1/1000 em. Segoe UI runs ~3% narrower,
# Verdana / DejaVu Sans ~11% wider; HEADROOM plus chip padding absorbs the spread.
_ARIAL = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]
_OTHER = {"·": 278, "•": 350, "–": 556, "—": 1000, "→": 1000}
HEADROOM = 1.06


def text_w(s, size, weight=400, spacing=0.0):
    units = sum(_ARIAL[ord(c) - 32] if 32 <= ord(c) < 127 else _OTHER.get(c, 1000) for c in s)
    bold = 1 + max(0, weight - 400) / 300 * 0.07
    return units / 1000 * size * bold * HEADROOM + spacing * len(s)


def mono_w(s, size, spacing=0.0):
    return len(s) * (size * 0.6 + spacing)


def fits(width, limit, what):
    if width > limit:
        raise ValueError(f"{what!r} is ~{width:.0f}px, over the {limit:.0f}px available")


def esc(s):
    return escape(s, {'"': "&quot;"})


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def ramp(n):
    """n accent colors running cyan -> violet."""
    return [mix(CYAN, VIOLET, i / max(1, n - 1)) for i in range(n)]


# --------------------------------------------------------------------------
# Building blocks
# --------------------------------------------------------------------------

BLINK = ".cur{animation:blink 1.1s steps(1,end) infinite}\n@keyframes blink{50%{fill-opacity:0}}\n"


def document(w, h, label, css, defs, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t">\n'
        f'<title id="t">{esc(label)}</title>\n'
        f'<style>\n.sans{{font-family:{SANS}}}\n.mono{{font-family:{MONO}}}\n{css}</style>\n'
        f'<defs>{defs}</defs>\n{body}\n</svg>\n'
    )


def frame(w, h, title, right="", hero=False):
    """Chrome shared by every card. Returns (defs, under, over)."""
    defs = (
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG[0]}"/>'
        f'<stop offset=".5" stop-color="{BG[1]}"/><stop offset="1" stop-color="{BG[2]}"/></linearGradient>'
        f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1" fill="{BORDER}" fill-opacity=".45"/></pattern>'
        f'<radialGradient id="glowA"><stop offset="0" stop-color="{CYAN}" stop-opacity=".13"/>'
        f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="glowB"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".12"/>'
        f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="clip"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15"/></clipPath>'
    )
    if hero:
        def cycle(a, b):
            return f'<animate attributeName="stop-color" values="{a};{b};{a}" dur="6s" repeatCount="indefinite"/>'
        defs += (
            f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{CYAN}">{cycle(CYAN, VIOLET)}</stop>'
            f'<stop offset="1" stop-color="{VIOLET}">{cycle(VIOLET, CYAN)}</stop></linearGradient>'
        )
        edge = (f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="none" '
                f'stroke="url(#edge)" stroke-width="1.5"/>')
    else:
        defs += (
            f'<linearGradient id="edge" gradientUnits="userSpaceOnUse" x1="24" y1="0" x2="{w - 24}" y2="0">'
            f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".3" stop-color="{CYAN}"/>'
            f'<stop offset=".7" stop-color="{VIOLET}"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/>'
            f'</linearGradient>'
        )
        edge = (f'<line x1="1" y1="55.5" x2="{w - 1}" y2="55.5" stroke="{HAIR}"/>'
                f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="none" stroke="{BORDER}"/>'
                f'<rect x="24" y=".25" width="{w - 48}" height="1.5" fill="url(#edge)"/>')
    under = (
        f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="url(#bg)"/>'
        f'<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="url(#dots)" opacity=".65"/>'
        f'<circle cx="{w - 70}" cy="30" r="{min(240, w * 0.55):.0f}" fill="url(#glowA)"/>'
        f'<circle cx="60" cy="{h - 20}" r="{min(220, w * 0.5):.0f}" fill="url(#glowB)"/></g>'
    )
    lights = "".join(f'<circle cx="{30 + 18 * i}" cy="28" r="5" fill="{c}"/>' for i, c in enumerate(LIGHTS))
    over = (lights + f'<text x="86" y="32" class="mono" font-size="12" fill="{FAINT}">{esc(title)}</text>'
            + right + edge)
    return defs, under, over


def bar_right(w, label, dot=None):
    """Right-aligned label in the window bar, with an optional colored dot."""
    x = w - 24 - mono_w(label, 12)
    out = f'<circle cx="{x - 10:.1f}" cy="28" r="4.5" fill="{dot}"/>' if dot else ""
    color = MUTED if dot else FAINT
    return out + f'<text x="{x:.1f}" y="32" class="mono" font-size="12" fill="{color}">{esc(label)}</text>'


def chip_w(label, size):
    return round(26 + text_w(label, size, 500) + 13)


def chip(x, y, label, dot, size=12.5, h=28):
    w = chip_w(label, size)
    return (
        f'<g transform="translate({x:g},{y:g})">'
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="7" fill="{SURFACE}" stroke="{BORDER}"/>'
        f'<circle cx="14" cy="{h / 2:g}" r="3" fill="{dot}"/>'
        f'<text x="24" y="{h / 2 + size * 0.35:.1f}" class="sans" font-size="{size:g}" font-weight="500" '
        f'fill="{TEXT2}">{esc(label)}</text></g>'
    )


def flow(items, x0, y0, max_w, size=12.5, h=28, gap=8):
    """Chips laid out left to right, wrapping at max_w. items: [(label, dot)]. Returns (svg, bottom)."""
    out, x, y = [], x0, y0
    for label, dot in items:
        w = chip_w(label, size)
        fits(w, max_w, label)
        if x > x0 and x + w > x0 + max_w:
            x, y = x0, y + h + gap
        out.append(chip(x, y, label, dot, size, h))
        x += w + gap
    return "".join(out), y + h


# --------------------------------------------------------------------------
# Cards
# --------------------------------------------------------------------------

def hero():
    w, h = 850, 360
    defs, under, over = frame(w, h, HERO_FILE, hero=True)
    defs += (f'<linearGradient id="name" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/>'
             f'<stop offset=".6" stop-color="#f0f6fc"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>')

    pw = round(28 + text_w(STATUS, 10.5, 600, spacing=0.8) + 18)
    pill = (
        f'<g transform="translate({w - 24 - pw},15)">'
        f'<rect x=".5" y=".5" width="{pw - 1}" height="25" rx="12.5" fill="{CYAN}" fill-opacity=".08" '
        f'stroke="{CYAN}" stroke-opacity=".3"/>'
        f'<circle class="ping" cx="16" cy="13" r="4" fill="none" stroke="{CYAN}" stroke-width="1.5"/>'
        f'<circle cx="16" cy="13" r="4" fill="{CYAN}"/>'
        f'<text x="28" y="17" class="sans" font-size="10.5" font-weight="600" letter-spacing=".8" '
        f'fill="{PILL}">{esc(STATUS)}</text></g>'
    )

    fits(text_w(NAME, 46, 800), w - 96 - pw, NAME)
    head = (
        f'<text x="48" y="104" class="mono" font-size="14" font-weight="500" letter-spacing="1" '
        f'fill="{CYAN}">{esc(HERO_LABEL)}</text>'
        f'<text x="46" y="152" class="sans" font-size="46" font-weight="800" letter-spacing="-.5" '
        f'fill="url(#name)">{esc(NAME)}</text>'
    )

    # Phrases cross-fade in turn; each carries its own cursor so it sits right
    # after the text in any font.
    roles = []
    for i, role in enumerate(ROLES):
        fits(mono_w(role + "  ▌", 15), w - 96 - 20, role)
        roles.append(f'<text class="mono role r{i}" x="20" y="0" font-size="15" font-weight="500" '
                     f'fill="{TEXT}">{esc(role)}<tspan class="cur" dx="6" fill="{CYAN}">▌</tspan></text>')
    line = (f'<g transform="translate(48,198)"><text x="0" y="0" class="mono" font-size="15" '
            f'fill="{MUTED}">&gt;</text>{"".join(roles)}</g>')

    fits(text_w(SUBTITLE, 14), w - 96, SUBTITLE)
    sub = (f'<text x="48" y="236" class="sans" font-size="14" fill="{MUTED}">{esc(SUBTITLE)}</text>'
           f'<line x1="48" y1="264.5" x2="{w - 48}" y2="264.5" stroke="{HAIR}"/>')

    gap = 10
    total = sum(chip_w(c, 12.5) for c in HERO_CHIPS) + gap * (len(HERO_CHIPS) - 1)
    fits(total, w - 96, "hero chip row")
    chips, x = [], 48
    for c, dot in zip(HERO_CHIPS, ramp(len(HERO_CHIPS))):
        chips.append(chip(x, 297, c, dot))
        x += chip_w(c, 12.5) + gap

    n, period = len(ROLES), 3.6 * len(ROLES)
    slot = 100 / n
    css = (
        ".role{opacity:0}.r0{opacity:1}.ping{opacity:0}\n"
        "@media (prefers-reduced-motion:no-preference){\n"
        f".role{{animation:roles {period:g}s ease-in-out infinite}}\n"
        + "".join(f".r{i}{{animation-delay:-{(n - i) * period / n:g}s}}\n" for i in range(1, n))
        + f"@keyframes roles{{0%{{opacity:0;transform:translateY(5px)}}"
          f"{slot * .1:.2f}%,{slot * .9:.2f}%{{opacity:1;transform:translateY(0)}}"
          f"{slot:.2f}%,100%{{opacity:0;transform:translateY(-5px)}}}}\n"
        + BLINK
        + ".ping{transform-box:fill-box;transform-origin:center;animation:ping 2.4s ease-out infinite}\n"
          "@keyframes ping{0%{transform:scale(1);opacity:.75}80%,100%{transform:scale(2.8);opacity:0}}\n"
          "}\n"
    )
    label = f"{NAME} - {ROLES[0]}. {SUBTITLE}."
    return document(w, h, label, css, defs, under + over + pill + head + line + sub + "".join(chips))


def about():
    w, size, lh = 850, 14.5, 25
    x0, xt, xr = 40, 60, 536
    rows, y, step = [], 92, 0

    def add(svg):
        nonlocal step
        rows.append(f'<g class="ln" style="animation-delay:{0.15 + step * 0.11:.2f}s">{svg}</g>')
        step += 1

    def t(x, text, color, weight=None):
        wt = f' font-weight="{weight}"' if weight else ""
        return f'<text x="{x}" y="{y}" class="mono" font-size="{size}"{wt} fill="{color}">{esc(text)}</text>'

    for kind, *a in ABOUT:
        if kind == "gap":
            y += 10
            continue
        if kind == "cmd":
            add(t(x0, "$", CYAN) + t(xt, a[0], TEXT, 600))
        elif kind in ("out", "dim"):
            fits(x0 + mono_w(a[0], size), w - 24, a[0])
            add(t(x0, a[0], TEXT2 if kind == "out" else MUTED))
        elif kind == "item":
            fits(xt + mono_w(a[0], size), xr - 12, a[0])
            fits(xr + mono_w(a[1], size), w - 24, a[1])
            add(t(x0, "•", VIOLET) + t(xt, a[0], TEXT2) + t(xr, a[1], MUTED))
        elif kind == "note":
            add(t(xt, a[0], MUTED))
        elif kind == "prompt":
            add(f'<text x="{x0}" y="{y}" class="mono" font-size="{size}"><tspan fill="{CYAN}">$</tspan>'
                f'<tspan class="cur" dx="10" fill="{CYAN}">▌</tspan></text>')
        y += lh
    h = y - lh + 30

    defs, under, over = frame(w, h, "prasath@github: ~", bar_right(w, "bash"))
    css = ("@media (prefers-reduced-motion:no-preference){\n"
           ".ln{animation:ln .5s ease-out backwards}\n@keyframes ln{from{opacity:0;transform:translateX(-6px)}}\n"
           + BLINK + "}\n")
    said = "; ".join(" - ".join(a) for kind, *a in ABOUT if kind in ("out", "dim", "item", "note"))
    return document(w, h, f"About Prasath: {said}.", css, defs, under + over + "".join(rows))


def project(p, w, fixed_h=None):
    """A repo card; returns (svg, natural height)."""
    wide = w >= 600
    x0, inner = 28, w - 56
    out, y = [], 100
    title_size, tag_size, body_size = (28, 13.5, 15) if wide else (24, 12.5, 14)

    fits(text_w(p["title"], title_size, 700), inner, p["title"])
    out.append(f'<text x="{x0}" y="{y}" class="sans" font-size="{title_size}" font-weight="700" '
               f'fill="{TEXT}">{esc(p["title"])}</text>')
    y += 28
    fits(mono_w(p["tagline"], tag_size), inner, p["tagline"])
    out.append(f'<text x="{x0}" y="{y}" class="mono" font-size="{tag_size}" fill="{CYAN}">{esc(p["tagline"])}</text>')
    y += 10
    for text in p.get("lines", []):
        y += 23 if wide else 22
        fits(text_w(text, body_size), inner, text)
        out.append(f'<text x="{x0}" y="{y}" class="sans" font-size="{body_size}" fill="{TEXT2}">{esc(text)}</text>')
    if "detail" in p:
        y += 26
        fits(mono_w(p["detail"], 12.5), inner, p["detail"])
        out.append(f'<text x="{x0}" y="{y}" class="mono" font-size="12.5" fill="{MUTED}">{esc(p["detail"])}</text>')
    if "stats" in p:
        y += 16
        tile = (inner - 16) / 3
        for k, (num, what) in enumerate(p["stats"]):
            fits(text_w(num, 20, 700) + 24, tile, num)
            out.append(
                f'<g transform="translate({x0 + k * (tile + 8):.1f},{y})">'
                f'<rect x=".5" y=".5" width="{tile - 1:.1f}" height="55" rx="8" fill="{SURFACE}" '
                f'fill-opacity=".75" stroke="{BORDER}"/>'
                f'<text x="12" y="27" class="sans" font-size="20" font-weight="700" fill="{TEXT}">{esc(num)}</text>'
                f'<text x="12" y="45" class="sans" font-size="11" fill="{MUTED}">{esc(what)}</text></g>')
        y += 56
    if "note" in p:
        y += 22
        fits(mono_w(p["note"], 11), inner, p["note"])
        out.append(f'<text x="{x0}" y="{y}" class="mono" font-size="11" fill="{MUTED}">{esc(p["note"])}</text>')
    chips, bottom = flow(list(zip(p["chips"], ramp(len(p["chips"])))), x0, y + 20, inner)
    natural = bottom + 26
    h = max(natural, fixed_h or 0)

    right = bar_right(w, p["lang"], p["lang_color"])
    fits(86 + mono_w(p["repo"], 12), w - 24 - mono_w(p["lang"], 12) - 24, p["repo"])
    defs, under, over = frame(w, h, p["repo"], right)
    said = ". ".join([p["tagline"]] + p.get("lines", []) + [p.get("detail", ""), p.get("note", "")]).strip(". ")
    label = f'{p["title"]} ({p["lang"]}): {said}.'
    return document(w, h, label, "", defs, under + over + "".join(out) + chips), natural


def stack():
    w, x0, xc = 850, 32, 170
    inner = w - xc - 32
    out, y = [], 80
    for label, items in STACK:
        fits(x0 + mono_w(label.upper(), 11.5, 1), xc - 12, label)
        out.append(f'<text x="{x0}" y="{y + 18}" class="mono" font-size="11.5" letter-spacing="1" '
                   f'fill="{MUTED}">{esc(label.upper())}</text>')
        svg, bottom = flow([(name, CYAN if kind == P else VIOLET) for name, kind in items], xc, y, inner)
        out.append(svg)
        y = bottom + 12
    h = y + 16

    # legend, right-aligned in the window bar
    keys, x = [], w - 24
    for text, dot in (("side projects", VIOLET), ("used at work", CYAN)):
        x -= mono_w(text, 12)
        keys.append(f'<circle cx="{x - 10:.1f}" cy="28" r="4" fill="{dot}"/>'
                    f'<text x="{x:.1f}" y="32" class="mono" font-size="12" fill="{MUTED}">{text}</text>')
        x -= 32
    defs, under, over = frame(w, h, "stack.yml", "".join(keys))
    work = ", ".join(n for _, items in STACK for n, k in items if k == P)
    side = ", ".join(n for _, items in STACK for n, k in items if k == S)
    label = f"Tech stack. Used at work: {work}. In side projects: {side}."
    return document(w, h, label, "", defs, under + over + "".join(out))


# --------------------------------------------------------------------------

def main():
    global SANS, MONO
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(here, "..", "assets"), help="output folder")
    ap.add_argument("--sans", help="override the sans font stack (for testing)")
    ap.add_argument("--mono", help="override the monospace font stack (for testing)")
    args = ap.parse_args()
    SANS, MONO = args.sans or SANS, args.mono or MONO

    alora, _ = project(PROJECTS["alora-auth"], 850)
    halves = [PROJECTS["krypt"], PROJECTS["sleep-apnea"]]
    tallest = max(project(p, 420)[1] for p in halves)
    cards = {
        "hero.svg": hero(),
        "about.svg": about(),
        "project-alora-auth.svg": alora,
        "project-krypt.svg": project(halves[0], 420, tallest)[0],
        "project-sleep-apnea.svg": project(halves[1], 420, tallest)[0],
        "stack.svg": stack(),
    }
    os.makedirs(args.out, exist_ok=True)
    for name, svg in cards.items():
        with open(os.path.join(args.out, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
        print(f"{name:<26} {len(svg.encode()):>6} bytes")


if __name__ == "__main__":
    main()
