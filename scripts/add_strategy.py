"""
add_strategy.py — Interactive CLI to add new biological strategies to the database.
Usage: python scripts/add_strategy.py
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "biomimicry.db")

KINGDOMS = ["Animal", "Plant", "Fungi", "Bacteria", "Protist"]
TAXONOMY_GROUPS = ["Protect", "Move", "Make", "Modify", "Process", "Sense", "Attach"]


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def prompt(label, required=True, default=None, options=None):
    """Prompt the user for input with an optional list of choices."""
    while True:
        hint = ""
        if options:
            hint = f" [{'/'.join(options)}]"
        if default:
            hint += f" (default: {default})"
        value = input(f"\n{label}{hint}: ").strip()
        if not value and default:
            return default
        if not value and required:
            print("  This field is required.")
            continue
        if options and value not in options:
            print(f"  Please choose from: {', '.join(options)}")
            continue
        return value if value else None


def add_strategy(conn):
    print("\n" + "=" * 60)
    print("  ADD A NEW BIOLOGICAL STRATEGY")
    print("=" * 60)
    print("Fill in the details below. Press Enter to skip optional fields.")

    organism = prompt("Organism common name (e.g. 'Namibian fog-basking beetle')")
    organism_scientific = prompt("Scientific name (e.g. 'Stenocara gracilipes')", required=False)
    kingdom = prompt("Kingdom", options=KINGDOMS)
    habitat = prompt("Habitat (e.g. 'Namib Desert, southwestern Africa')", required=False)
    biological_function = prompt(
        "Biological function\n  (What does it do? How does it work? Write 2-4 sentences\n   in plain language for a curious product designer.)"
    )
    taxonomy_group = prompt("Biomimicry taxonomy group", options=TAXONOMY_GROUPS)
    taxonomy_subgroup = prompt(
        "Biomimicry taxonomy subgroup (e.g. 'Collect and store water')", required=False
    )
    human_application = prompt(
        "Human application\n  (What have engineers built from this? 2-3 sentences.)"
    )
    real_world_products = prompt(
        "Real-world products/companies (comma-separated, or press Enter to skip)",
        required=False
    )
    industry_tags = prompt(
        "Industry tags (comma-separated, e.g. 'water, architecture, materials science')",
        required=False
    )
    key_principle = prompt(
        "Key design principle\n  (The transferable engineering insight. 1-2 sentences.)"
    )
    source_url = prompt("Source URL (AskNature page or academic paper)", required=False)

    # Auto-generate slug from organism name
    default_slug = slugify(organism)
    slug = prompt(f"URL slug", default=default_slug)

    # Preview the entry
    print("\n" + "-" * 60)
    print("PREVIEW:")
    print(f"  Organism: {organism} ({organism_scientific or 'no scientific name'})")
    print(f"  Kingdom:  {kingdom}")
    print(f"  Taxonomy: {taxonomy_group} > {taxonomy_subgroup or 'N/A'}")
    print(f"  Slug:     {slug}")
    print("-" * 60)

    confirm = input("\nSave this entry? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("Entry discarded.")
        return False

    try:
        conn.execute("""
            INSERT INTO strategies (
                organism, organism_scientific, kingdom, habitat,
                biological_function, biomimicry_taxonomy_group,
                biomimicry_taxonomy_subgroup, human_application,
                real_world_products, industry_tags, key_principle,
                source_url, slug
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            organism, organism_scientific, kingdom, habitat,
            biological_function, taxonomy_group, taxonomy_subgroup,
            human_application, real_world_products, industry_tags,
            key_principle, source_url, slug
        ))
        conn.commit()
        print(f"\nSaved! Strategy '{organism}' added with slug '{slug}'.")
        return True
    except sqlite3.IntegrityError:
        print(f"\nError: A strategy with slug '{slug}' already exists.")
        print("Try again with a different slug.")
        return False


def list_strategies(conn):
    """Show a summary of all strategies in the database."""
    rows = conn.execute(
        "SELECT id, organism, kingdom, biomimicry_taxonomy_group, slug FROM strategies ORDER BY id"
    ).fetchall()
    if not rows:
        print("  No strategies in database yet.")
        return
    print(f"\n  {'ID':<4} {'Organism':<40} {'Kingdom':<10} {'Taxonomy':<12} {'Slug'}")
    print("  " + "-" * 90)
    for row in rows:
        print(f"  {row[0]:<4} {row[1]:<40} {row[2]:<10} {row[3]:<12} {row[4]}")
    print(f"\n  Total: {len(rows)} strategies")


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("Run 'python scripts/seed_database.py' first.")
        return

    conn = sqlite3.connect(DB_PATH)

    while True:
        print("\n" + "=" * 60)
        print("  BIOMIMICRY DATABASE MANAGER")
        print("=" * 60)
        print("  1. Add a new strategy")
        print("  2. List all strategies")
        print("  3. Quit")
        choice = input("\nChoice (1/2/3): ").strip()

        if choice == "1":
            add_strategy(conn)
        elif choice == "2":
            list_strategies(conn)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Please enter 1, 2, or 3.")

    conn.close()


if __name__ == "__main__":
    main()
