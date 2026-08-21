# Persona authentication data boundary

## Evidence inspected

The sibling Affranchis implementation demonstrates a 128-bit access key with a
fixed 22-symbol emoji projection. Registration upserts a player record and
authentication appends or updates activity state. Its player schema can include
the canonical access key, full emoji projection, four- and six-symbol suffixes,
a reversible word phrase, nickname, role, consent flags, preferred mode,
session relations, status, joined time, and last-joined time.

The current TAKE OVER Notion manifest contains `persons` and `interactions`
sources, but no configured `persona` source. A workspace search on 2026-08-21
did not identify a TAKE OVER Persona database. Therefore the authentication test
page uses an explicitly provisional, session-local adapter and makes no remote
durability claim.

## What the test page compiles

### Persona

- canonical 128-bit access key;
- optional nickname;
- full 22-symbol emoji projection;
- four- and six-symbol discovery suffixes;
- explicit `provisional` authority;
- created and last-authenticated timestamps.

### Authentication interaction

- unique interaction identifier;
- `persona_minted` or `persona_authenticated` kind;
- persona key reference;
- timezone-aware occurrence time;
- explicit `provisional` authority;
- interface source (`authentication-test`).

## Recommended authoritative split

Do not copy every sibling player field into one Persona row. In particular,
the canonical key, full emoji projection, and word phrase are reversible forms
of the same credential. Persisting all three multiplies exposure rather than
adding identity information.

An authoritative Persona record can compile:

- an opaque persona identifier;
- a one-way credential verifier or keyed digest and its version;
- four- and six-symbol lookup suffixes only if short-suffix login remains a
  deliberate accepted risk;
- optional display alias;
- lifecycle status;
- created and last-authenticated timestamps;
- provenance and authority;
- separately governed consent references.

An Interaction record can compile:

- an opaque interaction identifier and Persona relation;
- event kind, result, timestamp, interface, and application/session context;
- credential representation used (`hex`, `emoji-full`, or `emoji-suffix`), but
  never the supplied credential value;
- storage receipt/provenance when a remote adapter confirms persistence.

Identity, capability, visibility, consent, inhabited-node information, and application
session membership remain separate concepts. The emoji projection is a display
and discovery device; it grants no capability.
