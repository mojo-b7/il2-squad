from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from .scrapers import SCRAPER_OPTIONS, DEFAULT_SCRAPER_IDENTIFIER
from django.utils.translation import gettext_lazy as _, gettext


class ModelWithPoints(models.Model):
    """
    Abstract base class for models that store combat points.
    """
    class Meta:
        abstract = True

    sortie_points = models.DecimalField(decimal_places=2, max_digits=6)
    air_combat_points = models.DecimalField(decimal_places=2, max_digits=6)
    ground_combat_points = models.DecimalField(decimal_places=2, max_digits=6)
    ship_combat_points = models.DecimalField(decimal_places=2, max_digits=6)
    leadership_points = models.DecimalField(decimal_places=2, max_digits=6)
    nco_points = models.DecimalField(decimal_places=2, max_digits=6)


class   IL2StatsServer(models.Model):
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
        verbose_name = "Pilot Stats Page"
        verbose_name_plural = "Pilot Stats Pages"

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
        verbose_name_plural = "Virtual Lives"
        ordering = ["pilot", "-number"]

    def __str__(self):
        return f"{self.pilot.username} - {self.start_date} - {self.end_date}"


class Aircraft(models.Model):
    """
    Model for an aircraft in the game
    """
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Aircraft"
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
            raise ValidationError(gettext("Timely overlapping sortie already exists."))

    class Meta:
        ordering = ["virtual_life", "start_at"]

    def __str__(self):
        return f"{self.virtual_life.pilot.username} - {self.start_at}"
