"""
Import pilots' sortie data from il2stats websites.
"""
import requests
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from stats.models import IL2StatsServer, PilotStatsPage, Sortie
from stats.scrapers import get_scraper_class

logger = logging.getLogger("management")

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
            if server_name:
                raise CommandError("Cannot specify both pilot and server.")
            try:
                pilot = User.objects.get(username=pilot_username)
                logger.info(f"Importing sortie data for pilot: {pilot}")
                for stats_page in PilotStatsPage.objects.filter(pilot=pilot).select_related("server", "pilot"):
                    self.scrape_pilot_stats(stats_page, tour_id)

            except User.DoesNotExist:
                raise CommandError(f"Pilot {pilot_username} does not exist.")

        # Limit the import to a single server?
        elif server_name:
            try:
                server = IL2StatsServer.objects.get(name=server_name)
                logger.info(f"Importing sortie data from server: {server}")
                for stats_page in server.pilotstatspage_set.all():
                    self.scrape_pilot_stats(stats_page, tour_id)
            except IL2StatsServer.DoesNotExist:
                raise CommandError(f"Server {server_name} does not exist.")

        else:
            # Normal mode, check all servers and all pilots.
            for server in IL2StatsServer.objects.all():
                for stats_page in server.pilotstatspage_set.all().select_related("server", "pilot"):
                    self.scrape_pilot_stats(stats_page, tour_id)

    @staticmethod
    def scrape_pilot_stats(stats_page, tour_id=None):
        """
        Parse a pilot's stats page on a particular server and import sortie data.
        
        @param stats_page: The statistics page to start scraping at.
        @param tour_id: Optional tour ID to import data from. If None, we import all unseen tours.
        """
        try:
            # Determine and initialize server specific scraper
            scraper = get_scraper_class(stats_page.server.scraper_type)(stats_page)
            scraper.scrape(tour_id)

        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            return

