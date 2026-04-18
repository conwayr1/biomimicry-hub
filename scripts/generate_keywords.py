"""
generate_keywords.py — Reads biomimicry.db and produces data/keyword_plan.json.

Each strategy maps to one organism page. Strategies are also grouped into
function pages (by biomimicry_taxonomy_group), industry pages (by industry_tags),
and curated list pages. Run: python scripts/generate_keywords.py
"""

import sqlite3
import json
import os
import re
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "biomimicry.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "keyword_plan.json")


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def short_organism(name):
    """Strip parenthetical scientific names and long qualifiers for keyword use."""
    name = re.sub(r"\s*\(.*?\)", "", name).strip()
    # Lowercase function words
    words = name.split()
    stopwords = {"the", "a", "an", "of", "and", "or", "in", "on", "at"}
    return " ".join(w if i == 0 or w.lower() not in stopwords else w.lower()
                    for i, w in enumerate(words))


# Maps taxonomy group → plain-English function phrase for page titles
TAXONOMY_DISPLAY = {
    "Protect":  "protection and defense",
    "Move":     "movement and locomotion",
    "Make":     "materials and manufacturing",
    "Modify":   "shape-changing and adaptation",
    "Process":  "resource processing and efficiency",
    "Sense":    "sensing and navigation",
    "Attach":   "adhesion and attachment",
}

# Maps raw industry tag → display name for page titles
INDUSTRY_DISPLAY = {
    "aerospace":               "Aerospace Engineering",
    "agriculture":             "Agriculture",
    "architecture":            "Architecture and Construction",
    "biotechnology":           "Biotechnology",
    "computing":               "Computing and AI",
    "construction":            "Architecture and Construction",
    "consumer products":       "Consumer Products",
    "defense":                 "Defense and Security",
    "electronics":             "Electronics and Displays",
    "energy":                  "Energy",
    "environmental technology":"Environmental Technology",
    "food science":            "Food Science",
    "humanitarian technology": "Humanitarian Technology",
    "manufacturing":           "Manufacturing",
    "marine engineering":      "Marine Engineering",
    "materials science":       "Materials Science",
    "medical devices":         "Medical Devices and Healthcare",
    "mining":                  "Mining and Robotics",
    "packaging":               "Packaging",
    "robotics":                "Robotics",
    "safety":                  "Safety and Hazard Communication",
    "sports equipment":        "Sports Equipment",
    "textiles":                "Textiles and Wearables",
    "transportation":          "Transportation",
    "water":                   "Water Technology",
}

# Canonical industry slugs (merge near-duplicates)
INDUSTRY_CANONICAL = {
    "construction": "architecture",  # merge into architecture
    "mining":       "robotics",      # small, merge into robotics
}

# Hand-curated list pages: (title, description, filter_fn)
# filter_fn receives a strategy dict and returns True if it belongs on this page
CURATED_LISTS = [
    {
        "title": "10 Best Biomimicry Examples in Materials Science",
        "keyword": "best biomimicry examples in materials science",
        "slug": "best-biomimicry-examples-materials-science",
        "industry_filter": "materials science",
        "taxonomy_filter": None,
        "description": "The ten most impactful nature-inspired innovations in materials science, from gecko adhesives to abalone-tough ceramics.",
    },
    {
        "title": "8 Best Biomimicry Examples in Architecture",
        "keyword": "best biomimicry examples in architecture",
        "slug": "best-biomimicry-examples-architecture",
        "industry_filter": "architecture",
        "taxonomy_filter": None,
        "description": "How nature's structures are reshaping building design — from termite-inspired ventilation to lily-pad floor plates.",
    },
    {
        "title": "10 Best Biomimicry Examples in Robotics",
        "keyword": "best biomimicry examples in robotics",
        "slug": "best-biomimicry-examples-robotics",
        "industry_filter": "robotics",
        "taxonomy_filter": None,
        "description": "Ten nature-inspired robots and robotic systems — from gecko-grip climbers to locust-speed collision avoidance.",
    },
    {
        "title": "8 Best Biomimicry Examples in Medical Devices",
        "keyword": "best biomimicry examples in medical devices",
        "slug": "best-biomimicry-examples-medical-devices",
        "industry_filter": "medical devices",
        "taxonomy_filter": None,
        "description": "How biology is transforming medicine: mussel glue for surgery, sea cucumber neural implants, and more.",
    },
    {
        "title": "8 Best Biomimicry Examples in Aerospace",
        "keyword": "best biomimicry examples in aerospace",
        "slug": "best-biomimicry-examples-aerospace",
        "industry_filter": "aerospace",
        "taxonomy_filter": None,
        "description": "Nature's blueprints for flight: whale-fin turbines, shark-skin aircraft, bat-wing morphing, and more.",
    },
    {
        "title": "Nature-Inspired Water Solutions: 7 Biomimicry Examples",
        "keyword": "nature-inspired water solutions biomimicry",
        "slug": "nature-inspired-water-solutions",
        "industry_filter": "water",
        "taxonomy_filter": None,
        "description": "From fog-collecting beetles to mangrove desalination membranes — how nature solves the world's water challenges.",
    },
    {
        "title": "Nature-Inspired Adhesives: 6 Biomimicry Examples",
        "keyword": "nature-inspired adhesives biomimicry",
        "slug": "nature-inspired-adhesives",
        "industry_filter": None,
        "taxonomy_filter": "Attach",
        "description": "Geckos, mussels, tree frogs, and more — the natural world's remarkably varied toolkit for sticking things together.",
    },
    {
        "title": "Biomimicry for Navigation: 5 Nature-Inspired Solutions",
        "keyword": "biomimicry for navigation nature-inspired",
        "slug": "biomimicry-navigation-nature-inspired",
        "industry_filter": None,
        "taxonomy_filter": "Sense",
        "description": "How desert ants, monarch butterflies, dung beetles, and homing pigeons solve navigation — and what engineers have learned from each.",
    },
    {
        "title": "7 Nature-Inspired Structural Materials",
        "keyword": "nature-inspired structural materials",
        "slug": "nature-inspired-structural-materials",
        "industry_filter": None,
        "taxonomy_filter": "Make",
        "description": "Bone, nacre, spider silk, honeycomb — how nature engineers materials that outperform our best synthetics.",
    },
    {
        "title": "Passive Cooling and Energy: 5 Biomimicry Examples",
        "keyword": "biomimicry passive cooling energy",
        "slug": "biomimicry-passive-cooling-energy",
        "industry_filter": "energy",
        "taxonomy_filter": None,
        "description": "Termite mounds, silver ants, pinecones — nature's zero-energy approaches to thermal management.",
    },
    {
        "title": "10 Most Famous Biomimicry Examples of All Time",
        "keyword": "most famous biomimicry examples",
        "slug": "most-famous-biomimicry-examples",
        "industry_filter": None,
        "taxonomy_filter": None,
        "description": "The classic cases every biomimicry student knows — Velcro, the Shinkansen, Lotusan paint, and seven more that changed how we think about design.",
        "manual_ids": [1, 2, 3, 4, 5, 6, 7, 9, 12, 13],  # gecko, lotus, shark, kingfisher, termite, spider, whale, velcro, beetle, honeycomb
    },
    {
        "title": "Biomimicry in Defense: 6 Nature-Inspired Military Technologies",
        "keyword": "biomimicry in defense military technology",
        "slug": "biomimicry-defense-military-technology",
        "industry_filter": "defense",
        "taxonomy_filter": None,
        "description": "From mantis shrimp armor to locust collision avoidance — how the military looks to nature for next-generation technology.",
    },
]


def fetch_strategies(conn):
    rows = conn.execute("""
        SELECT id, organism, organism_scientific, kingdom, biological_function,
               biomimicry_taxonomy_group, biomimicry_taxonomy_subgroup,
               human_application, industry_tags, key_principle, slug
        FROM strategies ORDER BY id
    """).fetchall()
    cols = ["id","organism","organism_scientific","kingdom","biological_function",
            "biomimicry_taxonomy_group","biomimicry_taxonomy_subgroup",
            "human_application","industry_tags","key_principle","slug"]
    return [dict(zip(cols, r)) for r in rows]


def derive_technology(s):
    """
    Return a short, natural-sounding technology phrase for the keyword pattern
    'how [organism] inspired [technology]'. We use a hand-tuned mapping keyed
    by strategy id so every organism page gets a clean, search-friendly phrase.
    Falls back to auto-extraction if the id isn't in the map.
    """
    TECH_MAP = {
        1:  "dry adhesives",
        2:  "self-cleaning surfaces",
        3:  "drag-reducing surfaces",
        4:  "the Shinkansen bullet train nose",
        5:  "passive building ventilation",
        6:  "synthetic spider silk",
        7:  "wind turbine blades",
        8:  "structural color and anti-counterfeiting",
        9:  "Velcro",
        10: "underwater surgical adhesives",
        11: "aerodynamic vehicle design",
        12: "fog-harvesting water collection",
        13: "honeycomb structural panels",
        14: "humidity-responsive building facades",
        15: "impact-absorbing helmets",
        16: "pulsed combustion and drug injection",
        17: "wet-surface adhesive grippers",
        18: "impact-resistant composite armor",
        19: "collision-avoidance sensors",
        20: "SLIPS non-stick coatings",
        21: "jet engine air intakes",
        22: "color-changing flexible displays",
        23: "water filtration membranes",
        24: "GPS-free navigation algorithms",
        25: "sustainable fungal farming systems",
        26: "hierarchical composite materials",
        27: "expandable and foldable structures",
        28: "precision liquid-jet systems",
        29: "snap-through soft robot actuators",
        30: "ultra-tough ceramic composites",
        31: "high-efficiency bioluminescent lighting",
        32: "polarized-light navigation",
        33: "long-range underwater acoustic communication",
        34: "chemosynthetic bioprocessing",
        35: "morphing aircraft wings",
        36: "diagonal-braced structural lattices",
        37: "biodegradable foam insulation",
        38: "cryopreservation technology",
        39: "dead-reckoning robot navigation",
        40: "variable-stiffness neural implants",
        41: "lightweight ribbed structural panels",
        42: "cellular reprogramming and stem cells",
        43: "aquaporin desalination membranes",
        44: "swarm intelligence algorithms",
        45: "membrane wing aircraft and wingsuits",
        46: "passive evaporative cooling structures",
        47: "viscoelastic reversible adhesives",
        48: "living building materials and biocement",
        49: "safety warning color design",
        50: "cavitation-based cleaning and microfluidics",
        51: "cognitive mapping for autonomous vehicles",
        52: "soft biobatteries",
        53: "micro air vehicle wings",
        54: "biomimetic microlens arrays",
        55: "electroreception sensors",
        56: "capillary wicking microfluidic devices",
        57: "passive radiative cooling materials",
    }
    if s["id"] in TECH_MAP:
        return TECH_MAP[s["id"]]
    # Fallback: take first sentence, strip leading adj, truncate at comma
    ha = s["human_application"].split(".")[0].strip()
    ha = re.sub(r"^(Ultra-strong|High-efficiency|Drag-reducing|Self-cleaning|"
                r"Lightweight|Passively|Passive|Biomimetic|Flexible|Sensitive|"
                r"Compact|Shape-changing|Studying)\s+", "", ha, flags=re.I)
    ha = re.split(r"[,\-—]", ha)[0].strip()
    ha = ha[0].lower() + ha[1:] if ha else ha
    if len(ha) > 55:
        ha = ha[:52].rsplit(" ", 1)[0] + "..."
    return ha


def title_case_tech(tech):
    """Capitalize a technology phrase for use in a page title."""
    # Don't lowercase words like 'Shinkansen', 'SLIPS', 'GPS', 'Velcro'
    minor = {"and", "or", "the", "a", "an", "of", "in", "on", "at", "for", "to"}
    words = tech.split()
    result = []
    for i, w in enumerate(words):
        if i == 0 or w.lower() not in minor:
            result.append(w[0].upper() + w[1:])
        else:
            result.append(w.lower())
    return " ".join(result)


def build_organism_pages(strategies):
    pages = []
    for s in strategies:
        org = short_organism(s["organism"])
        tech = derive_technology(s)
        keyword = f"how {org.lower()} inspired {tech}"
        title = f"How {org} Inspired {title_case_tech(tech)}"
        pages.append({
            "page_type": "organism",
            "keyword": keyword,
            "title": title,
            "slug": s["slug"],
            "strategy_ids": [s["id"]],
            "taxonomy_group": s["biomimicry_taxonomy_group"],
            "industries": [t.strip() for t in (s["industry_tags"] or "").split(",") if t.strip()],
            "description": (
                f"How the {org.lower()} inspired {tech} — "
                f"the biological mechanism, the engineering principle, and real-world applications."
            ),
        })
    return pages


def build_function_pages(strategies):
    grouped = defaultdict(list)
    for s in strategies:
        group = s["biomimicry_taxonomy_group"]
        if group:
            grouped[group].append(s["id"])

    pages = []
    for group, ids in sorted(grouped.items()):
        display = TAXONOMY_DISPLAY.get(group, group.lower())
        keyword = f"biomimicry for {display}"
        slug = f"biomimicry-for-{slugify(display)}"
        pages.append({
            "page_type": "function",
            "keyword": keyword,
            "title": f"Biomimicry for {display.title()}: How Nature Solves the Problem",
            "slug": slug,
            "strategy_ids": ids,
            "taxonomy_group": group,
            "industries": [],
            "description": (
                f"How nature's {display} strategies have inspired engineering solutions — "
                f"{len(ids)} biological examples with real-world applications."
            ),
        })
    return pages


def build_industry_pages(strategies):
    grouped = defaultdict(list)
    for s in strategies:
        tags = [t.strip().lower() for t in (s["industry_tags"] or "").split(",") if t.strip()]
        for tag in tags:
            canonical = INDUSTRY_CANONICAL.get(tag, tag)
            if canonical in INDUSTRY_DISPLAY:
                grouped[canonical].append(s["id"])

    # Deduplicate strategy IDs per industry
    for k in grouped:
        grouped[k] = sorted(set(grouped[k]))

    pages = []
    for industry, ids in sorted(grouped.items(), key=lambda x: -len(x[1])):
        if len(ids) < 2:
            continue  # Skip single-entry industries
        display = INDUSTRY_DISPLAY[industry]
        keyword = f"biomimicry in {display.lower()}"
        slug = f"biomimicry-in-{slugify(display)}"
        pages.append({
            "page_type": "industry",
            "keyword": keyword,
            "title": f"Biomimicry in {display}: Nature-Inspired Solutions",
            "slug": slug,
            "strategy_ids": ids,
            "taxonomy_group": None,
            "industries": [industry],
            "description": (
                f"How nature is transforming {display.lower()} — "
                f"{len(ids)} biomimicry examples with real-world products and research."
            ),
        })
    return pages


def build_list_pages(strategies, curated):
    strategy_by_id = {s["id"]: s for s in strategies}
    pages = []

    for spec in curated:
        # Determine strategy IDs for this list
        if "manual_ids" in spec:
            ids = spec["manual_ids"]
        else:
            ids = []
            for s in strategies:
                tags = [t.strip().lower() for t in (s["industry_tags"] or "").split(",")]
                industry_match = (
                    spec["industry_filter"] is None or
                    spec["industry_filter"].lower() in tags
                )
                taxonomy_match = (
                    spec["taxonomy_filter"] is None or
                    s["biomimicry_taxonomy_group"] == spec["taxonomy_filter"]
                )
                if industry_match and taxonomy_match:
                    ids.append(s["id"])

        # Find the number in the title (e.g. "10 Best...", "...7 Biomimicry Examples")
        # Cap IDs to that number, then rewrite the title to reflect actual count.
        num_match = re.search(r"\b(\d+)\b", spec["title"])
        title = spec["title"]
        if num_match:
            cap = int(num_match.group(1))
            ids = ids[:cap]
            actual = len(ids)
            if actual != cap:
                title = title.replace(num_match.group(1), str(actual), 1)

        pages.append({
            "page_type": "list",
            "keyword": spec["keyword"],
            "title": title,
            "slug": spec["slug"],
            "strategy_ids": ids,
            "taxonomy_group": spec.get("taxonomy_filter"),
            "industries": [spec["industry_filter"]] if spec.get("industry_filter") else [],
            "description": spec["description"],
        })

    return pages


def main():
    conn = sqlite3.connect(DB_PATH)
    strategies = fetch_strategies(conn)
    conn.close()

    organism_pages  = build_organism_pages(strategies)
    function_pages  = build_function_pages(strategies)
    industry_pages  = build_industry_pages(strategies)
    list_pages      = build_list_pages(strategies, CURATED_LISTS)

    all_pages = organism_pages + function_pages + industry_pages + list_pages

    # Check for slug collisions
    slugs = [p["slug"] for p in all_pages]
    dupes = [s for s in slugs if slugs.count(s) > 1]
    if dupes:
        print(f"WARNING: Duplicate slugs detected: {set(dupes)}")

    plan = {
        "meta": {
            "strategy_count": len(strategies),
            "page_counts": {
                "organism":  len(organism_pages),
                "function":  len(function_pages),
                "industry":  len(industry_pages),
                "list":      len(list_pages),
                "total":     len(all_pages),
            },
        },
        "pages": all_pages,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"Keyword plan written to: {os.path.abspath(OUT_PATH)}")
    print()
    print(f"  Organism pages:  {len(organism_pages)}")
    print(f"  Function pages:  {len(function_pages)}")
    print(f"  Industry pages:  {len(industry_pages)}")
    print(f"  List pages:      {len(list_pages)}")
    print(f"  -------------------------")
    print(f"  Total:           {len(all_pages)}")


if __name__ == "__main__":
    main()
