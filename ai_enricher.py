"""
LeadHarvester Pro - AI Data Enricher
======================================
Uses OpenAI GPT-4o-mini to clean, validate, categorize,
and enrich scraped business lead data.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from loguru import logger

from config import OPENAI_API_KEY


class AIEnricher:
    """
    AI-powered data cleaning and enrichment.

    Capabilities:
    - Validate & standardize business names
    - Categorize businesses into industry verticals
    - Score lead quality (1-10)
    - Generate personalized outreach suggestions
    - Detect and fix data inconsistencies
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or OPENAI_API_KEY
        self._client = None

        if self._api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._api_key)
                logger.info("AI Enricher initialized with OpenAI GPT-4o-mini")
            except ImportError:
                logger.warning("openai package not installed")
        else:
            logger.warning("No API key - AI enrichment disabled")

    @property
    def available(self) -> bool:
        return self._client is not None

    def enrich_leads(
        self,
        leads: list[dict],
        context: str = "",
        batch_size: int = 10,
    ) -> list[dict]:
        """
        Enrich a list of scraped leads with AI analysis.

        Adds:
        - industry_category: Standardized business category
        - lead_quality_score: 1-10 score
        - outreach_angle: Personalized pitch suggestion
        - data_confidence: How complete/reliable the data is
        """
        if not self.available:
            logger.info("AI unavailable - adding basic enrichment only")
            return self._basic_enrichment(leads)

        enriched = []
        total_batches = (len(leads) + batch_size - 1) // batch_size

        for batch_idx in range(0, len(leads), batch_size):
            batch = leads[batch_idx: batch_idx + batch_size]
            batch_num = batch_idx // batch_size + 1
            logger.info(f"Enriching batch {batch_num}/{total_batches} ({len(batch)} leads)")

            try:
                result = self._enrich_batch(batch, context)
                enriched.extend(result)
            except Exception as e:
                logger.error(f"Batch {batch_num} enrichment failed: {e}")
                # Fallback: return leads with basic enrichment
                enriched.extend(self._basic_enrichment(batch))

        logger.info(f"Enrichment complete: {len(enriched)} leads processed")
        return enriched

    def _enrich_batch(self, batch: list[dict], context: str) -> list[dict]:
        """Process a batch of leads through AI."""
        # Prepare compact lead data for the prompt
        compact = []
        for i, lead in enumerate(batch):
            compact.append({
                "idx": i,
                "name": lead.get("name", ""),
                "category": lead.get("category", ""),
                "address": lead.get("address", ""),
                "phone": lead.get("phone", ""),
                "website": lead.get("website", ""),
                "rating": lead.get("rating"),
                "review_count": lead.get("review_count"),
            })

        prompt = f"""You are a B2B lead qualification expert. Analyze these business leads scraped from Google Maps and enrich each one.

{f'Business context: {context}' if context else ''}

Leads to analyze:
{json.dumps(compact, indent=2)}

For EACH lead (by idx), return a JSON array with these fields:
- idx: the lead index
- industry_category: Standardized industry (e.g., "Restaurant & Food Service", "Home Services - Plumbing", "Healthcare - Dental", "Legal Services", "Retail", etc.)
- lead_quality_score: 1-10 (based on: has phone? has website? has reviews? good rating? complete data?)
- outreach_angle: One-sentence personalized cold outreach hook
- data_confidence: "high" | "medium" | "low" (how reliable/complete the data looks)
- estimated_revenue: rough annual revenue bracket ("<100K", "100K-500K", "500K-1M", "1M-5M", "5M+")
- is_franchise: true/false (best guess)

Return ONLY a valid JSON array. No markdown, no explanation."""

        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a B2B lead enrichment API. Always respond with valid JSON arrays only. No markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)

        # Handle both {"leads": [...]} and [...] formats
        if isinstance(parsed, dict):
            enrichment_data = parsed.get("leads", parsed.get("results", []))
        elif isinstance(parsed, list):
            enrichment_data = parsed
        else:
            enrichment_data = []

        # Merge enrichment data back into leads
        enrichment_map = {item.get("idx", i): item for i, item in enumerate(enrichment_data)}

        result = []
        for i, lead in enumerate(batch):
            enrichment = enrichment_map.get(i, {})
            lead["industry_category"] = enrichment.get("industry_category", "Uncategorized")
            lead["lead_quality_score"] = enrichment.get("lead_quality_score", 5)
            lead["outreach_angle"] = enrichment.get("outreach_angle", "")
            lead["data_confidence"] = enrichment.get("data_confidence", "medium")
            lead["estimated_revenue"] = enrichment.get("estimated_revenue", "Unknown")
            lead["is_franchise"] = enrichment.get("is_franchise", False)
            result.append(lead)

        return result

    def _basic_enrichment(self, leads: list[dict]) -> list[dict]:
        """Fallback enrichment without AI."""
        for lead in leads:
            # Calculate a basic quality score
            score = 0
            if lead.get("name"):
                score += 2
            if lead.get("phone"):
                score += 2
            if lead.get("website"):
                score += 2
            if lead.get("address"):
                score += 1
            if lead.get("rating") and lead["rating"] >= 4.0:
                score += 2
            if lead.get("review_count") and lead["review_count"] >= 10:
                score += 1

            lead["industry_category"] = lead.get("category", "Uncategorized")
            lead["lead_quality_score"] = min(score, 10)
            lead["outreach_angle"] = ""
            lead["data_confidence"] = (
                "high" if score >= 7 else "medium" if score >= 4 else "low"
            )
            lead["estimated_revenue"] = "Unknown"
            lead["is_franchise"] = False

        return leads

    def generate_outreach_email(self, lead: dict) -> str:
        """Generate a personalized cold outreach email for a lead."""
        if not self.available:
            return ""

        prompt = f"""Write a short, professional cold email (3-4 sentences max) for this business:

Business: {lead.get('name')}
Category: {lead.get('industry_category', lead.get('category', ''))}
Location: {lead.get('address', '')}
Rating: {lead.get('rating', 'N/A')} ({lead.get('review_count', 0)} reviews)
Website: {lead.get('website', 'No website')}

The email should:
- Be personalized to their specific business
- Mention something relevant about their online presence
- Offer to help with a common pain point
- Be casual-professional tone
- Include a soft CTA

Return ONLY the email body text, no subject line."""

        try:
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Email generation failed: {e}")
            return ""
