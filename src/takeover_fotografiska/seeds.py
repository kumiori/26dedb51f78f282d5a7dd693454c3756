"""Fotografiska RC0 application overlay; not an engine default."""

from takeover_engine import Entity, Necessity, Overlay, Relation, Visibility

RC0_OVERLAY = Overlay(
    id="fotografiska-rc0",
    entities=(
        Entity("kumiori", "person", "KUMIORI", label="Person • Alien / initiator / application", metadata={"display_name": "Andrés", "depth": 0}),
        Entity("ave", "person", "Ave", label="Person • Alien / artist / application", metadata={"depth": 0}),
        Entity("mai_brit", "person", "Mai-Brit", label="Person • Alien / voice / application", metadata={"depth": 0}),
        Entity("kenneerik", "person", "Kenn-Eerik", label="Person • Alien / sound / application", metadata={"depth": 0}),
        Entity("graziano", "person", "Graziano", label="Person • Alien / potential / application", status="latent_known", metadata={"depth": 1}),
        Entity("michela", "person", "Michela", status="latent_private", visibility=Visibility.PRIVATE, metadata={"internal_name": "Michela", "depth": 2}),
        Entity("latent_01", "person", "latent_01", status="unknown", visibility=Visibility.PRIVATE, metadata={"depth": 3}),
        Entity("latent_02", "person", "latent_02", status="unknown", visibility=Visibility.PRIVATE, metadata={"depth": 3}),
    ),
    relations=(
        Relation("seed-kumiori-ave", "kumiori", "ave", "collaborates_with"),
        Relation("seed-kumiori-mai-brit", "kumiori", "mai_brit", "collaborates_with"),
        Relation("seed-kumiori-kenneerik", "kumiori", "kenneerik", "collaborates_with"),
        Relation("seed-ave-kenneerik", "ave", "kenneerik", "collaborates_with"),
    ),
    necessities=tuple(
        Necessity(*row) for row in (
            ("need-abstract", "abstract", "application", "in_progress"),
            ("need-initial-kernel", "initial_kernel", "application", "found"),
            ("need-material", "material", "application", "collecting"),
            ("need-photographs", "photographs", "application", "found"),
            ("need-translation", "translation", "application", "open"),
            ("need-voices-sound", "voices_sound", "application", "agreed"),
            ("need-application", "application", "application", "to_submit"),
            ("need-production", "production", "production", "not_yet_activated"),
        )
    ),
)
