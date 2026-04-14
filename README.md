<div align="center">

# 🔎 DataScraping — Google Maps Scraper with AI Enrichment

**Scrape structured business data from Google Maps using Playwright stealth mode, then enrich leads with GPT-4o-mini for quality scoring, industry classification, and outreach insights. Exports to professional Excel workbooks and CSV.**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Stealth-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[Features](#-key-features) · [Quick Start](#-quick-start) · [Usage](#-usage) · [Output](#-what-gets-extracted)

</div>

---

## 📌 About This Project

A personal automation project combining web scraping with AI-powered data enrichment. This tool demonstrates expertise in Playwright stealth automation, OpenAI API integration, professional Excel report generation, and CLI design — built as a hands-on learning exercise and portfolio showcase.

---

## ✨ Key Features

- 🕵️ **Stealth Scraping** — Anti-detection JS injection, navigator overrides, WebDriver hiding
- 🧠 **AI Lead Enrichment** — GPT-4o-mini scores leads 1–10, categorizes industries, suggests outreach angles
- 📊 **Pro Excel Reports** — Multi-sheet workbooks with Hot Leads tab, Summary dashboard, conditional formatting
- 🔄 **Proxy Rotation** — Built-in proxy manager for high-volume scraping
- 🎭 **Human-Like Behavior** — Random delays, natural scrolling, mouse movements
- ⚡ **Batch Mode** — Scrape multiple keywords/locations from a single config file
- 📱 **Rich CLI** — Beautiful terminal UI with progress bars, stats, and colored output
- 🔁 **Retry Logic** — Smart retries with exponential backoff
- 📸 **Debug Screenshots** — Optional screenshot capture for troubleshooting

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Core runtime |
| Playwright | Browser automation with stealth |
| OpenAI API | GPT-4o-mini for lead enrichment |
| Rich | Terminal UI and progress display |
| Pandas | Data processing |
| openpyxl | Styled Excel export |
| python-dotenv | Environment configuration |

---

## 📁 Project Structure

```
DataScraping/
├── main.py                 # CLI entry point (4 commands)
├── scraper.py              # Core Google Maps scraper engine
├── ai_enricher.py          # AI-powered lead enrichment
├── exporter.py             # Excel/CSV export with styling
├── config.py               # Configuration management
├── requirements.txt        # Pinned dependencies
├── .env.example            # Environment template
├── .gitignore
├── batch_example.json      # Example batch config
├── data/
│   ├── raw/                # Raw scraped JSON
│   └── processed/          # Final Excel/CSV output
├── logs/                   # Application logs
├── screenshots/            # Debug screenshots
└── utils/
    ├── __init__.py
    ├── stealth.py           # Anti-detection browser wrapper
    └── helpers.py           # Text cleaning & file utilities
```

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repo
git clone https://github.com/facingshootingstar/DataScraping.git
cd DataScraping

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — add your OpenAI API key for AI enrichment (optional but recommended)
```

### 3. Check Setup

```bash
python main.py check
```

### 4. Scrape!

```bash
# Basic scrape — 50 restaurants in Austin
python main.py scrape -k "restaurants" -l "Austin, TX"

# Scrape 100 plumbers in LA with AI enrichment
python main.py scrape -k "plumbers" -l "Los Angeles, CA" -m 100 --enrich

# Export as both Excel & CSV
python main.py scrape -k "dentists" -l "Miami, FL" -m 75 -f both

# Batch mode — multiple searches at once
python main.py batch -f batch_example.json

# Enrich previously scraped data
python main.py enrich -i data/raw/restaurants_austin_tx_20260415.json
```

---

## 📊 What Gets Extracted

| Field | Example |
|-------|---------|
| `business_name` | Joe's Pizza |
| `address` | 7 Carmine St, New York, NY 10014 |
| `phone` | +1 212-366-1182 |
| `website` | joespizza.com |
| `rating` | 4.5 |
| `reviews_count` | 12,847 |
| `category` | Pizza restaurant |
| `google_maps_url` | https://maps.google.com/... |
| `ai_score` | 8.5 (with enrichment) |
| `ai_industry` | Food & Beverage (with enrichment) |
| `ai_outreach_hook` | High-volume location... (with enrichment) |

---

## 📤 Output

### Excel Output
Professional multi-sheet workbook with:
- **All Leads** — Full data with conditional formatting
- **Hot Leads** — Pre-filtered high-quality leads (score 7+)
- **Summary** — Dashboard with key metrics

### CLI Output
```
┌─────────────────────────────────────────┐
│           Lead Statistics               │
│  Total Leads:      50                   │
│  With Phone:       47 (94%)             │
│  With Website:     38 (76%)             │
│  Hot Leads (7+):   23                   │
└─────────────────────────────────────────┘
```

---

## ⚖️ Ethical Use & Legal Disclaimer

> **⚠️ This tool is for educational and research purposes only.**

- **Respect Google's Terms of Service.** Use responsibly with appropriate rate limiting.
- **Comply with local data protection laws** (GDPR, CCPA, etc.).
- **Do not use** for spam, harassment, or any illegal activity.
- **Public data only** — this tool only extracts publicly visible information.
- Use generous delays between requests (default: 2–5 seconds).
- The author assumes **no liability** for misuse of this tool.

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for details.

---

<div align="center">

**Built with ❤️ by [@facingshootingstar](https://github.com/facingshootingstar)**

*Made for personal learning and portfolio purposes.*

</div>
