"""Minimal scraper interfaces for Colorado Lottery data.

Endpoints:
- static.coloradolottery.com/media (Game Guideline PDFs)
- coloradolottery.com/en/scratch (remaining prizes)
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional


class GuidelinePDF:
    """Parser for Colorado Lottery Game Guideline PDFs."""

    BASE_URL = "https://static.coloradolottery.com/media"

    @classmethod
    def url_for_game(cls, game_number: int) -> str:
        # Heuristic; actual paths use filer_public hashes
        return f"{cls.BASE_URL}/game/{game_number}/guideline.pdf"

    @staticmethod
    def extract_ticket_count(text: str) -> Optional[int]:
        """Extract total tickets from PDF text (e.g., '1,385,473 WINNING TICKETS OUT OF 4,560,000')."""
        m = re.search(r"OUT OF ([0-9,]+)", text)
        if m:
            return int(m.group(1).replace(",", ""))
        return None

    @staticmethod
    def extract_top_odds(text: str) -> Optional[float]:
        """Extract top-prize odds (e.g., '1 IN 506,666.67')."""
        m = re.search(r"ODDS OF WINNING A TOP PRIZE,\s*1 IN ([0-9,.]+)", text)
        if m:
            return float(m.group(1).replace(",", ""))
        return None
