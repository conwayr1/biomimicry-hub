"""
build_internal_links.py -- Phase 4: Internal Linking & SEO Structure

Audits all generated content pages for:
  1. Internal link coverage  (related_slugs >= 3, linked from >= 2 pages)
  2. Title length            (target: 40-65 characters)
  3. Description length      (target: 120-160 characters)

Then fixes any issues directly in the markdown files.

Usage:
  py scripts/build_internal_links.py           # audit + fix everything
  py scripts/build_internal_links.py --audit   # report issues only, no changes
"""

import os
import re
import sys
from collections import defaultdict

CONTENT_ROOT = os.path.join(os.path.dirname(__file__), "..", "content")

DRY_RUN = "--audit" in sys.argv

# ---------------------------------------------------------------------------
# Corrected titles for organism pages whose auto-generated title is too long
# or too short.  Keys are content base names (no extension).
# ---------------------------------------------------------------------------
ORGANISM_TITLE_FIXES = {
    "blue-whale-low-frequency-underwater-communication":
        "How Blue Whales Inspired Underwater Communication",
    "bombardier-beetle-pulsed-combustion-drug-injection":
        "How Bombardier Beetles Inspired Precision Drug Delivery",
    "cocklebur-velcro-hook-loop-fastening":
        "How Cocklebur Inspired Velcro Hook-and-Loop Fasteners",
    "dinoflagellate-bioluminescence-efficient-lighting":
        "How Dinoflagellates Inspired Efficient Cold-light Lighting",
    "homing-pigeon-cognitive-mapping-autonomous-navigation":
        "How Homing Pigeons Inspired Autonomous Navigation AI",
    "immortal-jellyfish-cellular-reprogramming-stem-cells":
        "How the Immortal Jellyfish Inspired Stem Cell Research",
    "monarch-butterfly-navigation-gps-denied-robots":
        "How Monarch Butterflies Inspired GPS-free Navigation",
    "morpho-butterfly-structural-color-anti-counterfeiting":
        "How Morpho Butterflies Inspired Structural Color Tech",
    "namibian-beetle-fog-collection-water-harvesting":
        "How the Namibian Beetle Inspired Fog-harvesting Design",
    "pinecone-humidity-responsive-adaptive-facades":
        "How Pinecones Inspired Humidity-responsive Architecture",
    "pistol-shrimp-cavitation-cleaning-microfluidics":
        "How Pistol Shrimp Inspired Cavitation Microfluidics",
    "silver-ant-hairs-radiative-cooling-building-materials":
        "How Saharan Silver Ants Inspired Passive Cooling",
    "thorny-devil-capillary-wicking-microfluidic-chips":
        "How the Thorny Devil Inspired Microfluidic Chip Design",
}

FUNCTION_TITLE_FIXES = {
    "biomimicry-for-adhesion-and-attachment":
        "Biomimicry for Adhesion: How Nature Sticks",
    "biomimicry-for-materials-and-manufacturing":
        "Biomimicry for Materials: Nature-Inspired Manufacturing",
    "biomimicry-for-shape-changing-and-adaptation":
        "Biomimicry for Adaptive Structures and Shape Change",
    "biomimicry-for-movement-and-locomotion":
        "Biomimicry for Movement: Nature-Inspired Locomotion",
    "biomimicry-for-resource-processing-and-efficiency":
        "Biomimicry for Resource Processing and Efficiency",
    "biomimicry-for-protection-and-defense":
        "Biomimicry for Protection: Nature-Inspired Defense",
    "biomimicry-for-sensing-and-navigation":
        "Biomimicry for Sensing: Nature-Inspired Navigation",
}

INDUSTRY_TITLE_FIXES = {
    "biomimicry-in-architecture-and-construction":
        "Biomimicry in Architecture: Nature-Inspired Buildings",
    "biomimicry-in-medical-devices-and-healthcare":
        "Biomimicry in Medical Devices and Healthcare",
}

# ---------------------------------------------------------------------------
# Extra description text appended to short industry / list descriptions.
# Keyed by slug (filename without .md). Extras are kept short (~45 chars)
# so the combined description stays within 150-165 chars.
# ---------------------------------------------------------------------------
INDUSTRY_DESC_EXTRAS = {
    "biomimicry-in-aerospace-engineering":
        " Bird beaks, whale fins and shark skin have all inspired aerospace breakthroughs.",
    "biomimicry-in-agriculture":
        " Closed-loop systems and water-efficient crops inspired by nature.",
    "biomimicry-in-biotechnology":
        " Evolution has spent billions of years optimising biological processes.",
    "biomimicry-in-consumer-products":
        " Nature-inspired ideas are quietly embedded in everyday objects.",
    "biomimicry-in-defense-and-security":
        " Camouflage, sonar, and collision avoidance all have biological origins.",
    "biomimicry-in-electronics-and-displays":
        " Structural colour and flexible membranes are driving display innovation.",
    "biomimicry-in-energy":
        " Whale-fin turbines and bio-inspired solar cells are reshaping energy.",
    "biomimicry-in-environmental-technology":
        " Nature's filtration and water-harvesting systems inspire green tech.",
    "biomimicry-in-food-science":
        " Antifungal coatings and fermentation pathways drawn from biology.",
    "biomimicry-in-manufacturing":
        " Self-assembly and room-temperature fabrication, as nature does it.",
    "biomimicry-in-marine-engineering":
        " Hull drag, underwater adhesion, and bio-fouling all solved by nature.",
    "biomimicry-in-materials-science":
        " Nacre, bone, and silk reveal composite-design principles for engineers.",
    "biomimicry-in-packaging":
        " Shells and foams inspire biodegradable, impact-absorbing packaging.",
    "biomimicry-in-robotics":
        " Locomotion, adhesion, and sensing all drawn from living systems.",
    "biomimicry-in-medical-devices-and-healthcare":
        " Gecko adhesives and shark-skin coatings are already in clinical use.",
    "biomimicry-in-sports-equipment":
        " Swimsuits, helmets, and shoe soles refined by millions of years of biology.",
    "biomimicry-in-textiles-and-wearables":
        " Thermoregulation and structural colour woven into next-generation fabrics.",
    "biomimicry-in-transportation":
        " Kingfishers, boxfish, and whales have reshaped trains, cars, and aircraft.",
    "biomimicry-in-water-technology":
        " Beetles, cacti, and mangroves inspire passive water-harvesting systems.",
}

LIST_DESC_EXTRAS = {
    "best-biomimicry-examples-aerospace":
        " Ranked by impact and commercial readiness.",
    "best-biomimicry-examples-architecture":
        " From passive ventilation towers to load-optimised shells.",
    "best-biomimicry-examples-medical-devices":
        " Ranked by clinical relevance and real-world adoption.",
    "best-biomimicry-examples-robotics":
        " From gecko-grip climbers to swarm intelligence platforms.",
    "biomimicry-passive-cooling-energy":
        " All examples use zero active energy input.",
    "nature-inspired-adhesives":
        " Dry, wet, and reversible — nature's adhesives outperform most synthetics.",
    "nature-inspired-structural-materials":
        " Lightweight, tough, and self-assembling — lessons from living structures.",
    "nature-inspired-water-solutions":
        " Passive, energy-free water collection and filtration drawn from nature.",
}

ORGANISM_DESC_EXTRAS = {
    "cocklebur-velcro-hook-loop-fastening":
        " One of the most commercially successful biomimicry inventions of all time.",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def parse_fm(text):
    """Return dict of scalar/list values from TOML front matter."""
    m = re.match(r"^\+\+\+\n(.*?)\n\+\+\+", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        kv = re.match(r"(\w+)\s*=\s*(.*)", line.strip())
        if kv:
            k, v = kv.group(1), kv.group(2).strip()
            if v.startswith("["):
                fm[k] = re.findall(r'"([^"]+)"', v)
            elif v.startswith('"') or v.startswith("'"):
                fm[k] = v.strip('"').strip("'")
            else:
                fm[k] = v
    return fm


def replace_fm_value(text, key, new_value):
    """
    Replace a scalar string value in TOML front matter.
    Handles lines like:  key = "old value"
    """
    # Match the key inside the +++ block only
    pattern = re.compile(
        r'^(\+\+\+\n)(.*?)(\n\+\+\+)',
        re.DOTALL
    )
    m = pattern.match(text)
    if not m:
        return text
    fm_block = m.group(2)
    new_fm = re.sub(
        rf'^({key}\s*=\s*)"[^"]*"',
        rf'\1"{new_value}"',
        fm_block,
        flags=re.MULTILINE
    )
    return m.group(1) + new_fm + m.group(3) + text[m.end():]


def replace_fm_list(text, key, new_items):
    """Replace a list value in TOML front matter."""
    new_val = "[" + ", ".join(f'"{i}"' for i in new_items) + "]"
    pattern = re.compile(r'^(\+\+\+\n)(.*?)(\n\+\+\+)', re.DOTALL)
    m = pattern.match(text)
    if not m:
        return text
    fm_block = m.group(2)
    new_fm = re.sub(
        rf'^({key}\s*=\s*)\[.*?\]',
        rf'\g<1>{new_val}',
        fm_block,
        flags=re.MULTILINE
    )
    return m.group(1) + new_fm + m.group(3) + text[m.end():]


def scan_section(section):
    """Return list of (slug, filepath, fm_dict, full_text) for a section."""
    results = []
    sec_dir = os.path.join(CONTENT_ROOT, section)
    if not os.path.isdir(sec_dir):
        return results
    for fn in sorted(os.listdir(sec_dir)):
        if fn.endswith(".md") and not fn.startswith("_"):
            path = os.path.join(sec_dir, fn)
            text = read_file(path)
            fm = parse_fm(text)
            slug = fn[:-3]   # filename without .md
            results.append((slug, path, fm, text))
    return results


# ---------------------------------------------------------------------------
# 1. Link-graph audit and repair
# ---------------------------------------------------------------------------

def audit_link_graph():
    print("\n--- 1. Internal Link Graph ---")

    orgs = scan_section("organisms")
    org_slugs = {fm.get("slug", s) for s, _, fm, _ in orgs}

    # Build forward links: slug -> set of slugs it links to
    forward = defaultdict(set)
    # Build reverse links: slug -> set of page files that link to it
    reverse = defaultdict(set)

    # From organism related_slugs
    for slug, path, fm, _ in orgs:
        org_slug = fm.get("slug", slug)
        for rel in fm.get("related_slugs", []):
            forward[org_slug].add(rel)
            reverse[rel].add(org_slug)

    # From function / industry / list strategy_slugs
    for section in ("functions", "industries", "lists"):
        for slug, path, fm, _ in scan_section(section):
            for s in fm.get("strategy_slugs", []):
                reverse[s].add(f"{section}/{slug}")
                forward[f"{section}/{slug}"].add(s)

    # Check coverage
    few_forward = [(s, fm.get("slug", s), len(fm.get("related_slugs", [])))
                   for s, _, fm, _ in orgs
                   if len(fm.get("related_slugs", [])) < 3]
    few_backward = [(org_s, len(reverse[org_s]))
                    for _, _, fm, _ in orgs
                    for org_s in [fm.get("slug", "")]
                    if len(reverse[org_s]) < 2]

    if few_forward:
        print(f"  [WARN] {len(few_forward)} organisms have < 3 related_slugs:")
        for fn, sl, n in few_forward:
            print(f"    {fn}: {n}")
    else:
        print(f"  [OK] All {len(orgs)} organisms have 3+ related slugs.")

    if few_backward:
        print(f"  [WARN] {len(few_backward)} organisms linked from < 2 pages:")
        for sl, n in few_backward:
            print(f"    {sl}: {n} incoming links")
    else:
        print(f"  [OK] All {len(orgs)} organisms are linked from 2+ pages.")

    # Repair: top up related_slugs if needed
    if few_forward and not DRY_RUN:
        print("  Repairing related_slugs...")
        # Build similarity scores using taxonomy + shared industries
        org_map = {fm.get("slug", s): fm for s, _, fm, _ in orgs}
        for slug, filepath, fm, text in orgs:
            org_slug = fm.get("slug", slug)
            existing = set(fm.get("related_slugs", []))
            if len(existing) >= 3:
                continue
            # Score candidates
            own_industries = set(fm.get("industries", []))
            own_taxonomy = fm.get("taxonomy_group", "")
            scored = []
            for other_slug, other_fm in org_map.items():
                if other_slug == org_slug or other_slug in existing:
                    continue
                score = 0
                if other_fm.get("taxonomy_group") == own_taxonomy:
                    score += 2
                shared = own_industries & set(other_fm.get("industries", []))
                score += len(shared)
                if score > 0:
                    scored.append((score, other_slug))
            scored.sort(reverse=True)
            additions = [s for _, s in scored[:4 - len(existing)]]
            new_list = list(existing) + additions
            new_text = replace_fm_list(text, "related_slugs", new_list)
            write_file(filepath, new_text)
            print(f"    Updated {slug}: added {additions}")

    return len(few_forward), len(few_backward)


# ---------------------------------------------------------------------------
# 2. Title-length audit and repair
# ---------------------------------------------------------------------------

def audit_titles():
    print("\n--- 2. Title Lengths (target 40-65 chars) ---")

    all_fixes = []

    for section in ("organisms", "functions", "industries", "lists"):
        for slug, path, fm, text in scan_section(section):
            title = fm.get("title", "")
            tl = len(title)

            if tl > 65 or tl < 35:
                fix = None
                if section == "organisms":
                    fix = ORGANISM_TITLE_FIXES.get(slug)
                elif section == "functions":
                    fix = FUNCTION_TITLE_FIXES.get(slug)
                elif section == "industries":
                    fix = INDUSTRY_TITLE_FIXES.get(slug)

                if fix:
                    all_fixes.append((section, slug, path, text, tl, title, fix))
                    continue

                # Still flag for info even without a pre-written fix
                flag = "LONG" if tl > 65 else "SHORT"
                print(f"  [{flag} {tl}] {section}/{slug}: {title}")

    if all_fixes:
        print(f"  Found {len(all_fixes)} titles to fix.")
        for section, slug, path, text, tl, old_title, new_title in all_fixes:
            flag = "LONG" if tl > 65 else "SHORT"
            print(f"  [{flag} {tl}] {section}/{slug}")
            print(f"    Before: {old_title}")
            print(f"    After:  {new_title}")
            if not DRY_RUN:
                new_text = replace_fm_value(text, "title", new_title)
                write_file(path, new_text)
    else:
        print("  [OK] No pre-defined title fixes needed.")

    return len(all_fixes)


# ---------------------------------------------------------------------------
# 3. Description-length audit and repair
# ---------------------------------------------------------------------------

def audit_descriptions():
    print("\n--- 3. Description Lengths (target 120-160 chars) ---")

    fixes = []
    no_fix = []

    for section in ("organisms", "functions", "industries", "lists"):
        for slug, path, fm, text in scan_section(section):
            desc = fm.get("description", "")
            dl = len(desc)
            if dl < 120:
                extra = None
                if section == "organisms":
                    extra = ORGANISM_DESC_EXTRAS.get(slug)
                elif section == "industries":
                    extra = INDUSTRY_DESC_EXTRAS.get(slug)
                elif section == "lists":
                    extra = LIST_DESC_EXTRAS.get(slug)
                if extra:
                    new_desc = desc + extra
                    fixes.append((section, slug, path, text, dl, desc, new_desc))
                else:
                    no_fix.append((section, slug, dl, desc))
            elif dl > 165:
                no_fix.append((section, slug, dl, desc[:80]))

    if fixes:
        print(f"  Found {len(fixes)} descriptions to extend.")
        for section, slug, path, text, old_len, old_desc, new_desc in fixes:
            print(f"  [SHORT {old_len} -> {len(new_desc)}] {section}/{slug}")
            if not DRY_RUN:
                new_text = replace_fm_value(text, "description", new_desc)
                write_file(path, new_text)
    else:
        print("  [OK] No industry description fixes needed.")

    if no_fix:
        print(f"  [{len(no_fix)} pages outside range with no pre-defined fix — review manually:]")
        for section, slug, dl, d in no_fix[:8]:
            flag = "SHORT" if dl < 120 else "LONG"
            print(f"    [{flag} {dl}] {section}/{slug}: {d[:70]}...")

    return len(fixes)


# ---------------------------------------------------------------------------
# 4. Final build check
# ---------------------------------------------------------------------------

def summarise(link_issues, title_fixes, desc_fixes, dry):
    print("\n" + "=" * 55)
    mode = "AUDIT (no files changed)" if dry else "FIX COMPLETE"
    print(f"  build_internal_links.py  --  {mode}")
    print("=" * 55)
    orphan_fwd, orphan_bwd = link_issues
    if dry:
        print(f"  Link graph issues:      fwd={orphan_fwd}  bwd={orphan_bwd}")
        print(f"  Title fixes pending:    {title_fixes}")
        print(f"  Description fixes pending: {desc_fixes}")
        print("\n  Run without --audit to apply fixes.")
    else:
        print(f"  Title files updated:       {title_fixes}")
        print(f"  Description files updated: {desc_fixes}")
        link_str = "clean" if (orphan_fwd + orphan_bwd) == 0 else f"{orphan_fwd + orphan_bwd} issues (see above)"
        print(f"  Link graph:                {link_str}")
        print("\n  Rebuild with: hugo (or hugo server) to see changes.")
    print("=" * 55)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("build_internal_links.py", "(AUDIT MODE)" if DRY_RUN else "")

    link_issues = audit_link_graph()
    title_fixes = audit_titles()
    desc_fixes  = audit_descriptions()

    summarise(link_issues, title_fixes, desc_fixes, DRY_RUN)
