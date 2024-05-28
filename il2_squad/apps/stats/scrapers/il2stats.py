"""
Scraper class for IL2 stats pages
"""

from django.conf import settings
import logging
import requests
from lxml import html
from django.contrib.auth.models import User

logger = logging.getLogger("scraper")


class Il2StatsScraper(BaseScraper):
    """
    Scraper class for il2stats pages.
    """
    def __init__(self, stats_page):
        super().__init__(stats_page)

        # Get list of available tours
        tour_links = self.tree.xpath('//*[@id="nav_main"]//div[@class="nav_tour_items"]/a')
        self.tour_ids = [int(link.get("href").split("=")[-1]) for link in self.tour_links]

    def scrape(self):
        """
        Scrape the stats page.
        """
        raise NotImplementedError()