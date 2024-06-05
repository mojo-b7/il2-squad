from django.contrib import admin
from django.utils.translation import gettext_lazy
from django.conf import settings

from .models import IL2StatsServer, PilotStatsPage, SomePilot, PlayerOccurrence


class PilotStatsPageAdmin(admin.ModelAdmin):
    list_display = ("pilot_squad_name", "server", "url")

    def pilot_squad_name(self, obj):
        return f'{settings.SQUAD_TAG}{obj.pilot.username.capitalize()}'

admin.site.register(PilotStatsPage, PilotStatsPageAdmin)


class IL2StatsServerAdmin(admin.ModelAdmin):
    list_display = ("name", "url")

admin.site.register(IL2StatsServer, IL2StatsServerAdmin)


class SomePilotAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "site", "squad_pilot")

admin.site.register(SomePilot, SomePilotAdmin)


class PlayerOccurrenceAdmin(admin.ModelAdmin):
    list_display = ("pilot_name", "server", "coalition", "timestamp")
    list_filter = ("server", "coalition", "timestamp")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("pilot", "server")

    def pilot_name(self, obj):
        return obj.pilot.name()

admin.site.register(PlayerOccurrence, PlayerOccurrenceAdmin)


# Customize admin page
admin.site.site_header = gettext_lazy("IL-2 Squad Admin")
admin.site.site_title = gettext_lazy("IL-2 Squad Admin")