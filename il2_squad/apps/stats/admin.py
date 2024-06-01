from django.contrib import admin
from django.utils.translation import gettext_lazy

from .models import IL2StatsServer, PilotStatsPage


class PilotStatsPageAdmin(admin.ModelAdmin):
    list_display = ("pilot", "server", "url")

admin.site.register(PilotStatsPage, PilotStatsPageAdmin)


class IL2StatsServerAdmin(admin.ModelAdmin):
    list_display = ("name", "url")

admin.site.register(IL2StatsServer, IL2StatsServerAdmin)


# Customize admin page
admin.site.site_header = gettext_lazy("IL-2 Squad Admin")
admin.site.site_title = gettext_lazy("IL-2 Squad Admin")