"""Scrapers for different data sources."""
from .uldk_scraper import ULDKScraper
from .spatial_plans_scraper import SpatialPlansScraper

__all__ = ["ULDKScraper", "SpatialPlansScraper"]
