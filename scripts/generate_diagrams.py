"""
generate_diagrams.py
=====================

Generates an original SVG "mechanism figure" for every strategy in the
database, in a clean editorial / scientific-figure style.

Each figure reads left-to-right as a three-step flow:

    01 ORGANISM  ->  02 MECHANISM  ->  03 APPLICATION

The centre step carries a fine line-art "motif" chosen by the strategy's
biomimicry_taxonomy_group (Attach, Move, Make, Modify, Process, Protect,
Sense), so the seven families stay visually distinct.

Every shape is drawn from scratch, so the figures are 100% original work
with no copyright or licensing concerns.

Output: static/images/diagrams/<slug>.svg  (one per strategy)

Run from the project root:

    py scripts/generate_diagrams.py
"""

import os
import sqlite3

# --- Paths -----------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB_PATH = os.path.join(ROOT, "database", "biomimicry.db")
OUT_DIR = os.path.join(ROOT, "static", "images", "diagrams")

# --- Palette (restrained: ink + muted greys + one green accent) ------------
ACCENT = "#2d6a4f"   # site green, used sparingly
INK = "#1a1a1a"      # primary text
MUTED = "#5b5b5b"    # secondary text
FAINT = "#8a8a8a"    # labels / captions
HAIR = "#e7e7e7"     # hairlines / borders
WASH = "#f6f8f6"     # very light ground for the motif
BG = "#ffffff"

# Drawing canvas (scales responsively via width="100%")
W, H = 900, 320

# Column geometry
COLS = [186, 450, 714]          # x-centre of each step
COL_X = [58, 348, 612]          # left text edge of each step
COL_W = 232                     # usable text width per step


# --- Small helpers ----------------------------------------------------------
def esc(text):
    """Escape XML special characters so text is safe inside SVG."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def wrap(text, max_chars):
    """Greedy word-wrap into lines no longer than max_chars."""
    words = (text or "").split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if len(candidate) <= max_chars:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def tspans(text, x, y, max_chars, line_height, max_lines, cls, anchor="start"):
    """Render wrapped text as stacked <tspan> lines, truncating with an ellipsis."""
    lines = wrap(text, max_chars)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,;") + "…"
    out = [f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">']
    for i, ln in enumerate(lines):
        dy = 0 if i == 0 else line_height
        out.append(f'<tspan x="{x}" dy="{dy}">{esc(ln)}</tspan>')
    out.append("</text>")
    return "\n".join(out)


def first_clause(text, max_len=120):
    """A short, single-clause snippet from a longer field."""
    if not text:
        return ""
    snippet = text.split(". ")[0].strip()
    if len(snippet) > max_len:
        snippet = snippet[:max_len].rsplit(" ", 1)[0] + "…"
    return snippet


# --- Line-art motifs --------------------------------------------------------
# All motifs are stroke-only line art centred on (cx, cy), sized to sit inside
# a ~112px circle. Consistent 1.6px accent strokes keep the visual language calm.
STROKE = f'fill="none" stroke="{ACCENT}" stroke-width="1.6" ' \
         f'stroke-linecap="round" stroke-linejoin="round"'


def motif_attach(cx, cy):
    # Hierarchical fibres branching from a pad (gecko setae -> spatulae)
    top = cy - 34
    parts = [f'<line x1="{cx-40}" y1="{top}" x2="{cx+40}" y2="{top}" {STROKE}/>']
    for bx in (cx - 26, cx, cx + 26):
        midy = top + 26
        parts.append(f'<line x1="{bx}" y1="{top}" x2="{bx}" y2="{midy}" {STROKE}/>')
        for dx in (-11, 11):
            tipx, tipy = bx + dx, midy + 24
            parts.append(f'<line x1="{bx}" y1="{midy}" x2="{tipx}" y2="{tipy}" {STROKE}/>')
            parts.append(f'<line x1="{tipx-4}" y1="{tipy}" x2="{tipx+4}" y2="{tipy}" {STROKE}/>')
    return "".join(parts)


def motif_move(cx, cy):
    # Streamlined profile with laminar flow lines
    body = (f'<path d="M {cx-46} {cy} C {cx-30} {cy-26}, {cx+18} {cy-22}, {cx+50} {cy} '
            f'C {cx+18} {cy+22}, {cx-30} {cy+26}, {cx-46} {cy} Z" {STROKE}/>')
    flow = "".join(
        f'<path d="M {cx-60} {cy+dy} C {cx-20} {cy+dy//2}, {cx+20} {cy+dy//2}, {cx+60} {cy+dy}" '
        f'{STROKE} opacity="0.55"/>'
        for dy in (-34, 34)
    )
    return body + flow


def motif_make(cx, cy):
    # Offset stacked plates (nacre / laminated composite), light isometric skew
    parts = []
    for i in range(4):
        y = cy - 30 + i * 20
        sx = cx - 46 + (i % 2) * 12
        parts.append(
            f'<path d="M {sx} {y} l 70 0 l 14 -10 l -70 0 z" {STROKE}/>'
        )
    return "".join(parts)


def motif_modify(cx, cy):
    # Structured surface with a high-contact-angle droplet resting on it
    surf = (f'<path d="M {cx-52} {cy+28} '
            + " ".join(f"q 6.5 -16 13 0" for _ in range(8))
            + f'" {STROKE}/>')
    drop = (f'<path d="M {cx} {cy-18} C {cx+22} {cy-8}, {cx+22} {cy+18}, {cx} {cy+18} '
            f'C {cx-22} {cy+18}, {cx-22} {cy-8}, {cx} {cy-18} Z" {STROKE}/>')
    return surf + drop


def motif_process(cx, cy):
    # Two curved arrows forming a cycle (resource processing / efficiency loop)
    a1 = (f'<path d="M {cx+30} {cy-14} A 30 30 0 1 1 {cx-24} {cy+18}" {STROKE}/>'
          f'<path d="M {cx+30} {cy-14} l 3 -13 l -12 4" {STROKE}/>')
    a2 = (f'<path d="M {cx-30} {cy+14} A 30 30 0 1 1 {cx+24} {cy-18}" {STROKE}/>'
          f'<path d="M {cx-30} {cy+14} l -3 13 l 12 -4" {STROKE}/>')
    return a1 + a2


def motif_protect(cx, cy):
    # Minimal shield with an inner layer arc
    shield = (f'<path d="M {cx} {cy-38} L {cx+30} {cy-26} L {cx+30} {cy+2} '
              f'C {cx+30} {cy+24}, {cx+16} {cy+34}, {cx} {cy+40} '
              f'C {cx-16} {cy+34}, {cx-30} {cy+24}, {cx-30} {cy+2} '
              f'L {cx-30} {cy-26} Z" {STROKE}/>')
    arc = f'<path d="M {cx-18} {cy-8} C {cx-6} {cy-2}, {cx+6} {cy-2}, {cx+18} {cy-8}" {STROKE} opacity="0.6"/>'
    return shield + arc


def motif_sense(cx, cy):
    # Concentric wavefronts radiating from a source (detection / navigation)
    src = f'<circle cx="{cx}" cy="{cy+22}" r="3.2" fill="{ACCENT}"/>'
    waves = "".join(
        f'<path d="M {cx-r*0.78} {cy+22} A {r} {r} 0 0 1 {cx+r*0.78} {cy+22}" '
        f'{STROKE} opacity="{1 - i*0.22:.2f}"/>'
        for i, r in enumerate((16, 30, 44, 58))
    )
    return waves + src


MOTIFS = {
    "Attach": motif_attach,
    "Move": motif_move,
    "Make": motif_make,
    "Modify": motif_modify,
    "Process": motif_process,
    "Protect": motif_protect,
    "Sense": motif_sense,
}


def chevron(x, y):
    """A subtle right-pointing connector between two steps."""
    return (f'<path d="M {x-5} {y-7} L {x+5} {y} L {x-5} {y+7}" '
            f'fill="none" stroke="{FAINT}" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="0.75"/>')


def step_label(x, num, word):
    """Numbered step label, e.g. '01 ORGANISM' — accent number, muted word."""
    return (f'<text x="{x}" y="90" class="step">'
            f'<tspan class="num">{num}</tspan>'
            f'<tspan dx="8" class="word">{esc(word)}</tspan></text>')


# --- Build one figure -------------------------------------------------------
def build_svg(row):
    group = row["biomimicry_taxonomy_group"] or "Sense"
    motif_fn = MOTIFS.get(group, motif_sense)

    organism = row["organism"] or ""
    principle = row["key_principle"] or ""
    application = row["human_application"] or ""
    product = (row["real_world_products"] or "").split(",")[0].strip()

    s = []
    s.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'role="img" width="100%" style="max-width:{W}px;height:auto;font-family:'
        f'ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">'
    )
    s.append(f'''<style>
      .kicker {{ font-size:11px; font-weight:600; letter-spacing:.16em; fill:{FAINT}; }}
      .group  {{ font-size:11px; font-weight:600; letter-spacing:.14em; fill:{ACCENT}; }}
      .step   {{ font-size:11px; font-weight:600; letter-spacing:.12em; }}
      .step .num  {{ fill:{ACCENT}; }}
      .step .word {{ fill:{FAINT}; }}
      .name   {{ font-size:17px; font-weight:700; fill:{INK}; }}
      .lead   {{ font-size:13.5px; font-weight:600; fill:{INK}; }}
      .body   {{ font-size:12.5px; font-weight:400; fill:{MUTED}; }}
      .cap    {{ font-size:11.5px; font-weight:400; fill:{FAINT}; }}
    </style>''')

    # Card
    s.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" '
             f'fill="{BG}" stroke="{HAIR}"/>')

    # Header row + hairline
    s.append(f'<text x="40" y="44" class="kicker">BIOMIMICRY MECHANISM</text>')
    s.append(f'<circle cx="{W-40-len(group)*8-16}" cy="40" r="3" fill="{ACCENT}"/>')
    s.append(f'<text x="{W-40}" y="44" class="group" text-anchor="end">{esc(group.upper())}</text>')
    s.append(f'<line x1="40" y1="60" x2="{W-40}" y2="60" stroke="{HAIR}"/>')

    # Connector chevrons between steps
    s.append(chevron(300, 150))
    s.append(chevron(590, 150))

    # --- Step 1: ORGANISM ---
    s.append(step_label(COL_X[0], "01", "ORGANISM"))
    s.append(tspans(organism, COL_X[0], 124, 24, 21, 2, "name"))
    s.append(tspans(first_clause(row["biological_function"], 150),
                    COL_X[0], 176, 34, 18, 4, "body"))

    # --- Step 2: MECHANISM (line-art motif) ---
    s.append(step_label(COL_X[1], "02", "MECHANISM"))
    s.append(f'<circle cx="{COLS[1]}" cy="150" r="58" fill="{WASH}"/>')
    s.append(motif_fn(COLS[1], 150))
    s.append(tspans(first_clause(principle, 150),
                    COL_X[1], 240, 34, 17, 3, "body"))

    # --- Step 3: APPLICATION ---
    s.append(step_label(COL_X[2], "03", "APPLICATION"))
    s.append(tspans(first_clause(application, 150),
                    COL_X[2], 124, 32, 19, 4, "lead"))
    if product:
        s.append(tspans("Real-world: " + product, COL_X[2], 214, 34, 16, 3, "cap"))

    s.append("</svg>")
    return "\n".join(s)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM strategies ORDER BY id").fetchall()

    count = 0
    for row in rows:
        with open(os.path.join(OUT_DIR, f"{row['slug']}.svg"), "w", encoding="utf-8") as f:
            f.write(build_svg(row))
        count += 1

    conn.close()
    print(f"Wrote {count} diagrams to static/images/diagrams/")


if __name__ == "__main__":
    main()
