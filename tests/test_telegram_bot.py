import asyncio

import pytest

from takeover.models import Entity
from takeover.registry import SessionRegistry
from takeover.telegram_bot import TelegramBotService, load_settings


def service(state=None) -> TelegramBotService:
    registry = SessionRegistry({})
    registry.add_entity(Entity("michela", "person", "Michela"))
    registry.add_entity(Entity("graziano", "person", "Graziano"))
    return TelegramBotService(
        registry=registry,
        identities={
            "michela": {
                "drop_token": "michela-TEST",
            }
        },
        state=state if state is not None else {},
        app_url="https://takeover.invalid",
        bot_username="takeover_process_bot",
    )


def test_start_resolves_drop_token_and_welcomes_the_participant() -> None:
    state = {}
    reply = service(state).start(
        telegram_user_id=123, first_name="M", args=["michela-TEST"]
    )

    assert reply.text == (
        "WELCOME MICHELA\n\n"
        "You have entered TAKE OVER.\n"
        "Bring something. Make a connection. Pass it on."
    )
    assert state["telegram_identity_links"]["123"] == "michela"


def test_start_without_a_known_drop_token_stays_anonymous() -> None:
    reply = service().start(telegram_user_id=123, first_name="M", args=[])

    assert reply.text == "TAKE OVER\n\nYou are here, but I don't know you yet."
    assert reply.buttons == ()


def test_identity_consent_unlocks_the_participant_encrypted_drop() -> None:
    state = {}
    bot = service(state)
    bot.start(telegram_user_id=123, first_name="M", args=["michela-TEST"])
    reply = bot.bring(telegram_user_id=123)

    assert reply.text.startswith("BRING SOMETHING\nEncrypted in your browser before storage.")
    assert reply.buttons[0].url == "https://takeover.invalid/?view=resources&k=michela-TEST"
    assert state["telegram_identity_links"]["123"] == "michela"


def test_state_and_needs_are_projected_from_the_shared_registry() -> None:
    bot = service()

    assert "PEOPLE        6 ACTIVE" in bot.project_state().text
    needs = bot.needs().text
    assert "ABSTRACT · IN PROGRESS" in needs
    assert "PRODUCTION · NOT YET ACTIVATED" in needs


def test_connect_and_pass_record_proposals_without_mutating_the_graph() -> None:
    state = {}
    bot = service(state)
    bot.start(telegram_user_id=123, first_name="M", args=["michela-TEST"])

    relation = bot.connect(telegram_user_id=123, args=["graziano"])
    invitation = bot.pass_it_on(telegram_user_id=123, args=["sasha"])

    assert relation.text == "MICHELA → GRAZIANO\nRELATION PROPOSED"
    assert invitation.text == "PASS IT ON · INVITATION REQUESTED\nSASHA"
    assert [event["kind"] for event in state["telegram_events"]] == [
        "telegram_identity_linked",
        "relation_proposed",
        "invitation_requested",
    ]
    assert bot.project_state().text.endswith("RELATIONS     4 ACTIVE")


class FakeMessage:
    def __init__(self) -> None:
        self.replies = []

    async def reply_text(self, text, **kwargs) -> None:
        self.replies.append((text, kwargs))


class FakeUpdate:
    def __init__(self) -> None:
        self.effective_user = type("User", (), {"id": 123, "first_name": "M"})()
        self.effective_message = FakeMessage()


def test_start_handler_exposes_the_service_reply_at_the_telegram_boundary() -> None:
    bot = service()
    update = FakeUpdate()
    context = type(
        "Context",
        (),
        {"args": ["michela-TEST"], "application": type("App", (), {"bot_data": {"service": bot}})()},
    )()

    asyncio.run(bot.handle_start(update, context))

    assert update.effective_message.replies[0][0].startswith("WELCOME MICHELA")


def test_startup_reports_missing_configuration_instead_of_keyerror() -> None:
    with pytest.raises(SystemExit) as exc:
        load_settings({})

    assert str(exc.value) == (
        "Missing required environment variables: "
        "TAKEOVER_TELEGRAM_BOT_TOKEN, TAKEOVER_APP_URL"
    )


def test_startup_rejects_a_telegram_address_as_the_streamlit_app_url() -> None:
    with pytest.raises(SystemExit) as exc:
        load_settings({
            "TAKEOVER_TELEGRAM_BOT_TOKEN": "test-token",
            "TAKEOVER_APP_URL": "t.me/takeover_fotografiska_bot",
        })

    assert "absolute http:// or https:// URL" in str(exc.value)
    assert "Streamlit app" in str(exc.value)
