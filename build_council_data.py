#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "pandas",
# ]
# ///
"""
Generate individual JSON data files for each council + a council index.

Output:
  dash/index.json              — list of all councils (for the dropdown)
  dash/<slug>.json             — full dashboard data per council
  dash/categories.json         — all categories in one file (legacy)
  dash/categories/<cat>.json   — per-category comparison files
  dash/tax-comparison.json     — council tax comparison data

Usage: ./build_council_data.py
"""

import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

OUT_DIR = Path("dash")
CAT_DIR = OUT_DIR / "categories"

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
CAT_DESCRIPTIONS = {
    "education": "Funding for local schools, children's education services, and early years provision.",
    "childrens_social_care": "Services to protect and support children, including fostering, adoption, and family support.",
    "adult_social_care": "Care services for elderly and vulnerable adults, including home care and residential placements.",
    "public_health": "Health improvement programmes, sexual health services, drug and alcohol services, and health protection.",
    "transport": "Road maintenance, public transport subsidies, street lighting, and transport planning.",
    "housing": "Housing benefit, homelessness services, council housing management, and affordable housing programmes.",
    "cultural": "Libraries, museums, parks, leisure centres, sports facilities, and arts programmes.",
    "environmental": "Waste collection and recycling, street cleaning, environmental health, and regulatory services.",
    "planning": "Planning applications, building control, economic development, and regeneration projects.",
    "central_services": "Council tax collection, HR, finance, IT, legal services, and democratic governance.",
    "other": "Other service areas and cross-cutting budgets not allocated to specific categories.",
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

# ── Region lookup ──────────────────────────────────────────────────────────
# Maps each council slug to its English region based on ONS geography.
REGION_MAP = {
    # North East
    "county-durham": "North East", "darlington": "North East", "durham": "North East",
    "gateshead": "North East", "hartlepool": "North East", "middlesbrough": "North East",
    "newcastle-upon-tyne": "North East", "north-tyneside": "North East",
    "northumberland": "North East", "redcar-and-cleveland": "North East",
    "south-tyneside": "North East", "stockton-on-tees": "North East", "sunderland": "North East",
    # North West
    "blackburn-with-darwen": "North West", "blackpool": "North West", "bolton": "North West",
    "burnley": "North West", "bury": "North West", "cheshire-east": "North West",
    "cheshire-west-and-chester": "North West", "chorley": "North West", "cumberland": "North West",
    "fylde": "North West", "halton": "North West", "hyndburn": "North West", "knowsley": "North West",
    "lancashire": "North West", "lancaster": "North West", "liverpool": "North West",
    "manchester": "North West", "oldham": "North West", "pendle": "North West", "preston": "North West",
    "ribble-valley": "North West", "rochdale": "North West", "rossendale": "North West",
    "salford": "North West", "sefton": "North West", "south-ribble": "North West",
    "st-helens": "North West", "stockport": "North West", "tameside": "North West",
    "trafford": "North West", "warrington": "North West", "west-lancashire": "North West",
    "westmorland-and-furness": "North West", "wigan": "North West", "wirral": "North West",
    "wyre": "North West",
    # Yorkshire and The Humber
    "barnsley": "Yorkshire and The Humber", "bradford": "Yorkshire and The Humber",
    "calderdale": "Yorkshire and The Humber", "doncaster": "Yorkshire and The Humber",
    "east-riding-of-yorkshire": "Yorkshire and The Humber", "kingston-upon-hull": "Yorkshire and The Humber",
    "kirklees": "Yorkshire and The Humber", "leeds": "Yorkshire and The Humber",
    "north-east-lincolnshire": "Yorkshire and The Humber", "north-lincolnshire": "Yorkshire and The Humber",
    "north-yorkshire": "Yorkshire and The Humber", "rotherham": "Yorkshire and The Humber",
    "sheffield": "Yorkshire and The Humber", "wakefield": "Yorkshire and The Humber",
    "york": "Yorkshire and The Humber",
    # East Midlands
    "amber-valley": "East Midlands", "ashfield": "East Midlands", "bassetlaw": "East Midlands",
    "blaby": "East Midlands", "bolsover": "East Midlands", "boston": "East Midlands",
    "broxtowe": "East Midlands", "charnwood": "East Midlands", "chesterfield": "East Midlands",
    "derby": "East Midlands", "derbyshire": "East Midlands", "derbyshire-dales": "East Midlands",
    "east-lindsey": "East Midlands", "erewash": "East Midlands", "gedling": "East Midlands",
    "harborough": "East Midlands", "high-peak": "East Midlands",
    "hinckley-and-bosworth": "East Midlands", "leicester": "East Midlands",
    "leicestershire": "East Midlands", "lincoln": "East Midlands", "lincolnshire": "East Midlands",
    "mansfield": "East Midlands", "melton": "East Midlands", "newark-and-sherwood": "East Midlands",
    "north-east-derbyshire": "East Midlands", "north-kesteven": "East Midlands",
    "north-northamptonshire": "East Midlands", "north-west-leicestershire": "East Midlands",
    "nottingham": "East Midlands", "nottinghamshire": "East Midlands",
    "oadby-and-wigston": "East Midlands", "rushcliffe": "East Midlands", "rutland": "East Midlands",
    "south-derbyshire": "East Midlands", "south-holland": "East Midlands",
    "south-kesteven": "East Midlands", "west-lindsey": "East Midlands",
    "west-northamptonshire": "East Midlands",
    # West Midlands
    "birmingham": "West Midlands", "bromsgrove": "West Midlands", "cannock-chase": "West Midlands",
    "coventry": "West Midlands", "dudley": "West Midlands", "east-staffordshire": "West Midlands",
    "herefordshire": "West Midlands", "lichfield": "West Midlands", "malvern-hills": "West Midlands",
    "newcastle-under-lyme": "West Midlands", "north-warwickshire": "West Midlands",
    "nuneaton-and-bedworth": "West Midlands", "redditch": "West Midlands", "rugby": "West Midlands",
    "sandwell": "West Midlands", "shropshire": "West Midlands", "solihull": "West Midlands",
    "south-staffordshire": "West Midlands", "stafford": "West Midlands", "staffordshire": "West Midlands",
    "staffordshire-moorlands": "West Midlands", "stratford-on-avon": "West Midlands",
    "stoke-on-trent": "West Midlands", "tamworth": "West Midlands", "telford-and-wrekin": "West Midlands",
    "walsall": "West Midlands", "warwick": "West Midlands", "warwickshire": "West Midlands",
    "wolverhampton": "West Midlands", "worcester": "West Midlands", "worcestershire": "West Midlands",
    "wychavon": "West Midlands", "wyre-forest": "West Midlands",
    # East of England
    "babergh": "East of England", "basildon": "East of England", "bedford": "East of England",
    "braintree": "East of England", "breckland": "East of England", "brentwood": "East of England",
    "broadland": "East of England", "broxbourne": "East of England", "cambridge": "East of England",
    "cambridgeshire": "East of England", "castle-point": "East of England",
    "central-bedfordshire": "East of England", "chelmsford": "East of England",
    "colchester": "East of England", "dacorum": "East of England", "east-cambridgeshire": "East of England",
    "east-hertfordshire": "East of England", "east-suffolk": "East of England",
    "epping-forest": "East of England", "essex": "East of England", "fenland": "East of England",
    "great-yarmouth": "East of England", "harlow": "East of England", "hertfordshire": "East of England",
    "hertsmere": "East of England", "huntingdonshire": "East of England", "ipswich": "East of England",
    "kings-lynn-and-west-norfolk": "East of England", "luton": "East of England",
    "maldon": "East of England", "mid-suffolk": "East of England", "north-hertfordshire": "East of England",
    "north-norfolk": "East of England", "norfolk": "East of England", "norwich": "East of England",
    "peterborough": "East of England", "rochford": "East of England", "south-cambridgeshire": "East of England",
    "south-norfolk": "East of England", "southend-on-sea": "East of England",
    "st-albans": "East of England", "stevenage": "East of England", "suffolk": "East of England",
    "tendring": "East of England", "three-rivers": "East of England", "thurrock": "East of England",
    "uttlesford": "East of England", "watford": "East of England", "welwyn-hatfield": "East of England",
    "west-suffolk": "East of England",
    # South East
    "adur": "South East", "arun": "South East", "ashford": "South East",
    "basingstoke-and-deane": "South East", "bracknell-forest": "South East",
    "brighton-and-hove": "South East", "buckinghamshire": "South East", "canterbury": "South East",
    "cherwell": "South East", "chichester": "South East", "crawley": "South East",
    "dartford": "South East", "dover": "South East", "east-hampshire": "South East",
    "east-sussex": "South East", "eastbourne": "South East", "eastleigh": "South East",
    "elmbridge": "South East", "epsom-and-ewell": "South East", "fareham": "South East",
    "folkestone-and-hythe": "South East", "gosport": "South East", "gravesham": "South East",
    "guildford": "South East", "hampshire": "South East", "hart": "South East",
    "hastings": "South East", "havant": "South East", "horsham": "South East",
    "isle-of-wight": "South East", "kent": "South East", "lewes": "South East",
    "maidstone": "South East", "medway-towns": "South East", "mid-sussex": "South East",
    "milton-keynes": "South East", "mole-valley": "South East", "new-forest": "South East",
    "oxford": "South East", "oxfordshire": "South East", "portsmouth": "South East",
    "reading": "South East", "reigate-and-banstead": "South East", "rother": "South East",
    "runnymede": "South East", "rushmoor": "South East", "sevenoaks": "South East",
    "slough": "South East", "south-oxfordshire": "South East", "southampton": "South East",
    "spelthorne": "South East", "surrey": "South East", "surrey-heath": "South East",
    "sussex": "South East", "swale": "South East", "tandridge": "South East",
    "test-valley": "South East", "thanet": "South East", "tonbridge-and-malling": "South East",
    "tunbridge-wells": "South East", "vale-of-white-horse": "South East", "waverley": "South East",
    "wealden": "South East", "west-berkshire": "South East", "west-oxfordshire": "South East",
    "west-sussex": "South East", "winchester": "South East", "windsor-and-maidenhead": "South East",
    "woking": "South East", "wokingham": "South East", "worthing": "South East",
    # South West
    "bath-and-north-east-somerset": "South West", "bournemouth-christchurch-and-poole": "South West",
    "bristol": "South West", "cheltenham": "South West", "cornwall": "South West",
    "cotswold": "South West", "devon": "South West", "dorset-ua": "South West",
    "east-devon": "South West", "exeter": "South West", "forest-of-dean": "South West",
    "gloucester": "South West", "gloucestershire": "South West", "mid-devon": "South West",
    "north-devon": "South West", "north-somerset": "South West", "plymouth": "South West",
    "somerset": "South West", "south-gloucestershire": "South West", "south-hams": "South West",
    "stroud": "South West", "swindon": "South West", "teignbridge": "South West",
    "tewkesbury": "South West", "torbay": "South West", "torridge": "South West",
    "west-devon": "South West", "wiltshire": "South West", "isles-of-scilly": "South West",
    # London
    "barking-and-dagenham": "London", "barnet": "London", "bexley": "London",
    "brent": "London", "bromley": "London", "camden": "London",
    "city-of-london": "London", "croydon": "London", "ealing": "London",
    "enfield": "London", "greenwich": "London", "hackney": "London",
    "hammersmith-and-fulham": "London", "haringey": "London", "harrow": "London",
    "havering": "London", "hillingdon": "London", "hounslow": "London",
    "islington": "London", "kensington-and-chelsea": "London", "kingston-upon-thames": "London",
    "lambeth": "London", "lewisham": "London", "merton": "London",
    "newham": "London", "redbridge": "London", "richmond-upon-thames": "London",
    "southwark": "London", "sutton": "London", "tower-hamlets": "London",
    "waltham-forest": "London", "wandsworth": "London", "westminster": "London",
}

CAT_ORDER = [
    "education", "childrens_social_care", "adult_social_care", "public_health",
    "transport", "housing", "cultural", "environmental", "planning",
    "central_services", "other",
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


def get_region(slug, type_name):
    """Get region for a council slug, falling back to type-based inference."""
    if slug in REGION_MAP:
        return REGION_MAP[slug]
    # London Boroughs are always in London
    if type_name == "London Borough":
        return "London"
    return "England"


def load_rows():
    """Load council data from API JSON files in data_raw/."""
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
    for cat in CAT_ORDER:
        col = f"budget_{cat}"
        val = row.get(col)
        if val is not None and val != "":
            val = float(val)
            total += max(val, 0)
            budget_cats.append({
                "cat": cat, "label": CAT_LABELS.get(cat, cat),
                "icon": CAT_ICONS.get(cat, "📋"),
                "amount": round(val, 1),
                "description": CAT_DESCRIPTIONS.get(cat, ""),
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

    region = get_region(slug, tname)

    return {
        "slug": slug,
        "name": row["name"],
        "type": row["type"],
        "typeName": tname,
        "onsCode": row.get("ons_code", ""),
        "region": region,
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
    """Build categories.json (legacy single-file) and per-category files."""
    cat_data = defaultdict(list)

    for row in rows:
        data = build_council_data(row)
        slug = data["slug"]
        name = data["name"]
        ctype = data["type"]
        type_name = data["typeName"]
        region = data["region"]
        budget_total = data["budgetTotal"]
        households = HOUSEHOLDS.get(type_name, 80000)

        for cat in data["budgetCategories"]:
            amt = cat["amount"]  # thousands
            cat_key = cat["cat"]

            entry = {
                "slug": slug,
                "name": name,
                "type": ctype,
                "typeName": type_name,
                "region": region,
                "amount": amt,
                "budgetTotal": budget_total,
                "perHousehold": int(round(amt * 1000 / households, 0)) if households else 0,
                "percentOfBudget": round(amt / budget_total * 100, 1) if budget_total else 0,
            }
            cat_data[cat_key].append(entry)

    # Sort councils within each category by absolute amount descending
    result = []
    for cat_key in CAT_ORDER:
        if cat_key in cat_data:
            councils_list = cat_data[cat_key]
            councils_list.sort(key=lambda x: -abs(x["amount"]))
            result.append({
                "cat": cat_key,
                "label": CAT_LABELS.get(cat_key, cat_key),
                "icon": CAT_ICONS.get(cat_key, "📋"),
                "description": CAT_DESCRIPTIONS.get(cat_key, ""),
                "councils": councils_list,
            })

    # Legacy single-file output
    with open(OUT_DIR / "categories.json", "w") as f:
        json.dump({"categories": result}, f, indent=2)

    total_entries = sum(len(cat["councils"]) for cat in result)
    print(f"  Wrote categories.json ({len(result)} categories, {total_entries} council entries)")

    # Per-category files (Feature 5)
    CAT_DIR.mkdir(parents=True, exist_ok=True)
    for cat in result:
        cat_key = cat["cat"]
        cat_file = CAT_DIR / f"{cat_key}.json"
        with open(cat_file, "w") as f:
            json.dump(cat, f, indent=2)
    print(f"  Wrote {len(result)} per-category files to {CAT_DIR.resolve()}/")


def build_tax_comparison(rows):
    """Build tax-comparison.json: council tax data for all councils."""
    tax_data = []

    for row in rows:
        data = build_council_data(row)

        tax_cur = data["taxCurrent"]
        tax_prev = data["taxPrev"]

        # Per-household tax burden (Band D tax amount)
        tname = data["typeName"]
        hh = HOUSEHOLDS.get(tname, 80000)
        per_hh_tax = round(tax_cur, 0)  # Band D tax is per household already

        # Tax as % of average household income proxy
        # (Use the average Band D tax as the tax amount)
        tax_data.append({
            "slug": data["slug"],
            "name": data["name"],
            "type": data["type"],
            "typeName": tname,
            "region": data["region"],
            "taxCurrent": tax_cur,
            "taxPrev": tax_prev,
            "taxChange": data["taxChange"],
            "taxChangePct": data["taxChangePct"],
            "tax2021": data["taxBands"].get("2021", 0),
            "tax2022": data["taxBands"].get("2022", 0),
            "tax2023": data["taxBands"].get("2023", 0),
            "tax2024": tax_prev,
            "tax2025": tax_cur,
            "tax2026": data["taxBands"].get("2026", 0),
            "totalChange2021to2025": round(tax_cur - data["taxBands"].get("2021", tax_cur), 2),
        })

    # Sort by tax current descending
    tax_data.sort(key=lambda x: -x["taxCurrent"])

    with open(OUT_DIR / "tax-comparison.json", "w") as f:
        json.dump({"councils": tax_data}, f, indent=2)

    print(f"  Wrote tax-comparison.json ({len(tax_data)} councils)")


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
        slug = row["slug"]
        index.append({
            "slug": slug,
            "name": row["name"],
            "type": row["type"],
            "typeName": tname,
            "region": get_region(slug, tname),
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

    # Build category comparison data (legacy + per-category files)
    build_categories_json(rows)

    # Build tax comparison data (Feature 3)
    build_tax_comparison(rows)

    print(f"\n  Total: {len(rows)} council data files + index.json + categories* + tax-comparison.json")


if __name__ == "__main__":
    random.seed(42)
    main()
