"""
LeadHarvester Pro - Configuration Management
==============================================
Centralized config with environment variable support,
proxy rotation, and sensible production defaults.
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("true", "1", "yes")


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


# ── Paths ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
RAW_DIR = Path(_env("RAW_DIR", str(BASE_DIR / "data" / "raw")))
OUTPUT_DIR = Path(_env("OUTPUT_DIR", str(BASE_DIR / "data" / "processed")))
LOG_DIR = BASE_DIR / "logs"
SCREENSHOT_DIR = BASE_DIR / "screenshots"

for _dir in (RAW_DIR, OUTPUT_DIR, LOG_DIR, SCREENSHOT_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ── API Keys ─────────────────────────────────────────────────
OPENAI_API_KEY: str = _env("OPENAI_API_KEY")


# ── Browser Settings ─────────────────────────────────────────
@dataclass(frozen=True)
class BrowserConfig:
    headless: bool = _env_bool("HEADLESS", True)
    slow_mo: int = _env_int("SLOW_MO", 0)
    timeout: int = 60_000  # 60 seconds
    viewport_width: int = 1920
    viewport_height: int = 1080


BROWSER = BrowserConfig()


# ── Rate Limiting ────────────────────────────────────────────
@dataclass(frozen=True)
class RateLimitConfig:
    min_delay_ms: int = _env_int("MIN_DELAY", 2000)
    max_delay_ms: int = _env_int("MAX_DELAY", 5000)
    page_load_wait: int = 3000  # ms to wait after page loads
    scroll_delay: int = 1500   # ms between scroll actions
    max_retries: int = 3
    retry_backoff: float = 2.0

    @property
    def random_delay(self) -> float:
        """Return a random delay in seconds."""
        return random.uniform(self.min_delay_ms, self.max_delay_ms) / 1000


RATE_LIMIT = RateLimitConfig()


# ── Proxy Settings ───────────────────────────────────────────
class ProxyManager:
    """Manage and rotate proxies."""

    def __init__(self) -> None:
        self._proxies: list[str] = []
        self._index = 0

        # Load from single URL
        single = _env("PROXY_URL")
        if single:
            self._proxies.append(single)

        # Load from file
        proxy_file = _env("PROXY_LIST_FILE")
        if proxy_file and Path(proxy_file).exists():
            with open(proxy_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self._proxies.append(line)

    @property
    def available(self) -> bool:
        return len(self._proxies) > 0

    def get_next(self) -> dict | None:
        """Get next proxy in rotation. Returns Playwright proxy dict."""
        if not self._proxies:
            return None
        proxy_url = self._proxies[self._index % len(self._proxies)]
        self._index += 1
        return {"server": proxy_url}

    def get_random(self) -> dict | None:
        if not self._proxies:
            return None
        return {"server": random.choice(self._proxies)}


PROXY_MANAGER = ProxyManager()


# ── Scraping Defaults ────────────────────────────────────────
MAX_RESULTS: int = _env_int("MAX_RESULTS", 100)
LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")


# ── Stealth User Agents ─────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


# ── Validation ───────────────────────────────────────────────
def validate_config() -> list[str]:
    warnings: list[str] = []
    if not OPENAI_API_KEY:
        warnings.append("OPENAI_API_KEY not set - AI enrichment will be unavailable.")
    if not PROXY_MANAGER.available:
        warnings.append("No proxies configured - using direct connection (higher detection risk).")
    return warnings
