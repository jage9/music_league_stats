# Overview

This project builds a static website from one or more Music League export folders.

At a high level:

1. Read every league directory under `leagues/`
2. Load the exported CSV files
3. Normalize text and identifiers
4. Build an in-memory relational model
5. Compute aggregate stats and derived rankings
6. Render HTML pages into `site/`

The site is fully static. There is no server-side database or API at runtime.

## Inputs

Each league folder is expected to contain these CSV exports:

- `competitors.csv`
- `rounds.csv`
- `submissions.csv`
- `votes.csv`

Optional local configuration:

- `config.json`
  User-editable title and description for the site
- `config.sample.json`
  Template for `config.json`

Source-owned site metadata:

- `scripts/music_league/site_meta.py`
  Holds stable metadata such as the site version and changelog entries

## Main Code Paths

- `scripts/generate_site.py`
  Thin entrypoint. Loads data, enriches the model, records build metadata, and writes the site.
- `scripts/music_league/data_loader.py`
  Reads CSV files, normalizes strings, builds base objects, and applies config.
- `scripts/music_league/stats.py`
  Computes totals, rankings, placements, similarity scores, URLs, and page-ready collections.
- `scripts/music_league/render.py`
  Shared HTML helpers, common page shell, sortable-table helper, footer, and site build orchestration.
- `scripts/music_league/pages/`
  One module per page family.

## Generated Output

The generator recreates the `site/` directory on every run.

Important implication:

- `site/` is a build artifact
- source files are authoritative
- local edits inside `site/` will be lost on the next build

## Design Principles

- Static output only
- Text-heavy pages with dense cross-linking
- Derived stats are computed once at build time
- Shared rendering helpers should drive repeated behavior such as navigation, tables, and footer content
- Private league examples should stay out of committed documentation
