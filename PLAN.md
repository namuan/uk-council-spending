# SpendFeed — Feature Plan

## Done

- [x] Single-council dashboard: tax trend chart, budget breakdown, per-household estimates, feed, leadership
- [x] Council selector with search, type grouping, and keyboard navigation
- [x] Watchlist (localStorage) and shareable council URLs (`?council=slug`)
- [x] Category comparison view: pick a budget category, compare all councils
  - Metric toggle (total spend / per household / % of budget)
  - Council type filter chips
  - Region filter chips
  - Summary cards (count, median, highest, lowest)
  - Top-20 horizontal bar chart (Chart.js)
  - Sortable table with all 317 councils
  - Click any budget row to jump to comparison pre-filtered to that category
  - CSV export button on all comparison tables
- [x] Pre-commit hook auto-syncs `dash/` and `index.html` into `docs/` for GitHub Pages

---

## Quick wins

### 1. URL persistence for comparison view

- [x] `?compare=housing` and `?compare=housing&metric=perHousehold` query params
- [x] Shareable and bookmarked comparison URLs

### 2. Watchlist page

- [x] "Watched" section on landing page showing starred councils
- [x] Grid with council avatars, names, and budget stats
- [x] Auto-hides when watchlist is empty

### 3. Council tax comparison

- [x] Tax comparison data file (`dash/tax-comparison.json`) with 317 councils
- [x] Selectable comparison metrics: Band D tax, tax change (£), tax change (%)
- [x] Charts, summary cards, and sortable table
- [x] Type and region filter chips

---

## Medium effort

### 4. "Similar councils" section on dashboard

- [x] Below the council hero, shows 3–4 councils of the same type
- [x] Sorted by closest budget total
- [x] Clickable to jump directly

### 5. Split `categories.json` into per-category files

- [x] Per-category files at `dash/categories/<cat>.json`
- [x] Includes category description alongside data
- [x] Legacy `dash/categories.json` still generated for backward compatibility

### 6. Dark mode

- [x] Light/dark toggle button on landing page and dashboard header
- [x] Follows `prefers-color-scheme`
- [x] Persists choice to localStorage
- [x] Chart grid colors adapt to theme

---

## Larger features

### 7. Map view

- [x] ~~Interactive SVG map of the 9 English regions~~
- [x] ~~Colour intensity shows median spending per region~~
- [x] ~~Click a region to see stats (council count, median budget, avg tax)~~
- [x] ~~"View councils in this region" navigates to comparison pre-filtered by region~~
- [x] ~~URL-based region filtering (`?compare&region=London`)~~
- ⚠️ **Removed** — the map view was removed from the codebase but the `region` URL parameter and region filter chips remain for comparison view filtering.

### 8. Year-over-year trends per category

The CivAccount API does not provide historical budget breakdowns — only a single year of budget data is available. Tax trend data (2021–2026) is already shown in the dashboard chart. If the API adds historical budget data in the future, this feature can be added as a line chart similar to the existing tax trend chart.

### 9. CSV export

- [x] "Download CSV" button on budget category comparison tables
- [x] Works across all comparison types (budget categories, tax comparison)
- [x] Generates proper CSV with headers and UTF-8 BOM

### 10. Council detail page improvements

- [x] **Service descriptions** — short plain-English explanations of what each budget category covers
- [x] **Per-household estimates** — already present and shown in stats grid
- [x] **Budget change indicators** — tax change shown with direction (up/down) and percentage. Budget data is single-year only so per-category changes not applicable.

---

## Data improvements

### Add ONS geography codes

- [x] Region lookup for all 317 councils embedded in build script
- [x] Region added to council data, index, and comparison entries
- [x] Region shown in search dropdown, selector results, and comparison tables
- [x] Region filter chips on comparison view

### Regular data refresh

- [x] GitHub Actions workflow (`.github/workflows/refresh-data.yml`)
- [x] Runs monthly via cron, with manual dispatch option
- [x] Fetches latest data from CivAccount API, rebuilds, syncs docs/, and commits
