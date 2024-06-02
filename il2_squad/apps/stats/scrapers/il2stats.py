"""
Scraper class for IL2 stats pages
"""
import logging
import requests
from lxml import html
from django.contrib.auth.models import User
from . import BaseScraper


logger = logging.getLogger("scraper")


class Il2StatsScraper(BaseScraper):
    """
    Scraper class for il2stats pages.
    """

    def __init__(self, stats_page):
        super().__init__(stats_page)
        logger.info(f"Importing sortie data for pilot {stats_page.pilot} on server {stats_page.server}")

        # Get list of available tours
        tour_links = self.tree.xpath('//*[@id="nav_main"]//div[@class="nav_tour_items"]/a')
        self.tour_ids = [int(link.get("href").split("=")[-1]) for link in tour_links]
        if len(self.tour_ids) == 0:
            raise ValueError(f"No tours found on {stats_page}.")

    def scrape(self, tour_id=None):
        """
        Scrape a pilot's stats page.
        """


