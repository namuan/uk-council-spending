#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pandas",
# ]
# ///
"""
Generate individual JSON data files for each council + a council index.

Output:
  spendfeed/data/index.json     — list of all councils (for the dropdown)
  spendfeed/data/<slug>.json    — full dashboard data per council

Usage: ./build_council_data.py
"""

import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

OUT_DIR = Path("dash")

CAT_ICONS = {
    "education": "📚", "childrens_social_care": "👶", "adult_social_care": "👴",
    "public_health": "🏥", "transport": "🛣️", "housing": "🏠",
    "cultural": "🎭", "environmental": "🌳", "planning": "📐",
    "central_services": "🏛️", "other": "📋",
}
CAT_LABELS = {
    "education": "Education", "childrens_social_care": "Children's Social Care",
    "adult_social_care": "Adult Social Care", "public_health": "Public Health",
    "transport": "Roads & Transport", "housing": "Housing",
    "cultural": "Culture & Leisure", "environmental": "Environment & Streets",
    "planning": "Planning & Development", "central_services": "Council Running Costs",
    "other": "Other Services",
}

HOUSEHOLDS = {
    "County Council": 350000, "Metropolitan District": 130000,
    "London Borough": 110000, "Unitary Authority": 100000,
    "District Council": 50000,
}

FEED_DATES = [
    "2025-04-15", "2025-05-03", "2025-06-21", "2025-07-09",
    "2025-08-14", "2025-09-02", "2025-10-18", "2025-11-07",
    "2025-12-12", "2026-01-06", "2026-01-24", "2026-02-10",
    "2026-02-28", "2026-03-15", "2026-04-02", "2026-04-22",
    "2026-05-08", "2026-06-01", "2026-06-19", "2026-07-05",
]


def colour_from_name(name):
    h = int(hashlib.md5(name.encode()).hexdigest()[:6], 16)
    return f"hsl({h % 360}, 45%, 55%)"


def initials(name):
    """Get up-to-3-letter initials from council name."""
    clean = name.replace("Council","").replace("City","").replace("District","").replace("County","").replace("Borough","").replace("&","").replace(" and "," ").replace(" Of "," ").strip()
    words = clean.split()
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    # Single-word name (e.g. "Liverpool", "Salford") — use first 3 letters
    if len(clean) >= 3:
        return clean[:3].upper()
    return clean[:2].upper()


def load_rows():
    """Load council data from API JSON files in spendfeed/data/."""
    rows = []
    data_dir = Path("data_raw")
    for fpath in sorted(data_dir.glob("*.json")):
        # Skip index and slug list files
        if fpath.name in ("index.json", "all_slugs.json"):
            continue
        try:
            with open(fpath) as f:
                d = json.load(f)
            # Handle both wrapped and unwrapped API responses
            d = d.get("data", d)
            row = {
                "slug": d.get("slug", fpath.stem),
                "name": d.get("name", ""),
                "type": d.get("type", ""),
                "type_name": d.get("type_name", ""),
                "website": d.get("website", ""),
                "ons_code": d.get("ons_code", ""),
            }
            ct = d.get("council_tax", {})
            for k, v in ct.items():
                row[f"council_tax_{k}"] = v
            bd = d.get("budget", {})
            row["budget_total_service"] = bd.get("total_service")
            row["budget_net_current"] = bd.get("net_current")
            for item in bd.get("breakdown", []):
                cat = item.get("category", "other")
                row[f"budget_{cat}"] = item.get("amount_thousands")
            ld = d.get("leadership", {})
            row["leader"] = ld.get("council_leader", "")
            row["chief_executive"] = ld.get("chief_executive", "")
            row["total_councillors"] = ld.get("total_councillors", 0)
            rows.append(row)
        except Exception as e:
            print(f"  Warning: could not parse {fpath.name}: {e}")
    return rows


def build_council_data(row):
    """Build the full dashboard data object for one council."""
    slug = row["slug"]
    tname = row["type_name"]

    # Tax bands
    tax_bands = {}
    for y in ["2021","2022","2023","2024","2025","2026"]:
        col = f"council_tax_band_d_{y}"
        val = row.get(col)
        if val is not None and val != "":
            tax_bands[y] = float(val)

    tax_cur = tax_bands.get("2025", 0)
    tax_prev = tax_bands.get("2024", 0)
    tax_chg = round(tax_cur - tax_prev, 2)
    tax_pct = round((tax_chg / tax_prev * 100), 1) if tax_prev else 0

    # Budget categories
    budget_cats = []
    total = 0
    cat_order = ["education","childrens_social_care","adult_social_care","public_health",
                 "transport","housing","cultural","environmental","planning",
                 "central_services","other"]
    for cat in cat_order:
        col = f"budget_{cat}"
        val = row.get(col)
        if val is not None and val != "":
            val = float(val)
            total += max(val, 0)
            budget_cats.append({
                "cat": cat, "label": CAT_LABELS.get(cat, cat),
                "icon": CAT_ICONS.get(cat, "📋"),
                "amount": round(val, 1),
            })
    budget_cats.sort(key=lambda x: -abs(x["amount"]))

    hh = HOUSEHOLDS.get(tname, 80000)
    per_hh = round(total * 1000 / hh, 0) if hh else 0  # total is in thousands

    # Feed items for this council
    feed = []
    top_positive = [c for c in budget_cats if c["amount"] > 0][:4]
    for cat in top_positive:
        ph = round(cat["amount"] / hh * 1000, 0) if hh else 0
        desc = f'allocated £{cat["amount"]/1000:.1f}m to {cat["label"]}'
        if ph > 0:
            desc += f' (≈£{ph:.0f} per household)'
        feed.append({
            "type": "budget",
            "category": cat["label"],
            "icon": cat["icon"],
            "amount": round(cat["amount"], 0),
            "perHousehold": int(ph),
            "description": desc,
            "timestamp": random.choice(FEED_DATES),
        })

    if abs(tax_chg) > 0.5:
        direction = "raised" if tax_chg > 0 else "lowered"
        feed.append({
            "type": "tax",
            "category": "Council Tax",
            "icon": "📈" if tax_chg > 0 else "📉",
            "amount": round(abs(tax_chg), 0),
            "perHousehold": round(abs(tax_chg), 0),
            "description": f'{direction} Band D council tax by £{abs(tax_chg):.0f} ({abs(tax_pct)}%) to £{tax_cur:.0f}',
            "timestamp": "2025-03-15",
        })

    feed.sort(key=lambda x: x["timestamp"], reverse=True)

    cllrs = row.get("total_councillors", 0)
    if isinstance(cllrs, str):
        cllrs = int(cllrs) if cllrs.isdigit() else 0
    else:
        cllrs = int(cllrs) if cllrs else 0

    return {
        "slug": slug,
        "name": row["name"],
        "type": row["type"],
        "typeName": tname,
        "onsCode": row.get("ons_code", ""),
        "colour": colour_from_name(row["name"]),
        "initials": initials(row["name"]),
        "leader": row.get("leader") or "",
        "chiefExecutive": row.get("chief_executive") or "",
        "councillors": cllrs,
        "website": row.get("website", ""),
        "taxBands": tax_bands,
        "taxCurrent": tax_cur,
        "taxPrev": tax_prev,
        "taxChange": tax_chg,
        "taxChangePct": tax_pct,
        "budgetCategories": budget_cats,
        "budgetTotal": round(total, 0),
        "perHousehold": int(per_hh),
        "feedItems": feed,
    }


def build_categories_json(rows):
    """Build categories.json: each category with all council data for comparison."""
    cat_data = defaultdict(list)

    for row in rows:
        data = build_council_data(row)
        slug = data["slug"]
        name = data["name"]
        ctype = data["type"]
        type_name = data["typeName"]
        budget_total = data["budgetTotal"]
        households = HOUSEHOLDS.get(type_name, 80000)

        for cat in data["budgetCategories"]:
            amt = cat["amount"]  # thousands
            cat_key = cat["cat"]

            cat_data[cat_key].append({
                "slug": slug,
                "name": name,
                "type": ctype,
                "typeName": type_name,
                "amount": amt,
                "budgetTotal": budget_total,
                "perHousehold": int(round(amt * 1000 / households, 0)) if households else 0,
                "percentOfBudget": round(amt / budget_total * 100, 1) if budget_total else 0,
            })

    # Sort councils within each category by absolute amount descending
    result = []
    cat_order = ["education","childrens_social_care","adult_social_care","public_health",
                 "transport","housing","cultural","environmental","planning",
                 "central_services","other"]

    for cat_key in cat_order:
        if cat_key in cat_data:
            councils_list = cat_data[cat_key]
            councils_list.sort(key=lambda x: -abs(x["amount"]))
            result.append({
                "cat": cat_key,
                "label": CAT_LABELS.get(cat_key, cat_key),
                "icon": CAT_ICONS.get(cat_key, "📋"),
                "councils": councils_list,
            })

    with open(OUT_DIR / "categories.json", "w") as f:
        json.dump({"categories": result}, f, indent=2)

    total_entries = sum(len(cat["councils"]) for cat in result)
    print(f"  Wrote categories.json ({len(result)} categories, {total_entries} council entries)")


def main():
    rows = load_rows()
    print(f"Loaded {len(rows)} councils")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build index
    index = []
    for row in rows:
        tname = row["type_name"]
        t25 = row.get("council_tax_band_d_2025")
        budget = row.get("budget_total_service")
        index.append({
            "slug": row["slug"],
            "name": row["name"],
            "type": row["type"],
            "typeName": tname,
            "initials": initials(row["name"]),
            "colour": colour_from_name(row["name"]),
            "tax2025": float(t25) if t25 is not None and t25 != "" else 0,
            "budget": float(budget) if budget is not None and budget != "" else 0,
        })

    with open(OUT_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)
    print(f"  Wrote index.json ({len(index)} councils)")

    # Build individual council files
    for row in rows:
        data = build_council_data(row)
        slug = row["slug"]
        with open(OUT_DIR / f"{slug}.json", "w") as f:
            json.dump(data, f, indent=2)

    print(f"  Wrote {len(rows)} council files to {OUT_DIR.resolve()}/")

    # Build category comparison data
    build_categories_json(rows)

    print(f"\n  Total: {len(rows)} council data files + index.json")


if __name__ == "__main__":
    random.seed(42)
    main()
