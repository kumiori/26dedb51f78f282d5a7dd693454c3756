"""Small Telegram interface over the TAKE OVER application registries.

Telegram is an interface adapter here: project facts continue to come from the
same registry used by the Streamlit application. Identity links and proposal
events are process-local in V0 and are therefore explicitly provisional.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import tomllib
from typing import Any, Mapping, MutableMapping, Sequence
from urllib.parse import urlencode, urlparse

from .identity import resolve_drop_token
from .registry import Registry, SessionRegistry, with_rc0_seeds


@dataclass(frozen=True)
class BotButton:
    label: str
    callback_data: str = ""
    url: str = ""


@dataclass(frozen=True)
class BotReply:
    text: str
    buttons: tuple[BotButton, ...] = ()


@dataclass(frozen=True)
class BotSettings:
    token: str
    app_url: str
    bot_username: str
    secrets_path: Path
    notion_token: str


def load_settings(environ: Mapping[str, str]) -> BotSettings:
    """Validate runtime configuration without exposing secret values."""
    required = ("TAKEOVER_TELEGRAM_BOT_TOKEN", "TAKEOVER_APP_URL")
    missing = [name for name in required if not str(environ.get(name, "")).strip()]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    app_url = str(environ["TAKEOVER_APP_URL"]).strip().rstrip("/")
    parsed = urlparse(app_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit(
            "TAKEOVER_APP_URL must be an absolute http:// or https:// URL for the Streamlit app; "
            "it is not the Telegram t.me address."
        )
    return BotSettings(
        token=str(environ["TAKEOVER_TELEGRAM_BOT_TOKEN"]).strip(),
        app_url=app_url,
        bot_username=str(
            environ.get("TAKEOVER_TELEGRAM_BOT_USERNAME", "takeover_process_bot")
        ).lstrip("@").strip(),
        secrets_path=Path(environ.get("TAKEOVER_SECRETS_FILE", ".streamlit/secrets.toml")),
        notion_token=str(environ.get("NOTION_TOKEN", "")).strip(),
    )


class TelegramBotService:
    """Project-specific command behavior independent of Telegram transport."""

    def __init__(
        self,
        *,
        registry: Registry,
        identities: Mapping[str, Mapping[str, str]],
        state: MutableMapping[str, Any],
        app_url: str,
        bot_username: str,
    ) -> None:
        self.registry = registry
        self.identities = identities
        self.state = state
        self.app_url = app_url.rstrip("/")
        self.bot_username = bot_username.lstrip("@").strip()
        state.setdefault("telegram_identity_links", {})
        state.setdefault("telegram_events", [])

    def _entities(self):
        return with_rc0_seeds(
            self.registry.list_entities(), self.registry.list_relations()
        )

    def _linked_participant(self, telegram_user_id: int) -> str | None:
        return self.state["telegram_identity_links"].get(str(telegram_user_id))

    def _event(self, kind: str, actor_id: str, target: str = "") -> None:
        self.state["telegram_events"].append({
            "kind": kind,
            "actor_id": actor_id,
            "target": target,
            "occurred_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "visibility": "private",
            "authority": "provisional",
            "source": "telegram",
        })

    def start(
        self, *, telegram_user_id: int, first_name: str, args: Sequence[str]
    ) -> BotReply:
        del first_name
        token = args[0] if args else ""
        participant_id = resolve_drop_token(token, self.identities)
        if participant_id:
            telegram_id = str(telegram_user_id)
            if self.state["telegram_identity_links"].get(telegram_id) != participant_id:
                self.state["telegram_identity_links"][telegram_id] = participant_id
                self._event("telegram_identity_linked", participant_id)
            return BotReply(
                f"WELCOME {participant_id.upper()}\n\n"
                "You have entered TAKE OVER.\n"
                "Bring something. Make a connection. Pass it on."
            )
        return BotReply("TAKE OVER\n\nYou are here, but I don't know you yet.")

    def project_state(self) -> BotReply:
        entities, relations = self._entities()
        active_people = sum(
            row.type == "person" and row.status == "active" for row in entities
        )
        active_relations = sum(row.status == "active" for row in relations)
        return BotReply(
            "TAKE OVER\n"
            "REGISTRY      SHARED\n"
            f"PEOPLE        {active_people} ACTIVE\n"
            f"NEEDS         {len(self.registry.list_necessities())} TRACKED\n"
            f"RELATIONS     {active_relations} ACTIVE"
        )

    def needs(self) -> BotReply:
        rows = self.registry.list_necessities()
        lines = [
            f"{row.title.replace('_', ' ').upper()} · {row.status.replace('_', ' ').upper()}"
            for row in rows
        ]
        return BotReply("CURRENT NEEDS\n\n" + "\n".join(lines))

    def bring(self, *, telegram_user_id: int) -> BotReply:
        participant_id = self._linked_participant(telegram_user_id)
        if not participant_id:
            return BotReply("CONNECT YOUR TAKE OVER IDENTITY FIRST WITH A PRIVATE INVITATION.")
        drop_token = str(self.identities.get(participant_id, {}).get("drop_token", "")).strip()
        if not drop_token:
            return BotReply("PRIVATE DROP · NOT CONFIGURED")
        query = urlencode({"view": "resources", "k": drop_token})
        return BotReply(
            "BRING SOMETHING\nEncrypted in your browser before storage.\n"
            "Your material remains associated with your node.",
            (BotButton("OPEN PRIVATE DROP", url=f"{self.app_url}/?{query}"),),
        )

    def connect(self, *, telegram_user_id: int, args: Sequence[str]) -> BotReply:
        participant_id = self._linked_participant(telegram_user_id)
        if not participant_id:
            return BotReply("CONNECT YOUR TAKE OVER IDENTITY FIRST WITH A PRIVATE INVITATION.")
        target = " ".join(args).strip().lower()
        entities, _relations = self._entities()
        target_row = next(
            (row for row in entities if row.id == target or row.title.lower() == target),
            None,
        )
        if target_row is None:
            return BotReply("USE /connect FOLLOWED BY AN EXISTING NODE.")
        self._event("relation_proposed", participant_id, target_row.id)
        return BotReply(
            f"{participant_id.upper()} → {target_row.title.upper()}\nRELATION PROPOSED"
        )

    def pass_it_on(self, *, telegram_user_id: int, args: Sequence[str]) -> BotReply:
        participant_id = self._linked_participant(telegram_user_id)
        if not participant_id:
            return BotReply("CONNECT YOUR TAKE OVER IDENTITY FIRST WITH A PRIVATE INVITATION.")
        target = " ".join(args).strip()
        if not target:
            return BotReply("USE /pass FOLLOWED BY A NAME.")
        self._event("invitation_requested", participant_id, target)
        return BotReply(f"PASS IT ON · INVITATION REQUESTED\n{target.upper()}")

    async def _send(self, update, reply: BotReply) -> None:
        kwargs: dict[str, Any] = {}
        if reply.buttons:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = [[
                InlineKeyboardButton(
                    button.label,
                    callback_data=button.callback_data or None,
                    url=button.url or None,
                )
                for button in reply.buttons
            ]]
            kwargs["reply_markup"] = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(reply.text, **kwargs)

    async def handle_start(self, update, context) -> None:
        user = update.effective_user
        await self._send(update, self.start(
            telegram_user_id=user.id,
            first_name=user.first_name or "there",
            args=context.args,
        ))

    async def handle_state(self, update, _context) -> None:
        await self._send(update, self.project_state())

    async def handle_needs(self, update, _context) -> None:
        await self._send(update, self.needs())

    async def handle_bring(self, update, _context) -> None:
        await self._send(update, self.bring(telegram_user_id=update.effective_user.id))

    async def handle_connect(self, update, context) -> None:
        await self._send(update, self.connect(
            telegram_user_id=update.effective_user.id, args=context.args
        ))

    async def handle_pass(self, update, context) -> None:
        await self._send(update, self.pass_it_on(
            telegram_user_id=update.effective_user.id, args=context.args
        ))

    async def handle_callback(self, update, context) -> None:
        query = update.callback_query
        await query.answer()
        parts = str(query.data or "").split(":", 2)
        if parts[:2] == ["command", "state"]:
            reply = self.project_state()
        elif parts[:2] == ["command", "needs"]:
            reply = self.needs()
        elif parts[:2] == ["command", "bring"]:
            reply = self.bring(telegram_user_id=update.effective_user.id)
        else:
            reply = BotReply("USE /pass FOLLOWED BY A NAME.")
        await self._send(update, reply)

    async def handle_ready(self, application) -> None:
        from telegram import BotCommand

        await application.bot.set_my_commands([
            BotCommand("start", "Enter TAKE OVER"),
            BotCommand("state", "Where are we?"),
            BotCommand("bring", "Bring something"),
            BotCommand("needs", "What is needed?"),
            BotCommand("connect", "Propose a connection"),
            BotCommand("pass", "Pass it on"),
        ])
        identity = await application.bot.get_me()
        username = identity.username or self.bot_username
        print(
            f"TAKE OVER bot is polling as @{username}. Send /start in Telegram. "
            "Press Ctrl-C here to stop.",
            flush=True,
        )


def build_application(token: str, service: TelegramBotService):
    """Build the python-telegram-bot polling application."""
    from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

    app = ApplicationBuilder().token(token).post_init(service.handle_ready).build()
    app.bot_data["service"] = service
    for command, handler in (
        ("start", service.handle_start),
        ("state", service.handle_state),
        ("bring", service.handle_bring),
        ("needs", service.handle_needs),
        ("connect", service.handle_connect),
        ("pass", service.handle_pass),
    ):
        app.add_handler(CommandHandler(command, handler))
    app.add_handler(CallbackQueryHandler(service.handle_callback))
    return app


def _identities_from_secrets(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    return {
        str(key): {
            name: str(dict(values)[name])
            for name in ("drop_token",)
            if str(dict(values).get(name, "")).strip()
        }
        for key, values in dict(payload.get("takeover_identities", {})).items()
    }


def main() -> None:
    settings = load_settings(os.environ)
    if settings.notion_token:
        from .notion import NotionRegistry

        registry: Registry = NotionRegistry(
            settings.notion_token,
            Path(__file__).resolve().parents[1] / "config" / "takeover_notion.json",
        )
        registry_label = "NOTION"
    else:
        registry = SessionRegistry({})
        registry_label = "PROVISIONAL SESSION"
    identities = _identities_from_secrets(settings.secrets_path)
    service = TelegramBotService(
        registry=registry,
        identities=identities,
        state={},
        app_url=settings.app_url,
        bot_username=settings.bot_username,
    )
    print(
        f"Starting TAKE OVER Telegram bot · registry {registry_label} · "
        f"{len(identities)} configured Telegram identities…",
        flush=True,
    )
    build_application(settings.token, service).run_polling(
        allowed_updates=["message", "callback_query"]
    )


if __name__ == "__main__":
    main()
