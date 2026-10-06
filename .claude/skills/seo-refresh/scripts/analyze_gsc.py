"""
analyze_gsc.py — Parse a Google Search Console Performance export and diagnose
SEO opportunities for the Biomimicry Hub site.

Finds the newest export in ~/Downloads automatically, compares it against the
stored baseline history, and flags the recurring problem patterns.

Usage:
  py .claude/skills/seo-refresh/scripts/analyze_gsc.py
  py .claude/skills/seo-refresh/scripts/analyze_gsc.py --export <path.xlsx>
  py .claude/skills/seo-refresh/scripts/analyze_gsc.py --save      # record this run
"""

import glob
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl missing. Install with:  py -m pip install openpyxl")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CONTENT = os.path.join(REPO, "content")
HISTORY = os.path.join(REPO, "data", "seo-baseline.json")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

# Tuning thresholds for the diagnostic patterns.
THIN_WORDS = 400                   # below this a page counts as thin
PAGE2_MIN, PAGE2_MAX = 10.5, 30    # ranked just off page 1
CTR_POS_MAX = 10.5                 # on page 1
MIN_IMPRESSIONS = 8                # ignore noise below this


def newest_export(explicit=None):
    if explicit:
        return explicit
    hits = glob.glob(os.path.join(DOWNLOADS, "*Performance-on-Search*.xlsx"))
    if not hits:
        sys.exit("No GSC export found in " + DOWNLOADS +
                 "\nSearch Console > Performance > Export > Download XLSX")
    return max(hits, key=os.path.getmtime)


def load(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    return {ws.title: [r for r in ws.iter_rows(min_row=2, values_only=True)
                       if r and r[0] is not None] for ws in wb.worksheets}


def norm(url):
    return re.sub(r"^https?://biomimicry-hub\.com", "", url or "")


def totals(data):
    clicks = impressions = 0
    for r in data.get("Devices", []):
        clicks += r[1] or 0
        impressions += r[2] or 0
    return clicks, impressions


def weighted_position(data):
    rows = data.get("Pages", [])
    tot = sum(r[2] or 0 for r in rows)
    return sum((r[4] or 0) * (r[2] or 0) for r in rows) / tot if tot else 0


def word_count(path):
    if not path or not os.path.exists(path):
        return None
    body = open(path, encoding="utf-8").read()
    body = re.sub(r"^\+\+\+.*?\+\+\+", "", body, flags=re.S)   # strip front matter
    return len(body.split())


def local_file(page_path):
    """Map a site URL path back to its markdown source."""
    parts = [p for p in page_path.split("/") if p]
    if len(parts) != 2:
        return None
    section, slug = parts
    return os.path.join(CONTENT, section, slug + ".md")


def main():
    args = sys.argv[1:]
    explicit = args[args.index("--export") + 1] if "--export" in args else None
    export = newest_export(explicit)
    data = load(export)
    clicks, impressions = totals(data)
    pos = weighted_position(data)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(export))
    label = m.group(1) if m else "current"

    print("GSC export: " + os.path.basename(export) + "\n")
    print("=" * 64)
    ctr = clicks / impressions * 100 if impressions else 0
    print("  Impressions %6d   Clicks %4d   CTR %.2f%%   Pos %.1f"
          % (impressions, clicks, ctr, pos))

    history = []
    if os.path.exists(HISTORY):
        history = json.load(open(HISTORY, encoding="utf-8")).get("runs", [])
    # Compare against the most recent run from a *different* date, so re-running
    # --save on the same export doesn't produce a meaningless self-comparison.
    prior = [r for r in history if r["date"] != label]
    if prior:
        prev = prior[-1]
        print("\n  vs %s:  impressions %+d   clicks %+d   position %+.1f"
              % (prev["date"], impressions - prev["impressions"],
                 clicks - prev["clicks"], pos - prev["position"]))
    print("=" * 64)

    pages = {norm(r[0]): r for r in data.get("Pages", [])}
    queries = data.get("Queries", [])

    # --- pattern 1: thin pages ranking just off page 1 ----------------------
    print("\n[1] DEEPEN - real impressions, ranked off page 1, thin content")
    found = False
    for p, r in sorted(pages.items(), key=lambda x: -x[1][2]):
        impr, position = r[2], r[4]
        if impr < MIN_IMPRESSIONS or not (PAGE2_MIN <= position <= PAGE2_MAX):
            continue
        wc = word_count(local_file(p))
        if wc is not None and wc < THIN_WORDS:
            print("    %4d impr  pos %5.1f  %5d words  %s" % (impr, position, wc, p))
            found = True
    if not found:
        print("    none - the thin/page-2 pattern is cleared")

    # --- pattern 2: on page 1 but earning no clicks -------------------------
    print("\n[2] CTR - ranking on page 1 but no clicks (rewrite title + meta)")
    found = False
    for p, r in sorted(pages.items(), key=lambda x: -x[1][2]):
        if r[1] == 0 and r[4] <= CTR_POS_MAX and r[2] >= MIN_IMPRESSIONS:
            print("    %4d impr  pos %5.1f  %s" % (r[2], r[4], p))
            found = True
    if not found:
        print("    none")

    # --- pattern 3: cannibalisation -----------------------------------------
    # Only hub pages (lists / industries / functions) can cannibalise each other.
    # Organism pages are leaf content targeting their own long-tail query, so a
    # gecko page ranking alongside the adhesives list is correct, not a conflict.
    print("\n[3] CANNIBALISATION - hub pages competing on one topic")
    topics = {}
    for p in pages:
        if not re.match(r"^/(lists|industries|functions)/", p):
            continue
        key = re.sub(r"^/(lists|industries|functions)/", "", p).strip("/")
        for token in ("robotics", "architecture", "materials", "aerospace", "water",
                      "packaging", "medical", "energy", "textiles", "adhesive",
                      "agriculture", "transport", "defense", "consumer"):
            if token in key:
                topics.setdefault(token, []).append(p)
    any_dupes = False
    for token, ps in sorted(topics.items()):
        if len(ps) < 2:
            continue
        # Only a real conflict if both pages actually draw impressions.
        live = [p for p in ps if pages[p][2] >= 3]
        if len(live) < 2:
            continue
        any_dupes = True
        print("    " + token + ":")
        for p in sorted(live, key=lambda x: -pages[x][2]):
            r = pages[p]
            print("       %4d impr  pos %5.1f  %s" % (r[2], r[4], p))
    if not any_dupes:
        print("    none")

    # --- pattern 4: query gaps ----------------------------------------------
    print("\n[4] QUERY GAPS - demand where we rank poorly (new/expanded content)")
    found = False
    for q in sorted(queries, key=lambda r: -r[2])[:40]:
        if "site:" in q[0]:
            continue
        if q[4] > 20 and q[2] >= 3:
            print("    %3d impr  pos %5.1f  \"%s\"" % (q[2], q[4], q[0]))
            found = True
    if not found:
        print("    none")

    # --- pattern 5: duplicate boilerplate ------------------------------------
    print("\n[5] DUPLICATE BOILERPLATE - shared blocks across templated pages")
    for section in ("industries", "functions", "lists"):
        d = os.path.join(CONTENT, section)
        if not os.path.isdir(d):
            continue
        blocks = {}
        for f in os.listdir(d):
            if not f.endswith(".md") or f == "_index.md":
                continue
            body = open(os.path.join(d, f), encoding="utf-8").read()
            for line in body.split("\n"):
                s = line.strip()
                if len(s) > 60 and not s.startswith(("#", "+", "{", "-", ">", "[")):
                    blocks.setdefault(s, []).append(f)
        dupes = {k: v for k, v in blocks.items() if len(v) > 2}
        if dupes:
            worst = max(dupes.items(), key=lambda x: len(x[1]))
            print("    %s: %d shared sentence(s); worst appears on %d pages"
                  % (section, len(dupes), len(worst[1])))
            print('       "' + worst[0][:76] + '..."')
        else:
            print("    " + section + ": clean")

    if "--save" in args:
        os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
        runs = history + [{
            "date": label,
            "impressions": int(impressions),
            "clicks": int(clicks),
            "ctr": round(ctr, 2),
            "position": round(pos, 1),
            "export": os.path.basename(export),
        }]
        seen = {}
        for r in runs:
            seen[r["date"]] = r
        runs = [seen[k] for k in sorted(seen)]
        json.dump({"runs": runs}, open(HISTORY, "w", encoding="utf-8"), indent=2)
        print("\nSaved to data/seo-baseline.json (%d runs)" % len(runs))
    else:
        print("\n(Re-run with --save to record this run in the baseline history.)")


if __name__ == "__main__":
    main()
