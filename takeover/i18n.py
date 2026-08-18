"""Single registered corpus for every interface utterance spoken by TAKE OVER."""

from __future__ import annotations

from dataclasses import dataclass, field


LANGUAGES = {"en": "English", "et": "Eesti", "ru": "Русский"}
VOICE_LANGUAGES = tuple(LANGUAGES)


@dataclass(frozen=True)
class Utterance:
    key: str
    canonical: str
    weight: int = 12
    translations: dict[str, str] = field(default_factory=dict)
    note: str = ""

    def text(self, language: str) -> str:
        return self.canonical if language == "en" else self.translations.get(language, self.canonical)

    def status(self, language: str) -> str:
        return "CANONICAL" if language == "en" else "PROVISIONAL"


def u(key: str, canonical: str, weight: int = 12, et: str = "", ru: str = "", note: str = "") -> Utterance:
    return Utterance(key, canonical, weight, {"et": et or canonical, "ru": ru or canonical}, note)


# This ordered registry is both the UI copy source and the automatically rendered
# VOICES corpus. Non-English wording is intentionally provisional in M2.0.
UTTERANCES = (
    u("project_name", "TAKE OVER", 100, "TAKE OVER", "TAKE OVER", "Title, imperative, protocol and invitation."),
    u("interactive_progress", "INTERACTIVE IN PROGRESS", 72, "INTERAKTIIVNE, ARENEMAS", "ИНТЕРАКТИВ В ПРОЦЕССЕ"),
    u("start_here", "START HERE", 66, "ALUSTA SIIT", "НАЧНИТЕ ЗДЕСЬ"),
    u("take_wall", "TAKE OVER THE WALL.", 34, "VÕTA SEIN ÜLE.", "ЗАХВАТИ СТЕНУ."),
    u("take_opening", "TAKE OVER THE OPENING.", 34, "VÕTA AVAMINE ÜLE.", "ЗАХВАТИ ОТКРЫТИЕ."),
    u("take_sound", "TAKE OVER THE SOUND.", 34, "VÕTA HELI ÜLE.", "ЗАХВАТИ ЗВУК."),
    u("take_restaurant", "TAKE OVER THE RESTAURANT.", 34, "VÕTA RESTORAN ÜLE.", "ЗАХВАТИ РЕСТОРАН."),
    u("take_night", "TAKE OVER THE NIGHT.", 34, "VÕTA ÖÖ ÜLE.", "ЗАХВАТИ НОЧЬ."),
    u("take_web", "TAKE OVER THE WEB SURFACE.", 34, "VÕTA VEEBIRUUM ÜLE.", "ЗАХВАТИ ВЕБ-ПРОСТРАНСТВО."),
    u("take_photography", "TAKE OVER PHOTOGRAPHY.", 34, "VÕTA FOTOGRAAFIA ÜLE.", "ЗАХВАТИ ФОТОГРАФИЮ."),
    u("pass_it_on", "PASS IT ON.", 62, "ANNA EDASI.", "ПЕРЕДАЙ ДАЛЬШЕ."),
    u("invitation", "Bring your voice, your image, your practice.", 52, "Too oma hääl, oma pilt, oma praktika.", "Принесите свой голос, своё изображение, свою практику."),
    u("necessities_title", "WHAT THE PROJECT NEEDS NOW", 48, "MIDA PROJEKT PRAEGU VAJAB", "ЧТО НУЖНО ПРОЕКТУ СЕЙЧАС"),
    u("voices", "VOICES", 46, "HÄÄLED", "ГОЛОСА"),
    u("timeline", "TIMELINE", 38, "AJATELG", "ХРОНОЛОГИЯ"),
    u("necessities", "NECESSITIES", 38, "VAJADUSED", "НЕОБХОДИМОСТИ"),
    u("network", "NETWORK", 38, "VÕRGUSTIK", "СЕТЬ"),
    u("you", "YOU?", 34, "SINA?", "ВЫ?"),
    u("enter_network", "ENTER THE NETWORK", 30, "SISENE VÕRGUSTIKKU", "ВОЙТИ В СЕТЬ"),
    u("manifesto_remains", "We start from what remains.", 25, "Alustame sellest, mis on alles.", "Мы начинаем с того, что осталось."),
    u("manifesto_doors", "We open doors.", 25, "Me avame uksi.", "Мы открываем двери."),
    u("manifesto_listen", "We listen. We respond.", 25, "Me kuulame. Me vastame.", "Мы слушаем. Мы отвечаем."),
    u("manifesto_build", "We build what comes next, together.", 25, "Me ehitame koos seda, mis tuleb järgmisena.", "Мы вместе создаём то, что будет дальше."),
    u("manifesto_live", "This is a live project.", 24, "See on elav projekt.", "Это живой проект."),
    u("manifesto_grows", "It grows with every connection.", 24, "See kasvab iga ühendusega.", "Он растёт с каждой связью."),
    u("application", "APPLICATION", 20, "TAOTLUS", "ЗАЯВКА"),
    u("in_progress", "IN PROGRESS", 20, "TÖÖS", "В ПРОЦЕССЕ"),
    u("collecting", "COLLECTING", 20, "KOGUMISEL", "СБОР"),
    u("found", "FOUND", 20, "LEITUD", "НАЙДЕНО"),
    u("agreed", "AGREED", 20, "KOKKU LEPITUD", "СОГЛАСОВАНО"),
    u("open", "OPEN", 20, "AVATUD", "ОТКРЫТО"),
    u("abstract", "ABSTRACT", 18, "KOKKUVÕTE", "АННОТАЦИЯ"),
    u("material", "MATERIAL", 18, "MATERJAL", "МАТЕРИАЛ"),
    u("initial_kernel", "INITIAL KERNEL", 18, "ALGNE TUUM", "НАЧАЛЬНОЕ ЯДРО"),
    u("photographs", "PHOTOGRAPHS", 18, "FOTOD", "ФОТОГРАФИИ"),
    u("voices_sound", "VOICES + SOUND", 18, "HÄÄLED + HELI", "ГОЛОСА + ЗВУК"),
    u("translation", "TRANSLATION", 18, "TÕLGE", "ПЕРЕВОД"),
    u("open_node", "Open the central node to begin.", 15, "Alustamiseks ava keskne sõlm.", "Чтобы начать, откройте центральный узел."),
    u("explicit_relations", "The system grows from explicit relations.", 15, "Süsteem kasvab selgetest suhetest.", "Система растёт из явных связей."),
    u("suggested_listening", "SUGGESTED LISTENING", 18, "SOOVITATAV KUULAMINE", "РЕКОМЕНДУЕМ ПОСЛУШАТЬ"),
    u("listening_work", "ARVO PÄRT · TABULA RASA", 16, "ARVO PÄRT · TABULA RASA", "АРВО ПЯРТ · TABULA RASA"),
    u("need_stage_state", "Need → stage → state. This is not a resources directory.", 12, "Vajadus → etapp → olek. See ei ole ressursside kataloog.", "Потребность → этап → состояние. Это не каталог ресурсов."),
    u("improve_translation", "IMPROVE THIS TRANSLATION", 12, "PARANDA SEDA TÕLGET", "УЛУЧШИТЬ ЭТОТ ПЕРЕВОД"),
    u("proposals_closed", "Proposals are not open yet.", 10, "Ettepanekud ei ole veel avatud.", "Предложения пока не принимаются."),
    u("voices_intro", "Every registered utterance currently spoken by TAKE OVER, arranged by weight.", 12, "Kõik TAKE OVERi registreeritud väljendid, järjestatud kaalu järgi.", "Все зарегистрированные высказывания TAKE OVER, расположенные по весу."),
    u("source_key", "SOURCE KEY", 8, "LÄHTEVÕTI", "КЛЮЧ ИСТОЧНИКА"),
    u("weight", "WEIGHT", 8, "KAAL", "ВЕС"),
    u("status", "STATUS", 8, "OLEK", "СТАТУС"),
    u("nodes", "NODES", 8, "SÕLMED", "УЗЛЫ"),
    u("connections", "CONNECTIONS", 8, "ÜHENDUSED", "СВЯЗИ"),
    u("connections_node", "CONNECTIONS/NODE", 8, "ÜHENDUSI/SÕLM", "СВЯЗЕЙ/УЗЕЛ"),
    u("project_navigation", "PROJECT NAVIGATION", 8, "PROJEKTI NAVIGATSIOON", "НАВИГАЦИЯ ПРОЕКТА"),
    u("registry", "REGISTRY", 8, "REGISTER", "РЕЕСТР"),
    u("development_interface", "DEVELOPMENT INTERFACE", 8, "ARENDUSLIIDES", "ИНТЕРФЕЙС РАЗРАБОТКИ"),
    u("access_door", "ACCESS DOOR", 10, "SISSEPÄÄSU UKS", "ВХОДНАЯ ДВЕРЬ"),
    u("project_formation", "A PROJECT IN FORMATION", 10, "KUJUNEV PROJEKT", "ПРОЕКТ В СТАНОВЛЕНИИ"),
    u("door_intro", "The door opens onto what exists now. Other routes remain visible, but unopened.", 10, "Uks avaneb sellele, mis praegu olemas on. Teised teed jäävad nähtavaks, kuid avamata.", "Дверь открывается в то, что существует сейчас. Другие пути видны, но пока закрыты."),
    u("follow_trajectory", "FOLLOW THE TRAJECTORY", 10, "JÄRGI TRAJEKTOORI", "СЛЕДОВАТЬ ТРАЕКТОРИИ"),
    u("open_timeline", "Open timeline →", 8, "Ava ajatelg →", "Открыть хронологию →"),
    u("see_needed", "SEE WHAT IS NEEDED", 10, "VAATA, MIDA ON VAJA", "ПОСМОТРЕТЬ, ЧТО НУЖНО"),
    u("open_necessities", "Open necessities →", 8, "Ava vajadused →", "Открыть необходимости →"),
    u("contribute_unopened", "CONTRIBUTE — UNOPENED", 8, "PANUSTA — AVAMATA", "ВНЕСТИ ВКЛАД — ЗАКРЫТО"),
    u("door_inactive", "This door is not active yet", 8, "See uks ei ole veel aktiivne", "Эта дверь пока не активна"),
    u("explore_dormant", "EXPLORE — DORMANT", 8, "AVASTA — UINUV", "ИССЛЕДОВАТЬ — НЕАКТИВНО"),
    u("node", "NODE", 8, "SÕLM", "УЗЕЛ"),
    u("stage", "STAGE", 8, "ETAPP", "ЭТАП"),
    u("registry_id", "REGISTRY ID", 8, "REGISTRI ID", "ID РЕЕСТРА"),
    u("no_necessities", "No necessities have been activated yet.", 8, "Ühtegi vajadust ei ole veel aktiveeritud.", "Ни одна необходимость пока не активирована."),
    u("timeline_source", "READ-ONLY M2 VIEW · YAML REMAINS THE TIMELINE SOURCE", 8, "M2 AINULT LUGEMISEKS · YAML JÄÄB AJATELJE ALLIKAKS", "M2 ТОЛЬКО ДЛЯ ЧТЕНИЯ · YAML ОСТАЁТСЯ ИСТОЧНИКОМ ХРОНОЛОГИИ"),
    u("timeline_fallback", "A trajectory toward the opening of TAKE OVER.", 8, "Trajektoor TAKE OVERi avamise suunas.", "Траектория к открытию TAKE OVER."),
    u("developer_add", "Developer controls · Add node", 6, "Arendaja tööriistad · Lisa sõlm", "Инструменты разработчика · Добавить узел"),
    u("admin_note", "Local/admin validation only. This surface is absent unless TAKEOVER_ADMIN_MODE=1.", 6, "Ainult kohalikuks/admin-kontrolliks. Seda pinda ei kuvata ilma TAKEOVER_ADMIN_MODE=1 seadeta.", "Только для локальной/административной проверки. Эта поверхность скрыта без TAKEOVER_ADMIN_MODE=1."),
    u("entity_type", "Entity type", 6, "Olemi tüüp", "Тип сущности"),
    u("name_title", "Name / title", 6, "Nimi / pealkiri", "Имя / название"),
    u("id", "ID", 6, "ID", "ID"),
    u("label", "Label", 6, "Silt", "Метка"),
    u("image_audio_url", "Image or audio URL", 6, "Pildi või heli URL", "URL изображения или аудио"),
    u("add_entity", "Add entity", 6, "Lisa olem", "Добавить сущность"),
)

REGISTRY = {item.key: item for item in UTTERANCES}


def translate(key: str, language: str = "en") -> str:
    """Render a registered key in one of the active M2.0 languages."""
    if language not in LANGUAGES:
        language = "en"
    try:
        return REGISTRY[key].text(language)
    except KeyError as exc:
        raise KeyError(f"Unregistered interface utterance: {key}") from exc
