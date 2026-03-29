import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _sqlite_path = (DATA_DIR / "bot.db").resolve().as_posix()
    DATABASE_URL = f"sqlite+aiosqlite:///{_sqlite_path}"


def get_sync_database_url() -> str:
    """Синхронный URL для Alembic и sync-движка (sqlite вместо sqlite+aiosqlite)."""
    url = make_url(DATABASE_URL)
    if url.drivername == "sqlite+aiosqlite":
        return url.set(drivername="sqlite").render_as_string(hide_password=False)
    return url.render_as_string(hide_password=False)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()


def _parse_admin_user_ids(raw: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        p = part.strip()
        if p.isdigit():
            ids.add(int(p))
    return frozenset(ids)


# Пустой набор = доступ к /admin только по паролю для любого user_id.
ADMIN_USER_IDS = _parse_admin_user_ids(os.getenv("ADMIN_USER_IDS", ""))

RATE_WINDOW_SEC = float(os.getenv("RATE_WINDOW_SEC", "30"))
RATE_MAX_EVENTS = int(os.getenv("RATE_MAX_EVENTS", "25"))
CHECK_SUB_COOLDOWN_SEC = float(os.getenv("CHECK_SUB_COOLDOWN_SEC", "5"))
GET_ACCESS_COOLDOWN_SEC = float(os.getenv("GET_ACCESS_COOLDOWN_SEC", "2"))

# Повторы при блокировке SQLite «database is locked».
DB_RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", "3"))
DB_RETRY_DELAY_SEC = float(os.getenv("DB_RETRY_DELAY_SEC", "0.15"))


def _parse_channel(raw: str) -> tuple[str | int | None, str | None]:
    """(chat_id для get_chat_member, username без @ для t.me или None)."""
    s = raw.strip()
    if not s:
        return None, None
    if s.startswith("-") and s[1:].isdigit():
        return int(s), None
    name = s.lstrip("@")
    return f"@{name}", name


TELEGRAM_CHANNEL_RAW = os.getenv("TELEGRAM_CHANNEL", "").strip()
CHANNEL_CHAT_ID, CHANNEL_USERNAME = _parse_channel(TELEGRAM_CHANNEL_RAW)


def get_channel_subscribe_url() -> str | None:
    override = os.getenv("TELEGRAM_CHANNEL_SUBSCRIBE_URL", "").strip()
    if override:
        return override
    if CHANNEL_USERNAME:
        return f"https://t.me/{CHANNEL_USERNAME}"
    return None
