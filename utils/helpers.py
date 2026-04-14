"""
LeadHarvester Pro - Helper Utilities
======================================
Common utility functions for data cleaning,
file I/O, and text processing.
"""

from __future__ import annotations

import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any


def clean_text(text: str | None) -> str:
    """Strip and normalize whitespace from text."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text.strip())
    # Remove special unicode chars that break exports
    text = text.encode("ascii", errors="ignore").decode("ascii").strip()
    return text


def clean_phone(phone: str | None) -> str:
    """Extract and format phone number."""
    if not phone:
        return ""
    # Extract digits
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == "1":
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) >= 7:
        return phone.strip()
    return ""


def clean_url(url: str | None) -> str:
    """Clean and normalize URL."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    # Remove trailing slashes
    url = url.rstrip("/")
    return url


def extract_email_from_text(text: str) -> str:
    """Try to extract an email from text."""
    if not text:
        return ""
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def extract_rating(text: str | None) -> float | None:
    """Extract numeric rating from text like '4.5 stars'."""
    if not text:
        return None
    match = re.search(r"(\d+\.?\d*)", text)
    if match:
        val = float(match.group(1))
        if 0 <= val <= 5:
            return val
    return None


def extract_review_count(text: str | None) -> int | None:
    """Extract review count from text like '(1,234 reviews)'."""
    if not text:
        return None
    # Remove commas/periods used as thousand separators
    cleaned = text.replace(",", "").replace(".", "")
    match = re.search(r"(\d+)", cleaned)
    return int(match.group(1)) if match else None


def generate_filename(keyword: str, location: str, ext: str = "json") -> str:
    """Generate a unique filename based on search parameters."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = re.sub(r"[^\w]", "_", keyword.lower())[:30]
    safe_location = re.sub(r"[^\w]", "_", location.lower())[:20]
    return f"{safe_keyword}_{safe_location}_{timestamp}.{ext}"


def generate_hash(text: str) -> str:
    """Generate MD5 hash for deduplication."""
    return hashlib.md5(text.encode()).hexdigest()[:12]


def save_json(data: Any, filepath: str | Path) -> Path:
    """Save data as JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    return filepath


def load_json(filepath: str | Path) -> Any:
    """Load JSON file."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def truncate(text: str, max_len: int = 100) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def parse_hours_text(text: str | None) -> dict[str, str]:
    """Parse business hours from messy text."""
    if not text:
        return {}
    hours = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in days:
        pattern = rf"{day}[:\s]+([\d:]+\s*(?:AM|PM|am|pm)\s*[-–]\s*[\d:]+\s*(?:AM|PM|am|pm)|Closed|Open 24 hours)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            hours[day] = match.group(1).strip()
    return hours
