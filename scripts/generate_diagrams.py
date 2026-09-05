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

Text handling (so nothing gets cut off awkwardly):
  * short_phrase() trims each DB field to a complete phrase at a natural
    boundary (comma, em dash, semicolon) rather than a hard character cut.
  * fit_text() shrinks the font just enough to fit its box, so long phrases
    stay fully visible instead of being truncated with an ellipsis.

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
W, H = 900, 340

# Panel geometry: left edge, width, centre, right edge, text-left, text-width
PL = [28, 308, 588]          # panel left edges
PW = 244                     # panel width
PC = [pl + PW // 2 for pl in PL]   # panel centres -> [150, 430, 710]
PR = [pl + PW for pl in PL]        # panel right edges
TX = [pl + 30 for pl in PL]        # text left edges -> [58, 338, 618]
TW = 196                     # usable text width (px)
PANEL_TOP = 96
PANEL_BOT = 332

# Average glyph advance as a fraction of font size (slightly generous so text
# never overruns the right edge). Used to estimate characters-per-line.
CHAR_W = 0.55


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


def short_phrase(text, max_len=120):
    """Trim a long field to a complete-reading phrase.

    Keeps the first sentence; if that's still too long, cuts at the last
    natural boundary (em dash, comma, semicolon, colon) before max_len so the
    result reads as a finished thought. Only falls back to a word-boundary cut
    with an ellipsis when no punctuation boundary is available.
    """
    if not text:
        return ""
    s = text.split(". ")[0].strip()
    if len(s) <= max_len:
        return s.rstrip(".")
    boundary = -1
    for d in ("—", "; ", ", ", ": "):
        i = s.rfind(d, 0, max_len)
        if i > boundary:
            boundary = i
    if boundary >= 45:                      # a boundary that leaves a real phrase
        return s[:boundary].rstrip(" ,;:—")
    return s[:max_len].rsplit(" ", 1)[0].rstrip(" ,;:—") + "…"


def fit_text(text, x, y_top, box_w, box_h, color, weight,
             max_font=13.0, min_font=9.5, anchor="start"):
    """Render text shrunk just enough to fit inside (box_w x box_h).

    Tries progressively smaller fonts until the wrapped text fits the box; only
    at the minimum size (a near-impossible case for our trimmed phrases) does it
    fall back to truncating with an ellipsis.
    """
    if not text:
        return ""
    font = max_font
    while font >= min_font:
        cpl = max(6, int(box_w / (CHAR_W * font)))
        lh = font * 1.3
        lines = wrap(text, cpl)
        if len(lines) * lh <= box_h:
            break
        font -= 0.5
    else:
        font = min_font
        cpl = max(6, int(box_w / (CHAR_W * font)))
        lh = font * 1.3
        lines = wrap(text, cpl)
        max_lines = max(1, int(box_h / lh))
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip(" ,;:—") + "…"

    y0 = y_top + font                        # first baseline sits just below top
    out = [f'<text x="{x}" y="{y0:.1f}" text-anchor="{anchor}" '
           f'style="font-size:{font:.1f}px;font-weight:{weight};fill:{color};">']
    for i, ln in enumerate(lines):
        dy = 0 if i == 0 else lh
        out.append(f'<tspan x="{x}" dy="{dy:.1f}">{esc(ln)}</tspan>')
    out.append("</text>")
    return "\n".join(out)


# --- Line-art motifs --------------------------------------------------------
# All motifs are stroke-only line art centred on (cx, cy), sized to sit inside
# a ~90px circle. Consistent 1.6px accent strokes keep the visual language calm.
STROKE = f'fill="none" stroke="{ACCENT}" stroke-width="1.6" ' \
         f'stroke-linecap="round" stroke-linejoin="round"'


def motif_attach(cx, cy):
    # Hierarchical fibres branching from a pad (gecko setae -> spatulae)
    top = cy - 30
    parts = [f'<line x1="{cx-38}" y1="{top}" x2="{cx+38}" y2="{top}" {STROKE}/>']
    for bx in (cx - 24, cx, cx + 24):
        midy = top + 22
        parts.append(f'<line x1="{bx}" y1="{top}" x2="{bx}" y2="{midy}" {STROKE}/>')
        for dx in (-10, 10):
            tipx, tipy = bx + dx, midy + 20
            parts.append(f'<line x1="{bx}" y1="{midy}" x2="{tipx}" y2="{tipy}" {STROKE}/>')
            parts.append(f'<line x1="{tipx-4}" y1="{tipy}" x2="{tipx+4}" y2="{tipy}" {STROKE}/>')
    return "".join(parts)


def motif_move(cx, cy):
    # Streamlined profile with laminar flow lines
    body = (f'<path d="M {cx-42} {cy} C {cx-28} {cy-24}, {cx+16} {cy-20}, {cx+46} {cy} '
            f'C {cx+16} {cy+20}, {cx-28} {cy+24}, {cx-42} {cy} Z" {STROKE}/>')
    flow = "".join(
        f'<path d="M {cx-54} {cy+dy} C {cx-18} {cy+dy//2}, {cx+18} {cy+dy//2}, {cx+54} {cy+dy}" '
        f'{STROKE} opacity="0.55"/>'
        for dy in (-30, 30)
    )
    return body + flow


def motif_make(cx, cy):
    # Offset stacked plates (nacre / laminated composite), light isometric skew
    parts = []
    for i in range(4):
        y = cy - 26 + i * 18
        sx = cx - 42 + (i % 2) * 10
        parts.append(f'<path d="M {sx} {y} l 64 0 l 12 -9 l -64 0 z" {STROKE}/>')
    return "".join(parts)


def motif_modify(cx, cy):
    # Structured surface with a high-contact-angle droplet resting on it
    surf = (f'<path d="M {cx-48} {cy+26} '
            + " ".join("q 6 -15 12 0" for _ in range(8))
            + f'" {STROKE}/>')
    drop = (f'<path d="M {cx} {cy-16} C {cx+20} {cy-7}, {cx+20} {cy+16}, {cx} {cy+16} '
            f'C {cx-20} {cy+16}, {cx-20} {cy-7}, {cx} {cy-16} Z" {STROKE}/>')
    return surf + drop


def motif_process(cx, cy):
    # Two curved arrows forming a cycle (resource processing / efficiency loop)
    a1 = (f'<path d="M {cx+28} {cy-13} A 28 28 0 1 1 {cx-22} {cy+16}" {STROKE}/>'
          f'<path d="M {cx+28} {cy-13} l 3 -12 l -11 4" {STROKE}/>')
    a2 = (f'<path d="M {cx-28} {cy+13} A 28 28 0 1 1 {cx+22} {cy-16}" {STROKE}/>'
          f'<path d="M {cx-28} {cy+13} l -3 12 l 11 -4" {STROKE}/>')
    return a1 + a2


def motif_protect(cx, cy):
    # Minimal shield with an inner layer arc
    shield = (f'<path d="M {cx} {cy-34} L {cx+27} {cy-23} L {cx+27} {cy+2} '
              f'C {cx+27} {cy+22}, {cx+14} {cy+31}, {cx} {cy+36} '
              f'C {cx-14} {cy+31}, {cx-27} {cy+22}, {cx-27} {cy+2} '
              f'L {cx-27} {cy-23} Z" {STROKE}/>')
    arc = f'<path d="M {cx-16} {cy-7} C {cx-5} {cy-1}, {cx+5} {cy-1}, {cx+16} {cy-7}" {STROKE} opacity="0.6"/>'
    return shield + arc


def motif_sense(cx, cy):
    # Concentric wavefronts radiating from a source (detection / navigation)
    src = f'<circle cx="{cx}" cy="{cy+20}" r="3" fill="{ACCENT}"/>'
    waves = "".join(
        f'<path d="M {cx-r*0.78:.0f} {cy+20} A {r} {r} 0 0 1 {cx+r*0.78:.0f} {cy+20}" '
        f'{STROKE} opacity="{1 - i*0.22:.2f}"/>'
        for i, r in enumerate((15, 28, 41, 54))
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


def step_label(x, y, num, word):
    """Numbered step label, e.g. '01 ORGANISM' — accent number, muted word."""
    return (f'<text x="{x}" y="{y}" class="step">'
            f'<tspan class="num">{num}</tspan>'
            f'<tspan dx="8" class="word">{esc(word)}</tspan></text>')


# --- Build one figure -------------------------------------------------------
def build_svg(row):
    group = row["biomimicry_taxonomy_group"] or "Sense"
    motif_fn = MOTIFS.get(group, motif_sense)

    organism = row["organism"] or ""
    principle = row["key_principle"] or ""
    application = row["human_application"] or ""
    # First named product only; drop a trailing "(source)" so it can't be left
    # dangling by the comma split (e.g. "HygroSkin pavilion (Achim Menges").
    product = (row["real_world_products"] or "").split(",")[0].split(" (")[0].strip()

    label_y = PANEL_TOP + 24            # 120
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
    </style>''')

    # Card
    s.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" '
             f'fill="{BG}" stroke="{HAIR}"/>')

    # Header row + hairline
    s.append('<text x="40" y="44" class="kicker">BIOMIMICRY MECHANISM</text>')
    s.append(f'<circle cx="{W-40-len(group)*8-16}" cy="40" r="3" fill="{ACCENT}"/>')
    s.append(f'<text x="{W-40}" y="44" class="group" text-anchor="end">{esc(group.upper())}</text>')
    s.append(f'<line x1="40" y1="64" x2="{W-40}" y2="64" stroke="{HAIR}"/>')

    # Connector chevrons between steps
    s.append(chevron((PR[0] + PL[1]) // 2, 214))
    s.append(chevron((PR[1] + PL[2]) // 2, 214))

    # --- Step 1: ORGANISM ---
    s.append(step_label(TX[0], label_y, "01", "ORGANISM"))
    s.append(fit_text(organism, TX[0], 132, TW, 46, INK, 700, max_font=16.5, min_font=12.5))
    s.append(fit_text(short_phrase(row["biological_function"], 115),
                      TX[0], 186, TW, 134, MUTED, 400, max_font=12.5, min_font=9.5))

    # --- Step 2: MECHANISM (line-art motif) ---
    s.append(step_label(TX[1], label_y, "02", "MECHANISM"))
    s.append(f'<circle cx="{PC[1]}" cy="176" r="46" fill="{WASH}"/>')
    s.append(motif_fn(PC[1], 176))
    s.append(fit_text(short_phrase(principle, 130),
                      TX[1], 228, TW, 96, MUTED, 400, max_font=12.0, min_font=9.5))

    # --- Step 3: APPLICATION ---
    s.append(step_label(TX[2], label_y, "03", "APPLICATION"))
    s.append(fit_text(short_phrase(application, 120),
                      TX[2], 132, TW, 118, INK, 600, max_font=13.0, min_font=9.5))
    if product:
        s.append(fit_text("Real-world: " + product, TX[2], 260, TW, 50,
                          FAINT, 400, max_font=11.0, min_font=8.5))

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
