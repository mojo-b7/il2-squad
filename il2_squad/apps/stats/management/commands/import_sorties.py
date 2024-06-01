"""
Import pilots' sortie data from il2stats websites.

"""

import requests
import lxml
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from stats.models import IL2StatsServer, PilotStatsPage, Tour, Sortie
from scrapers import get_scraper_class

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 120)  # seconds; stats servers tend to be slow


class Command(BaseCommand):
    help = "Import pilots' sortie data from il2stats websites."

    def add_arguments(self, parser):
        """
        Add command line arguments to the management command.
        """
        parser.add_argument(
            "--pilot",
            type=str,
            help="Pilot's username to import data for.",
        )
        parser.add_argument(
            "--server",
            type=str,
            help="Server name; if omitted, all servers' data is imported.",
        )
        parser.add_argument(
            "--tour",
            type=int,
            help="Tour ID to import data from; if omitted, all tours are checked for updates.",
        )

    def handle(self, *args, **options):
        """
        Handle management command to import sortie data from il2stats websites.
        """
        pilot = None
        server = None

        tour_id = getattr(options, "tour", None)
        server_name = getattr(options, "server", None)
        pilot_username = getattr(options, "pilot", None)

        # Limit the import to a single pilot?
        if pilot_username:
            try:
                pilot = User.objects.get(username=pilot_username)
                logger.info(f"Importing sortie data for pilot: {pilot}")
                for stats_page in PilotStatsPage.objects.filter(pilot=pilot):
                    self.scrape_pilot_stats(pilot, stats_page.server, tour_id)

            except User.DoesNotExist:
                raise CommandError(f"Pilot {pilot_username} does not exist.")

        # Limit the import to a single server?
        if server_name:
            try:
                server = IL2StatsServer.objects.get(name=server_name)
                logger.info(f"Importing sortie data from server: {server}")
                for pilot in server.pilot_set.all():
                    self.scrape_pilot_stats(pilot, server, tour_id)
            except IL2StatsServer.DoesNotExist:
                raise CommandError(f"Server {server_name} does not exist.")

            # Get the pilot's stats page URL from the database
            # Get the server URL from the database
            # Scrape the server

    def scrape_pilot_stats(self, pilot, server, tour_id=None):
        """
        Parse a pilot's stats page on a particular server and import sortie data.
        
        @param pilot: User object representing the pilot.
        @param server: IL2StatsServer object representing the server.
        @param tour_id: Optional tour ID to import data from. If None, we import all unseen tours.
        """
        try:
            stats_page = PilotStatsPage.objects.get(pilot=pilot, server=server)
            scraper = get_scraper_class(server.scraper_type)(stats_page)
        except PilotStatsPage.DoesNotExist:
            logger.error(f"No stats page found for pilot {pilot} on server {server}.")
            return
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            return

