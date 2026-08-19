# TAKE OVER · Milestone 2.0

A sparse, multilingual operating surface for a growing multiplex community.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
streamlit run app.py
```

Run the test suite with `pytest` from the repository root.

The public app reads Notion when `NOTION_TOKEN` is available, or when Streamlit secrets contain either `NOTION_TOKEN`, `[notion].token`, or `[notion].api_key`. Without one of these, the app uses a session-local registry so the UI remains testable without creating external records.

The M2.0 Needs corpus is shared by the local fallback and the Notion sync. Apply it to the live registry after providing `NOTION_TOKEN`:

```bash
python scripts/bootstrap_takeover_notion.py sync-necessities
```

The operation is idempotent: it creates or updates the eight M2.0 records, preserves their application/production stages, and archives obsolete seeded Needs.

Developer-only node creation is enabled explicitly:

```bash
TAKEOVER_ADMIN_MODE=1 streamlit run app.py
```

This flag is intentionally off by default. M2.0 has no public or anonymous write path.

## Sources of truth

- `config/takeover_trajectory.yaml` — read-only timeline input (`trajectory-plan/v2`).
- `config/takeover_resources.yaml` — three zero-valued allocation observations and a separate investment-intention impulse; the impulse is dimensionless and never represented as available funds.
- `config/takeover_notion.json` — provisioned Notion database and data-source IDs.
- Notion page **Takeover** — live entity, relation, necessity and interaction registry.
- `takeover/i18n.py` — registered EN/ET/RU interface corpus, weights and translation status.

The three visual entity classes are separate by design: Person, Photograph and Audio. Stage is explicit metadata and is never inferred from dates.

## Repository conventions

- Keep credentials in environment variables or `.streamlit/secrets.toml`; never commit them.
- Treat `config/takeover_trajectory.yaml` and Notion as the documented sources of truth above.
- Add or update tests alongside behavioural changes.
- Use short-lived branches and keep commits focused on one logical change.
