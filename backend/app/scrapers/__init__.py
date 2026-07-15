"""Scrapers for external designation sources."""
from .aia_lombardia import AiaLombardiaScraper, ScrapedDesignation
from .aia_national import NATIONAL_HUBS, scrape_national_hubs

__all__ = ["AiaLombardiaScraper", "ScrapedDesignation", "NATIONAL_HUBS", "scrape_national_hubs"]
