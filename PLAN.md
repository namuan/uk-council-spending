# SpendFeed — Feature Plan

## Done

- [x] Single-council dashboard: tax trend chart, budget breakdown, per-household estimates, feed, leadership
- [x] Council selector with search, type grouping, and keyboard navigation
- [x] Watchlist (localStorage) and shareable council URLs (`?council=slug`)
- [x] Category comparison view: pick a budget category, compare all councils
  - Metric toggle (total spend / per household / % of budget)
  - Council type filter chips
  - Summary cards (count, median, highest, lowest)
  - Top-20 horizontal bar chart (Chart.js)
  - Sortable table with all 317 councils
  - Click any budget row to jump to comparison pre-filtered to that category
- [x] Pre-commit hook auto-syncs `dash/` and `index.html` into `docs/` for GitHub Pages

---

## Quick wins

### 1. URL persistence for comparison view

Currently you can't share or bookmark a comparison. Add query params:

- `?compare=housing`
- `?compare=housing&metric=perHousehold`

~20 lines of JS. Makes comparison views linkable and shareable.

### 2. Watchlist page

The ★ button already persists to localStorage. Add a "Watched" tab or section on the landing page showing all starred councils in a grid with key stats (tax, budget). Lets users build their own custom comparison set.

### 3. Council tax comparison

Same pattern as budget categories — reuse the comparison UI to rank councils by Band D tax, tax change, or tax change %. Needs a new data file (`dash/tax-comparison.json` or an extra entry in the category selector).

---

## Medium effort

### 4. "Similar councils" section on dashboard

Below the council hero, show 3–4 councils of the same type with similar budget totals. Clickable to jump directly. Helps discovery — especially for users comparing their council to neighbours.

### 5. Split `categories.json` into per-category files

The current `dash/categories.json` is ~1.5 MB / 27k lines. Loading one category at a time (`dash/categories/housing.json`) would make the comparison view noticeably faster on slow connections. Modest change to the build script and one fetch path in the frontend.

### 6. Dark mode

Add a light/dark toggle or follow `prefers-color-scheme`. Low effort, high polish — the CSS variables are already named sensibly.

---

## Larger features

### 7. Map view

Plot all 317 councils on an interactive England map. Colour by spending per household or council tax band. Needs ONS boundary/centroid data and a lightweight mapping library (Leaflet or a static SVG map).

### 8. Year-over-year trends per category

Tax data already covers 2021–2026. If the CivAccount API provides historical budget breakdowns, show spending trends per category over time — line charts similar to the existing tax trend chart.

### 9. CSV export

"Download as CSV" button on any comparison table. Simple to add on the frontend (generate CSV from the in-memory data, trigger download). Useful for journalists and researchers who want to analyse the data themselves.

### 10. Council detail page improvements [x]

- **Spending per capita** — shows spending per resident using ONS mid-2024 population estimates
- **Service descriptions** — shows a short plain-English explanation for every budget category
- **Change indicators** — shows whether category spending went up or down when historical budget data is supplied

---

## Data improvements

### Add ONS geography codes

The API returns `ons_code`. Cross-reference with ONS lookup tables to add:

- Region (North West, South East, etc.)
- Population
- Number of households (actual, not estimated by type)
- Ward count

This would make the comparison view more useful (filter by region, show actual per-household figures).

### Regular data refresh

The CivAccount data changes over time (new budgets, updated tax rates). Consider:

- A GitHub Actions workflow that runs `fetch_all_councils.py` and `build_council_data.py` on a schedule (e.g. monthly)
- Auto-commits and pushes the updated `docs/` so the live site stays current

---
