"""
fix_organism_meta.py
====================

Retro-fixes the title and meta description in the front matter of existing
organism pages, without touching the body prose.

Why this exists: generate_content.py never overwrites an existing file (by
design — pages get hand-edited after generation), so improving the generator
alone does not fix the 80-odd pages already on disk. This script applies the
same improved title/description logic to those files in place.

It only rewrites a page whose description still matches the old boilerplate
formula, so any page whose meta has been hand-written is left alone
automatically.

Usage:
  py scripts/fix_organism_meta.py           # dry run — show what would change
  py scripts/fix_organism_meta.py --apply   # write the changes
"""

import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_keywords import (           # noqa: E402  (path set above)
    short_organism,
    derive_technology,
    organism_title,
    organism_display,
    organism_description,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB_PATH = os.path.join(ROOT, "database", "biomimicry.db")
ORGANISM_DIR = os.path.join(ROOT, "content", "organisms")

# A page is considered "still generated boilerplate" if its description contains
# this clause, which the old template appended to every organism page.
# Match only the stable prefix: fix_meta_descriptions.py truncated some of these
# mid-word ("...and real-w"), and those are exactly the ones most worth fixing.
BOILERPLATE = "the biological mechanism, the engineering principle"


def read_field(md, field):
    m = re.search(rf'^{field}\s*=\s*"(.*)"$', md, re.M)
    return m.group(1) if m else None


def set_field(md, field, value):
    return re.sub(rf'^{field}(\s*)=\s*".*"$',
                  lambda m: f'{field}{m.group(1)}= "{value}"',
                  md, count=1, flags=re.M)


def main():
    apply_changes = "--apply" in sys.argv

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    strategies = {r["slug"]: r for r in conn.execute("SELECT * FROM strategies")}

    changed = skipped_handwritten = missing = 0

    for fname in sorted(os.listdir(ORGANISM_DIR)):
        if not fname.endswith(".md") or fname == "_index.md":
            continue
        path = os.path.join(ORGANISM_DIR, fname)
        slug = fname[:-3]
        s = strategies.get(slug)
        if s is None:
            print(f"  ?  no database row for {slug}")
            missing += 1
            continue

        md = open(path, encoding="utf-8").read()
        old_title = read_field(md, "title")
        old_desc = read_field(md, "description")

        # Leave hand-written meta alone.
        if not old_desc or BOILERPLATE not in old_desc:
            skipped_handwritten += 1
            continue

        tech = derive_technology(s)
        org = short_organism(s["organism"])
        new_desc = organism_description(s["biological_function"], tech)

        # Repair the title surgically rather than regenerating it. Several
        # existing titles are better than what the generator produces (shorter,
        # punchier), so only fix the actual bug: the organism name sitting in
        # the title in database sentence case ("How Abalone shell Inspired...").
        new_title = old_title
        if org in old_title and org != organism_display(org).removeprefix("the "):
            new_title = old_title.replace(org, organism_display(org), 1)

        print(f"\n{slug}")
        if new_title != old_title:
            print(f"  T  {old_title}")
            print(f"  -> {new_title}   [{len(new_title)}]")
        else:
            print(f"  T  (kept) {old_title}")
        print(f"  D  {old_desc[:88]}...")
        print(f"  -> {new_desc}   [{len(new_desc)}]")

        if apply_changes:
            if new_title != old_title:
                md = set_field(md, "title", new_title)
            md = set_field(md, "description", new_desc)
            open(path, "w", encoding="utf-8").write(md)
        changed += 1

    conn.close()
    print()
    print(f"{'Updated' if apply_changes else 'Would update'}: {changed} pages")
    print(f"Left alone (hand-written meta): {skipped_handwritten}")
    if missing:
        print(f"No database row: {missing}")
    if not apply_changes:
        print("\nDry run. Re-run with --apply to write these changes.")


if __name__ == "__main__":
    main()
