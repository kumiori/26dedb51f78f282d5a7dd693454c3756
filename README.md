# takeover-engine · TAKE OVER M2.0

TAKEOVER • Fotografiska • 2026

A small typed engine extracted from the working TAKE OVER application, with the Fotografiska Streamlit interface retained as its first consumer.

The engine turns validated facts into explicit registry state, applies reversible temporary overlays, emits events through injected boundaries, and produces interface-neutral projections.

## Install the engine

```bash
python -m pip install "takeover-engine @ git+https://github.com/kumiori/26dedb51f78f282d5a7dd693454c3756.git@v0.1.0"
```

```python
from takeover_engine import Entity, Overlay, RegistryState, apply_overlay, project_network

facts = RegistryState(entities=(Entity("host", "person", "Host"),))
preview = Overlay("preview", entities=(Entity("guest", "person", "Guest"),))
network = project_network(apply_overlay(facts, preview).state)
```

The root `takeover_engine` exports the stable API. Adapters and `takeover_fotografiska` are experimental in 0.x. See `ARCHITECTURE.md`, `MIGRATION.md`, `AGENTS.md`, and `examples/minimal_consumer`.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[app,dev]'
streamlit run app.py
```

Run the test suite with `pytest` from the repository root.

## Telegram bot V0

The Telegram bot is a separate Python process and a second interface to the
same TAKE OVER registry. It does not contain a duplicate project state. The V0
supports `/start`, `/state`, `/bring`, `/needs`, `/connect`, and `/pass`.

Install the bot transport with the application dependencies:

```bash
python -m pip install -e '.[app,telegram,dev]'
```

Keep the replacement BotFather token outside Git. The token previously shared
in conversation must be revoked before this service is connected to Telegram.

```bash
export TAKEOVER_TELEGRAM_BOT_TOKEN="<replacement token>"
export TAKEOVER_APP_URL="https://<your Streamlit host>"
export TAKEOVER_TELEGRAM_BOT_USERNAME="takeover_process_bot"
export NOTION_TOKEN="<Science workspace connection token>"
python -m takeover.telegram_bot
```

Telegram `/start` resolves the existing participant drop token from the same
ignored secrets file used by the Streamlit application:

```toml
[takeover_identities.michela]
drop_token = "<existing private drop token>"
```

The private bot link is then
`https://t.me/takeover_process_bot?start=<drop_token>`. A recognised token links
that Telegram user to the participant for the lifetime of the bot process and
unlocks `/bring`. This convenience means the participant-scoped drop token is
transmitted through Telegram; rotate it if the link is disclosed.

Identity links and `/connect` or `/pass` proposal events are process-local and
explicitly provisional in V0. Restarting the bot clears them. They do not write
relations or invitations into Notion. Durable consent and proposal persistence
requires a dedicated Notion adapter before production use.

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

## Invitation events and analytics

Any non-empty `a` query parameter, for example `?a=application` or `?a=reviewer-qr`, is normalised and recorded once in the visible session event log as an invitation activation. This log is session-local; interaction persistence to Notion is not implemented yet.

Google Analytics emission is optional. Set a TAKE OVER property ID without committing it:

```bash
TAKEOVER_GA_MEASUREMENT_ID=G-XXXXXXXXXX streamlit run app.py
```

The same key may be placed in `.streamlit/secrets.toml`. When configured, the app sends `takeover_session_started` and `invitation_activation`; the latter includes only the normalised invitation source. The exact `?a=application` route also sends `commission_application_visit` as a commission-context referral signal. It does not authenticate or prove the visitor's identity. Without a valid `G-...` ID, no analytics component is loaded.

## Sources of truth

- `config/takeover_trajectory.yaml` — read-only timeline input (`trajectory-plan/v2`).
- `config/takeover_resources.yaml` — three zero-valued allocation observations and a separate investment-intention impulse; the impulse is dimensionless and never represented as available funds.
- `config/takeover_listening.yaml` — the open suggested-listening field and its reversible addendum presentation toggle.
- `config/takeover_notion.json` — provisioned Notion database and data-source IDs.
- Notion page **Takeover** — live entity, relation, necessity and interaction registry.
- `takeover/i18n.py` — registered EN/ET/RU interface corpus, weights and translation status.

The three visual entity classes are separate by design: Person, Photograph and Audio. Stage is explicit metadata and is never inferred from dates.

## Repository conventions

- Keep credentials in environment variables or `.streamlit/secrets.toml`; never commit them.
- Treat `config/takeover_trajectory.yaml` and Notion as the documented sources of truth above.
- Add or update tests alongside behavioural changes.
- Use short-lived branches and keep commits focused on one logical change.
