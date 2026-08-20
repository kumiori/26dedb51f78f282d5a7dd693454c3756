# Working on takeover-engine

## Origin and purpose

This package was extracted from the Fotografiska TAKE OVER application at its RC0 packaging milestone. Its narrow job is to represent validated social/project facts, read them through explicit registries, add temporary state without corrupting authority, record events through injected boundaries, and create interface-neutral projections.

The original application remains in this repository as the first consumer and integration fixture. Fotografiska wording, people, invitation material, images, YAML, CSS, Streamlit routes, and release copy are application material, not engine defaults.

## Mental model

Follow this flow in code and explanations:

`validated facts -> registry state -> temporary overlays -> events -> projections -> interfaces`

- `takeover_engine.domain` owns immutable validated records.
- `takeover_engine.protocols` owns extension seams (`Registry`, `Clock`, `EventSink`).
- `takeover_engine.operations` changes or annotates state without choosing persistence or UI.
- `takeover_engine.projections` derives neutral data for consumers.
- `takeover_engine.schemas` owns validated contribution and storage envelopes.
- `takeover_adapters` translates external systems into those contracts.
- `takeover_fotografiska` contains the RC0 seed/configuration boundary.
- the root Streamlit application renders the Fotografiska experience.

## Invariants

1. The engine imports no Streamlit, Plotly, Notion, boto3, browser, or Fotografiska module.
2. Domain instances are valid at construction. Reject blank identifiers, naive timestamps, dangling relations, unsupported visibility, and unsupported crypto versions.
3. Authority is data. A session/local fallback is always `provisional`; never silently label it authoritative.
4. Overlays are non-mutating, idempotent by record identifier, and reversible using their `AppliedOverlay` receipt.
5. Application seeds live outside the engine. A new consumer works with zero Fotografiska imports.
6. Event time and persistence are injected. Domain code does not read a session dictionary or wall clock directly.
7. Identity says who; capability says what action and scope; visibility says who may observe. Never collapse them.
8. Emoji renderings and suffixes are display/discovery devices, not credentials or capabilities.
9. Contribution metadata contains ciphertext location and crypto envelope metadata only. Plaintext never enters a registry or storage adapter.
10. Projections return typed/plain data. Rendering belongs to an adapter or application.
11. Never claim production replication, recovery, remote durability, or successful upload without direct evidence.

## Adding an extension

1. Start from a protocol or add the smallest protocol that expresses the demonstrated need.
2. Put provider translation in `takeover_adapters`, never in the engine.
3. Declare the adapter's authority and failure behaviour.
4. Add an adapter-contract test matching the observable contract of existing adapters.
5. Add a consuming-application integration test when a user path changes.
6. Keep secrets in runtime configuration. Never add tokens, access keys, presigned URLs, or secret-bearing fixtures.

## Building a consumer

Create a separate virtual environment, install the wheel or Git URL, import only `takeover_engine`, construct a `RegistryState`, apply optional overlays, and render a projection with the consumer's own interface. Begin with `examples/minimal_consumer/consumer.py`.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install "takeover-engine @ git+https://github.com/kumiori/26dedb51f78f282d5a7dd693454c3756.git@v0.1.0"
python -c "from takeover_engine import RegistryState; print(RegistryState())"
```

## Safe modification sequence

1. Read `ARCHITECTURE.md` and relevant tests.
2. Change or add a failing focused test.
3. Implement inside the narrowest layer.
4. Run the focused test, then full suite and Ruff.
5. Build a wheel and inspect it. Confirm the engine has no framework imports.
6. Install the wheel into a clean target and run the reference consumer.
7. Update README, migration notes, and changelog when public compatibility changes.

## Exact verification commands

```bash
python -m pytest
python -m ruff check .
python -m build
python -m zipfile -l dist/takeover_engine-*.whl
python -m pip install --no-deps --target /tmp/takeover-engine-consumer dist/takeover_engine-*.whl
PYTHONPATH=/tmp/takeover-engine-consumer python examples/minimal_consumer/consumer.py
```

Use a fresh temporary path for clean-install verification.

## Release procedure

1. Ensure the worktree contains only intended release changes.
2. Update `takeover_engine.__version__` and `[project].version` together using semantic versioning.
3. Update `CHANGELOG.md` and `MIGRATION.md`.
4. Run every verification command above and the Streamlit application tests.
5. Commit the verified release.
6. Create an annotated tag: `git tag -a vX.Y.Z -m "takeover-engine vX.Y.Z"`.
7. Push the commit and tag only when publication is explicitly requested.
8. Verify the remote branch and tag before reporting a release as pushed.

Stable API is the symbol set exported from `takeover_engine.__init__`. Unexported module helpers are internal. Protocol implementations are supported extension points. Adapter modules and all `takeover_fotografiska` APIs are experimental in 0.x.
