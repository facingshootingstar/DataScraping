"""
LeadHarvester Pro - Main CLI Entry Point
==========================================
Google Maps Lead Scraper with AI Enrichment.

Usage:
    python main.py scrape --keyword "restaurants" --location "Austin, TX" --max 50
    python main.py scrape -k "plumbers" -l "Los Angeles, CA" --max 100 --enrich
    python main.py enrich --input data/raw/leads.json
    python main.py check
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from loguru import logger

import config
from scraper import GoogleMapsScraper
from ai_enricher import AIEnricher
from exporter import LeadExporter
from utils.helpers import save_json, load_json

# ── Logging ──────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    level=config.LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{message}</cyan>",
)
logger.add(
    config.LOG_DIR / "leadharvester_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="30 days",
    level="DEBUG",
)

console = Console()

BANNER = r"""
[bold cyan]
  ██╗     ███████╗ █████╗ ██████╗ 
  ██║     ██╔════╝██╔══██╗██╔══██╗
  ██║     █████╗  ███████║██║  ██║
  ██║     ██╔══╝  ██╔══██║██║  ██║
  ███████╗███████╗██║  ██║██████╔╝
  ╚══════╝╚══════╝╚═╝  ╚═╝╚═════╝ 
[/bold cyan][bold yellow]
  ██╗  ██╗ █████╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗███████╗██████╗ 
  ██║  ██║██╔══██╗██╔══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗
  ███████║███████║██████╔╝██║   ██║█████╗  ███████╗   ██║   █████╗  ██████╔╝
  ██╔══██║██╔══██║██╔══██╗╚██╗ ██╔╝██╔══╝  ╚════██║   ██║   ██╔══╝  ██╔══██╗
  ██║  ██║██║  ██║██║  ██║ ╚████╔╝ ███████╗███████║   ██║   ███████╗██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
[/bold yellow]
[dim]  Google Maps Lead Scraper Pro  v1.0.0  |  Stealth Mode[/dim]
"""


@click.group()
@click.version_option(version="1.0.0", prog_name="LeadHarvester Pro")
def cli():
    """LeadHarvester Pro - Google Maps Lead Scraper with AI Enrichment."""
    pass


# ══════════════════════════════════════════════════════════════
# SCRAPE COMMAND
# ══════════════════════════════════════════════════════════════

@cli.command()
@click.option("--keyword", "-k", required=True, help="Business type to search (e.g., 'restaurants', 'plumbers')")
@click.option("--location", "-l", required=True, help="Location to search (e.g., 'Austin, TX', 'New York, NY')")
@click.option("--max", "-m", "max_results", default=50, help="Maximum number of results (default: 50)")
@click.option("--enrich/--no-enrich", default=True, help="Enable AI enrichment (default: enabled)")
@click.option("--format", "-f", "output_format", type=click.Choice(["excel", "csv", "both", "json"]), default="excel")
@click.option("--screenshot", is_flag=True, help="Take debug screenshots")
@click.option("--context", "-c", default="", help="Business context for AI enrichment")
def scrape(keyword, location, max_results, enrich, output_format, screenshot, context):
    """Scrape Google Maps for business leads."""
    console.print(BANNER)
    console.print(Panel(
        f"[bold]Searching:[/bold] {keyword}\n[bold]Location:[/bold] {location}\n[bold]Max Results:[/bold] {max_results}",
        title="[bold green]Starting Lead Scrape[/bold green]",
        border_style="green",
    ))

    # Run the async scraper
    leads = asyncio.run(_run_scrape(keyword, location, max_results, screenshot))

    if not leads:
        console.print("[red]No leads found. Try a different keyword or location.[/red]")
        return

    console.print(f"\n[green]Scraped {len(leads)} leads successfully![/green]")

    # AI Enrichment
    if enrich:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Enriching leads with AI...", total=None)
            enricher = AIEnricher()
            leads = enricher.enrich_leads(leads, context=context)
            progress.update(task, description=f"Enriched {len(leads)} leads")

    # Export
    exporter = LeadExporter()

    if output_format in ("excel", "both"):
        excel_path = exporter.to_excel(leads, keyword=keyword, location=location)
        console.print(f"[green]Excel saved:[/green] {excel_path}")

    if output_format in ("csv", "both"):
        csv_path = exporter.to_csv(leads, keyword=keyword, location=location)
        console.print(f"[green]CSV saved:[/green] {csv_path}")

    if output_format == "json":
        from utils.helpers import generate_filename
        json_path = config.OUTPUT_DIR / generate_filename(keyword, location, "json")
        save_json(leads, json_path)
        console.print(f"[green]JSON saved:[/green] {json_path}")

    # Print results table
    _print_leads_table(leads)

    # Print stats
    _print_stats(leads)

    console.print(Panel("[bold green]Scraping complete![/bold green]", border_style="green"))


async def _run_scrape(keyword: str, location: str, max_results: int, screenshot: bool) -> list[dict]:
    """Run the async scraper."""
    scraper = GoogleMapsScraper()
    return await scraper.scrape(
        keyword=keyword,
        location=location,
        max_results=max_results,
        save_raw=True,
        screenshot=screenshot,
    )


# ══════════════════════════════════════════════════════════════
# ENRICH COMMAND
# ══════════════════════════════════════════════════════════════

@cli.command()
@click.option("--input", "-i", "input_path", required=True, help="Path to raw JSON leads file")
@click.option("--context", "-c", default="", help="Business context for AI")
@click.option("--format", "-f", "output_format", type=click.Choice(["excel", "csv", "both"]), default="excel")
def enrich(input_path, context, output_format):
    """Enrich previously scraped leads with AI analysis."""
    console.print(BANNER)
    console.print(Panel("Enriching existing leads with AI", title="[bold cyan]AI Enrichment[/bold cyan]", border_style="cyan"))

    # Load leads
    leads = load_json(input_path)
    console.print(f"Loaded {len(leads)} leads from {input_path}")

    # Enrich
    enricher = AIEnricher()
    leads = enricher.enrich_leads(leads, context=context)

    # Export
    exporter = LeadExporter()
    stem = Path(input_path).stem

    if output_format in ("excel", "both"):
        path = exporter.to_excel(leads, filename=f"enriched_{stem}")
        console.print(f"[green]Excel saved:[/green] {path}")

    if output_format in ("csv", "both"):
        path = exporter.to_csv(leads)
        console.print(f"[green]CSV saved:[/green] {path}")

    _print_leads_table(leads)
    _print_stats(leads)


# ══════════════════════════════════════════════════════════════
# CHECK COMMAND
# ══════════════════════════════════════════════════════════════

@cli.command()
def check():
    """Check configuration and environment."""
    console.print(BANNER)
    console.print(Panel("Configuration Check", title="[bold cyan]System Check[/bold cyan]", border_style="cyan"))

    checks = [
        ("Data directory", str(config.RAW_DIR), config.RAW_DIR.exists()),
        ("Output directory", str(config.OUTPUT_DIR), config.OUTPUT_DIR.exists()),
        ("Log directory", str(config.LOG_DIR), config.LOG_DIR.exists()),
        ("OpenAI API Key", "***" + config.OPENAI_API_KEY[-4:] if config.OPENAI_API_KEY else "NOT SET", bool(config.OPENAI_API_KEY)),
        ("Proxy configured", str(config.PROXY_MANAGER.available), config.PROXY_MANAGER.available),
        ("Headless mode", str(config.BROWSER.headless), True),
    ]

    table = Table(title="Configuration", show_lines=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="bold")

    for name, value, ok in checks:
        status = "[green]OK[/green]" if ok else "[yellow]WARN[/yellow]"
        table.add_row(name, value, status)

    console.print(table)

    # Check Playwright
    try:
        from playwright.sync_api import sync_playwright
        console.print("[green]Playwright: Installed[/green]")
    except ImportError:
        console.print("[red]Playwright: NOT INSTALLED - run 'pip install playwright && playwright install chromium'[/red]")

    warnings = config.validate_config()
    if warnings:
        console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
        for w in warnings:
            console.print(f"  [yellow]>[/yellow] {w}")
    else:
        console.print("\n[green]All checks passed![/green]")


# ══════════════════════════════════════════════════════════════
# BATCH COMMAND
# ══════════════════════════════════════════════════════════════

@cli.command()
@click.option("--file", "-f", "batch_file", required=True, help="Path to batch config JSON file")
@click.option("--enrich/--no-enrich", default=True)
def batch(batch_file, enrich):
    """Run batch scraping from a config file.

    Batch JSON format:
    [
        {"keyword": "restaurants", "location": "Austin, TX", "max": 30},
        {"keyword": "plumbers", "location": "Houston, TX", "max": 50}
    ]
    """
    console.print(BANNER)

    jobs = load_json(batch_file)
    console.print(f"Loaded {len(jobs)} batch jobs from {batch_file}")

    all_leads = []
    for i, job in enumerate(jobs, 1):
        kw = job.get("keyword", "")
        loc = job.get("location", "")
        max_r = job.get("max", 50)
        console.print(f"\n[bold][Job {i}/{len(jobs)}][/bold] {kw} in {loc} (max {max_r})")

        leads = asyncio.run(_run_scrape(kw, loc, max_r, False))
        if leads:
            if enrich:
                enricher = AIEnricher()
                leads = enricher.enrich_leads(leads)
            all_leads.extend(leads)

            # Save per-job results
            exporter = LeadExporter()
            exporter.to_excel(leads, keyword=kw, location=loc)

        console.print(f"  [green]Got {len(leads)} leads[/green]")

    # Save combined results
    if all_leads:
        exporter = LeadExporter()
        exporter.to_excel(all_leads, keyword="batch_combined", location="multi")
        console.print(f"\n[bold green]Batch complete: {len(all_leads)} total leads from {len(jobs)} searches[/bold green]")


# ══════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════

def _print_leads_table(leads: list[dict], max_rows: int = 15) -> None:
    """Print leads as a rich table."""
    table = Table(title=f"Scraped Leads ({len(leads)} total)", show_lines=False, expand=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Business Name", style="bold cyan", max_width=30)
    table.add_column("Phone", max_width=18)
    table.add_column("Rating", justify="center", max_width=8)
    table.add_column("Reviews", justify="center", max_width=10)
    table.add_column("Score", justify="center", max_width=7)
    table.add_column("Website", max_width=30, overflow="fold")

    for i, lead in enumerate(leads[:max_rows], 1):
        rating = str(lead.get("rating", "-")) if lead.get("rating") else "-"
        reviews = str(lead.get("review_count", "-")) if lead.get("review_count") else "-"
        score = str(lead.get("lead_quality_score", "-"))
        score_style = "green" if lead.get("lead_quality_score", 0) >= 7 else "yellow" if lead.get("lead_quality_score", 0) >= 4 else "red"

        table.add_row(
            str(i),
            lead.get("name", "")[:30],
            lead.get("phone", ""),
            rating,
            reviews,
            f"[{score_style}]{score}[/{score_style}]",
            lead.get("website", "")[:30],
        )

    console.print(table)
    if len(leads) > max_rows:
        console.print(f"  [dim]... and {len(leads) - max_rows} more leads[/dim]")


def _print_stats(leads: list[dict]) -> None:
    """Print summary statistics."""
    total = len(leads)
    has_phone = sum(1 for l in leads if l.get("phone"))
    has_website = sum(1 for l in leads if l.get("website"))
    has_rating = sum(1 for l in leads if l.get("rating"))
    hot_leads = sum(1 for l in leads if l.get("lead_quality_score", 0) >= 7)

    avg_rating = 0
    rated = [l["rating"] for l in leads if l.get("rating")]
    if rated:
        avg_rating = sum(rated) / len(rated)

    stats_panel = f"""
  [bold]Total Leads:[/bold]     {total}
  [bold]With Phone:[/bold]      {has_phone} ({has_phone/total*100:.0f}%)
  [bold]With Website:[/bold]    {has_website} ({has_website/total*100:.0f}%)
  [bold]With Rating:[/bold]     {has_rating} ({has_rating/total*100:.0f}%)
  [bold]Avg Rating:[/bold]      {avg_rating:.1f} / 5.0
  [bold]Hot Leads (7+):[/bold]  [bold green]{hot_leads}[/bold green]
"""
    console.print(Panel(stats_panel, title="[bold]Lead Statistics[/bold]", border_style="blue"))


# ── Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    cli()
