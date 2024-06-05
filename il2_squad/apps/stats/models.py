from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from .scrapers import SCRAPER_OPTIONS, DEFAULT_SCRAPER_IDENTIFIER
from django.utils.translation import gettext_lazy as _
from urllib.parse import urlparse
from django.utils import timezone


# Coalition symbols
COALITION_RED = "red"
COALITION_BLUE = "blue"
COALITION_CHOICES = (
    (COALITION_BLUE, "Blue"),
    (COALITION_RED, "Red"), 
)


class ModelWithPoints(models.Model):
    """
    Abstract base class for models that store combat points.
    """
    class Meta:
        abstract = True

    # Points for the sortie itself, depending on its length
    sortie_points = models.DecimalField(decimal_places=2, max_digits=6)
    # Points for air combat (kills, assists, etc)
    air_combat_points = models.DecimalField(decimal_places=2, max_digits=6)
    # Points for ground targets destroyed
    ground_combat_points = models.DecimalField(decimal_places=2, max_digits=6)
    # Points for ships destroyed
    ship_combat_points = models.DecimalField(decimal_places=2, max_digits=6)
    # Points for leadership
    leadership_points = models.DecimalField(decimal_places=2, max_digits=6)
    # Points for NCO duties (e.g. assisting the flight leader)
    nco_points = models.DecimalField(decimal_places=2, max_digits=6)


class IL2StatsServer(models.Model):
    """
    Model for a game server that provides stats via il2stats.

    This is a server that we scrape for mission results, e.g.
    http://ts3.virtualpilots.fi:8000/
    """
    name = models.CharField(max_length=50, unique=True)
    url = models.URLField()
    scraper_type = models.CharField(max_length=50, choices=SCRAPER_OPTIONS, 
                                    default=DEFAULT_SCRAPER_IDENTIFIER)

    class Meta:
        verbose_name = "IL-2 Stats Server"
        verbose_name_plural = "IL-2 Stats Servers"
        
    def clean(self):
        # Ensure the url is valid and is the base URL of the server
        try:
            url = urlparse(self.url)
            scheme = url.scheme or "http"
            self.url = f"{scheme}://{url.netloc}"
            if url.port:
                self.url += f":{url.port}"
        except Exception as e:
            raise ValidationError("Invalid URL: " + str(e))

    def __str__(self):
        return self.name


class PilotStatsPage(models.Model):
    """
    A pilot's stats page on an il2stats server.
    """
    pilot = models.ForeignKey(User, on_delete=models.CASCADE)
    server = models.ForeignKey(IL2StatsServer, on_delete=models.CASCADE)
    url = models.URLField()

    class Meta:
        verbose_name = _("Pilot Stats Page")
        verbose_name_plural = _("Pilot Stats Pages")

    def clean(self):
        # Cut off eventual ?tour parameter from the URL; calling this URL
        # without tour parameter will return the pilot's stats of the current tour.
        self.url = self.url.split("?")[0]

    def __str__(self):
        return f"{self.pilot.username} - {self.server.name}"


class VirtualLife(ModelWithPoints):
    """
    Model for a pilot's virtual life.
    """
    pilot = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    number = models.IntegerField()
    flight_time = models.DurationField(default=0)

    was_wounded = models.BooleanField()
    air_kills = models.IntegerField()
    ground_kills = models.IntegerField()
    ship_kills = models.IntegerField()

    class Meta:
        verbose_name = _("Virtual Life")
        verbose_name_plural = _("Virtual Lives")
        ordering = ["pilot", "-number"]

    def __str__(self):
        return f"{self.pilot.username} - {self.start_date} - {self.end_date}"


class Aircraft(models.Model):
    """
    Model for an aircraft in the game
    """
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = _("Aircraft")
        verbose_name_plural = _("Aircraft")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Sortie(ModelWithPoints):
    """
    Model for a pilot's sortie.
    """
    virtual_life = models.ForeignKey(VirtualLife, on_delete=models.CASCADE)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    was_wounded = models.BooleanField()
    air_kills = models.IntegerField()
    ground_kills = models.IntegerField()
    ship_kills = models.IntegerField()

    # Tour and sortie ID are taken from the scraped site (il2stats)
    tour_id = models.IntegerField(default=0)
    sortie_id = models.IntegerField(default=0, unique=True)

    def clean(self):
        # Ensure that there are no overlapping sorties for the same pilot.
        if Sortie.objects.filter(
            virtual_life__pilot=self.virtual_life.pilot,
            start_at__lte=self.end_at,
            end_at__gte=self.start_at,
        ).exists():
            raise ValidationError(_("Timely overlapping sortie already exists."))

    class Meta:
        ordering = ["virtual_life", "start_at"]

    def __str__(self):
        return f"{self.virtual_life.pilot.username} - {self.start_at}"


class SomePilot(models.Model):
    """
    Model for some pilot.
    
    This is usually a pilot seen on the "online" page of the server, i.e. the page that lists
    the current players. The pilot is not necessarily a member of this squad.
    """
    site = models.ForeignKey(IL2StatsServer, on_delete=models.CASCADE)
    # User id of this pilot on the site we got him from
    id_on_site = models.IntegerField(unique=True)
    # How many times has this pilot been seen on the server?
    red_occ_count = models.IntegerField(default=0, help_text=_("Number of times this pilot has been seen on the red side"))
    blue_occ_count = models.IntegerField(default=0, help_text=_("Number of times this pilot has been seen on the blue side"))
    # If the pilot is a member of this squad, we can link him to a user account
    squad_pilot = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _("Some Pilot")
        verbose_name_plural = _("Some Pilots")
        ordering = ["site", "id_on_site"]
        
    def set_current_name(self, name, url):
        """
        Set/update the current name if applicable.
        
        This also updates the `last_seen` timestamp.
        
        @param name: the name to set as current
        @param url: pilot's URL on the site
        """
        current = self.somepilotname_set.filter(is_current=True).first()
        if current and current.name == name:
            current.last_seen=timezone.now()
            current.save()
            return
          
        name_rec = SomePilotName.objects.filter(name=name, pilot=self).first()
        if name_rec:
            name_rec.set_current()
        else:
            SomePilotName.objects.create(
                name=name,
                pilot=self,
                first_seen=timezone.now(),
                last_seen=timezone.now(),
                url=url
            )
        
    def name(self):
        """
        Get the current name of this pilot.
        
        @return: the current name of this pilot
        """
        return self.somepilotname_set.filter(is_current=True).first().name
        
    def __str__(self):
        return f'{self.id_on_site}'
        
        
class SomePilotName(models.Model):
    """
    Name of a pilot that is not necessarily registered with this site or member of this squad.
    
    Reason for having this in a separate model is the fact that some pilots seem to like changing
    their names every now and then. When I changed my name (joining a new squad), my history stayed, my ID
    stayed, just the name changed. So I am assuming that the player ID is unique and tied to the IL-2 
    game license or whatever. Having this in a separate model allows us to keep track of the names
    pilots used in the past.
    """
    name = models.CharField(max_length=100)
    pilot = models.ForeignKey(SomePilot, on_delete=models.CASCADE)
    # When was this name first and last seen in the server's player list?
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()
    # Unfortunately, the URL to a player is name specific, so we need to store it here
    url = models.URLField()

    is_current = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("Some pilot's name")
        verbose_name_plural = _("Some pilot names")
        ordering = ["-last_seen", "name"]
        # Only one current name per pilot
        unique_together = ["is_current", "pilot"]
        
    def set_current(self):
        """
        Set this name as the current name of the pilot.
        
        This also updates the `last_seen` timestamp.
        """
        if self.is_current:
            self.last_seen = timezone.now()
        else:
            # Clear `is_current` for all other names
            SomePilotName.objects.filter(pilot=self.pilot, is_current=True).update(is_current=False)
            # Set this name as current
            self.is_current = True
            self.last_seen = timezone.now()
        self.save()
        
    def __str__(self):
        return self.name
    
    
class PlayerOccurrence(models.Model):
    """
    Model that stores an occurrence of a player on a server.
    """
    server = models.ForeignKey(IL2StatsServer, on_delete=models.CASCADE)
    pilot = models.ForeignKey(SomePilot, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_created=True)
    coalition = models.CharField(max_length=10, choices=COALITION_CHOICES)
    
    class Meta:
        verbose_name = _("Player Occurrence")
        verbose_name_plural = _("Player Occurrences")
        ordering = ["-timestamp", "server", "pilot"]

    def player_cnt_at(self, timestamp):
        """
        Get the number of players on the server at the given timestamp.

        This is not 100% accurate, as we only poll/sample players at a given time. So this function
        returns the number of players sample taken closest to the given timestamp.

        Uses raw SQL to optimize speed.

        @param timestamp: the timestamp to check
        @return: dict with the number of players on the server at the given timestamp for each coalition
        """
        samples = PlayerOccurrence.objects.raw('SELECT * FROM stats_playeroccurrence WHERE server_id = %s AND timestamp <= %s ORDER BY timestamp DESC LIMIT 1', [self.server.id, timestamp])
        red_cnt = PlayerOccurrence.objects.filter(server=self.server, coalition=COALITION_RED, timestamp__lte=timestamp).count()
        blue_cnt = PlayerOccurrence.objects.filter(server=self.server, coalition=COALITION_BLUE, timestamp__lte=timestamp).count()
        return {"red": red_cnt, "blue": blue_cnt}

    def __str__(self):
        return f"{self.pilot} on {self.server} at {self.timestamp}"


