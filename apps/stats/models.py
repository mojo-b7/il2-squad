from django.db import models
from django.contrib.auth.models import User


class IL2StatsServer(models.Model):
    """
    Model for a game server that provides stats via il2stats.

    This is a server that we scrape for mission results, e.g.
    http://ts3.virtualpilots.fi:8000/
    """
    name = models.CharField(max_length=50)
    url = models.UrlField()

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
    pilot_url = models.UrlField()

    class Meta:
        verbose_name = "Pilot Stats Page"
        verbose_name_plural = "Pilot Stats Pages"

    def __str__(self):
        return f"{self.user.username} - {self.server.name}"


class VirtualLife(models.Model):
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

    # Points are float numbers, but we store them as integers to avoid rounding errors.
    # To get a point from a stored value, divide by 100.
    sortie_points = models.IntegerField()
    air_combat_points = models.IntegerField()
    ground_combat_points = models.IntegerField()
    ship_combat_points = models.IntegerField()
    leadership_points = models.IntegerField()
    nco_points = models.IntegerField()

    class Meta:
        verbose_name_plural = "Virtual Lives"
        ordering = ["user", "number"]

    def __str__(self):
        return f"{self.user.username} - {self.start_date} - {self.end_date}"


class Sortie(models.Model):
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

    # Points are float numbers, but we store them as integers to avoid rounding
    # problems. To get a point from a stored value, divide by 100.
    sortie_points = models.IntegerField()
    air_combat_points = models.IntegerField()
    ground_combat_points = models.IntegerField()
    ship_combat_points = models.IntegerField()
    leadership_points = models.IntegerField()
    nco_points = models.IntegerField()

    class Meta:
        ordering = ["virtual_life", "date", "time"]

    def __str__(self):
        return f"{self.virtual_life.user.username} - {self.date} - {self.time}"
