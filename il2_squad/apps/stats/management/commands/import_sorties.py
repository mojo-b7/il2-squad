"""
Import pilots' sortie data from il2stats websites.

"""

import requests
import lxml
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 120)  # seconds; stats servers tend to be slow


class Command(BaseCommand):
    help = "Import pilots' sortie data from il2stats websites."

    def add_arguments(self, parser):
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
            help="Tour ID to import data from; if ommitted, all tours are checked for updates.",
        )


    def handle(self, *args, **options):

        pilot = None
        server = None

        tour_id = getattr(options, "tour", None)
        server_name = getattr(options, "server", None)
        pilot_username = getattr(options, "pilot", None)

        # Limit the import to a single pilot?
        if pilot_name:
            try:
                pilot = User.objects.get(username=pilot_username)
                logger.info(f"Importing sortie data for pilot: {pilot}")
            except User.DoesNotExist:
                raise CommandError(f"Pilot {pilot_username} does not exist.")

        # Limit the import to a single server?
        if server_name:
            try:
                server = IL2StatsServer.objects.get(name=server_name)
                logger.info(f"Importing sortie data from server: {server}")
            except IL2StatsServer.DoesNotExist:
                raise CommandError(f"Server {server_name} does not exist.")

            # Get the pilot's stats page URL from the database
            # Get the server URL from the database
            # Scrape the server

    def scrape_pilot(self, pilot, server, tour_id=None):
        """
        Parse the pilot's stats page and import sortie data.
        """
        try:
            stats_page = PilotStatsPage.objects.get(pilot=pilot, server=server)
        except PilotStatsPage.DoesNotExist:
            logger.error(f"No stats page found for pilot {pilot} on server {server}.")
            return

        # Get the pilot's stats page
        try:
            response = requests.get(stats_page.url, timeout=REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error while fetching {stats_page.url}: {e}")
            return

        # Get available tours
        if not tour_id:
            tours = self.get_tours(response)
