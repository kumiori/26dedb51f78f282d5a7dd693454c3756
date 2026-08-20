Takeover Engine Extraction and Packaging Brief

1. Objective

Extract the reusable protocol engine currently embedded in Takeover into a clean, independently installable, versioned package.

Takeover must remain a living application and the principal proving ground for the engine. It must consume the same packaged engine that external applications consume.

The first external consumer is expected to be Tebka.science, but the architecture must not contain assumptions specific to Tebka or Fotografiska.

This is an extraction from demonstrated working behavior, not a rewrite and not an attempt to invent a universal framework.

⸻

2. What the engine actually is

The engine is not a Streamlit website, exhibition framework, visualization library, or collection of reusable UI components.

Its working abstraction is:

A privacy-aware state-transition and projection engine for a partially known collective network, with explicit provenance, identity, uncertainty, and visibility boundaries.

Its purpose is to allow networks of people, works, needs, contributions, relations, and events to evolve without collapsing important distinctions between:

- known and unknown;
- public and private;
- proposed and realised;
- latent and active;
- observation and intention;
- authoritative and provisional state.

The architectural flow should be made explicit:

validated facts
↓
registry state
↓
temporary overlays
↓
events
↓
projections
↓
interfaces

Interfaces are downstream consumers.

The graph, timeline, sidebar, Streamlit application, Notion database, encrypted upload interface, and Plotly visualisations are not the engine itself.

⸻

3. Why this extraction exists

Takeover has evolved into a working interactive system containing concepts that are demonstrably useful beyond the original exhibition application.

The motivation for extraction is therefore not merely code reuse.

It is to preserve and propagate a disciplined way of constructing collaborative systems in which:

- incomplete knowledge remains incomplete;
- privacy remains explicit;
- state changes have provenance;
- scenarios do not silently become facts;
- visual representations cannot redefine reality;
- external infrastructure does not become the domain model.

The desired relationship is:

                    Takeover
                       │
                       │ dogfoods
                       ▼
               takeover-engine
                 /     |      \
                /      |       \
               ▼       ▼        ▼
            Tebka    future    research /
                    artworks   collaborative
                               applications

There must remain one implementation of the engine.

No sibling project should need to scavenge Takeover source code.

⸻

4. Core engine contracts

The following principles should become explicit architectural invariants.

State is declared, not guessed

The system must not infer semantic state merely because some related data exists.

Absence is meaningful

No data must not automatically mean false, inactive, nonexistent, or zero.

Private knowledge is not automatically public knowledge

Knowledge and visibility are separate dimensions.

Lifecycle states are semantic

Application, activation, production, exhibition, propagation, and equivalent lifecycle stages must be explicit rather than inferred from timestamps.

Intentions are not facts

The system must preserve distinctions between:

proposal
intention
observation
realised contribution

History annotates state

Historical information must not silently mutate authoritative current state.

Projections are not truth

Graphs, timelines, dashboards, maps and figures are projections of state.

They must never become authoritative state merely because something appeared visually.

Overlays are reversible

Temporary kernels, scenarios, invitations, simulations and proposed states must be capable of being superimposed without mutating the underlying authoritative registry.

Overlay operations should be idempotent where appropriate.

Infrastructure does not define semantics

Notion, Streamlit, Plotly, S3/Filebase, browser sessions and analytics are adapters.

Replacing them should not require redesigning the domain model.

Storage proves storage

The existence of ciphertext in object storage proves that ciphertext exists.

It does not prove the semantic meaning of the plaintext that may have produced it.

⸻

5. Architectural audit

Before extraction, produce a short architecture document mapping the existing Takeover codebase.

Every significant component should be classified as:

ENGINE
ADAPTER
TAKEOVER/FOTOGRAFISKA APPLICATION
UNRESOLVED

Specifically identify:

- entities;
- relations;
- necessities;
- lifecycle/state;
- registry operations;
- identity;
- capabilities;
- visibility;
- overlays;
- events;
- contribution handling;
- encryption metadata;
- storage semantics;
- schemas;
- projections;
- UI rendering;
- external integrations;
- project-specific content.

Do not begin major restructuring until this map exists.

⸻

6. Proposed extraction boundary

Use the following as a starting architecture, modifying it only when the existing implementation provides evidence for a better boundary.

takeover_engine/
│
├── domain/
│ ├── entities.py
│ ├── relations.py
│ ├── necessities.py
│ ├── contributions.py
│ └── identity.py
│
├── protocols/
│ ├── registry.py
│ ├── event_sink.py
│ ├── object_store.py
│ └── clock.py
│
├── operations/
│ ├── overlay.py
│ ├── activation.py
│ ├── contribution.py
│ └── visibility.py
│
├── projections/
│ ├── network.py
│ ├── timeline.py
│ ├── storage.py
│ └── resources.py
│
└── schemas/
├── trajectory.py
├── listening.py
└── call.py

External integrations should live separately:

takeover_adapters/
├── notion.py
├── session.py
├── filebase.py
├── streamlit_encryption.py
└── plotly.py

Takeover/Fotografiska-specific material should remain application-level:

takeover_fotografiska/
├── seeds.py
├── corpus.py
├── configuration/
└── interface/

The exact module names are negotiable.

The separation of domain → protocols/operations → projections → adapters/application is not.

⸻

7. Typed domain model

The engine should operate primarily on typed domain objects.

Existing concepts including:

Entity
Relation
Necessity
Contribution
Identity
Event
Visibility

should receive explicit validation and documented semantics.

In particular:

- bring Relation and Necessity validation to the level expected of Entity;
- replace important dict[str, Any] structures with typed value objects;
- create versioned schemas for cryptographic metadata;
- normalize storage objects before they reach projections;
- make visibility policy a first-class domain concern.

The public API should expose meaningful domain concepts, not raw Notion rows, Streamlit state dictionaries or S3-shaped objects.

⸻

8. Registry boundary

Preserve and strengthen the Registry protocol.

The registry is a critical abstraction separating domain operations from persistence.

An application should be capable of changing:

Notion
↓
PostgreSQL
↓
local test registry
↓
future distributed registry

without changing the semantics of the engine.

Local fallback state must never silently impersonate authoritative persisted state.

The authoritative/provisional distinction must remain explicit.

⸻

9. Non-destructive overlays

The existing overlay pattern is one of the engine’s strongest abstractions and should be promoted to a first-class feature.

The current with_rc0_seeds() idea should be generalized appropriately.

An overlay should allow:

authoritative state +
scenario / seed / invitation / draft
↓
projected temporary state

without writing the temporary state into the authoritative registry.

Potential applications include:

- initial social kernels;
- invitations;
- curatorial hypotheses;
- simulations;
- staged activations;
- speculative network extensions;
- private previews;
- alternative scenarios.

RC0-specific people and necessities themselves belong outside the engine.

The overlay mechanism belongs inside it.

⸻

10. Events

Events should be semantic domain events rather than analytics clicks.

Introduce or strengthen:

Event
EventSink
Clock

The engine should accept an injected clock rather than generating timestamps through hidden global/session dependencies.

Events should have stable semantic labels and typed payloads.

A session dictionary must not be the event architecture.

This should make it possible for the same engine to emit events into:

memory
database
file
analytics
message queue
test harness

without changing domain operations.

⸻

11. Identity, capabilities and privacy

Identity must remain independent from UI session identity.

Preserve the distinction between:

participant identity
invitation capability
scoped contribution/drop token
browser session
public projection

Emoji suffixes or other human-readable identifiers may remain useful projections but must not be treated as authentication mechanisms.

Privacy states should remain semantically distinguishable, including concepts equivalent to:

active
known-latent
private-latent
unknown

The system must be able to represent that someone or something may exist without making that knowledge public.

⸻

12. Contributions and encrypted storage

Separate:

contribution semantics
cryptographic envelope
object storage
visibility
ownership

The engine should not depend directly on Filebase/S3-shaped dictionaries.

Define normalized typed storage and contribution objects.

Cryptographic metadata must use an explicit, validated, versioned schema.

The local encrypted JSON registry should either gain appropriate concurrency guarantees or remain clearly marked as a development/test adapter.

⸻

13. Projection architecture

Projections should convert domain state into neutral, typed representations suitable for interfaces.

Examples include:

network projection
timeline projection
storage projection
resource projection
event projection
language-status projection

A network projection should not return Plotly objects or HTML.

It should return a neutral representation from which an adapter can construct:

- Plotly;
- D3;
- Streamlit;
- React;
- static SVG;
- API JSON;
- another future interface.

This is fundamental to making the engine reusable outside the current application.

⸻

14. What must remain outside the engine

Do not package application material merely because Takeover currently uses it.

Keep outside the core:

- Fotografiska-specific text;
- exhibition application material;
- photographs;
- PDFs;
- QR artwork;
- exhibition frames;
- current CSS and visual language;
- weighted TAKE OVER utterance corpus;
- named RC0 participants;
- hard-coded social seeds;
- Streamlit navigation/dialogs;
- Plotly figure construction;
- Notion database identifiers;
- Filebase credentials;
- bucket configuration;
- Google Analytics;
- application-specific prompts and copy.

These may consume the engine.

They do not define it.

⸻

15. Packaging

Create an independently installable Python package using pyproject.toml.

Prefer a src/ layout.

The package must install into a clean Python environment with no undeclared dependency on Takeover application files.

Initially support versioned GitHub installation.

Registry publication such as PyPI can follow when useful.

⸻

16. Takeover must dogfood the package

After extraction, Takeover itself must import the packaged engine.

There must never be:

Takeover's real engine

- external reusable engine

There must be:

one engine
↑
│
Takeover + external consumers

Local Takeover development may use an editable package installation.

⸻

17. Public API

Design a deliberately small public API.

Consumers should import semantic concepts from documented namespaces rather than internal implementation paths.

Explicitly document:

- stable API;
- experimental API;
- internal implementation;
- extension points.

Do not promise backwards compatibility for every internal module.

⸻

18. Versioning and propagation

Use semantic versioning.

Downstream applications should pin releases rather than follow main.

Desired propagation:

Takeover development
↓
engine improvement
↓
engine tests
↓
Takeover integration tests
↓
version bump
↓
tagged release
↓
dependency-update PR in consumers
↓
consumer tests
↓
preview deployment
↓
merge / production

Eventually use Dependabot, Renovate or equivalent automation to propose engine upgrades to Tebka and other consumers.

An engine release should never silently deploy breaking behavior into every application.

⸻

19. Testing

Tests should exist at several boundaries.

Domain tests

Validate entities, relations, necessities, contributions, lifecycle and visibility semantics.

Operation tests

Test activation, overlays, contributions and state transitions.

Projection tests

Given known state, projections should produce deterministic neutral representations.

Adapter contract tests

Verify adapters satisfy their declared protocols.

Takeover integration tests

Run Takeover against the extracted engine.

Clean-consumer smoke test

Install the released package in a fresh environment and instantiate a minimal independent application.

⸻

20. Reference consumer

Create a deliberately tiny application that demonstrates engine usage without Fotografiska or Takeover assumptions.

It should demonstrate at least:

create/load registry
add typed entities
create relations
apply temporary overlay
perform state transition
emit event
generate projection
render projection through one simple adapter

Its purpose is to prove that the abstraction genuinely exists outside Takeover.

⸻

21. AGENTS.md

Create a substantial AGENTS.md inside the package.

This is not merely coding guidance.

It should transmit the conceptual constitution of the engine to future human and AI developers.

Origin

Explain that the engine emerged from Takeover, a living collaborative artistic application.

The exhibition supplied the first concrete world.

The abstraction emerged when it became clear that the useful technology was not the particular website but the disciplined treatment of a growing, partially known collective.

Purpose

State the core abstraction:

A state-transition and projection engine for a partially known collective network, with explicit provenance and privacy boundaries.

Mental model

Include:

validated facts
↓
registry state
↓
temporary overlays
↓
events
↓
projections
↓
interfaces

Explain every boundary.

Invariants

Agents must understand:

- state is declared, not guessed;
- absence is represented honestly;
- private knowledge is not automatically public;
- proposal, intention, observation and realisation differ;
- projections are not sources of truth;
- overlays must not silently mutate authoritative state;
- external services are adapters;
- storage existence does not establish semantic truth;
- authoritative and fallback state must remain distinguishable.

Extension test

Before adding something to the engine, ask:

1. Is this domain behavior rather than presentation?
2. Is it demonstrated by more than one plausible consumer?
3. Can it be expressed using an existing abstraction?
4. Would placing it here couple the engine to a specific application?
5. Can it be represented and tested without Streamlit, Plotly, Notion or Filebase?

When uncertain, prefer keeping functionality in the consuming application until reuse is demonstrated.

How to build a new consumer

Document the minimum path from package installation to a working independent experience.

How to modify the engine

Document:

understand invariant
→ modify domain/operation
→ test
→ verify Takeover
→ update version
→ release
→ upgrade consumer

Release procedure

Provide exact commands and repository procedures for versioning and publishing.

⸻

22. Potential applications

These are evidence of the abstraction’s reach, not requirements for immediate implementation.

Potential consumers include:

- artistic collaborations;
- participatory exhibitions;
- research networks;
- collaborative scientific projects;
- participatory archives;
- oral-history systems;
- community protocols;
- staged invitations;
- experimental organisations;
- residency networks;
- distributed creative projects;
- provenance-sensitive collections;
- collaborative photographic projects;
- scientific collaboration maps;
- agent-mediated collective systems.

The shared characteristic is not their visual form.

It is that they contain partially known networks whose state evolves through meaningful actions under constraints of identity, provenance, uncertainty and visibility.

⸻

23. Possible future extensions

Leave conceptual room for, but do not prematurely implement:

- pluggable registries;
- richer policy/visibility engines;
- declarative lifecycle definitions;
- schema migration;
- cryptographic identity;
- signed events;
- decentralized registries;
- event sourcing;
- collaborative/multiplayer state;
- offline synchronization;
- agent participants;
- agent-mediated contributions;
- headless/API operation;
- alternate front ends;
- replayable histories;
- scenario branching;
- federated networks;
- exportable provenance;
- richer capability systems.

These possibilities should influence avoidance of unnecessary coupling, but must not generate speculative infrastructure today.

⸻

24. Naming

Do not prematurely rename the engine.

takeover-engine is an acceptable working package name because it records provenance.

Once the extraction reveals the stable abstraction and at least one external consumer exists, reconsider whether the engine deserves an identity independent of Takeover.

Naming should follow understanding.

⸻

25. Definition of done

The extraction is complete when:

- Existing architecture has been classified into engine, adapter and application layers.
- Engine boundary is documented.
- Core domain objects are typed and validated.
- Registry is represented through an explicit protocol.
- EventSink and Clock are injectable.
- Important free-form dictionaries have become typed value objects.
- Visibility policy is explicit.
- RC0/Fotografiska-specific seeds have left the core.
- Overlay mechanism remains generic, reversible and tested.
- Storage projections consume normalized objects.
- Cryptographic metadata has a validated versioned schema.
- Projection outputs are interface-neutral.
- Streamlit, Plotly, Notion and Filebase remain adapters.
- Engine is independently installable.
- Takeover consumes that package.
- No duplicate engine implementation exists.
- Domain, operation and projection tests exist.
- Takeover integration tests pass.
- Minimal independent reference consumer works.
- README.md documents normal human consumption.
- AGENTS.md documents conceptual and architectural invariants.
- First version is tagged.
- Clean installation from another repository is demonstrated.
- Upgrade/release procedure is documented.

⸻

26. Final implementation report

At completion, provide:

1. the extraction map;
2. final package tree;
3. dependency diagram;
4. public API;
5. domain model;
6. adapter boundaries;
7. remaining coupling or technical debt;
8. installation instructions;
9. minimal external-consumer example;
10. release procedure;
11. migration notes for Takeover;
12. recommended first experiment integrating the engine into Tebka.science.

The final report should explicitly identify anything that was not extracted and why.

⸻

Governing principle

Abstract from demonstrated reuse, not imagined universality.

The photographs and exhibition supplied the engine’s first world.

The package should preserve what turned out to be more general: a disciplined mechanism by which a partially known collective can grow without pretending that every person, relationship, contribution, intention, or future state is already known.
