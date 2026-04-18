"""
generate_content.py — Generates Hugo markdown files for all pages in keyword_plan.json.

Usage:
  python scripts/generate_content.py            # generate all pages
  python scripts/generate_content.py --sample   # generate 1 page of each type only
  python scripts/generate_content.py --type organisms  # one type only
"""

import sqlite3
import json
import os
import re
import sys
import textwrap
from datetime import date
from collections import defaultdict

DB_PATH      = os.path.join(os.path.dirname(__file__), "..", "database", "biomimicry.db")
PLAN_PATH    = os.path.join(os.path.dirname(__file__), "..", "data", "keyword_plan.json")
CONTENT_ROOT = os.path.join(os.path.dirname(__file__), "..", "content")

TODAY = date.today().isoformat()

# ── Helpers ────────────────────────────────────────────────────────────────────

def slug_to_title(slug):
    return slug.replace("-", " ").title()


def wrap(text, width=9000):
    """Return text as a single paragraph — no hard wraps in markdown."""
    return " ".join(text.split())


def fm_list(items):
    """Format a Python list for TOML front matter."""
    return "[" + ", ".join(f'"{i}"' for i in items) + "]"


def write_page(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def fetch_all_strategies(conn):
    rows = conn.execute("""
        SELECT id, organism, organism_scientific, kingdom, habitat,
               biological_function, biomimicry_taxonomy_group,
               biomimicry_taxonomy_subgroup, human_application,
               real_world_products, industry_tags, key_principle,
               source_url, slug
        FROM strategies ORDER BY id
    """).fetchall()
    cols = ["id","organism","organism_scientific","kingdom","habitat",
            "biological_function","biomimicry_taxonomy_group",
            "biomimicry_taxonomy_subgroup","human_application",
            "real_world_products","industry_tags","key_principle",
            "source_url","slug"]
    return {r[0]: dict(zip(cols, r)) for r in rows}


def find_related(strategy, all_strategies, n=4):
    """Return up to n slugs of related strategies (same taxonomy or shared industry)."""
    own_tags = set(t.strip().lower() for t in (strategy["industry_tags"] or "").split(",") if t.strip())
    own_group = strategy["biomimicry_taxonomy_group"]
    scored = []
    for sid, s in all_strategies.items():
        if sid == strategy["id"]:
            continue
        score = 0
        if s["biomimicry_taxonomy_group"] == own_group:
            score += 2
        other_tags = set(t.strip().lower() for t in (s["industry_tags"] or "").split(",") if t.strip())
        score += len(own_tags & other_tags)
        if score > 0:
            scored.append((score, s["slug"]))
    scored.sort(reverse=True)
    return [slug for _, slug in scored[:n]]


# ── Organism page ──────────────────────────────────────────────────────────────

HOOK_TEMPLATES = [
    "What if the solution to {problem} was already solved — by a {organism} millions of years ago?",
    "Engineers spent decades trying to crack {problem}. Then someone looked at a {organism}.",
    "Few animals have inspired as much engineering curiosity as the {organism} — and for good reason.",
    "Nature has had {years} million years to solve hard engineering problems. The {organism} cracked {problem} a long time ago.",
    "The {organism} doesn't have a research lab or a materials science team. It doesn't need one.",
]

HOOK_DATA = {
    # id: (problem, years)
    1:  ("reversible dry adhesion", "50"),
    2:  ("self-cleaning surfaces", "100"),
    3:  ("turbulent drag reduction", "400"),
    4:  ("pressure wave management at high speed", "50"),
    5:  ("passive climate control in buildings", "30"),
    6:  ("high-performance structural fibers", "350"),
    7:  ("stall-resistant lift generation", "30"),
    8:  ("permanent, pigment-free color", "50"),
    9:  ("simple releasable fastening", "50"),
    10: ("wet-surface adhesion", "20"),
    11: ("passive aerodynamic stability", "20"),
    12: ("water harvesting from fog", "50"),
    13: ("maximally efficient space packing", "30"),
    14: ("humidity-driven shape change", "100"),
    15: ("multi-layer shock absorption", "50"),
    16: ("high-pressure chemical ejection", "50"),
    17: ("wet-condition gripping", "20"),
    18: ("impact resistance in composites", "20"),
    19: ("ultra-fast collision detection", "200"),
    20: ("omniphobic surfaces", "30"),
    21: ("high-speed intake airflow management", "50"),
    22: ("active, full-gamut color change", "100"),
    23: ("passive, clog-resistant filtration", "200"),
    24: ("long-distance navigation without GPS", "50"),
    25: ("closed-loop agricultural systems", "50"),
    26: ("combining stiffness and toughness", "400"),
    27: ("large-volume reversible expansion", "100"),
    28: ("precision liquid-jet targeting", "50"),
    29: ("ultrafast movement without motors", "50"),
    30: ("fracture-resistant brittle materials", "500"),
    31: ("high-efficiency cold light production", "500"),
    32: ("navigation by light polarization", "50"),
    33: ("long-range underwater sound transmission", "50"),
    34: ("accessing otherwise indigestible nutrients", "50"),
    35: ("passive aerodynamic shape adaptation", "50"),
    36: ("shear-resistant lightweight lattices", "500"),
    37: ("low-energy foam fabrication", "100"),
    38: ("surviving complete cellular freezing", "50"),
    39: ("position tracking without landmarks", "50"),
    40: ("on-demand stiffness switching in materials", "100"),
    41: ("maximizing structural load capacity per gram", "100"),
    42: ("reversing cellular differentiation", "100"),
    43: ("salt-free water filtration at low energy", "50"),
    44: ("decentralized collective decision-making", "30"),
    45: ("lift from a membrane wing", "50"),
    46: ("passive water-mediated thermal regulation", "1000"),
    47: ("residue-free reversible adhesion on wet surfaces", "50"),
    48: ("colonizing bare rock to create soil", "400"),
    49: ("passive danger signaling", "50"),
    50: ("cavitation as a force multiplier", "50"),
    51: ("multi-cue cognitive map building", "50"),
    52: ("biocompatible electrical energy generation", "100"),
    53: ("efficient low-speed lift generation", "300"),
    54: ("optical aberration elimination at micro scale", "500"),
    55: ("passive electric field detection", "50"),
    56: ("passive directional fluid transport", "50"),
    57: ("sub-ambient passive radiative cooling", "50"),
}


def generate_organism_page(s, all_strategies, plan_page):
    slug    = s["slug"]
    org     = s["organism"]
    sci     = s["organism_scientific"] or ""
    kingdom = s["kingdom"] or "Animal"
    habitat = s["habitat"] or "various habitats"
    bf      = wrap(s["biological_function"])
    ha      = wrap(s["human_application"])
    kp      = wrap(s["key_principle"])
    rp      = s["real_world_products"] or ""
    src     = s["source_url"] or "https://asknature.org"
    group   = s["biomimicry_taxonomy_group"] or ""
    tags    = [t.strip() for t in (s["industry_tags"] or "").split(",") if t.strip()]
    related = find_related(s, all_strategies)

    title   = plan_page["title"]
    desc    = plan_page["description"]

    hdata   = HOOK_DATA.get(s["id"], ("this engineering challenge", "100"))
    hook    = (f"What if the solution to {hdata[0]} had already been perfected — "
               f"by a {org.lower()} over {hdata[1]} million years of evolution?")

    # Real-world products sentence
    rp_sentence = ""
    if rp:
        rp_sentence = f"\n\nReal-world implementations include: {rp}."

    # Subgroup context
    subgroup_line = ""
    if s["biomimicry_taxonomy_subgroup"]:
        subgroup_line = (f"In the language of biomimicry, this falls under the "
                         f"**{group} › {s['biomimicry_taxonomy_subgroup']}** category — "
                         f"one of the most actively researched areas in bio-inspired engineering.")

    industries_str = ", ".join(tags) if tags else "engineering"

    content = f"""\
+++
title       = "{title}"
description = "{desc}"
date        = "{TODAY}"
slug        = "{slug}"
type        = "organisms"
kingdom     = "{kingdom}"
organism_scientific = "{sci}"
habitat     = "{habitat}"
taxonomy_group = "{group}"
industries  = {fm_list(tags)}
related_slugs = {fm_list(related)}
key_principle = "{kp.replace('"', "'")}"
source_url  = "{src}"
+++

{hook}

The answer — as engineers have discovered — is yes. The **{org}** (*{sci}*) has evolved a
solution to this problem that is elegant, efficient, and increasingly influential across
{industries_str}. This page explains what the {org.lower()} does, why it matters to
engineers, and what has already been built as a result.

## The Natural Innovation

{bf}

The {org.lower()} lives in {habitat}. Over millions of years of evolutionary pressure,
this capability became not just useful but essential — a matter of survival. That kind of
long-term optimization is precisely what makes biological systems such productive starting
points for engineering research.

{subgroup_line}

## The Design Principle

What makes this biologically remarkable also makes it technically transferable. Strip away
the biology and you're left with a core engineering insight:

> {kp}

This principle is deceptively simple to state but difficult to achieve with conventional
manufacturing methods — which is exactly why engineers have found it so valuable. Nature
arrives at this solution through materials and processes that are often room-temperature,
water-based, and self-assembling. That stands in sharp contrast to the high-energy,
high-precision fabrication that human industry typically relies on.

## Human Applications

{ha}
{rp_sentence}

The translation from biology to engineering is rarely direct — researchers typically spend
years understanding the mechanism at a molecular or microstructural level before they can
replicate it synthetically. But the payoff can be significant: solutions that are lighter,
stronger, more energy-efficient, or capable of things no conventional approach can match.

## Why This Matters

Biomimicry works not because nature is clever for its own sake, but because evolution is
an extraordinarily long and selective optimization process. Every feature of the {org.lower()}
described here has been tested across millions of generations in real-world conditions.
It either worked — conferring survival advantage — or it disappeared.

That track record gives bio-inspired engineers a valuable head start: they're not
guessing at solutions, they're reverse-engineering ones that are already proven.

{{{{< affiliate "learn-biomimicry" >}}}}
{{{{< affiliate "amazon-book" >}}}}
"""
    return content


# ── Function page ──────────────────────────────────────────────────────────────

FUNCTION_INTROS = {
    "Protect": (
        "Nature faces the same fundamental protective challenges as human engineers: "
        "how to resist fracture, repel unwanted substances, absorb impact, and signal "
        "danger — all while keeping systems lightweight and energy-efficient. The solutions "
        "evolution has arrived at are often counter-intuitive and structurally sophisticated "
        "in ways that conventional materials science is only beginning to match."
    ),
    "Move": (
        "Locomotion is one of evolution's oldest engineering problems. Over hundreds of "
        "millions of years, organisms have refined strategies for moving through air, water, "
        "and across surfaces with extraordinary efficiency, speed, and precision. Each "
        "environment imposes different physical constraints — and biology has found "
        "specialized answers to every one of them."
    ),
    "Make": (
        "Biological manufacturing operates under remarkable constraints: ambient temperature, "
        "water as the primary solvent, no toxic feedstocks, and structures that must assemble "
        "themselves. The result is a toolkit of materials — silk, bone, nacre, honeycomb — "
        "that combine properties (toughness + stiffness, strength + flexibility) that remain "
        "difficult or impossible to replicate in a conventional factory."
    ),
    "Modify": (
        "The ability to change — shape, stiffness, color, behavior — in response to "
        "environmental conditions is one of nature's most powerful capabilities. Organisms "
        "that can adapt in real time gain enormous advantages. Engineers are now learning "
        "how to embed that same adaptive capacity into materials and structures."
    ),
    "Process": (
        "Every organism is a chemical processing plant: filtering water, converting sunlight, "
        "storing energy, managing heat. Biology performs these functions with a precision and "
        "efficiency that industrial processes rarely match — and without the toxic byproducts "
        "that conventional chemistry often generates."
    ),
    "Sense": (
        "Biological sensing systems are extraordinarily diverse and sensitive. Eyes that "
        "detect single photons, ears that hear infrasound across ocean basins, noses that "
        "identify molecules at parts-per-trillion concentrations. Each represents a different "
        "engineering approach to information gathering — many of which remain more sensitive, "
        "more energy-efficient, or more compact than anything human engineers have built."
    ),
    "Attach": (
        "Adhesion is a deceptively complex problem. The right amount of stickiness — "
        "strong enough to hold, weak enough to release — has challenged engineers for "
        "decades. Biological systems have arrived at a remarkable diversity of attachment "
        "strategies: dry friction, wet capillary forces, molecular bonds, mechanical "
        "interlocking, and viscoelastic flow. Each works optimally in specific conditions."
    ),
}

FUNCTION_PRINCIPLE_INTROS = {
    "Protect":  "Across these protective strategies, several engineering themes recur:",
    "Move":     "These locomotion strategies share a set of underlying physical principles:",
    "Make":     "Nature's manufacturing strategies converge on a set of structural principles:",
    "Modify":   "These adaptive strategies share key enabling mechanisms:",
    "Process":  "Nature's processing strategies point to a set of transferable principles:",
    "Sense":    "These sensing strategies highlight several engineering design patterns:",
    "Attach":   "Nature's attachment strategies reveal consistent underlying mechanisms:",
}

FUNCTION_PRINCIPLES = {
    "Protect":  [
        "**Hierarchy defeats brittleness.** Structures organized at multiple length scales (nano → micro → macro) distribute stress rather than concentrating it.",
        "**Geometry beats mass.** Corrugation, helicoidal layering, and brick-and-mortar arrangements provide fracture resistance without adding weight.",
        "**Passive signaling works.** High-contrast color patterns communicate danger without energy expenditure or active mechanisms.",
    ],
    "Move":     [
        "**Boundary layer management is everything.** Whether reducing drag or preventing stall, controlling the fluid immediately adjacent to a surface drives efficiency.",
        "**Passive stability reduces control overhead.** Shapes that self-correct in fluid flow need less active steering energy.",
        "**Stored elastic energy enables power amplification.** Spring-latch mechanisms release energy faster than muscles can contract.",
    ],
    "Make":     [
        "**Hierarchy creates emergent properties.** Combining stiff and compliant phases at multiple scales produces materials that are simultaneously tough and strong.",
        "**Geometry is a material.** A honeycomb, a corrugation, or a helicoidal stack achieves structural performance that its constituent material alone could never match.",
        "**Self-assembly reduces fabrication cost.** Biological structures grow themselves from simple molecular building blocks, eliminating precision manufacturing.",
    ],
    "Modify":   [
        "**Bilayer designs enable autonomous response.** Two layers with different expansion properties create bending or curling driven by environmental conditions alone.",
        "**Cross-link density controls stiffness.** Changing the density of molecular bonds in a polymer or fiber matrix tunes material modulus across orders of magnitude.",
        "**Reversibility requires metastability.** Bistable geometries and reversible chemistry allow repeated switching without energy accumulation.",
    ],
    "Process":  [
        "**Selectivity over brute force.** Biological filters and channels achieve separation through precise geometry and surface chemistry, not pressure.",
        "**Symbiosis extends metabolic reach.** Partnering with specialized microorganisms allows organisms to access energy sources their own biochemistry cannot.",
        "**Passive driving forces.** Capillary pressure, osmosis, and convection move fluids without pumps — reducing energy cost to near zero.",
    ],
    "Sense":    [
        "**Multi-modal fusion beats single-sensor precision.** Combining redundant sensory inputs produces navigation and detection that is robust to individual sensor failure.",
        "**Sparse coding is efficient.** Neuromorphic sensors that respond only to biologically relevant signals (looming objects, electric fields) use orders of magnitude less computation than dense imaging.",
        "**Material as sensor.** Structural materials (calcite lenses, silver hairs, scale networks) that perform sensing functions eliminate the need for separate sensor components.",
    ],
    "Attach":   [
        "**Contact geometry determines adhesion mode.** Micro-fibrillar structures are strong in shear but release in peel; viscoelastic fluids behave oppositely. Geometry selects the mechanism.",
        "**Drainage channels prevent hydroplaning.** Structured surfaces maintain thin, uniform fluid films that generate capillary adhesion without flooding the interface.",
        "**Catechol chemistry works anywhere wet.** DOPA-inspired molecules form coordination bonds with metal oxide surfaces — the universal interface present on most natural and manufactured materials.",
    ],
}


def generate_function_page(plan_page, all_strategies):
    group  = plan_page["taxonomy_group"]
    title  = plan_page["title"]
    desc   = plan_page["description"]
    slug   = plan_page["slug"]
    s_ids  = plan_page["strategy_ids"]
    slugs  = [all_strategies[i]["slug"] for i in s_ids if i in all_strategies]

    intro  = FUNCTION_INTROS.get(group, "Nature has evolved remarkable solutions to this challenge.")
    p_intro = FUNCTION_PRINCIPLE_INTROS.get(group, "Several design principles emerge:")
    principles = FUNCTION_PRINCIPLES.get(group, [])
    principles_md = "\n".join(f"- {p}" for p in principles)

    n = len(s_ids)
    content = f"""\
+++
title       = "{title}"
description = "{desc}"
date        = "{TODAY}"
slug        = "{slug}"
type        = "functions"
taxonomy_group = "{group}"
strategy_slugs = {fm_list(slugs)}
+++

## The Challenge

{intro}

This page brings together **{n} biological strategies** that all address the
**{group.lower()}** challenge in different ways — drawn from organisms across kingdoms,
habitats, and evolutionary lineages. Taken together, they reveal a set of design
principles that engineers are actively translating into real-world technologies.

## Key Design Principles

{p_intro}

{principles_md}

Each strategy below illustrates one or more of these principles in action. Click through
to any organism page for the full biological story, the engineering mechanism, and the
products that have already emerged.

{{{{< affiliate "learn-biomimicry" >}}}}
{{{{< affiliate "amazon-book" >}}}}
"""
    return content


# ── Industry page ──────────────────────────────────────────────────────────────

INDUSTRY_INTROS = {
    "medical devices and healthcare": (
        "Healthcare faces engineering problems that are uniquely demanding: materials must be "
        "biocompatible, devices must work in wet, chemically complex environments, and "
        "interventions must be minimally invasive. These are precisely the conditions that "
        "biological systems have evolved to handle. The human body itself is the most complex "
        "engineering system on Earth — and studying how other organisms solve similar problems "
        "is producing a wave of bio-inspired medical technology."
    ),
    "aerospace engineering": (
        "Aerospace engineering demands the most extreme material and aerodynamic performance "
        "of any industry: maximum strength at minimum weight, precise flow control at high "
        "speeds, and structures that survive temperature swings from -60°C to 200°C. "
        "Birds, insects, and marine animals have been solving analogous problems for hundreds "
        "of millions of years — and aerospace engineers are increasingly looking to biology "
        "for solutions that conventional materials and design cannot match."
    ),
    "robotics": (
        "Robots that must operate in the real world — on uneven terrain, in tight spaces, "
        "underwater, or in contact with humans — face challenges that conventional rigid "
        "mechanisms handle poorly. Biological locomotion, sensing, adhesion, and collective "
        "behavior offer blueprints for soft, adaptive, and capable robotic systems. "
        "Bio-inspired robotics is one of the fastest-growing areas of biomimicry research."
    ),
    "materials science": (
        "The materials science community has long known that biological materials — bone, "
        "silk, nacre, wood — achieve property combinations that synthetic materials struggle "
        "to match: simultaneously stiff and tough, strong and lightweight, self-healing. "
        "Understanding the structural principles behind these materials — hierarchy, "
        "anisotropy, controlled porosity — is reshaping how engineers design everything "
        "from aerospace composites to biomedical implants."
    ),
    "architecture and construction": (
        "Buildings are the largest material objects humans produce — and among the most "
        "energy-intensive to operate. Nature offers two centuries of proven solutions to "
        "structural efficiency, passive climate control, and adaptive facades. From "
        "termite-inspired ventilation to lily-pad floor plates to fog-harvesting surfaces, "
        "biomimicry is helping architects design buildings that do more with less."
    ),
    "energy": (
        "The energy sector needs materials and systems that capture, store, and distribute "
        "power more efficiently than current technology allows. Biological systems — which "
        "have been running on solar energy for billions of years — offer surprising models: "
        "passive cooling without refrigerants, wind capture geometries that work at low "
        "speeds, and soft power sources that charge without rigid electrodes."
    ),
    "water technology": (
        "Fresh water scarcity is one of the defining challenges of this century. Biology has "
        "been solving water collection, purification, and transport problems in arid and "
        "marine environments for millions of years — using passive mechanisms, selective "
        "membranes, and capillary networks that require no energy input. These strategies "
        "are now informing a new generation of water technology."
    ),
    "transportation": (
        "Transportation engineering is fundamentally about moving mass through fluids "
        "efficiently. Every vehicle — car, plane, ship, train — is fighting aerodynamic "
        "or hydrodynamic drag, managing stability, and seeking to do so with less energy. "
        "Nature's fastest and most efficient movers have been optimizing these same "
        "problems for hundreds of millions of years."
    ),
    "defense and security": (
        "Defense applications demand performance at extremes: materials that absorb massive "
        "impacts without failing, sensors that detect threats before they arrive, and "
        "systems that navigate without GPS in adversarial environments. Biological systems "
        "have evolved precisely these capabilities — under the ultimate selection pressure "
        "of predator-prey competition."
    ),
    "textiles and wearables": (
        "Modern textiles must do far more than cover the body — they must manage moisture, "
        "regulate temperature, resist contamination, and increasingly, sense and respond to "
        "the wearer. Nature has been building high-performance body coverings for hundreds "
        "of millions of years: shark skin, lotus leaves, silver ant hairs, pinecone scales. "
        "Each offers a different design lesson for the textiles industry."
    ),
    "biotechnology": (
        "Biotechnology operates at the interface of biology and engineering — and biomimicry "
        "in this sector often means borrowing biological mechanisms directly, rather than "
        "abstracting design principles. From spider silk proteins expressed in yeast to "
        "aquaporin membranes assembled in lipid bilayers, bio-inspired biotech is collapsing "
        "the distance between the laboratory and nature."
    ),
    "environmental technology": (
        "Environmental challenges — contamination, plastic pollution, water scarcity, "
        "habitat destruction — require solutions that work at ecosystem scale with minimal "
        "energy input. Biological systems that pioneer harsh environments, sequester carbon, "
        "and filter pollutants naturally are providing blueprints for a new generation of "
        "environmental technology."
    ),
    "electronics and displays": (
        "Electronics miniaturization is reaching physical limits — and biology may point "
        "toward what comes next. Structural color, distributed sensing, flexible substrates, "
        "and low-power bioluminescence represent biological approaches to information "
        "display and detection that work at scales and efficiencies silicon cannot match."
    ),
    "marine engineering": (
        "The ocean is one of the most demanding engineering environments: high pressure, "
        "corrosive saltwater, biofouling, and acoustic complexity. Marine organisms have "
        "evolved solutions to all of these challenges — and their adaptations are informing "
        "ship hull design, underwater acoustics, filtration systems, and subsea adhesives."
    ),
    "packaging": (
        "Packaging must protect its contents efficiently, then disappear — ideally without "
        "leaving a waste stream. Nature's packaging solutions (eggshells, seed pods, "
        "spittlebug foam) are strong, lightweight, and biodegradable by design. "
        "They offer a template for the next generation of sustainable packaging."
    ),
    "sports equipment": (
        "Sports equipment must be simultaneously lightweight, stiff, impact-resistant, and "
        "aerodynamically efficient — a combination of properties that pushes materials "
        "science to its limits. Biological structures that have evolved under similar "
        "physical constraints are providing new design directions."
    ),
    "manufacturing": (
        "Advanced manufacturing increasingly requires precision at micro and nano scales, "
        "the ability to process fragile or wet materials, and fabrication of complex "
        "three-dimensional structures. Biological systems that build intricate structures "
        "at room temperature — from bone to silk to shell — offer manufacturing blueprints "
        "that conventional machining cannot replicate."
    ),
    "agriculture": (
        "Sustainable agriculture must produce more food with less land, water, and chemical "
        "input. Nature's 50-million-year-old farming systems — leafcutter ant fungiculture, "
        "mycorrhizal networks, nitrogen-fixing symbioses — represent highly optimized "
        "closed-loop food production models that modern agriculture is only beginning to emulate."
    ),
    "consumer products": (
        "Consumer products that last longer, clean themselves, use less energy, and work "
        "more intuitively represent a massive market opportunity for biomimicry. Several "
        "of the most commercially successful biomimicry applications — Velcro, Lotusan "
        "paint, Speedo Fastskin — started as observations about everyday organisms."
    ),
    "food science": (
        "Food science biomimicry ranges from cryopreservation inspired by freeze-tolerant "
        "frogs to fermentation systems inspired by leafcutter ant fungiculture. Biology "
        "offers models for processing, preservation, and nutrient conversion that the "
        "food industry is beginning to systematically explore."
    ),
}


def generate_industry_page(plan_page, all_strategies):
    industry = plan_page["industries"][0] if plan_page["industries"] else ""
    title    = plan_page["title"]
    desc     = plan_page["description"]
    slug     = plan_page["slug"]
    s_ids    = plan_page["strategy_ids"]
    slugs    = [all_strategies[i]["slug"] for i in s_ids if i in all_strategies]

    intro_key = industry.lower()
    intro = INDUSTRY_INTROS.get(intro_key, f"Biomimicry is producing significant advances in {industry}.")
    n = len(s_ids)

    content = f"""\
+++
title       = "{title}"
description = "{desc}"
date        = "{TODAY}"
slug        = "{slug}"
type        = "industries"
industries  = {fm_list([industry])}
strategy_slugs = {fm_list(slugs)}
+++

## Why {industry.title()} Needs Nature

{intro}

This page documents **{n} biological strategies** with direct relevance to
{industry.lower()}. Each links to a full organism page with the biological mechanism,
the engineering principle, and the products or research that have already emerged.

## What These Strategies Have in Common

The strategies below — despite coming from organisms as different as beetles, sponges,
and ferns — tend to share a set of properties that make them attractive to {industry.lower()}
engineers:

- **They work at ambient conditions.** Most biological processes run at room temperature
  and pressure, avoiding the energy costs of high-temperature manufacturing.
- **They are hierarchical.** Biological structures are organized at multiple length scales,
  producing emergent properties that no single scale could achieve alone.
- **They are selective.** Whether filtering water, detecting signals, or managing heat,
  biological systems achieve precision through geometry and chemistry rather than brute force.

{{{{< affiliate "learn-biomimicry" >}}}}
{{{{< affiliate "amazon-book" >}}}}
"""
    return content


# ── List page ──────────────────────────────────────────────────────────────────

LIST_INTROS = {
    "best-biomimicry-examples-materials-science": (
        "Materials science has arguably benefited more from biomimicry than any other field. "
        "Bone, silk, nacre, and shark skin have each revealed structural principles that are "
        "reshaping composites, coatings, and surface engineering. Here are ten of the most "
        "impactful nature-inspired materials science breakthroughs."
    ),
    "best-biomimicry-examples-architecture": (
        "Architecture has always borrowed from nature — but biomimicry goes deeper than "
        "aesthetic inspiration. The examples below describe buildings and structural systems "
        "that copy specific biological mechanisms to achieve performance that conventional "
        "engineering cannot match: passive ventilation, humidity-responsive facades, "
        "lightweight floor plates, and fog-harvesting surfaces."
    ),
    "best-biomimicry-examples-robotics": (
        "Robots that work in the real world need to grip, navigate, move, and sense the "
        "way animals do — not the way factory robots do. Biomimicry is producing a new "
        "generation of soft, adaptive robots inspired by geckos, tree frogs, ants, and "
        "locusts. Here are ten of the most significant biology-to-robotics translations."
    ),
    "best-biomimicry-examples-medical-devices": (
        "Medical devices must work inside — or in intimate contact with — the human body. "
        "That means biocompatibility, wet-surface function, and precision that conventional "
        "engineering struggles to achieve. Biology, which built the body in the first place, "
        "is an increasingly productive source of medical device inspiration."
    ),
    "best-biomimicry-examples-aerospace": (
        "Aerospace demands the most extreme performance of any engineering sector. Every gram "
        "matters, every watt of drag has a cost, and failures are catastrophic. Nature's "
        "flyers — and swimmers — have been optimizing for the same physical constraints for "
        "hundreds of millions of years. Here are eight of the most significant aerospace "
        "applications of biomimicry."
    ),
    "nature-inspired-water-solutions": (
        "Water scarcity is one of the defining engineering challenges of this century. "
        "Biological systems have been solving water collection, transport, and purification "
        "in arid and marine environments for millions of years — passively, efficiently, "
        "and without chemical inputs. Here are five nature-inspired approaches that are "
        "informing real water technology."
    ),
    "nature-inspired-adhesives": (
        "Adhesion — the right amount of stickiness, in the right conditions, with clean "
        "release on demand — is a deceptively hard engineering problem. Nature has solved "
        "it in at least five completely different ways, each optimized for a specific "
        "environment and use case. Here are the most instructive examples."
    ),
    "biomimicry-navigation-nature-inspired": (
        "GPS works most of the time. But autonomous vehicles, military robots, and "
        "underground drones need navigation that works when GPS doesn't. Animals navigate "
        "with remarkable precision using polarized light, magnetic fields, step counting, "
        "and multi-cue cognitive maps — all without a satellite network. Here are five "
        "biological navigation strategies that engineers are now replicating."
    ),
    "nature-inspired-structural-materials": (
        "The best structural materials in nature — bone, silk, nacre, honeycomb, the "
        "glass sponge lattice — achieve property combinations that synthetic materials "
        "struggle to match. They do it through hierarchy: organizing matter at multiple "
        "length scales so that each level contributes a different mechanical function. "
        "Here are six of the most instructive natural structural materials."
    ),
    "biomimicry-passive-cooling-energy": (
        "Passive cooling — managing temperature without mechanical refrigeration — is one "
        "of biomimicry's most commercially promising areas. As global temperatures rise "
        "and energy costs increase, technologies that cool buildings and surfaces for free "
        "are attracting serious investment. Nature has been doing this for millions of years."
    ),
    "most-famous-biomimicry-examples": (
        "Some biomimicry examples have become so well-known they've entered popular culture. "
        "Velcro, the Shinkansen bullet train, Lotusan self-cleaning paint, and spider silk "
        "are the cases that appear in every biomimicry introduction — for good reason. "
        "They are clear, well-documented, and commercially significant. Here are the ten "
        "most famous nature-inspired innovations of all time."
    ),
    "biomimicry-defense-military-technology": (
        "Defense applications demand performance at extremes: materials that survive "
        "catastrophic impact, sensors that detect threats before they're visible, navigation "
        "that works in hostile environments. The same selection pressures that produced "
        "mantis shrimp clubs, locust collision avoidance, and desert ant path integration "
        "are exactly what military engineers are trying to replicate."
    ),
}


def generate_list_page(plan_page, all_strategies):
    title  = plan_page["title"]
    desc   = plan_page["description"]
    slug   = plan_page["slug"]
    s_ids  = plan_page["strategy_ids"]
    slugs  = [all_strategies[i]["slug"] for i in s_ids if i in all_strategies]

    intro  = LIST_INTROS.get(slug, desc)

    content = f"""\
+++
title       = "{title}"
description = "{desc}"
date        = "{TODAY}"
slug        = "{slug}"
type        = "lists"
strategy_slugs = {fm_list(slugs)}
+++

{intro}

Each entry below links to a full organism page with the complete biological story,
the engineering mechanism, and real-world products that have already emerged.

{{{{< affiliate "learn-biomimicry" >}}}}
{{{{< affiliate "amazon-book" >}}}}
"""
    return content


# ── Section index pages ────────────────────────────────────────────────────────

def generate_section_indexes():
    sections = {
        "organisms":  ("All Biomimicry Organisms", "Browse all biological strategies in the database — sorted by organism, from gecko to glass sponge."),
        "functions":  ("Biomimicry by Function", "Browse nature-inspired strategies grouped by what they do: move, protect, sense, make, process, attach, or modify."),
        "industries": ("Biomimicry by Industry", "Find nature-inspired innovations relevant to your field — from aerospace to water technology."),
        "lists":      ("Best-Of Biomimicry Lists", "Curated lists of the best biomimicry examples by category, industry, and application."),
    }
    for section, (title, desc) in sections.items():
        path = os.path.join(CONTENT_ROOT, section, "_index.md")
        content = f"""\
+++
title       = "{title}"
description = "{desc}"
+++
"""
        write_page(path, content)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    sample_only  = "--sample" in args
    type_filter  = None
    if "--type" in args:
        i = args.index("--type")
        type_filter = args[i + 1] if i + 1 < len(args) else None

    conn = sqlite3.connect(DB_PATH)
    all_strategies = fetch_all_strategies(conn)
    conn.close()

    with open(PLAN_PATH, encoding="utf-8") as f:
        plan = json.load(f)

    pages = plan["pages"]
    if type_filter:
        pages = [p for p in pages if p["page_type"] == type_filter]

    generate_section_indexes()

    counts = defaultdict(int)
    for page in pages:
        ptype = page["page_type"]
        if sample_only and counts[ptype] >= 1:
            continue

        if ptype == "organism":
            s_id = page["strategy_ids"][0]
            s    = all_strategies.get(s_id)
            if not s:
                continue
            content = generate_organism_page(s, all_strategies, page)
            path    = os.path.join(CONTENT_ROOT, "organisms", f"{page['slug']}.md")

        elif ptype == "function":
            content = generate_function_page(page, all_strategies)
            path    = os.path.join(CONTENT_ROOT, "functions", f"{page['slug']}.md")

        elif ptype == "industry":
            content = generate_industry_page(page, all_strategies)
            path    = os.path.join(CONTENT_ROOT, "industries", f"{page['slug']}.md")

        elif ptype == "list":
            content = generate_list_page(page, all_strategies)
            path    = os.path.join(CONTENT_ROOT, "lists", f"{page['slug']}.md")

        else:
            continue

        write_page(path, content)
        counts[ptype] += 1
        label = "SAMPLE" if sample_only else ""
        print(f"  {label} [{ptype:10}] {page['slug']}")

    print()
    print("Pages generated:")
    for ptype, n in sorted(counts.items()):
        print(f"  {ptype:12} {n}")
    print(f"  {'total':12} {sum(counts.values())}")


if __name__ == "__main__":
    main()
