import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = env("OPENAI_API_KEY")
OPENAI_MODEL = env("OPENAI_MODEL", "gpt-5.5")
OPENAI_IMAGE_MODEL = env("OPENAI_IMAGE_MODEL", "gpt-image-2.5-flare")
BOT_NAME = env("BOT_NAME", "CYGAD AI")
DEFAULT_LANGUAGE = env("DEFAULT_LANGUAGE", "en").lower()
DATABASE_PATH = Path(env("DATABASE_PATH", str(ROOT / "data" / "cygad.sqlite3")))
ENABLE_WEB_SEARCH = env("ENABLE_WEB_SEARCH", "true").lower() in {"1", "true", "yes", "on"}
ADMIN_IDS = {
    int(item.strip())
    for item in env("ADMIN_IDS").split(",")
    if item.strip().isdigit()
}
