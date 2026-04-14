# 🎯 LeadHarvester Pro — Google Maps Lead Scraper

> **Scrape hundreds of verified business leads from Google Maps in minutes — with AI-powered enrichment, lead scoring, and beautiful Excel reports. Built for agencies, recruiters, and sales teams who need leads fast.**

LeadHarvester Pro is a production-grade Python scraper that extracts business data from Google Maps using Playwright stealth mode. It handles anti-bot detection, cleans data automatically, enriches leads with GPT-4o-mini (quality scoring, industry classification, outreach hooks), and exports everything to professional Excel workbooks.

---

## 🔥 Why This Exists

| Pain Point | LeadHarvester Solution |
|---|---|
| *"I need 500 plumber leads in Houston"* | One command: `python main.py scrape -k "plumbers" -l "Houston, TX" -m 500` |
| *"I waste hours copy-pasting from Maps"* | Fully automated — scrape, clean, export |
| *"The data is always messy"* | AI-powered cleaning + phone/address standardization |
| *"I don't know which leads are good"* | AI lead scoring 1-10 + Hot Leads sheet |
| *"I get blocked by Google"* | Stealth mode, human-like behavior, proxy rotation |
| *"I need different formats"* | Excel (styled), CSV, JSON — your choice |

---

## ✨ Key Features

- **🕵️ Stealth Scraping** — Anti-detection JS injection, navigator overrides, WebDriver hiding
- **🧠 AI Lead Enrichment** — GPT-4o-mini scores leads 1-10, categorizes industries, suggests outreach angles
- **📊 Pro Excel Reports** — Multi-sheet workbooks with Hot Leads tab, Summary dashboard, conditional formatting
- **🔄 Proxy Rotation** — Built-in proxy manager for high-volume scraping
- **🎭 Human-Like Behavior** — Random delays, natural scrolling, mouse movements
- **⚡ Batch Mode** — Scrape multiple keywords/locations from a single config file
- **📱 Rich CLI** — Beautiful terminal UI with progress bars, stats, and colored output
- **🔁 Retry Logic** — Smart retries with exponential backoff
- **📸 Debug Screenshots** — Optional screenshot capture for troubleshooting

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repo
git clone https://github.com/facingshootingstar/DataScraping.git
cd DataScraping

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 2. Configure

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Edit .env — add your OpenAI API key for AI enrichment
# (optional but recommended)
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

# Scrape without AI enrichment
python main.py scrape -k "gyms" -l "Chicago, IL" --no-enrich

# With debug screenshots
python main.py scrape -k "lawyers" -l "NYC" --screenshot

# Batch mode — multiple searches at once
python main.py batch -f batch_example.json

# Enrich previously scraped data
python main.py enrich -i data/raw/restaurants_austin_tx_20260415.json
```

---

## 📊 What Gets Extracted

| Field | Example |
|---|---|
| Business Name | Joe's Pizza |
| Industry Category | Restaurant & Food Service |
| Address | 123 Main St, Austin, TX 78701 |
| Phone | (512) 555-0123 |
| Website | https://joespizza.com |
| Rating | 4.7 |
| Review Count | 1,234 |
| Lead Quality Score | 9/10 |
| Price Level | $$ |
| Outreach Hook | *"Your 4.7-star rating shows customers love you..."* |
| Data Confidence | High |
| Est. Revenue | $500K-1M |
| Google Maps URL | Full link |
| Coordinates | Lat/Long |

---

## 📂 Project Structure

```
DataScraping/
├── main.py               # CLI entry point (4 commands)
├── scraper.py            # Core Google Maps scraper engine
├── ai_enricher.py        # AI-powered lead enrichment
├── exporter.py           # Excel/CSV export with styling
├── config.py             # Configuration management
├── requirements.txt      # Pinned dependencies
├── .env.example          # Environment template
├── .gitignore
├── batch_example.json    # Example batch config
├── data/
│   ├── raw/              # Raw scraped JSON
│   └── processed/        # Final Excel/CSV output
├── logs/                 # Application logs
├── screenshots/          # Debug screenshots
└── utils/
    ├── __init__.py
    ├── stealth.py        # Anti-detection browser wrapper
    └── helpers.py        # Text cleaning & file utilities
```

---

## 🛠️ Tech Stack

| Library | Version | Purpose |
|---|---|---|
| playwright | 1.49.1 | Browser automation (stealth) |
| pandas | 2.2.3 | Data manipulation |
| openpyxl | 3.1.5 | Excel read/write |
| xlsxwriter | 3.2.2 | Advanced Excel formatting |
| openai | 1.58.1 | AI lead enrichment (GPT-4o-mini) |
| click | 8.1.8 | CLI framework |
| rich | 13.9.4 | Terminal UI |
| loguru | 0.7.3 | Logging |
| pydantic | 2.10.3 | Data validation |
| tenacity | 9.0.0 | Retry logic |
| python-dotenv | 1.0.1 | Environment config |
| fake-useragent | 2.0.3 | User agent rotation |

---

## ⚠️ Ethical Use & Legal Disclaimer

This tool is provided **for educational and legitimate business purposes only.**

- **Respect Google's Terms of Service.** Use responsibly with appropriate rate limiting.
- **Comply with local data protection laws** (GDPR, CCPA, etc.).
- **Do not use for spam**, harassment, or any illegal activity.
- **Public data only.** This tool only extracts publicly visible information.
- The author is **not responsible** for misuse of this tool.

**Best Practices:**
- Use generous delays between requests (default: 2-5 seconds)
- Don't scrape more than you need
- Use proxies for volume to avoid IP bans
- Store data securely and comply with privacy regulations

---

## 💰 How to Sell as Fixed-Price Service

### Pricing Tiers

| Tier | Price | What's Included |
|---|---|---|
| **Starter** | $600 | Single keyword + location, up to 200 leads, Excel output |
| **Professional** | $1,200 | 5 keyword/location combos, AI enrichment, Hot Leads filtering, batch mode |
| **Enterprise** | $1,800–$2,000 | Unlimited searches, custom data fields, proxy setup, scheduling, 30 days support |

### Sales Pitch

> *"I'll build you a custom lead generation machine that scrapes hundreds of verified business leads from Google Maps in minutes. You'll get phone numbers, websites, ratings, and AI-scored lead quality — all delivered in a beautiful Excel spreadsheet ready for your sales team. One-time setup, use it forever. No monthly SaaS fees."*

### Where to Find Clients
- **Upwork / Fiverr** — Search for "scraping" or "lead generation" gigs
- **LinkedIn** — Target marketing agencies, real estate agents, recruiters
- **Facebook Groups** — Business owner groups, local business communities
- **Cold email** — Use the tool itself to find prospects 😎

---

## 📸 Screenshots

### Terminal Output
```
  ██╗     ███████╗ █████╗ ██████╗     ██╗  ██╗ █████╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗███████╗██████╗
  ...

  Starting Lead Scrape
  Searching: plumbers
  Location: Austin, TX
  Max Results: 50

  [1/50] Joe's Plumbing
  [2/50] Austin Plumbing Co
  ...

  ┌─────────────────────────────────────────┐
  │ Lead Statistics                         │
  │  Total Leads:     50                    │
  │  With Phone:      47 (94%)             │
  │  With Website:    38 (76%)             │
  │  Hot Leads (7+):  23                    │
  └─────────────────────────────────────────┘
```

### Excel Output
> Professional multi-sheet workbook with:
> - **All Leads** — Full data with conditional formatting
> - **Hot Leads** — Pre-filtered high-quality leads (score 7+)
> - **Summary** — Dashboard with key metrics

---

## 📄 License

MIT License — Use commercially, modify freely.

---

## 🤝 Author

Built with 🔥 by [facingshootingstar](https://github.com/facingshootingstar)

---

<p align="center">
  <strong>LeadHarvester Pro</strong> — Stop manually searching Google Maps. Start harvesting leads.
</p>
