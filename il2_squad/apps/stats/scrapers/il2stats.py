"""
Scraper class for IL2 stats pages
"""
import logging
import requests
import re
from urllib.parse import urlparse

from lxml import html
from django.contrib.auth.models import User
from . import BaseScraper
from django.conf import settings


logger = logging.getLogger("scraper")
REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 120)  # seconds; stats servers tend to be slow


class Il2StatsScraper(BaseScraper):
    """
    Scraper class for il2stats pages.
    """

    def __init__(self, stats_page):
        super().__init__(stats_page)
        logger.info(f"Importing sortie data for pilot {stats_page.pilot} on server {stats_page.server}")
        # Regexp to force an English page
        self.force_en_re = re.compile(r"(http[s]*:\/\/[^\/]+)\/\w{2}\/(.*)")
        # Get server base URL (protocol, host, port)
        url = urlparse(stats_page.url)
        self.server_base_url = f"{url.scheme}://{url.netloc}"

        # Get list of available tours
        tour_links = self.tree.xpath('//*[@id="nav_main"]//div[@class="nav_tour_items"]/a')
        self.tour_ids = [int(link.get("href").split("=")[-1]) for link in tour_links]
        if len(self.tour_ids) == 0:
            raise ValueError(f"No tours found on {stats_page}.")

    def scrape(self, only_tour_id=None):
        """
        Scrape a pilot's stats page.
        """
        # After init, we have a list of tours
        for tour_id in self.tour_ids:
            # If a tour_id is specified, only scrape that tour
            if only_tour_id is not None and tour_id != only_tour_id:
                continue
            logger.info(f"Loading sorties for tour {tour_id}")
            # Get link to list of sorties; the sorties list URL is the same as the pilots
            # stats page, but with "sorties" instead of "pilot".
            sorties_list_url = self.stats_page.url.replace("/pilot/", "/sorties/")
            # Cut off eventual tour, then add the tour we want
            sorties_list_url = sorties_list_url.split("?")[0]
            logger.info(f"Loading sortie list from {sorties_list_url}")
            sorties_list_url += f"?tour={tour_id}"
            # Load sorties, parse 
            response = requests.get(sorties_list_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            sorties_tree = html.fromstring(response.content)
            
            # Loop through sortie list and load each sortie
            for sortie_row in sorties_tree.xpath('//div[@class="content_table"]/a[@class="row"]'):
                # Get the sortie log; insert "log" into URL
                sortie_url = self.server_base_url + sortie_row.get("href").replace("/sortie/", "/sortie/log/")
                # And make sure it's in English
                sortie_url = re.sub(self.force_en_re, r'\1/en/\2', sortie_url)
                logging.info(f"Loading sortie from log at {sortie_url}")
                response = requests.get(sortie_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                sortie_log_tree = html.fromstring(response.content)
                
                




