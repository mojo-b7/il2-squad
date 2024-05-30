"""
Base class for stats page scrapers.
"""
from django.conf import settings
import logging
from lxml import html
import requests

from scrapers.il2stats import Il2StatsScraper


logger = logging.getLogger("scraper")
REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 120)  # seconds; stats servers tend to be slow

DEFAULT_SCRAPER_IDENTIFIER = Il2StatsScraper.identifier

# Tuple that defines the available scrapers; this can be used to set the values
# for Django choices in select fields.
SCRAPER_OPTIONS = (
    (Il2StatsScraper.identifier, "IL2Stats"),
)

# Map scraper names to their classes.
SCRAPER_MAP = {
    Il2StatsScraper.identifier: Il2StatsScraper,
}


class BaseScraper(object):
    """
    Base class for stats page scrapers.
    """
    identifier = "__base__"

    def __init__(self, stats_page):
        """
        Initialize the scraper with a PilotStatsPage object.

        This GETs the request page and parses its content with lxml.
        """
        self.stats_page = stats_page
        response = requests.get(stats_page.url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        self.tree = html.fromstring(response.content)
        logger.info(f"Successfully loaded {stats_page.url}")

    def scrape(self):
        """
        Scrape the stats page.
        """
        raise NotImplementedError()
