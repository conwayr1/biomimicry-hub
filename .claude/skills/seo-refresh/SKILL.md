---
name: seo-refresh
description: Data-driven SEO and monetization refresh for the Biomimicry Hub site. Analyzes a Google Search Console export, diagnoses underperforming pages, proposes a prioritized worklist, and on approval deepens content, fixes click-through rate, resolves cannibalization, plans new articles, and audits affiliate programs. Use when the user asks to review site performance, run the SEO refresh, analyze Search Console data, check how the site is doing, find what to write next, or evaluate affiliate and monetization options.
---

# SEO & monetization refresh

A repeatable cycle for `biomimicry-seo/` (Hugo site at https://biomimicry-hub.com).
Each run answers two questions: **did last cycle's changes work**, and **what is
the highest-leverage thing to do next**.

## Operating rule

**Analyze, then propose, then stop.** Phases 1–3 are automatic. Do not edit
content, change affiliate links, commit, or push until the user approves the
worklist. Affiliate program changes are business decisions — research and
recommend, never sign up or swap links unilaterally.

---

## Phase 1 — Intake

Ask the user to export fresh data if they have not already:

> **Both exports, please — they find different problems.**
>
> 1. **Performance:** Search Console → property `https://biomimicry-hub.com` →
>    **Performance** → date **Last 28 days** → **Export** → **Download XLSX**.
> 2. **Coverage:** **Indexing → Pages** → **Export**. Then click the
>    **"Not found (404)"** row (and any other row with a real count) and export
>    that drilldown too — the URL list lives one level deeper than it looks.
>
> Leave them all in Downloads.

Then run both scripts:

```bash
py .claude/skills/seo-refresh/scripts/analyze_gsc.py        # rankings
py .claude/skills/seo-refresh/scripts/check_indexation.py   # indexation + links
```

`analyze_gsc.py` auto-finds the newest `*Performance-on-Search*.xlsx`, prints
headline metrics versus the previous run, and flags the five ranking patterns.
Add `--save` once the run is accepted to append it to `data/seo-baseline.json`.

`check_indexation.py` parses the Coverage exports (indexed-vs-not trend, issue
counts, and the 404 URL list grouped by prefix to expose systematic causes) and,
given `--build <dir>`, crawls a Hugo build for broken internal links, baseURL
leakage, and sitemap sanity.

Always use **28-day windows** so runs are comparable.

## Phase 2 — Diagnose

**Check indexation first.** An unindexed page cannot rank at all, so indexation
problems outrank every ranking optimization. If `check_indexation.py` reports the
indexed count falling, make that the headline finding regardless of how good the
Performance numbers look. Likewise a 404 or a broken sitewide link beats any
amount of content polish.

The October run is the cautionary example: Performance looked excellent (clicks
+95%, position 19.6 → 8.3) while indexed pages had quietly fallen 92 → 83 and a
footer link to `/about/` was 404ing on all 161 pages.

Then the ranking patterns. Interpret them, don't just relay them:

1. **DEEPEN** — real impressions, ranked just off page 1, thin content. The
   highest-value pattern. Fix with the deepening playbook.
2. **CTR** — ranks on page 1 but earns no clicks. A snippet problem, not a
   ranking problem. Fix titles and meta descriptions only.
3. **CANNIBALISATION** — two *hub* pages (list / industry / function) competing
   for one topic. Give each a distinct intent; don't delete one.
4. **QUERY GAPS** — demand where the site ranks 20+. Either expand an existing
   page or write a new one.
5. **DUPLICATE BOILERPLATE** — shared sentences across templated pages. Strong
   suppressor; worth fixing in batches.

See `reference/patterns.md` for how to read each one and what *not* to conclude.

**Always state the sample size.** This site measures in tens of clicks. Page-level
swings of ±60 impressions are frequently noise. Report direction and magnitude,
flag what is too small to trust, and never present a single page's movement as
proof on its own.

## Phase 3 — Propose

Produce a prioritized worklist: what, why (tied to specific numbers), expected
effect, and effort. Order by impressions × fixability. Then **stop and ask**.

Also report movement on everything changed last cycle — including anything that
got worse.

## Phase 4 — Execute (after approval)

Follow `reference/playbook.md` for the deepening and CTR templates. In short:

- **Deepen**: ~1,000+ words, themed sections grouped by what the thing *does*,
  one inline link per entry, a "what these share" section, an FAQ answering the
  literal queries from the data, re-curate weak entries out.
- **CTR**: rewrite title (≤ 55 chars) and meta description (145–158 chars),
  leading with a specific fact rather than a formula.
- **Cannibalisation**: give each page a separate job and cross-link them.

## Phase 5 — New articles

When the DEEPEN pattern comes back empty, the gains from optimizing existing
pages are largely harvested and **coverage becomes the lever**. Source ideas from:

- Queries in the data with no dedicated page
- Query clusters ranking 20+ that no page targets directly
- Google Trends for rising adjacent topics
- Gaps in the database (`strategies` rows with no list-page appearance)

## Phase 6 — Affiliate audit

See `reference/affiliate-audit.md`. Order matters: **instrument before
optimizing** — without click tracking you cannot tell "never clicked" from
"clicked but didn't convert", and those have opposite fixes.

## Phase 7 — Verify & ship

Never skip verification; it has caught real bugs every cycle.

```bash
# Hugo is NOT installed on this machine. Fetch the matching version to temp:
# https://github.com/gohugoio/hugo/releases/download/v0.160.1/hugo_extended_0.160.1_windows-amd64.zip
"$HUGO" --gc --minify --destination "$TEMP/bh_verify"
```

Check: build succeeds (202 pages), word counts moved as intended, every
`strategy_slugs` entry and inline `/organisms/<slug>/` link resolves, titles and
descriptions are within length, and no page lost content unintentionally.

Then commit with a message explaining *why*, update `BACKLOG.md`, push, and
re-run the analyzer with `--save`.

---

## Known traps

Hard-won; re-learning these costs hours.

- **`generate_content.py` with `--force` destroys hand-written content.** It is
  guarded now (skips existing files by default). Never pass `--force` casually.
- **Do not run `fix_meta_descriptions.py`.** It blunt-trims to 159 chars + "...",
  which truncates descriptions mid-word. Superseded by `fix_organism_meta.py`.
- **Hugo is not installed.** Download v0.160.1 extended (matching `deploy.yml`)
  to a temp dir for verification builds.
- **Minified HTML strips attribute quotes.** Grepping for `href="..."` finds
  nothing in `public/`. Match `/organisms/` rather than quoted attributes.
- **`grep -c` exits 1 on zero matches**, silently breaking `&&` chains.
- **Set `PYTHONIOENCODING=utf-8`** — the console is cp1252 and dies on em dashes.
- **Numbers in titles can be load-bearing.** "10 Most Famous…" ranks for
  "10 examples of biomimicry". Check the query data before changing a count.
- **Impressions falling while position improves is often good** — the page
  stopped appearing for junk queries it never converted. Check clicks, not
  impressions, before calling it a regression.
- **Never let the deploy workflow override `baseURL`.** `deploy.yml` used to pass
  `--baseURL "${{ steps.pages.outputs.base_url }}/"`, which before the custom
  domain was configured resolved to the GitHub Pages *project path* and baked a
  `/biomimicry-hub/` prefix into every URL. Google indexed 27 of them and they all
  404. `config.toml` is the single source of truth; `check_indexation.py` asserts
  the prefix never reappears.
- **Antivirus quarantines `hugo.exe`** from the scratchpad between runs. If the
  binary vanishes or extraction throws "access denied", re-extract to a new
  directory name rather than retrying the same path.
- **Don't trust counts from summarized web fetches.** A "231 URLs in the sitemap"
  figure from a fetch summary was wrong and sent me chasing 70 URLs that were
  never missing. Count locally from the build.
