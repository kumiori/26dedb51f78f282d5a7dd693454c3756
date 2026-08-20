# Migration to takeover-engine 0.1

The old `takeover` namespace mixed domain rules, external services, plotting, and Fotografiska material. Version 0.1 introduces explicit boundaries.

| Before | After | Status |
|---|---|---|
| `takeover.models.Entity` | `takeover_engine.Entity` | Stable; constructor field `type` becomes `kind`, while `.type` remains a read-only property. |
| `takeover.registry.Registry` | `takeover_engine.Registry` | Stable protocol reads one `RegistryState` with explicit authority. |
| `takeover.registry.with_rc0_seeds` | `takeover_engine.apply_overlay` plus `takeover_fotografiska.RC0_OVERLAY` | Generic operation stable; RC0 payload experimental/application-owned. |
| session dictionary registry | `takeover_adapters.SessionRegistry` | Experimental provisional adapter. |
| session dictionary events | `takeover_engine.emit_event` with injected `Clock` and `EventSink` | Stable boundary; session persistence is an adapter. |
| dictionary crypto/object fields | `Contribution`, `CryptoEnvelope`, `StorageObject` | Stable validated schemas. |
| raw S3 storage projection | normalize with `storage_object_from_s3`, then `project_storage` | Adapter plus stable projection. |
| Plotly/HTML builders | neutral `project_*` result followed by consumer rendering | Renderers remain application-specific. |

The original `takeover` modules remain temporarily as application compatibility surfaces. New consumers must not import them. They are excluded from the `takeover-engine` wheel, so there is no duplicate engine implementation in the distribution.
