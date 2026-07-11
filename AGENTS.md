# AGENTS.md

Guidance for AI agents working on this repository.

## Project overview

SpendFeed is a static GitHub Pages site for exploring English council spending data.

- Root `index.html` is the local development entry point.
- `dash/` contains generated dashboard JSON used by root `index.html`.
- `docs/` is the GitHub Pages publish directory.
- `docs/index.html` and `docs/dash/` must stay in sync with `index.html` and `dash/`.
- `data_raw/` contains downloaded source API data and is intentionally ignored by git.

## Common commands

Fetch or refresh source data:

```bash
./fetch_all_councils.py
```

Rebuild generated dashboard JSON:

```bash
./build_council_data.py
```

Serve locally:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080/`.

## Data pipeline

1. `fetch_all_councils.py` downloads council API responses into `data_raw/`.
2. `build_council_data.py` reads `data_raw/*.json`.
3. It writes generated files into root `dash/`.
4. The git pre-commit hook syncs root files into `docs/` for GitHub Pages.

Do not commit `data_raw/`.

## Git hooks

This repo uses a tracked hooks directory:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook syncs and stages:

- `dash/` → `docs/dash/`
- `index.html` → `docs/index.html`

If you clone the repo fresh, run the `git config` command above before committing.

You can bypass hooks with:

```bash
git commit --no-verify
```

Only bypass hooks when you intentionally do not want to update GitHub Pages output.

## Important implementation notes

- `index.html` fetches data using relative paths: `dash/index.json` and `dash/<slug>.json`.
- This is why both root `dash/` and `docs/dash/` exist.
- If `build_council_data.py` reports `Loaded 0 councils`, check that `data_raw/` exists and contains council JSON files.
- Running `build_council_data.py` with no input will overwrite `dash/index.json` with an empty list.

## Before committing

For changes affecting data or frontend behaviour:

1. Run `./build_council_data.py` if generated data may need updating.
2. Serve locally and sanity-check the page.
3. Commit normally; the pre-commit hook will sync `docs/` automatically.
