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
- [x] Deepen **architecture** list page — 126 -> 1,074 words, expanded to 10 entries (2026-09-04).
- [x] Deepen **materials-science** list page — 123 -> 1,119 words, re-curated to 12 (2026-09-04).
- [x] Deepen **most-famous** list page — 141 -> 1,066 words, kept at 10 to preserve the "10 examples of biomimicry" match (2026-09-04).
- [x] Quick CTR win: rewrote titles + meta descriptions on 10 page-1, zero-click pages
      (~215 impressions at 0% CTR: woodpecker, boxfish, mantis shrimp, cocklebur, thorny devil,
      aerospace list, adhesives list, sports-equipment, packaging, electronics) (2026-09-04).
- [x] Fixed sitewide <title> bloat: the full site tagline was appended to all 202 pages
      (54-char suffix; home page doubled its own title at 106 chars). Now uses a short
      `brand` param — saves 38 chars per page (2026-09-04).
- [x] **Title/description debt — done (2026-09-04).** Fixed the duplicate description formula
      (all 82 organism descriptions are now unique and specific), the sentence-case organism
      title bug, and 4 pages whose meta had been truncated mid-word by fix_meta_descriptions.py.
      Applied via scripts/fix_organism_meta.py, which only touches pages still carrying the
      boilerplate, so hand-written meta is left alone.
- [x] **Fixed a data-loss bug: generate_content.py overwrote every file** despite the README
      claiming it skipped existing ones. It now preserves existing pages and reports what it kept;
      --force is required to overwrite (2026-09-04).
- [ ] Retire or fix `fix_meta_descriptions.py` — it blunt-trims to 159 chars + "..." and is what
      truncated those 4 descriptions mid-word. Superseded by fix_organism_meta.py for organisms.
- [x] Fix the architecture **industry** page — 219 -> 959 words, repositioned to industry analysis
      (energy case, built projects, adoption barriers, direction) instead of a second examples list.
      Cannibalization resolved by giving each page a distinct intent + explicit cross-links (2026-09-04).
- [ ] **HIGH PRIORITY — systemic duplicate content across industry pages.** All 21 industry pages share
      an identical "What These Strategies Have in Common" block, 8 share the same opening filler sentence,
      and they average only 243 words. This is near-duplicate thin content across 21 URLs and is the most
      likely cause of industry pages ranking pos 33-61 (aerospace 33, water-tech 35, environmental 54,
      textiles 58, architecture was 61). Architecture is now fixed as the template — replicate that
      treatment (unique industry-specific prose, no shared block) across the remaining 20.
- [ ] Consider new page types: comparison pages ("X adhesive vs Y adhesive") and mechanism "how it works" explainers.

## Indexation (found 2026-10-06 via Coverage export)
- [x] Fixed `/about/` 404 — footer linked it from all 161 pages but the page did not
      exist. Created content/about.md with sourcing methodology + a proper affiliate
      disclosure (Amazon Associates requires one) (2026-10-06).
- [x] Fixed the baseURL override in deploy.yml that caused 27 indexed `/biomimicry-hub/*`
      URLs to 404. config.toml is now the single source of truth (2026-10-06).
- [ ] **Indexed pages are declining: 92 -> 83** (Aug 4 -> Sep 20), not-indexed 59 -> 68.
      Google knows 151 URLs; roughly half are not indexed. This outranks ranking work.
      Re-check after the /about/ and baseURL fixes land.
- [x] Removed 34 orphan taxonomy pages via `disableKinds = ["taxonomy", "term"]`.
      They were linked from nowhere, duplicated the 21 hand-written industry pages in
      the same URL namespace, and matched the "Alternate page with proper canonical
      tag - 32 pages" count exactly. Sitemap 162 -> 128 URLs, all real content
      preserved (2026-10-06).
- [ ] 8 pages "Crawled - currently not indexed" = thin-content signal; cross-reference
      with the DEEPEN list.

## Housekeeping
- [ ] Homepage still hardcodes "83 documented strategies"; database has 82. Fold into a future edit.
