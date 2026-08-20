# TAKE OVER architecture audit

This audit records the repository boundary immediately before engine extraction. It is intentionally about the code that exists, not a speculative future platform.

## Demonstrated flow

The working application already follows a recognisable sequence:

1. YAML, Notion, session state, and storage metadata provide observed facts.
2. A registry exposes entities, relations, and necessities.
3. the Fotografiska RC0 seed set overlays missing registry records without persisting them.
4. interface actions append diagnostic events.
5. network, timeline, resource, storage, and language functions project state.
6. Streamlit, Plotly, Histropedia, and HTML render those projections.

The extraction preserves this sequence while making each boundary explicit: validated facts -> registry state -> temporary overlays -> events -> projections -> interfaces.

## Component classification

| Current component | Classification | Extraction decision |
|---|---|---|
| `takeover/models.py` | ENGINE | Replace with validated, typed domain records in `takeover_engine.domain`. |
| Registry protocol in `takeover/registry.py` | ENGINE | Move to `takeover_engine.protocols`; distinguish authoritative and provisional reads. |
| `SessionRegistry` | ADAPTER | Move to `takeover_adapters.session`; it is a development/test adapter. |
| RC0 entities, relations, and necessity rows | TAKEOVER/FOTOGRAFISKA APPLICATION | Move to `takeover_fotografiska.seeds`; never ship as engine defaults. |
| `with_rc0_seeds` | MIXED | Generalise the reversible/idempotent overlay operation in the engine; keep the RC0 payload in the application package. |
| `takeover/events.py` | MIXED | Make typed events, `Clock`, and `EventSink` engine concepts; keep session-state persistence in an adapter. |
| `takeover/identity.py` | MIXED | Keep key/emoji encoding as an engine utility, but move configured identities and invitation policy to the application. Emoji suffixes are display/discovery helpers, not authentication. |
| `takeover/encrypted_storage.py` | MIXED | Move typed contribution, crypto envelope, and storage-object schemas into the engine; keep the local JSON registry as an explicitly development-only adapter. |
| `takeover/storage_timeline.py` | ENGINE | Replace raw S3 dictionaries with a neutral storage projection over `StorageObject`. |
| `takeover/notion.py` | ADAPTER | Move to `takeover_adapters.notion`; the manifest remains application-owned. |
| `takeover/browser_encrypt.py` | ADAPTER | Move to `takeover_adapters.streamlit_encryption`; browser and Streamlit details are not engine concerns. |
| `takeover/graph.py` | ADAPTER/APPLICATION | Split neutral network projection from Fotografiska HTML presentation. |
| `takeover/timeline.py` | MIXED | Put neutral event/timeline rows in engine projections; keep YAML loading, Plotly, and Histropedia presentation outside the engine. |
| `takeover/resources.py` | MIXED | Keep semantic resource/storage projection neutral; keep Plotly figures and the Fotografiska resource vocabulary in the application package. |
| `takeover/analytics.py` | ADAPTER | Google Analytics emission is an external interface; activation-string normalisation is a small application utility. |
| `takeover/call.py`, `takeover/listening.py` | TAKEOVER/FOTOGRAFISKA APPLICATION | These validate project corpus/configuration, not reusable engine state. |
| `takeover/i18n.py` | TAKEOVER/FOTOGRAFISKA APPLICATION | The multilingual corpus and translation workflow are application-owned. |
| `takeover/style.py` | TAKEOVER/FOTOGRAFISKA APPLICATION | Visual language is application presentation. |
| `app.py`, `pages/` | TAKEOVER/FOTOGRAFISKA APPLICATION | Remain delivery interfaces, importing the installed package boundaries. |
| `config/`, exhibition images, application PDFs and TeX | TAKEOVER/FOTOGRAFISKA APPLICATION | Remain repository assets; they are not package engine data. |
| IPFS/Filebase production durability, cross-provider replication, and remote key recovery | UNRESOLVED | Not extracted or claimed: the repository demonstrates client encryption, presigned upload, and local metadata only. |

## Boundary invariants

- Engine modules import neither Streamlit, Plotly, Notion, boto3, nor Fotografiska configuration.
- Domain records validate identifiers, enumerated states, timestamps, and nested schemas when constructed.
- Registry authority is observable by callers; an adapter cannot silently present provisional state as authoritative.
- Overlays return a new state, do not mutate the source registry, are idempotent by semantic identifier, and can be removed by overlay identifier.
- Event time comes from an injected clock and event persistence from an injected sink.
- Identity, capability, and visibility are separate values. A rendered emoji suffix never grants a capability.
- Plaintext is not part of the contribution or storage schemas. Crypto metadata is versioned and validated.
- Projections return plain typed data. UI libraries render that data outside the engine.

## Public extraction boundary

The independently installable distribution is named `takeover-engine`. It exposes a small root API for stable domain records, protocols, operations, and projections. Adapter and Fotografiska namespaces are included as optional integration/application layers in this repository, but neither is imported by `takeover_engine`.

Compatibility modules may re-export new implementations during migration, but there is one implementation of each engine rule: `takeover_engine`.
