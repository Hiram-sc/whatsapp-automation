import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

FRONT_DIR = BASE_DIR / "front"
STATIC_DIR = FRONT_DIR / "static"
INDEX_FILE = FRONT_DIR / "index.html"

UPLOAD_DIR = Path(
    os.getenv("WHATSAPP_UPLOAD_DIR", str(BASE_DIR / "uploads"))
).expanduser().resolve()

SESSION_DIR = Path(
    os.getenv("WHATSAPP_SESSION_DIR", str(BASE_DIR / "session"))
).expanduser().resolve()

WHATSAPP_URL = "https://web.whatsapp.com"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.0.0 Safari/537.36"
)

PLAYWRIGHT_CHANNEL = os.getenv("PLAYWRIGHT_CHANNEL", "chromium").strip() or None
PLAYWRIGHT_HEADLESS = os.getenv(
    "PLAYWRIGHT_HEADLESS", "true"
).strip().lower() not in {"0", "false", "no", "off"}

NAVIGATION_TIMEOUT_MS = 60_000
ELEMENT_TIMEOUT_MS = 15_000
QR_WAIT_TIMEOUT_MS = 15_000

INTERVALO_MINIMO_MINUTOS = 1
INTERVALO_MAXIMO_MINUTOS = 1440

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_NOME_GRUPO = 120

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"
