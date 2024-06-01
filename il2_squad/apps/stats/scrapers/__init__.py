"""
Base class for stats page scrapers.
"""
from django.conf import settings
import logging
from lxml import html
import requests
import importlib


logger = logging.getLogger("scraper")
REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 120)  # seconds; stats servers tend to be slow

IL2STATS_SCRAPER_IDENTIFIER = "il2stats"
DEFAULT_SCRAPER_IDENTIFIER = IL2STATS_SCRAPER_IDENTIFIER

# Tuple that defines the available scrapers; this can be used to set the values
# for Django choices in select fields.
SCRAPER_OPTIONS = (
    (IL2STATS_SCRAPER_IDENTIFIER, "IL2Stats"),
)

# Map scraper names to their class names.
SCRAPER_MAP = {
    IL2STATS_SCRAPER_IDENTIFIER: "Il2StatsScraper",
}


def get_scraper_class(scraper_identifier):
    """
    Return a scraper class for a scraper identifier.
    """
    scraper_class_name = SCRAPER_MAP.get(scraper_identifier)
    if not scraper_class_name:
        raise ValueError(f"Unknown scraper identifier: {scraper_identifier}")
    module = importlib.import_module("scrapers")
    scraper_class = getattr(module, scraper_class_name)
    return scraper_class


class BaseScraper(object):
    """
    Base class for stats page scrapers.
    """

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
