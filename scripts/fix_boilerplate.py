"""
fix_boilerplate.py — Strips repeated boilerplate from all organism pages.

Every organism page was generated with 7 identical text blocks that add no
value and signal duplicate content to search engines. This script removes them,
leaving only the genuinely unique content on each page.

Blocks removed:
  1. Opening paragraph ("The answer — as engineers have discovered — is yes...")
  2. Habitat boilerplate tail ("Over millions of years of evolutionary pressure...")
  3. Taxonomy line suffix ("— one of the most actively researched areas...")
  4. Design Principle opener ("What makes this biologically remarkable...")
  5. Design Principle closer ("This principle is deceptively simple to state...")
  6. Human Applications closer ("The translation from biology to engineering...")
  7. Entire "Why This Matters" section

What stays (the unique content):
  - Hook question (opening line, unique per page)
  - The Natural Innovation paragraph (what the organism actually does)
  - Habitat sentence ("The X lives in Y.")
  - Taxonomy subgroup line (shortened)
  - Key principle blockquote
  - Human applications paragraph
  - Real-world implementations line

Usage:
  python scripts/fix_boilerplate.py              # fix all pages in place
  python scripts/fix_boilerplate.py --dry-run    # preview only, no writes
  python scripts/fix_boilerplate.py --file gecko-adhesion-dry-adhesives.md  # one file
"""

import os
import re
import sys

ORGANISMS_DIR = os.path.join(os.path.dirname(__file__), "..", "content", "organisms")

# ── Boilerplate patterns ───────────────────────────────────────────────────────
# Each entry is a (name, pattern, replacement) tuple.
# Most removals use "" as the replacement; the taxonomy suffix swaps in a "." to
# preserve sentence punctuation. Applied in order — sequence matters.

REMOVALS = [

    # 1. Opening paragraph that appears after the hook on every page.
    #    Matches from "The answer" to end of the sentence about "built as a result."
    (
        "opening_paragraph",
        re.compile(
            r"\nThe answer\s*[—\-]+\s*as engineers have discovered\s*[—\-]+\s*is yes\..*?"
            r"what has already been built as a result\.",
            re.DOTALL
        ),
        ""
    ),

    # 2. Boilerplate tail that follows the habitat sentence.
    #    The "X lives in Y." sentence is kept; only the generic paragraph after it is removed.
    (
        "habitat_boilerplate",
        re.compile(
            r"Over millions of years of evolutionary pressure,\s+"
            r"this capability became not just useful but essential.*?"
            r"engineering research\.",
            re.DOTALL
        ),
        ""
    ),

    # 3. Taxonomy line suffix.
    #    Replaces "— one of the most actively researched areas..." with "." to keep punctuation.
    (
        "taxonomy_suffix",
        re.compile(
            r"\s*[—\-]+\s*one of the most actively researched areas in bio-inspired engineering\."
        ),
        "."
    ),

    # 4. Design Principle section opener boilerplate.
    #    Removes the two sentences before the key-principle blockquote.
    (
        "design_principle_opener",
        re.compile(
            r"What makes this biologically remarkable also makes it technically transferable\.\s+"
            r"Strip away\s+the biology and you're left with a core engineering insight:\s*",
            re.DOTALL
        ),
        ""
    ),

    # 5. Design Principle section closer boilerplate.
    #    Removes the paragraph after the key-principle blockquote.
    (
        "design_principle_closer",
        re.compile(
            r"This principle is deceptively simple to state but difficult to achieve.*?"
            r"human industry typically relies on\.",
            re.DOTALL
        ),
        ""
    ),

    # 6. Human Applications section closer boilerplate.
    #    Removes the generic paragraph after the unique applications content.
    (
        "human_applications_closer",
        re.compile(
            r"The translation from biology to engineering is rarely direct.*?"
            r"no conventional approach can match\.",
            re.DOTALL
        ),
        ""
    ),

    # 7. Entire "Why This Matters" section — 100% boilerplate (only the organism name differs).
    (
        "why_this_matters_section",
        re.compile(
            r"## Why This Matters\s+Biomimicry works not because.*?are already proven\.",
            re.DOTALL
        ),
        ""
    ),
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def fix_page(content):
    """Apply all boilerplate removals (and replacements) to a page's content."""
    for _name, pattern, replacement in REMOVALS:
        content = pattern.sub(replacement, content)
    return clean_whitespace(content)


def clean_whitespace(text):
    """
    After removing blocks there can be 3-4 consecutive blank lines.
    Collapse them to a single blank line and strip trailing spaces.
    """
    # Strip trailing spaces from every line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse 3+ blank lines to exactly one blank line (two newlines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Ensure the file ends with exactly one newline
    return text.strip() + "\n"


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    dry_run     = "--dry-run" in sys.argv
    single_file = None
    if "--file" in sys.argv:
        idx = sys.argv.index("--file")
        if idx + 1 < len(sys.argv):
            single_file = sys.argv[idx + 1]

    # Build file list
    if single_file:
        files = [single_file]
    else:
        files = sorted(
            f for f in os.listdir(ORGANISMS_DIR)
            if f.endswith(".md") and f != "_index.md"
        )

    changed  = 0
    skipped  = 0

    print(f"{'DRY RUN — ' if dry_run else ''}Processing {len(files)} organism pages...\n")

    for filename in files:
        path = os.path.join(ORGANISMS_DIR, filename)
        with open(path, encoding="utf-8") as f:
            original = f.read()

        fixed = fix_page(original)

        if fixed == original:
            skipped += 1
            print(f"  SKIP  {filename}  (already clean)")
        else:
            changed += 1
            if dry_run:
                print(f"  WOULD FIX  {filename}")
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(fixed)
                print(f"  FIXED {filename}")

    print(f"\n{'Would fix' if dry_run else 'Fixed'}: {changed}   Skipped: {skipped}   Total: {len(files)}")
    if dry_run and changed:
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
