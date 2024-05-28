"""
Base class for stats page scrapers.
"""
fro django.conf import settings
import logging
from lxml import html


logger = logging.getLogger("scraper")
REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 120)  # seconds; stats servers tend to be slow


class BaseScraper(object):
    """
    Base class for stats page scrapers.
    """

    def __init__(self, stats_page):
        """
        Initialize the scraper with a PilotStatsPage object.

        This GETs the request page and parses its conotent with lxml.
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
