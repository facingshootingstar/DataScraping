"""
LeadHarvester Pro - Stealth Browser Module
============================================
Anti-detection browser wrapper using Playwright.
Implements stealth techniques to avoid bot detection:
- Random user agent rotation
- Realistic viewport & locale
- WebGL/Canvas fingerprint randomization
- Navigator property overrides
- Human-like mouse movements & delays
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from config import BROWSER, RATE_LIMIT, PROXY_MANAGER, get_random_user_agent


# JavaScript to inject for stealth
STEALTH_JS = """
() => {
    // Override navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

    // Override navigator.plugins (make it look populated)
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });

    // Override navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'vi'],
    });

    // Override permissions query
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);

    // Override chrome runtime
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {},
    };

    // Prevent iframe detection
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
        get: function() {
            return window;
        }
    });

    // Override toString for modified functions
    const nativeToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === window.navigator.permissions.query) {
            return 'function query() { [native code] }';
        }
        return nativeToString.call(this);
    };
}
"""


class StealthBrowser:
    """
    Anti-detection browser wrapper with stealth mode.

    Usage:
        async with StealthBrowser() as browser:
            page = await browser.new_page()
            await page.goto("https://example.com")
            content = await page.content()
    """

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> StealthBrowser:
        await self.launch()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def launch(self) -> None:
        """Launch stealth browser."""
        self._playwright = await async_playwright().start()

        launch_args = {
            "headless": BROWSER.headless,
            "slow_mo": BROWSER.slow_mo,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--lang=en-US,en",
            ],
        }

        # Add proxy if available
        proxy = PROXY_MANAGER.get_next()
        if proxy:
            launch_args["proxy"] = proxy
            logger.info(f"Using proxy: {proxy['server']}")

        self._browser = await self._playwright.chromium.launch(**launch_args)

        # Create context with stealth settings
        user_agent = get_random_user_agent()
        self._context = await self._browser.new_context(
            user_agent=user_agent,
            viewport={
                "width": BROWSER.viewport_width + random.randint(-100, 100),
                "height": BROWSER.viewport_height + random.randint(-50, 50),
            },
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            permissions=["geolocation"],
            color_scheme="light",
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
        )

        # Inject stealth script on every page
        await self._context.add_init_script(STEALTH_JS)

        logger.info(f"Stealth browser launched (headless={BROWSER.headless}, ua={user_agent[:50]}...)")

    async def new_page(self) -> Page:
        """Create a new stealth page."""
        if not self._context:
            raise RuntimeError("Browser not launched. Call launch() or use 'async with'.")
        page = await self._context.new_page()
        page.set_default_timeout(BROWSER.timeout)
        return page

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Stealth browser closed")

    # ── Human-like Actions ───────────────────────────────────

    @staticmethod
    async def human_delay(min_ms: int | None = None, max_ms: int | None = None) -> None:
        """Wait a human-like random delay."""
        lo = min_ms or RATE_LIMIT.min_delay_ms
        hi = max_ms or RATE_LIMIT.max_delay_ms
        delay = random.uniform(lo, hi) / 1000
        await asyncio.sleep(delay)

    @staticmethod
    async def human_type(page: Page, selector: str, text: str) -> None:
        """Type text with human-like speed and occasional pauses."""
        await page.click(selector)
        await asyncio.sleep(random.uniform(0.1, 0.3))

        for char in text:
            await page.keyboard.type(char, delay=random.uniform(50, 150))
            # Occasional pause (simulates thinking)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.3, 0.8))

    @staticmethod
    async def human_scroll(page: Page, times: int = 3, direction: str = "down") -> None:
        """Scroll page with human-like behavior."""
        for i in range(times):
            delta = random.randint(300, 700)
            if direction == "up":
                delta = -delta
            await page.mouse.wheel(0, delta)
            await asyncio.sleep(random.uniform(0.5, 1.5))

    @staticmethod
    async def random_mouse_move(page: Page) -> None:
        """Move mouse to random position (avoid detection)."""
        x = random.randint(100, 1200)
        y = random.randint(100, 600)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.3))

    @staticmethod
    async def safe_goto(page: Page, url: str, wait_until: str = "domcontentloaded") -> bool:
        """Navigate with error handling and retry logic."""
        for attempt in range(RATE_LIMIT.max_retries):
            try:
                await page.goto(url, wait_until=wait_until, timeout=BROWSER.timeout)
                await asyncio.sleep(RATE_LIMIT.page_load_wait / 1000)
                return True
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < RATE_LIMIT.max_retries - 1:
                    backoff = RATE_LIMIT.retry_backoff ** attempt
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed to navigate to {url} after {RATE_LIMIT.max_retries} attempts")
                    return False
