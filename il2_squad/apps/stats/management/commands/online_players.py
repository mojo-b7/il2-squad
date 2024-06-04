"""
Import pilots' sortie data from il2stats websites.
"""
import requests
from lxml import html
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth.models import User
from stats.models import IL2StatsServer, SomePilot, PlayerOccurrence, COALITION_BLUE, COALITION_RED
from urllib.parse import urljoin
from django.utils import timezone


logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = getattr(settings, "REQUEST_TIMEOUT", 120)  # seconds; stats servers tend to be slow


class Command(BaseCommand):
    help = "Get current online players from il2stats websites."
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.players = []

    def add_arguments(self, parser):
        """
        Add command line arguments to the management command.
        """
        parser.add_argument(
            "--server",
            type=str,
            help="Server name; if omitted, all servers' are polled.",
        )

    def handle(self, *args, **options):
        """
        Handle management command to get the current online players.
        """
        server_name = getattr(options, "server", None)
        servers = IL2StatsServer.objects.all()
        if server_name:
            servers = servers.filter(name=server_name)
            
        for server in servers:
            logger.info(f"Getting online players for server: {server}")
            # Build online list URL
            url = urljoin(server.url, "/en/online")
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            tree = html.fromstring(response.content)
            
            self.scrape_coalition(tree, '//div[@class="online_players"]//div[@class="online_coal_1"]')
            self.scrape_coalition(tree, '//div[@class="online_players"]//div[@class="online_coal_2"]')

    @staticmethod
    def scrape_coalition(tree, xpath):
        """
        Scrape a coalition of online players.
        """
        # Get coalition root element
        root_el = tree.xpath(xpath)
        if not root_el:
            logger.error(f"Could not find node {xpath}")
            return
        root_el = root_el[0]
        
        # header
        header = root_el.xpath('.//div[@class="header"]')
        try:
            coalition_name = header[0].text
        except Exception as e:
            logger.error(f"Could not get coalition name: {e}")
            return

        coalition = COALITION_RED if "allies" in coalition_name.lower() else COALITION_BLUE
        
        # Player list
        for row in root_el.xpath('./div[@class="content_table"]/a[@class="row"]'):
            href = row.get("href")
            id_on_site = int(href.split("/")[-1])
            name = row.xpath('./div[@class="cell"]')[0].text
            logger.info(f"Player {name} ({id_on_site}) in coalition {coalition}")
            # Check if this player is already in the database
            if SomePilot.objects.filter(id_on_site=id_on_site).exists():
                pilot = SomePilot.objects.get(id_on_site=id_on_site)
            else:
                pilot = SomePilot.objects.create(
                    site=server,
                    id_on_site=id_on_site,

                )
            
            if coalition == COALITION_RED:
                pilot.red_occ_count += 1
            else:
                pilot.blue_occ_count += 1
            
            # Squad member?
            member = User.objects.filter(username=name)
            if len(member):
                pilot.squad_pilot = member[0]
            pilot.save()
            
            # Check if name is known and up to date
            pilot.set_current_name(name)
            
            # Save occurrence
            PlayerOccurrence.objects.create(
                pilot=pilot,
                server=server,
                coalition=coalition,
                time=timezone.now(),
            )
            
