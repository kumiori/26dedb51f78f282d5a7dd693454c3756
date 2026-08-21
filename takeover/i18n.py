"""Single registered corpus for every interface utterance spoken by TAKE OVER."""

from __future__ import annotations

from dataclasses import dataclass, field


LANGUAGES = {
    "en": "English",
    "et": "Eesti",
    "fi": "Suomi",
    "sv": "Svenska",
}
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
        if language == "en":
            return "CANONICAL"
        return "PROVISIONAL" if language in self.translations else "UNTRANSLATED"


def u(key: str, canonical: str, weight: int = 12, et: str = "", ru: str = "", note: str = "") -> Utterance:
    return Utterance(key, canonical, weight, {"et": et or canonical, "ru": ru or canonical}, note)


# This ordered registry is both the UI copy source and the automatically rendered
# VOICES corpus. Non-English wording is intentionally provisional in M2.0.
UTTERANCES = (
    u("project_name", "TAKE OVER", 100, "TAKE OVER", "TAKE OVER", "Title, imperative, protocol and invitation."),
    u("interactive_progress", "INTERACTIVE IN PROGRESS", 72, "INTERAKTIIVNE, ARENEMAS", "ИНТЕРАКТИВ В ПРОЦЕССЕ"),
    u("start_here", "START HERE", 66, "ALUSTA SIIT", "НАЧНИТЕ ЗДЕСЬ"),
    u("take_wall", "Take over the wall.", 34, "Võta sein üle.", "Захвати стену."),
    u("take_oven", "Take over the oven.", 34, "Võta ahi üle.", "Захвати печь."),
    u("take_sound", "Take over the sound.", 34, "Võta heli üle.", "Захвати звук."),
    u("take_restaurant", "Take over the restaurant.", 34, "Võta restoran üle.", "Захвати ресторан."),
    u("take_night", "Take over the night.", 34, "Võta öö üle.", "Захвати ночь."),
    u("take_web", "Take over the web surface.", 34, "Võta veebiruum üle.", "Захвати веб-пространство."),
    u("take_photography", "TAKE OVER PHOTOGRAPHY.", 34, "VÕTA FOTOGRAAFIA ÜLE.", "ЗАХВАТИ ФОТОГРАФИЮ."),
    u("pass_it_on", "PASS IT ON.", 62, "ANNA EDASI.", "ПЕРЕДАЙ ДАЛЬШЕ."),
    u("invitation", "Bring your voice, your image, your practice.", 52, "Too oma hääl, oma pilt, oma praktika.", "Принесите свой голос, своё изображение, свою практику."),
    u("necessities_title", "WHAT THE PROJECT NEEDS NOW", 48, "MIDA PROJEKT PRAEGU VAJAB", "ЧТО НУЖНО ПРОЕКТУ СЕЙЧАС"),
    u("voices", "VOICES", 46, "HÄÄLED", "ГОЛОСА"),
    u("resources", "RESOURCES", 46, "RESSURSID", "РЕСУРСЫ"),
    u("order_art", "ORDER / ART", 46, "TELLI / KUNST", "ЗАКАЗ / ИСКУССТВО"),
    u("order_art_intro", "A place to encounter works that may move into another context.", 12),
    u("order_art_empty", "No artwork is available to order yet.", 12),
    u("order_art_status", "RC2 · CATALOGUE AND FULFILMENT NOT YET ACTIVE", 10),
    u("resource_action_buy", "BUY", 30, "OSTA", "КУПИТЬ"),
    u("resource_action_buy_explanation", "Acquire a work and carry it into another context.", 12),
    u("resource_action_donate", "DONATE", 30, "ANNETA", "ПОЖЕРТВОВАТЬ"),
    u("resource_action_donate_explanation", "Give resources without claiming ownership or return.", 12),
    u("resource_action_invest", "INVEST", 30, "INVESTEERI", "ИНВЕСТИРОВАТЬ"),
    u("resource_action_invest_explanation", "Commit capacity to what the project may become.", 12),
    u("resource_action_bet", "BET", 30, "PANUSTA", "СДЕЛАТЬ СТАВКУ"),
    u("resource_action_bet_explanation", "Take a position on an uncertain outcome.", 12),
    u("resource_action_play", "PLAY", 30, "MÄNGI", "ИГРАТЬ"),
    u("resource_action_play_explanation", "Enter the process and change its next move.", 12),
    u("resource_action_pending", "RC2 PATHWAY VISIBLE · TRANSACTION NOT YET ACTIVE", 10),
    u("timeline", "TIMELINE", 38, "AJATELG", "ХРОНОЛОГИЯ"),
    u("needs", "NEEDS", 38, "VAJADUSED", "ПОТРЕБНОСТИ"),
    u("process", "PROCESS", 38, "PROTSESS", "ПРОЦЕСС"),
    u("you", "YOU?", 34, "SINA?", "ВЫ?"),
    u("landing_action", "TAKEOVER", 30, "TAKEOVER", "TAKEOVER"),
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
    u("production", "PRODUCTION", 18, "TOOTMINE", "ПРОИЗВОДСТВО"),
    u("to_submit", "TO SUBMIT", 20, "ESITADA", "ПОДАТЬ"),
    u("done", "DONE", 20, "TEHTUD", "ГОТОВО"),
    u("not_yet_activated", "NOT YET ACTIVATED", 20, "POLE VEEL AKTIVEERITUD", "ЕЩЁ НЕ АКТИВИРОВАНО"),
    u("open_node", "Open the central node.", 15, "Ava keskne sõlm.", "Откройте центральный узел."),
    u("suggested_listening", "SUGGESTED LISTENING", 18, "SOOVITATAV KUULAMINE", "РЕКОМЕНДУЕМ ПОСЛУШАТЬ"),
    u("listening_work", "ARVO PÄRT · TABULA RASA", 16, "ARVO PÄRT · TABULA RASA", "АРВО ПЯРТ · TABULA RASA"),
    u("need_stage_state", "Need → stage → state. This is not a resources directory.", 12, "Vajadus → etapp → olek. See ei ole ressursside kataloog.", "Потребность → этап → состояние. Это не каталог ресурсов."),
    u("improve_translation", "IMPROVE THIS TRANSLATION", 12, "PARANDA SEDA TÕLGET", "УЛУЧШИТЬ ЭТОТ ПЕРЕВОД"),
    u("proposals_closed", "Proposals are not open yet.", 10, "Ettepanekud ei ole veel avatud.", "Предложения пока не принимаются."),
    u("record_voice", "RECORD YOUR VOICE", 30, "SALVESTA OMA HÄÄL", "ЗАПИШИТЕ СВОЙ ГОЛОС"),
    u("record_voice_intro", "Use the microphone beside a principal text to record your voice.", 12, "Kasuta põhiteksti kõrval olevat mikrofoni oma hääle salvestamiseks.", "Используйте микрофон рядом с основным текстом, чтобы записать свой голос."),
    u("add_translation", "ADD TRANSLATION", 18, "LISA TÕLGE", "ДОБАВИТЬ ПЕРЕВОД"),
    u("voice_contribution_intro", "Add a voice recording or propose a translation beside any fragment.", 12, "Lisa katkendi kõrvale häälsalvestus või paku tõlge.", "Добавьте к фрагменту запись голоса или предложите перевод."),
    u("translation_language", "TRANSLATION LANGUAGE", 10, "TÕLKE KEEL", "ЯЗЫК ПЕРЕВОДА"),
    u("original", "ORIGINAL", 10, "ORIGINAAL", "ОРИГИНАЛ"),
    u("current_translation", "CURRENT TRANSLATION", 10, "PRAEGUNE TÕLGE", "ТЕКУЩИЙ ПЕРЕВОД"),
    u("your_version", "YOUR VERSION", 10, "SINU VERSIOON", "ВАША ВЕРСИЯ"),
    u("propose_translation", "PROPOSE TRANSLATION", 10, "PAKU TÕLGE", "ПРЕДЛОЖИТЬ ПЕРЕВОД"),
    u("translation_required", "Write a translation before proposing it.", 8, "Kirjuta tõlge enne selle esitamist.", "Напишите перевод перед отправкой."),
    u("translation_saved", "Proposal saved for review. The registered translation is unchanged.", 8, "Ettepanek salvestati ülevaatamiseks. Registris olev tõlge ei muutunud.", "Предложение сохранено для проверки. Зарегистрированный перевод не изменён."),
    u("languages_to_read", "WHAT LANGUAGES DO YOU WANT TO READ?", 12, "MILLISTES KEELTES SOOVID LUGEDA?", "НА КАКИХ ЯЗЫКАХ ВЫ ХОТИТЕ ЧИТАТЬ?"),
    u("language_status", "LANGUAGE STATUS", 12, "KEELE OLEK", "СТАТУС ЯЗЫКА"),
    u("voices_statistics", "VOICES STATISTICS", 18, "HÄÄLTE STATISTIKA", "СТАТИСТИКА ГОЛОСОВ"),
    u("recordings_complete", "RECORDINGS COMPLETE", 10, "SALVESTUSED VALMIS", "ЗАПИСИ ЗАВЕРШЕНЫ"),
    u("translation_proposals", "TRANSLATION PROPOSALS", 10, "TÕLKEETTEPANEKUD", "ПРЕДЛОЖЕНИЯ ПЕРЕВОДА"),
    u("corpus_status", "CORPUS STATUS", 10, "KORPUSE OLEK", "СТАТУС КОРПУСА"),
    u("canonical", "CANONICAL", 8, "KANOONILINE", "КАНОНИЧЕСКИЙ"),
    u("provisional", "PROVISIONAL", 8, "ESIALGNE", "ПРЕДВАРИТЕЛЬНЫЙ"),
    u("untranslated", "UNTRANSLATED", 8, "TÕLKIMATA", "НЕ ПЕРЕВЕДЕНО"),
    u("resources_intro", "Resources change what becomes possible. Money is the first visible dimension; intention, committed funds and spending remain distinct.", 12, "Ressursid muudavad seda, mis saab võimalikuks. Raha on esimene nähtav mõõde; kavatsus, siduv rahastus ja kulutused jäävad eraldi.", "Ресурсы меняют то, что становится возможным. Деньги — первое видимое измерение; намерение, обязательства и расходы остаются раздельными."),
    u("observed_intention", "OBSERVED INTENTION · NOT AVAILABLE FUNDS", 10, "TÄHELDATUD KAVATSUS · MITTE KÄTTESAADAV RAHA", "ЗАФИКСИРОВАННОЕ НАМЕРЕНИЕ · НЕ ДОСТУПНЫЕ СРЕДСТВА"),
    u("datasets", "RELEVANT DATASETS", 12, "ASJAKOHASED ANDMESTIKUD", "РЕЛЕВАНТНЫЕ НАБОРЫ ДАННЫХ"),
    u("allocated_dataset", "BUCKET OF DOUGH", 10, "ERALDATUD RESSURSID", "ВЫДЕЛЕННЫЕ РЕСУРСЫ"),
    u("intentions_dataset", "INVESTMENT INTENTIONS", 10, "INVESTEERIMISKAVATSUSED", "ИНВЕСТИЦИОННЫЕ НАМЕРЕНИЯ"),
    u("trajectory_dataset", "TRAJECTORY EVENTS USED", 10, "KASUTATUD TRAJEKTOORI SÜNDMUSED", "ИСПОЛЬЗОВАННЫЕ СОБЫТИЯ ТРАЕКТОРИИ"),
    u("time_mapping", "TENTATIVE LINEAR ↔ NONLINEAR TIME MAP", 12, "ESIALGNE LINEAARSE ↔ MITTELINEAARSE AJA KAART", "ПРЕДВАРИТЕЛЬНАЯ КАРТА ЛИНЕЙНОГО ↔ НЕЛИНЕЙНОГО ВРЕМЕНИ"),
    u("time_mapping_note", "Let u be calendar-linear time and q the qualitative trajectory coordinate. The current tentative map is the monotone piecewise-linear interpolation through event pairs (uᵢ,qᵢ); Δᵢ=qᵢ−uᵢ shows temporal distortion. This comparison does not rewrite the plan.", 10, "Olgu u kalendriline aeg ja q kvalitatiivne trajektoorikoordinaat. Praegune esialgne kaart on monotoonne tükiti lineaarne interpolatsioon sündmuspaaride (uᵢ,qᵢ) kaudu; Δᵢ=qᵢ−uᵢ näitab ajalist moonutust. Võrdlus ei kirjuta plaani ümber.", "Пусть u — календарно-линейное время, а q — качественная координата траектории. Текущая предварительная карта — монотонная кусочно-линейная интерполяция через пары событий (uᵢ,qᵢ); Δᵢ=qᵢ−uᵢ показывает временное искажение. Сравнение не переписывает план."),
    u("voice_recording", "VOICE RECORDING", 18, "HÄÄLESALVESTUS", "ЗАПИСЬ ГОЛОСА"),
    u("recording_prompt", "Speak in your own language. Your recording stays in this browser session unless you explicitly share it later.", 12, "Räägi oma keeles. Sinu salvestus jääb sellesse brauseriseanssi, kuni otsustad selle hiljem selgesõnaliselt jagada.", "Говорите на своём языке. Запись останется в этой сессии браузера, пока вы явно не решите поделиться ею позже."),
    u("start_recording", "Start recording", 10, "Alusta salvestamist", "Начать запись"),
    u("recording_ready", "Your voice is ready to review. It has not been shared or added to the registry.", 10, "Sinu hääl on ülekuulamiseks valmis. Seda ei ole jagatud ega registrisse lisatud.", "Ваш голос готов к прослушиванию. Запись не опубликована и не добавлена в реестр."),
    u("voices_intro", "Every registered utterance currently spoken by TAKE OVER, arranged by weight.", 12, "Kõik TAKE OVERi registreeritud väljendid, järjestatud kaalu järgi.", "Все зарегистрированные высказывания TAKE OVER, расположенные по весу."),
    u("source_key", "SOURCE KEY", 8, "LÄHTEVÕTI", "КЛЮЧ ИСТОЧНИКА"),
    u("weight", "WEIGHT", 8, "KAAL", "ВЕС"),
    u("status", "STATUS", 8, "OLEK", "СТАТУС"),
    u("need", "NEED", 8, "VAJADUS", "ПОТРЕБНОСТЬ"),
    u("state", "STATE", 8, "OLEK", "СОСТОЯНИЕ"),
    u("nodes", "NODES", 8, "SÕLMED", "УЗЛЫ"),
    u("connections", "CONNECTIONS", 8, "ÜHENDUSED", "СВЯЗИ"),
    u("connections_node", "(1+CONNECTIONS)/NODES", 8, "(1+ÜHENDUSED)/SÕLMED", "(1+СВЯЗИ)/УЗЛЫ"),
    u("project_navigation", "PROJECT NAVIGATION", 8, "PROJEKTI NAVIGATSIOON", "НАВИГАЦИЯ ПРОЕКТА"),
    u("registry", "REGISTRY", 8, "REGISTER", "РЕЕСТР"),
    u("development_interface", "DEVELOPMENT INTERFACE", 8, "ARENDUSLIIDES", "ИНТЕРФЕЙС РАЗРАБОТКИ"),
    u("event_log", "EVENT LOG", 12, "SÜNDMUSTE LOGI", "ЖУРНАЛ СОБЫТИЙ"),
    u("event_session_started", "SESSION STARTED", 6, "SEANSS ALGAS", "СЕССИЯ НАЧАТА"),
    u("event_navigate", "NAVIGATED", 6, "LIIGUTI", "ПЕРЕХОД"),
    u("event_language_changed", "LANGUAGE CHANGED", 6, "KEEL MUUDETUD", "ЯЗЫК ИЗМЕНЁН"),
    u("event_reading_languages", "READING LANGUAGES CHANGED", 6, "LUGEMISKEELED MUUDETUD", "ЯЗЫКИ ЧТЕНИЯ ИЗМЕНЕНЫ"),
    u("event_access_opened", "ACCESS DOOR OPENED", 6, "SISSEPÄÄSU UKS AVATI", "ВХОДНАЯ ДВЕРЬ ОТКРЫТА"),
    u("event_node_opened", "NODE OPENED", 6, "SÕLM AVATI", "УЗЕЛ ОТКРЫТ"),
    u("event_connection_opened", "CONNECTION OPENED", 6, "ÜHENDUS AVATI", "СВЯЗЬ ОТКРЫТА"),
    u("event_state_opened", "STATE OF THE ART OPENED", 6, "STATE OF THE ART AVATI", "STATE OF THE ART ОТКРЫТО"),
    u("event_recording_opened", "VOICE RECORDER OPENED", 6, "HÄÄLESALVESTI AVATI", "ДИКТОФОН ОТКРЫТ"),
    u("event_recording_ready", "VOICE RECORDING READY", 6, "HÄÄLESALVESTUS VALMIS", "ЗАПИСЬ ГОЛОСА ГОТОВА"),
    u("event_translation_opened", "TRANSLATION PROPOSAL OPENED", 6, "TÕLKEETTEPANEK AVATI", "ПРЕДЛОЖЕНИЕ ПЕРЕВОДА ОТКРЫТО"),
    u("event_translation_saved", "TRANSLATION PROPOSAL SAVED", 6, "TÕLKEETTEPANEK SALVESTATI", "ПРЕДЛОЖЕНИЕ ПЕРЕВОДА СОХРАНЕНО"),
    u("event_entity_added", "ENTITY ADDED", 6, "OLEM LISATI", "СУЩНОСТЬ ДОБАВЛЕНА"),
    u("event_invitation_activation", "INVITATION ACTIVATION", 12, "KUTSE AKTIVEERIMINE", "АКТИВАЦИЯ ПРИГЛАШЕНИЯ"),
    u("application_window", "APPLICATION WINDOW", 24, "TAOTLUSVOOR", "ОКНО ПОДАЧИ ЗАЯВКИ"),
    u("before_submission", "D0 · BEFORE SUBMISSION", 12, "D0 · ENNE ESITAMIST", "D0 · ДО ПОДАЧИ"),
    u("current_state", "CURRENT STATE", 12, "PRAEGUNE OLEK", "ТЕКУЩЕЕ СОСТОЯНИЕ"),
    u("participants", "PARTICIPANTS", 8, "OSALEJAD", "УЧАСТНИКИ"),
    u("production_budget", "PRODUCTION BUDGET", 8, "TOOTMISEELARVE", "ПРОИЗВОДСТВЕННЫЙ БЮДЖЕТ"),
    u("jury", "JURY", 8, "ŽÜRII", "ЖЮРИ"),
    u("selection", "SELECTION", 8, "VALIK", "ОТБОР"),
    u("response_time", "RESPONSE TIME", 8, "VASTAMISE AEG", "СРОК ОТВЕТА"),
    u("exhibition_feasibility", "EXHIBITION / FEASIBILITY", 8, "NÄITUS / TEOSTATAVUS", "ВЫСТАВКА / ОСУЩЕСТВИМОСТЬ"),
    u("future_contributors", "FUTURE CONTRIBUTORS", 8, "TULEVASED PANUSTAJAD", "БУДУЩИЕ УЧАСТНИКИ"),
    u("next_state", "NEXT STATE", 8, "JÄRGMINE OLEK", "СЛЕДУЮЩЕЕ СОСТОЯНИЕ"),
    u("unknown", "UNKNOWN", 12, "TEADMATA", "НЕИЗВЕСТНО"),
    u("none_secured", "NONE SECURED", 12, "POLE TAGATUD", "НЕ ОБЕСПЕЧЕН"),
    u("conditional", "CONDITIONAL", 12, "TINGIMUSLIK", "УСЛОВНО"),
    u("unresolved", "UNRESOLVED", 12, "LAHENDAMATA", "НЕ ОПРЕДЕЛЕНО"),
    u("uncertainty_statement", "We do not know whether this will happen. That is part of the current state.", 22, "Me ei tea, kas see juhtub. See on osa praegusest olekust.", "Мы не знаем, произойдёт ли это. Это часть текущего состояния."),
    u("open_application_file", "OPEN APPLICATION FILE", 28, "AVA TAOTLUSE FAIL", "ОТКРЫТЬ ФАЙЛ ЗАЯВКИ"),
    u("state_of_art", "STATE OF THE ART", 28, "STATE OF THE ART", "STATE OF THE ART"),
    u("state_of_art_intro", "Who is here, what they bring, how they connect.", 18, "Kes on siin, mida nad toovad, kuidas nad ühenduvad.", "Кто здесь, что они привносят, как они связаны."),
    u("connectivity", "CONNECTIVITY", 10, "ÜHENDATUS", "СВЯЗНОСТЬ"),
    u("contributions_active", "CONTRIBUTIONS ACTIVE", 10, "AKTIIVSED PANUSED", "АКТИВНЫЕ ВКЛАДЫ"),
    u("active_relations", "ACTIVE RELATIONS", 10, "AKTIIVSED SUHTED", "АКТИВНЫЕ СВЯЗИ"),
    u("active_people", "ACTIVE PEOPLE", 10, "AKTIIVSED INIMESED", "АКТИВНЫЕ ЛЮДИ"),
    u("latent_known", "LATENT KNOWN", 10, "LATENTNE TEATUD", "ЛАТЕНТНО ИЗВЕСТНЫЙ"),
    u("latent_private", "LATENT PRIVATE", 10, "LATENTNE PRIVAATNE", "ЛАТЕНТНО ПРИВАТНЫЙ"),
    u("additions_opening_next", "+ ADD NODE · + ADD CONNECTION / OPENING NEXT", 8, "+ LISA SÕLM · + LISA ÜHENDUS / AVANEB JÄRGMISENA", "+ ДОБАВИТЬ УЗЕЛ · + ДОБАВИТЬ СВЯЗЬ / ОТКРОЕТСЯ ДАЛЕЕ"),
    u("connection", "CONNECTION", 12, "ÜHENDUS", "СВЯЗЬ"),
    u("contribution", "CONTRIBUTION", 12, "PANUS", "ВКЛАД"),
    u("active_contribution", "ACTIVE CONTRIBUTION", 12, "AKTIIVNE PANUS", "АКТИВНЫЙ ВКЛАД"),
    u("active_relation", "ACTIVE RELATION", 12, "AKTIIVNE SUHE", "АКТИВНАЯ СВЯЗЬ"),
    u("network_state", "NETWORK STATE", 12, "VÕRGUSTIKU OLEK", "СОСТОЯНИЕ СЕТИ"),
    u("connection_explainer", "This connection records how a contribution currently enters the network.", 12, "See ühendus salvestab, kuidas panus praegu võrgustikku siseneb.", "Эта связь фиксирует, как вклад сейчас входит в сеть."),
    u("relation_explainer", "This edge records an explicit relationship already present in the active social field.", 12, "See serv salvestab aktiivses sotsiaalses väljas juba olemasoleva selgesõnalise suhte.", "Это ребро фиксирует явную связь, уже существующую в активном социальном поле."),
    u("node_question", "Who / what is here?", 10, "Kes / mis on siin?", "Кто / что здесь?"),
    u("connection_question", "How are they related?", 10, "Kuidas nad on seotud?", "Как они связаны?"),
    u("contribution_question", "What flows through the relationship?", 10, "Mis voolab läbi suhte?", "Что проходит через это отношение?"),
    u("state_question", "What does the network look like now?", 10, "Milline on võrgustik praegu?", "Как сейчас выглядит сеть?"),
    u("access_door", "ACCESS DOOR", 10, "SISSEPÄÄSU UKS", "ВХОДНАЯ ДВЕРЬ"),
    u("project_formation", "A PROJECT IN FORMATION", 10, "KUJUNEV PROJEKT", "ПРОЕКТ В СТАНОВЛЕНИИ"),
    u("door_intro", "The door opens onto what exists now. Other routes remain visible, but unopened.", 10, "Uks avaneb sellele, mis praegu olemas on. Teised teed jäävad nähtavaks, kuid avamata.", "Дверь открывается в то, что существует сейчас. Другие пути видны, но пока закрыты."),
    u("follow_trajectory", "FOLLOW THE TRAJECTORY", 10, "JÄRGI TRAJEKTOORI", "СЛЕДОВАТЬ ТРАЕКТОРИИ"),
    u("open_timeline", "Open timeline →", 8, "Ava ajatelg →", "Открыть хронологию →"),
    u("see_needed", "SEE WHAT IS NEEDED", 10, "VAATA, MIDA ON VAJA", "ПОСМОТРЕТЬ, ЧТО НУЖНО"),
    u("open_necessities", "Open needs →", 8, "Ava vajadused →", "Открыть потребности →"),
    u("contribute_unopened", "CONTRIBUTE — UNOPENED", 8, "PANUSTA — AVAMATA", "ВНЕСТИ ВКЛАД — ЗАКРЫТО"),
    u("door_inactive", "This door is not active yet", 8, "See uks ei ole veel aktiivne", "Эта дверь пока не активна"),
    u("explore_dormant", "EXPLORE — DORMANT", 8, "AVASTA — UINUV", "ИССЛЕДОВАТЬ — НЕАКТИВНО"),
    u("node", "NODE", 8, "SÕLM", "УЗЕЛ"),
    u("stage", "STAGE", 8, "ETAPP", "ЭТАП"),
    u("phase", "PHASE", 8, "FAAS", "ФАЗА"),
    u("registry_id", "REGISTRY ID", 8, "REGISTRI ID", "ID РЕЕСТРА"),
    u("no_necessities", "No needs have been activated yet.", 8, "Ühtegi vajadust ei ole veel aktiveeritud.", "Ни одна потребность пока не активирована."),
    u("timeline_source", "READ-ONLY M2 VIEW · YAML REMAINS THE TIMELINE SOURCE", 8, "M2 AINULT LUGEMISEKS · YAML JÄÄB AJATELJE ALLIKAKS", "M2 ТОЛЬКО ДЛЯ ЧТЕНИЯ · YAML ОСТАЁТСЯ ИСТОЧНИКОМ ХРОНОЛОГИИ"),
    u("timeline_proposition", "Application formation moving toward an unknown trajectory.", 12, "Taotluse kujunemine liigub tundmatu trajektoori poole.", "Формирование заявки движется к неизвестной траектории."),
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


def language_term(code: str) -> str:
    """Return the compact public label used by language controls."""
    return f"{code.upper()} · {LANGUAGES[code]}"


def language_status_metrics() -> dict[str, dict[str, int]]:
    """Derive corpus-wide status counts; never maintain a duplicate tally."""
    output: dict[str, dict[str, int]] = {}
    for code in VOICE_LANGUAGES:
        counts = {"CANONICAL": 0, "PROVISIONAL": 0, "UNTRANSLATED": 0}
        for utterance in UTTERANCES:
            counts[utterance.status(code)] += 1
        output[code] = counts
    return output


def record_translation_proposal(state: dict, utterance_key: str, language: str, proposal: str) -> dict[str, str]:
    """Append a review-only proposal without mutating the registered corpus."""
    clean = proposal.strip()
    if not clean:
        raise ValueError("A translation proposal cannot be empty.")
    item = {"utterance_key": utterance_key, "language": language, "proposal": clean}
    state.setdefault("takeover_translation_proposals", []).append(item)
    return item
