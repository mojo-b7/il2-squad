from django.db import models
from django.contrib.auth.models import User


class ModelWithPoints(models.Model):
    """
    Abstract base class for models that store combat points.
    """
    class Meta:
        abstract = True

    sortie_points = models.DecimalField(decimal_places=2)
    air_combat_points = models.DecimalField(decimal_places=2)
    ground_combat_points = models.DecimalField(decimal_places=2)
    ship_combat_points = models.DecimalField(decimal_places=2)
    leadership_points = models.DecimalField(decimal_places=2)
    nco_points = models.DecimalField(decimal_places=2)


class IL2StatsServer(models.Model):
    """
    Model for a game server that provides stats via il2stats.

    This is a server that we scrape for mission results, e.g.
    http://ts3.virtualpilots.fi:8000/
    """
    name = models.CharField(max_length=50)
    url = models.URLField()

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
    pilot_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Pilot Stats Page"
        verbose_name_plural = "Pilot Stats Pages"

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
        ordering = ["user", "number"]

    def __str__(self):
        return f"{self.pilot.username} - {self.start_date} - {self.end_date}"


class Sortie(ModelWithPoints):
    """
    Model for a pilot's sortie.
    """
    virtual_life = models.ForeignKey(VirtualLife, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    aircraft = models.CharField(max_length=50)
    duration = models.DurationField()
    was_wounded = models.BooleanField()
    air_kills = models.IntegerField()
    ground_kills = models.IntegerField()
    ship_kills = models.IntegerField()

    # Tour and sortie ID are taken from the scraped site (il2stats)
    tour_id = models.IntegerField(default=0)
    sortie_id = models.IntegerField(default=0)

    class Meta:
        ordering = ["virtual_life", "date", "time"]

    def __str__(self):
        return f"{self.virtual_life.pilot.username} - {self.date} - {self.time}"
