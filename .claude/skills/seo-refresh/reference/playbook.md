# Execution playbook

The templates that produced the Sept→Oct result: clicks +95%, CTR 1.47%→2.86%,
average position 19.6→8.3.

## Deepening a thin hub page

The proven case: the robotics list page went 135 → 1,094 words and moved from
position 18.1 to 8.0, clicks 2 → 9.

**Structure**

1. **Opening** (2 short paragraphs). Lead with the real-world tension, not a
   definition. Work the head query in naturally once, bolded.
2. **Themed sections**, grouped by *what the thing does* — not by organism, not
   alphabetically. Robotics used: gripping / soft bodies / sensing / navigation /
   swarms. Architecture used: climate control / responsive facades / structure.
3. **One inline link per entry**, in prose, at first mention:
   `[Tokay gecko](/organisms/gecko-adhesion-dry-adhesives/)`. These carry more
   weight than the template's auto-generated card grid.
4. **"What these share"** — 3–5 transferable principles. This is the section that
   makes the page worth linking to rather than just another list.
5. **FAQ** — answer the literal queries from the GSC data, in their words.
   Queries like "what is biomimicry in robotics" become H3s verbatim.
6. End with `## The full list at a glance` — the list template renders its card
   grid immediately after `.Content`, so this heading gives those cards a home.

**Re-curate while deepening.** The robotics list had pinecone facades and bat-wing
aircraft in it; swapping them for genuinely robotic entries (elephant trunk, fire
ant rafts, starling swarms) sharpened the topical signal. Check `industry_tags`
in the database to find better fits.

**Accuracy**: pull every factual claim from the database row — `biological_function`,
`key_principle`, `human_application`, `real_world_products`. Named products and
real numbers are what make the page non-generic. Never invent a statistic.

## CTR rewrite (title + meta)

For pages ranking on page 1 with no clicks. **Do not touch body content** — the
ranking is already fine, the snippet is the problem.

- **Title**: ≤ 55 characters (a 16-char ` | Biomimicry Hub` suffix is appended).
  Front-load the keyword. Prefer a concrete hook over a category label:
  *"How the Boxfish Inspired the Mercedes Bionic Car"* beats
  *"How Boxfish Inspired Aerodynamic Vehicle Design"*.
- **Description**: 145–158 characters. Lead with the single most surprising
  specific fact, then what it became:
  > "Woodpeckers strike 20 times a second at 1,200 g without brain damage. Four
  > nested structures make it possible — and now shape helmet and black-box design."
- Never end mid-word, and never reuse a formula across pages.

Before changing a title, check whether a number in it is matching a query
("10 Most Famous…" ranks for "10 examples of biomimicry").

## Resolving cannibalisation

Two hub pages competing. **Do not delete one** — give each a distinct job.

The architecture case: the list page (pos 12) and industry page (pos 61) both
targeted "examples", and the industry page's strategy set was a strict superset
of the list's.

- **List page** → the *examples* intent. Curated walkthrough, themed.
- **Industry page** → the *industry* intent. The business case, real projects,
  adoption barriers, where the field is heading. No example-listing.
- **Cross-link both ways**, explicitly, so the hierarchy is legible.

Result: industry page went 61 → 20, list page 12 → 8.8 with impressions up
118 → 196.

## Fixing duplicate boilerplate

Templated sections share sentences verbatim — currently 20 industry pages, 7
function pages, 8 list pages. Fix in batches of ~5 and verify between batches.

Each page needs genuinely page-specific prose. Use the architecture industry page
as the model: energy case → where it shows up → projects that proved it → what
blocks adoption → where it is heading → FAQ.

## Verification checklist

```bash
# word counts moved as intended
wc -w < content/lists/<slug>.md

# every strategy_slug and inline link resolves
# (script this; broken links have slipped through manual checks)

# build cleanly — 202 pages, zero errors
"$HUGO" --gc --minify --destination "$TEMP/bh_verify"

# titles/descriptions within length, in the RENDERED html
# note: minification strips attribute quotes
```
