# Biomimicry Hub — Programmatic SEO Site

A programmatic SEO website about biomimicry (nature-inspired engineering) built with a Python data pipeline + Hugo static site generator, deployed to GitHub Pages or Cloudflare Pages.

**Live site:** https://biomimicry-hub.com

---

## Project structure

```
biomimicry-seo/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Auto-deploys to GitHub Pages on push to main
├── content/
│   ├── organisms/              # 57 organism strategy pages (the core content)
│   ├── functions/              # 7 biomimicry function pages
│   ├── industries/             # 20 industry pages
│   └── lists/                  # 12 "Best of" list pages
├── data/
│   ├── affiliates.json         # Affiliate link config (update with real IDs)
│   └── keyword_plan.json       # Generated keyword/page plan
├── database/
│   └── biomimicry.db           # SQLite database — 57 biological strategies
├── layouts/                    # Hugo templates (no theme — all custom)
│   ├── _default/
│   ├── organisms/
│   ├── functions/
│   ├── industries/
│   ├── lists/
│   ├── partials/
│   └── shortcodes/
├── scripts/
│   ├── seed_database.py        # Populates the SQLite database
│   ├── add_strategy.py         # Interactive CLI to add new strategies
│   ├── generate_keywords.py    # Generates data/keyword_plan.json
│   ├── generate_content.py     # Generates all Hugo markdown files
│   └── build_internal_links.py # Audits + fixes SEO and internal linking
├── static/
│   └── robots.txt
└── config.toml                 # Hugo config — update baseURL before deploying
```

---

## Quick start (local preview)

**Requirements:** Python 3.10+, Hugo Extended v0.160+

```
# Windows (Command Prompt)
"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Hugo.Hugo.Extended_Microsoft.Winget.Source_8wekyb3d8bbwe\hugo.exe" server
```

Site is then live at http://localhost:1313

---

## Python data pipeline

Run these scripts in order when setting up from scratch, or after adding new strategies:

```bash
# 1. Create and populate the database
py scripts/seed_database.py

# 2. Generate the keyword/page plan
py scripts/generate_keywords.py

# 3. Generate all Hugo markdown content files
py scripts/generate_content.py

# 4. Audit and fix SEO + internal links
py scripts/build_internal_links.py
```

To add a new organism strategy interactively:
```bash
py scripts/add_strategy.py
```

---

## Deployment

### Option A — GitHub Pages (free)

1. **Create a GitHub repository** and push this project to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Enable GitHub Pages via Actions:**
   - Go to your repo on GitHub
   - Settings → Pages → Source → **GitHub Actions**
   - Click Save

3. **Push any change to `main`** — the workflow in `.github/workflows/deploy.yml` builds Hugo and deploys automatically. Your site will appear at:
   ```
   https://YOUR_USERNAME.github.io/YOUR_REPO/
   ```

4. **Custom domain (optional):** Add a `CNAME` file to the `static/` folder containing your domain (e.g. `biomimicry-hub.com`), then point your DNS to GitHub Pages. Update `baseURL` in `config.toml` to match.

---

### Option B — Cloudflare Pages (free, faster)

Cloudflare Pages is often faster than GitHub Pages because it uses Cloudflare's global CDN. It can deploy directly from your GitHub repository.

1. **Connect your repo:**
   - Go to https://pages.cloudflare.com → Create a project → Connect to Git
   - Authorise Cloudflare to access your GitHub account
   - Select your repository

2. **Configure the build:**

   | Setting | Value |
   |---|---|
   | Framework preset | Hugo |
   | Build command | `hugo --minify` |
   | Build output directory | `public` |
   | Environment variable | `HUGO_VERSION` = `0.160.1` |

3. **Deploy** — Cloudflare builds and deploys on every push to `main`. You get a free `.pages.dev` subdomain immediately, and you can add a custom domain in the dashboard.

4. **Update `baseURL`** in `config.toml` to match your final domain.

---

## Configuration

### Update affiliate IDs (Phase 6)

Edit `data/affiliates.json`:
- Replace `AFFILIATE_ID` with your Learn Biomimicry referral code
- Replace `AMAZON_TAG` with your Amazon Associates tracking ID

### Enable Google Analytics

In `config.toml`, add your GA4 Measurement ID:
```toml
[params]
  googleAnalytics = "G-XXXXXXXXXX"
```

### Change the site title / domain

Edit `config.toml`:
```toml
baseURL = "https://your-domain.com/"
title   = "Your Site Title"
```

---

## Adding content

To add a new biological strategy to the site:

1. `py scripts/add_strategy.py` — enter the organism details
2. `py scripts/generate_keywords.py` — regenerates the keyword plan
3. `py scripts/generate_content.py` — regenerates markdown files (skips existing ones)
4. `py scripts/build_internal_links.py` — re-audits SEO and links
5. Commit and push — GitHub Actions deploys automatically

---

## Tech stack

| Layer | Technology |
|---|---|
| Static site generator | Hugo Extended v0.160+ |
| Data pipeline | Python 3.10+ / SQLite |
| Hosting | GitHub Pages or Cloudflare Pages |
| Monetisation | Learn Biomimicry affiliate + Amazon Associates |
| Analytics | Google Analytics 4 (optional) |
