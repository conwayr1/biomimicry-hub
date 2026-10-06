# Affiliate & monetization audit

Run this as its own phase. Sequence matters — step 2 before step 3, or the
analysis is guesswork.

## 1. Inventory what is actually live

Read `biomimicry-seo/data/affiliates.json` and the two places links render:
`layouts/partials/affiliate-cta.html` (bottom of every page) and
`layouts/shortcodes/affiliate.html` (inline, invoked from markdown).

Check each program for:

- **Is the tracking ID real?** A placeholder like `AFFILIATE_ID` or `AMAZON_TAG`
  means the link is live on every page but credits nobody.
- **Is the account in good standing?** Note any program-specific requirement.
- **Does the link actually resolve?** Programs change URL structures.

> **Known issue:** `learn_biomimicry.url` has been
> `https://www.learnbiomimicry.com/short-courses?ref=AFFILIATE_ID` — a placeholder
> for a program the user is not enrolled in, rendering a prominent CTA on all 122
> pages. Either enrol, point it at the clean URL, or remove the block. The user
> has chosen to leave it for now; re-raise it, don't silently change it.

## 2. Instrument before optimizing

**Do not evaluate affiliate performance without click data.** There is currently
no outbound click tracking, which means "nobody clicks the link" and "people click
but don't buy" are indistinguishable — and they have opposite fixes (placement/copy
vs. program/offer).

GA4 is already installed (`G-96035Z7LSP`) but no events are configured. Propose
adding outbound click events on affiliate links, then let a cycle pass before
judging any program. On the first run this phase will usually conclude *"cannot
evaluate yet — instrument first"*. That is a legitimate finding; say so plainly
rather than inventing an assessment.

What to measure once instrumented:

- Clicks per affiliate link, by page and by placement
- Click-through rate from page view → affiliate click
- Which page types convert attention (organism vs list vs industry)

## 3. Research alternatives

**Always verify current rates with a web search at run time.** Commission rates,
cookie windows, and eligibility rules change; never quote them from memory or from
a previous run of this skill.

For each candidate capture: commission rate, cookie window, payout threshold,
approval requirements, and whether it fits this audience (engineers, designers,
architects, students, educators).

Categories worth evaluating:

- **Books** — Amazon Associates is the incumbent. Bookshop.org is the usual
  higher-rate alternative for books specifically. Compare rate *and* conversion:
  Amazon's advantage is that people already have accounts.
- **Courses** — Learn Biomimicry (claims 20–25% on short courses, 10% on the
  Practitioner Programme, per the existing config), plus the general platforms
  (Coursera, edX, Udemy, Skillshare). Course commissions are typically far higher
  than physical-goods rates, and the audience intent is a good match.
- **Professional tools** — CAD/simulation/design software with affiliate or
  referral programs. Highest potential value per conversion, hardest to get
  approved for.
- **Display advertising** — not affiliate, but the realistic alternative at low
  conversion volume. AdSense has no traffic minimum; Ezoic is low-threshold;
  Mediavine and Raptive require substantial monthly sessions. Check current
  thresholds against actual traffic before recommending.

## 4. Weigh against traffic reality

Tie recommendations to the measured numbers, not to theoretical rates. At ~37
clicks per 28 days, *no* affiliate program will produce meaningful revenue yet —
so the honest recommendation is usually:

1. Fix anything broken (placeholder links, dead CTAs).
2. Instrument so the next cycle has data.
3. Keep programs that cost nothing to retain.
4. Revisit program choice when traffic justifies it.

Do not recommend switching programs on commission rate alone when the binding
constraint is traffic.

## 5. Flag hard deadlines

Some programs close inactive accounts. **Amazon Associates requires qualifying
sales within a set window of signup or the account is closed** — the user has
flagged theirs as at risk. Check the current rule and the account's actual
deadline, and surface it as a constraint that may force a decision before the SEO
work matures.

## Output

A table: program | current status | commission | cookie | requirements | fit |
recommendation. Plus a clear statement of what cannot yet be assessed and what
instrumentation would unlock it.

Never enrol in a program, create an account, or swap a live affiliate link
without explicit approval.
