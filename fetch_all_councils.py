#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "requests",
# ]
# ///
"""
Download ALL 317 council details from the CivAccount API.

Uses the council slug list extracted from the sitemap at:
  https://www.civaccount.co.uk/sitemap.xml

Rate-limited to ~80 req/min (0.75s delay) to stay under the 100/min limit.
Resumes from existing files — only fetches councils we don't already have.

Output: spendfeed/data/<slug>.json  (one per council)

Usage:
  ./fetch_all_councils.py           # Fetch all missing councils
  ./fetch_all_councils.py -v        # Verbose
  ./fetch_all_councils.py --force   # Re-fetch all, overwrite existing
"""

import json
import logging
import time
from argparse import ArgumentParser
from pathlib import Path

import requests

API_BASE = "https://www.civaccount.co.uk/api/v1"
DATA_DIR = Path("data_raw")
SLUGS_FILE = DATA_DIR / "all_slugs.json"
DELAY = 0.75  # seconds between requests


def setup_logging(verbosity):
    level = logging.WARNING
    if verbosity == 1: level = logging.INFO
    elif verbosity >= 2: level = logging.DEBUG
    logging.basicConfig(
        handlers=[logging.StreamHandler()],
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
        level=level,
    )


def parse_args():
    p = ArgumentParser(description=__doc__)
    p.add_argument("-v", "--verbose", action="count", default=0)
    p.add_argument("--force", action="store_true", help="Re-fetch all, overwrite existing files")
    p.add_argument("--delay", type=float, default=DELAY, help="Seconds between requests")
    return p.parse_args()


def load_slugs():
    if not SLUGS_FILE.exists():
        logging.error(f"Slug list not found at {SLUGS_FILE}. Run get_slugs_from_sitemap() first.")
        return []
    with open(SLUGS_FILE) as f:
        return json.load(f)


def fetch_council(slug):
    """Fetch a single council from the API. Returns the 'data' dict or None."""
    try:
        resp = requests.get(f"{API_BASE}/councils/{slug}", timeout=30)
        if resp.status_code == 404:
            logging.warning(f"  {slug}: 404 not found")
            return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", data)
    except Exception as e:
        logging.error(f"  {slug}: {e}")
        return None


def write_council_file(slug, data):
    """Write council data to a JSON file."""
    path = DATA_DIR / f"{slug}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def main():
    args = parse_args()
    setup_logging(args.verbose)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    slugs = load_slugs()
    if not slugs:
        print("No slugs found. Download the sitemap first:")
        print("  curl -s https://www.civaccount.co.uk/sitemap.xml | grep '/council/' | sed 's/.*\\/council\\///;s/<.*//' | sort -u")
        return

    # Determine which slugs need fetching
    to_fetch = []
    skipped = 0
    for slug in slugs:
        path = DATA_DIR / f"{slug}.json"
        if path.exists() and not args.force:
            skipped += 1
        else:
            to_fetch.append(slug)

    print(f"Total council slugs: {len(slugs)}")
    print(f"Already have: {skipped}")
    print(f"To fetch: {len(to_fetch)}")
    if not to_fetch:
        print("Nothing to do — all councils already downloaded.")
        return

    print(f"\nFetching {len(to_fetch)} councils from CivAccount API...")
    print(f"(Rate limit: 100/min, using {args.delay}s delay ≈ {60/args.delay:.0f}/min)\n")

    success = 0
    failed = 0
    not_found = 0

    for i, slug in enumerate(to_fetch, 1):
        data = fetch_council(slug)
        if data is None:
            not_found += 1
            failed += 1
        elif "error" in data:
            logging.warning(f"  {slug}: API error — {data.get('error', 'unknown')}")
            failed += 1
        else:
            write_council_file(slug, data)
            success += 1
            if success % 20 == 0 or i <= 3:
                logging.info(f"  [{i}/{len(to_fetch)}] ✓ {slug} ({data.get('name', '?')})")

        time.sleep(args.delay)

    print(f"\n── Done ──")
    print(f"  Success: {success}")
    print(f"  Failed (404/error): {failed}")
    print(f"  Total files: {skipped + success}")
    print(f"  Saved to: {DATA_DIR.resolve()}/")


if __name__ == "__main__":
    main()
