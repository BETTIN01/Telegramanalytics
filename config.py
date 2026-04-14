import os
from pathlib import Path
from dotenv import load_dotenv, set_key

ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(ENV_FILE)

def get_token() -> str:
    return os.getenv("BOT_TOKEN", "")

def set_token(token: str):
    os.environ["BOT_TOKEN"] = token
    set_key(str(ENV_FILE), "BOT_TOKEN", token)

PORT          = int(os.getenv("PORT", 5000))
DATABASE_PATH = str(Path(__file__).parent / "database" / "analytics.db")
PAGE_SIZE     = 50