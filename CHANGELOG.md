# Changelog

## Unreleased

- Changed the invite generator into a session-only, copy-out tool: it no longer modifies a secrets file and now generates a separate `?c=` capability for editing the participant's own profile.
- Added read-only database diagnostics in the main sidebar and a dedicated test page that distinguishes connected-empty registries from provider errors.
- Added a distinct `commission_application_visit` analytics event for the `?a=application` invitation route without treating the route as visitor authentication.
- Changed new Fotografiska encrypted-upload object keys from `private/…` to the application-owned `public/…` bucket prefix; encryption and registry visibility are unchanged.

## 0.1.0 - 2026-08-20

- Extracted immutable validated domain records and explicit registry authority.
- Added reversible/idempotent overlays and injected event sink/clock protocols.
- Added typed encrypted-contribution and normalized storage schemas.
- Added interface-neutral network, event, and storage projections.
- Added session, S3-normalization, and development-only JSON adapters.
- Moved the Fotografiska RC0 seed payload behind an application namespace.
- Added a clean reference consumer and package/adapter/integration verification.
