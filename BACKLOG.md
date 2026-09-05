# Backlog

Running list of improvements to come back to. Newest at top.

## Content & visuals
- [ ] **Improve diagram visuals.** The mechanism diagrams (`scripts/generate_diagrams.py`,
      output in `static/images/diagrams/`) are a solid v1 in an editorial figure style, but
      there's room to make them richer. Ideas to explore:
      - More specific, hand-tuned motifs per strategy (v1 shares one motif per taxonomy group,
        so all "Move" organisms look alike). Could key the motif off `biomimicry_taxonomy_subgroup`
        or add per-strategy overrides.
      - Better use of the middle panel (illustrate the actual mechanism, not just a generic glyph).
      - Optional: light labels/annotations on the motif; a small scale cue.
      - Consider bespoke diagrams for the top-traffic pages once Google Search Console shows
        which pages get impressions.
- [ ] Add real images (public-domain organism photos) as a second visual layer — see the image
      strategy discussed: NOAA / USFWS / NASA / Wikimedia CC0 only, with attribution tracked in the DB.

## SEO / growth (driven by GSC data pulled 2026-09-04)
GSC baseline (28d): 1,289 impressions, 19 clicks, ~1.5% CTR, avg position ~20.
The four "best-of" list pages carry ~37% of impressions but rank page 2 because they were thin (~130 words). Plan: deepen them to ~1,000+ words with themed sections, internal links, and an FAQ.
- [x] Deepen **robotics** list page — 135 → 1,094 words, re-curated to 12 robotics strategies, FAQ added (2026-09-04).
- [ ] Deepen **architecture** list page (118 impr, pos 12) — same pattern.
- [ ] Deepen **materials-science** list page (97 impr, pos 18).
- [ ] Deepen **most-famous** list page (95 impr, pos 18) — also target the "biomimicry examples/inventions/products" head cluster.
- [ ] Quick CTR win: rewrite titles + meta descriptions on page-1, zero-click pages (woodpecker pos 8, boxfish pos 8, aerospace list pos 10).
- [ ] Fix the architecture **industry** page (76 impr but buried at pos 61) + resolve architecture list/industry cannibalization.
- [ ] Consider new page types: comparison pages ("X adhesive vs Y adhesive") and mechanism "how it works" explainers.

## Housekeeping
- [ ] Homepage still hardcodes "83 documented strategies"; database has 82. Fold into a future edit.
