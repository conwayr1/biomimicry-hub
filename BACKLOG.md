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

## SEO / growth (pending Search Console data)
- [ ] Deepen the pages that get the most impressions (check GSC Performance after ~1-2 weeks;
      sitemap submitted 2026-08-13).
- [ ] Consider new page types: comparison pages ("X adhesive vs Y adhesive") and mechanism
      "how it works" explainers.

## Housekeeping
- [ ] Homepage still hardcodes "83 documented strategies"; database has 82. Fold into a future edit.
