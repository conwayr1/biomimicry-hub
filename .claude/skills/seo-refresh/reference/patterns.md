# Reading the five patterns

How to interpret `analyze_gsc.py` output — including what *not* to conclude.

## Sample size comes first

This site measures in tens of clicks. Before interpreting anything:

- Site-level metrics (total clicks, CTR, average position) are reasonably
  trustworthy — they aggregate everything.
- **Page-level swings are frequently noise.** A page moving ±60 impressions can be
  one query's SERP reshuffling.
- A page at position 8 with 20 impressions and 0 clicks is **not** evidence of a
  CTR problem. Expected clicks there are well under one. Only treat zero-click as
  a signal with meaningful impressions behind it.

Always state the sample size alongside any claim.

## [1] DEEPEN

High impressions + ranked just off page 1 + thin content. **The most reliable
pattern.** Google is already showing the page; it just isn't good enough to rank.

Acting on it moved the robotics page from position 18.1 to 8.0 and 2 → 9 clicks.

When this list comes back empty, the easy ranking gains are harvested — shift
effort to Phase 5 (new articles). An empty DEEPEN list is a *milestone*, not a
failure.

## [2] CTR

Page 1, no clicks. A snippet problem — the title and description aren't earning
the click. Fix meta only; leave the body alone.

Caveats:
- Filter by impressions. See the sample-size note above.
- Check the query behind the page. Sometimes the page ranks for something it
  shouldn't, and the fix is relevance, not copywriting.

## [3] CANNIBALISATION

Two *hub* pages (list / industry / function) on one topic. Organism pages are
excluded — a gecko page ranking alongside the adhesives list is correct.

Diagnosis: compare their `strategy_slugs`. If one is a superset of the other, the
overlap is real. Confirm by checking whether they rank for the same queries.

Fix by **differentiating intent**, not deleting. See `playbook.md`.

## [4] QUERY GAPS

Queries earning impressions where the site ranks 20+. Two reasons, different fixes:

- **No page targets it** → write one (Phase 5).
- **A page targets it but ranks badly** → that's really a DEEPEN item.

Watch for queries that *disappear* between runs. "biomimicry examples" (15 impr,
pos 42) vanished after the September rewrite. Disappearance can mean dropping out
of the top 100, or a page being re-assessed after a substantial edit. Flag it,
watch it next cycle, don't panic on one data point.

## [5] DUPLICATE BOILERPLATE

Sentences repeated verbatim across templated pages. Measured directly from the
content files, so unlike the others it's exact rather than inferred.

Current state: 20 industry pages, 7 function pages, 8 list pages share blocks.
This correlates with industry pages clustering at poor positions.

Fix in batches of ~5, verifying between batches.

## Interpreting direction correctly

**Impressions down + position up is often a win.** Narrowing a page's topical
focus makes it stop appearing for loosely-related queries it never converted.
Losing 68 impressions that sat at position 61 costs nothing.

Judge by **clicks**, then position, then impressions — in that order.

The one combination that genuinely warrants concern: position flat or worse
*and* clicks down, on a page that was recently edited.
