"""
fix_meta_descriptions.py
Trims meta descriptions that exceed 162 characters to exactly 159 chars + '...'
Run from project root: python scripts/fix_meta_descriptions.py
"""

import os
import re

CONTENT_ROOT = os.path.join(os.path.dirname(__file__), "..", "content")
MAX_LEN = 159


def trim_description(desc):
    """Trim a description to MAX_LEN chars, breaking at a word boundary."""
    if len(desc) <= MAX_LEN:
        return desc
    trimmed = desc[:MAX_LEN].rsplit(" ", 1)[0].rstrip(" ,;:")
    return trimmed + "..."


def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    def replace_desc(m):
        original = m.group(1)
        if len(original) <= 162:
            return m.group(0)  # no change needed
        fixed = trim_description(original)
        return f'description = "{fixed}"'

    new_content = re.sub(r'description\s*=\s*"(.+?)"', replace_desc, content)

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def main():
    fixed = 0
    for folder in ["organisms", "functions", "industries", "lists"]:
        d = os.path.join(CONTENT_ROOT, folder)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(d, fn)
            if fix_file(path):
                print(f"  FIXED: {folder}/{fn}")
                fixed += 1

    print(f"\nDone. {fixed} files updated.")


if __name__ == "__main__":
    main()
