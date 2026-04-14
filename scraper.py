"""
LeadHarvester Pro - Google Maps Scraper Engine
================================================
Production-grade scraper for extracting business leads
from Google Maps. Uses Playwright with stealth mode,
human-like behavior, and intelligent data extraction.

Extracts per business:
- Business name, category, address
- Phone number, website URL
- Rating, review count
- Business hours
- Google Maps URL
- Plus Code / Coordinates
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

from playwright.async_api import Page, ElementHandle
from loguru import logger

from config import RATE_LIMIT, MAX_RESULTS, RAW_DIR, SCREENSHOT_DIR
from utils.stealth import StealthBrowser
from utils.helpers import (
    clean_text,
    clean_phone,
    clean_url,
    extract_rating,
    extract_review_count,
    generate_filename,
    generate_hash,
    save_json,
)


# ── Data Model ───────────────────────────────────────────────

@dataclass
class BusinessLead:
    """Structured business lead data."""
    name: str = ""
    category: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: float | None = None
    review_count: int | None = None
    hours: dict[str, str] = field(default_factory=dict)
    google_maps_url: str = ""
    latitude: float | None = None
    longitude: float | None = None
    plus_code: str = ""
    price_level: str = ""
    # Metadata
    scraped_at: str = ""
    search_query: str = ""
    search_location: str = ""
    _hash: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("_hash", None)
        return d


# ── Scraper Engine ───────────────────────────────────────────

class GoogleMapsScraper:
    """
    Production Google Maps lead scraper.

    Usage:
        scraper = GoogleMapsScraper()
        leads = await scraper.scrape(
            keyword="restaurants",
            location="New York, NY",
            max_results=50,
        )
    """

    MAPS_URL = "https://www.google.com/maps"
    SEARCH_URL = "https://www.google.com/maps/search/{query}"

    def __init__(self) -> None:
        self._browser: StealthBrowser | None = None
        self._page: Page | None = None
        self._leads: list[BusinessLead] = []
        self._seen_hashes: set[str] = set()

    async def scrape(
        self,
        keyword: str,
        location: str,
        max_results: int | None = None,
        save_raw: bool = True,
        screenshot: bool = False,
    ) -> list[dict]:
        """
        Scrape Google Maps for business leads.

        Args:
            keyword: Business type to search (e.g., "plumber", "restaurant")
            location: Geographic location (e.g., "Austin, TX")
            max_results: Maximum number of results to scrape
            save_raw: Save raw JSON data
            screenshot: Take screenshots during scraping

        Returns:
            List of business lead dictionaries
        """
        max_results = max_results or MAX_RESULTS
        query = f"{keyword} in {location}"
        logger.info(f"Starting scrape: '{query}' (max {max_results} results)")

        self._leads = []
        self._seen_hashes = set()

        async with StealthBrowser() as browser:
            self._browser = browser
            self._page = await browser.new_page()

            try:
                # Step 1: Navigate to Google Maps search
                search_url = self.SEARCH_URL.format(query=query.replace(" ", "+"))
                logger.info(f"Navigating to: {search_url}")

                success = await StealthBrowser.safe_goto(self._page, search_url)
                if not success:
                    logger.error("Failed to load Google Maps")
                    return []

                # Wait for results to load
                await self._wait_for_results()

                if screenshot:
                    await self._take_screenshot("search_results")

                # Step 2: Handle consent dialog if present
                await self._handle_consent()

                # Step 3: Scroll through results list
                await self._scroll_results_list(max_results)

                # Step 4: Extract listing URLs
                listing_elements = await self._get_listing_elements()
                logger.info(f"Found {len(listing_elements)} listing elements")

                # Step 5: Extract data from each listing
                count = 0
                for i, element in enumerate(listing_elements):
                    if count >= max_results:
                        break

                    try:
                        lead = await self._extract_listing_data(element, i)
                        if lead and lead.name:
                            # Deduplication
                            hash_key = generate_hash(f"{lead.name}{lead.address}")
                            if hash_key not in self._seen_hashes:
                                lead._hash = hash_key
                                lead.search_query = keyword
                                lead.search_location = location
                                lead.scraped_at = datetime.now().isoformat()
                                self._leads.append(lead)
                                self._seen_hashes.add(hash_key)
                                count += 1
                                logger.info(f"  [{count}/{max_results}] {lead.name}")

                        # Human-like delay between extractions
                        await StealthBrowser.human_delay(800, 2000)

                    except Exception as e:
                        logger.warning(f"Failed to extract listing {i}: {e}")
                        continue

                if screenshot:
                    await self._take_screenshot("final_state")

            except Exception as e:
                logger.error(f"Scraping error: {e}")
                if screenshot:
                    await self._take_screenshot("error_state")

        # Save raw data
        results = [lead.to_dict() for lead in self._leads]
        if save_raw and results:
            raw_file = RAW_DIR / generate_filename(keyword, location, "json")
            save_json(results, raw_file)
            logger.info(f"Raw data saved: {raw_file}")

        logger.info(f"Scraping complete: {len(results)} leads extracted")
        return results

    # ── Private Methods ──────────────────────────────────────

    async def _wait_for_results(self) -> None:
        """Wait for the results panel to load."""
        try:
            # Wait for the results feed
            await self._page.wait_for_selector(
                'div[role="feed"], div[role="main"]',
                timeout=15_000,
            )
            await asyncio.sleep(2)
        except Exception:
            logger.warning("Results panel not found, trying alternative selectors...")
            await asyncio.sleep(3)

    async def _handle_consent(self) -> None:
        """Handle Google consent / cookie dialogs."""
        try:
            # Look for common consent buttons
            consent_selectors = [
                'button:has-text("Accept all")',
                'button:has-text("Accept")',
                'button:has-text("I agree")',
                'button:has-text("Reject all")',
                'form[action*="consent"] button',
            ]
            for selector in consent_selectors:
                btn = await self._page.query_selector(selector)
                if btn:
                    await btn.click()
                    logger.debug("Consent dialog handled")
                    await asyncio.sleep(1)
                    break
        except Exception:
            pass  # No consent dialog

    async def _scroll_results_list(self, target_count: int) -> None:
        """Scroll the results panel to load more listings."""
        logger.info("Scrolling results panel to load listings...")

        # Find the scrollable results container
        feed_selector = 'div[role="feed"]'
        feed = await self._page.query_selector(feed_selector)

        if not feed:
            # Try alternative container
            feed_selector = 'div[role="main"] div[tabindex="-1"]'
            feed = await self._page.query_selector(feed_selector)

        if not feed:
            logger.warning("Could not find scrollable results container")
            return

        prev_count = 0
        no_change_count = 0
        max_no_change = 5  # Stop if no new results after 5 scrolls

        for scroll_num in range(50):  # Max 50 scroll iterations
            # Count current listings
            listings = await self._page.query_selector_all(
                'div[role="feed"] > div > div[jsaction]'
            )
            current_count = len(listings)

            if current_count >= target_count:
                logger.info(f"Reached target: {current_count} listings loaded")
                break

            if current_count == prev_count:
                no_change_count += 1
                if no_change_count >= max_no_change:
                    logger.info(f"No more results loading ({current_count} total)")
                    break
            else:
                no_change_count = 0

            prev_count = current_count

            # Scroll the feed container
            await self._page.evaluate(
                f'document.querySelector(\'{feed_selector}\').scrollTop += 800'
            )

            # Check for "end of list" indicator
            end_marker = await self._page.query_selector(
                'span:has-text("end of the list"), p:has-text("end of results")'
            )
            if end_marker:
                logger.info("Reached end of results list")
                break

            await asyncio.sleep(RATE_LIMIT.scroll_delay / 1000)

            if scroll_num % 5 == 0 and scroll_num > 0:
                logger.debug(f"  Scroll #{scroll_num}: {current_count} listings loaded")

    async def _get_listing_elements(self) -> list:
        """Get all listing link elements from the results panel."""
        # Primary selector: individual result cards
        selectors = [
            'div[role="feed"] a[href*="/maps/place/"]',
            'a[href*="/maps/place/"]',
        ]

        for selector in selectors:
            elements = await self._page.query_selector_all(selector)
            if elements:
                # Deduplicate by href
                seen_hrefs = set()
                unique = []
                for el in elements:
                    href = await el.get_attribute("href") or ""
                    if href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        unique.append(el)
                return unique

        return []

    async def _extract_listing_data(
        self, element: ElementHandle, index: int
    ) -> BusinessLead | None:
        """Extract data from a listing element by clicking into it."""
        lead = BusinessLead()

        try:
            # Get the Maps URL from the link
            href = await element.get_attribute("href")
            if href:
                lead.google_maps_url = href

            # Click into the listing to open detail panel
            await element.click()
            await asyncio.sleep(1.5)

            # Wait for detail panel to load
            try:
                await self._page.wait_for_selector(
                    'div[role="main"] h1, h1[data-attrid]',
                    timeout=8_000,
                )
            except Exception:
                pass

            # ── Extract business name ────────────────────────
            name_el = await self._page.query_selector(
                'div[role="main"] h1'
            )
            if name_el:
                lead.name = clean_text(await name_el.inner_text())

            if not lead.name:
                # Try from the aria-label of the clicked element
                aria = await element.get_attribute("aria-label")
                if aria:
                    lead.name = clean_text(aria)

            if not lead.name:
                return None

            # ── Extract rating & reviews ─────────────────────
            rating_el = await self._page.query_selector(
                'div[role="main"] span[role="img"][aria-label*="star"]'
            )
            if rating_el:
                aria = await rating_el.get_attribute("aria-label") or ""
                lead.rating = extract_rating(aria)

            review_el = await self._page.query_selector(
                'div[role="main"] span[aria-label*="review"]'
            )
            if review_el:
                review_text = await review_el.get_attribute("aria-label") or ""
                lead.review_count = extract_review_count(review_text)
            else:
                # Try button text like "(1,234)"
                review_btn = await self._page.query_selector(
                    'div[role="main"] button[jsaction*="review"] span'
                )
                if review_btn:
                    txt = await review_btn.inner_text()
                    lead.review_count = extract_review_count(txt)

            # ── Extract category ─────────────────────────────
            cat_el = await self._page.query_selector(
                'div[role="main"] button[jsaction*="category"]'
            )
            if cat_el:
                lead.category = clean_text(await cat_el.inner_text())

            # ── Extract info buttons (address, phone, website, hours) ──
            info_buttons = await self._page.query_selector_all(
                'div[role="main"] button[data-item-id]'
            )

            for btn in info_buttons:
                item_id = await btn.get_attribute("data-item-id") or ""
                aria_label = await btn.get_attribute("aria-label") or ""
                text = clean_text(await btn.inner_text()) if not aria_label else ""
                value = aria_label or text

                if item_id.startswith("address") or "address" in item_id.lower():
                    lead.address = clean_text(value.replace("Address:", "").strip())
                elif item_id.startswith("phone") or "phone" in item_id.lower():
                    lead.phone = clean_phone(value.replace("Phone:", "").strip())
                elif item_id.startswith("authority") or "website" in item_id.lower():
                    raw_url = value.replace("Website:", "").strip()
                    lead.website = clean_url(raw_url)
                elif "oloc" in item_id:
                    lead.plus_code = clean_text(value.replace("Plus code:", "").strip())

            # ── Fallback: try aria-label patterns ────────────
            if not lead.address:
                addr_el = await self._page.query_selector(
                    'button[aria-label*="Address:"], button[data-tooltip*="address"]'
                )
                if addr_el:
                    aria = await addr_el.get_attribute("aria-label") or ""
                    lead.address = clean_text(aria.replace("Address:", "").strip())

            if not lead.phone:
                phone_el = await self._page.query_selector(
                    'button[aria-label*="Phone:"], a[href^="tel:"]'
                )
                if phone_el:
                    href = await phone_el.get_attribute("href") or ""
                    aria = await phone_el.get_attribute("aria-label") or ""
                    if href.startswith("tel:"):
                        lead.phone = clean_phone(href.replace("tel:", ""))
                    else:
                        lead.phone = clean_phone(aria.replace("Phone:", ""))

            if not lead.website:
                web_el = await self._page.query_selector(
                    'a[data-item-id="authority"]'
                )
                if web_el:
                    href = await web_el.get_attribute("href") or ""
                    lead.website = clean_url(href)

            # ── Extract price level ──────────────────────────
            price_el = await self._page.query_selector(
                'div[role="main"] span[aria-label*="Price"]'
            )
            if price_el:
                lead.price_level = clean_text(
                    await price_el.get_attribute("aria-label") or await price_el.inner_text()
                )

            # ── Extract coordinates from URL ─────────────────
            current_url = self._page.url
            coord_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", current_url)
            if coord_match:
                lead.latitude = float(coord_match.group(1))
                lead.longitude = float(coord_match.group(2))

            # Update Maps URL from current page
            if "/maps/place/" in current_url:
                lead.google_maps_url = current_url

            # ── Go back to results list ──────────────────────
            back_btn = await self._page.query_selector(
                'button[aria-label="Back"], button[jsaction*="back"]'
            )
            if back_btn:
                await back_btn.click()
                await asyncio.sleep(1)
            else:
                await self._page.go_back()
                await asyncio.sleep(1.5)

            return lead

        except Exception as e:
            logger.debug(f"Extraction error for listing {index}: {e}")
            # Try to recover by going back
            try:
                await self._page.go_back()
                await asyncio.sleep(1)
            except Exception:
                pass
            return None

    async def _take_screenshot(self, name: str) -> None:
        """Save a debug screenshot."""
        if self._page:
            path = SCREENSHOT_DIR / f"{name}_{datetime.now().strftime('%H%M%S')}.png"
            await self._page.screenshot(path=str(path), full_page=False)
            logger.debug(f"Screenshot saved: {path}")
