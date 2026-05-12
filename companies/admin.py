from django.contrib import admin

from .models import Sponsor, UserSponsorEntry


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ("organisation_name", "town_city", "county", "type_rating", "route")
    list_filter = ("county", "route")
    search_fields = ("organisation_name", "town_city", "county")


@admin.register(UserSponsorEntry)
class UserSponsorEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "sponsor", "is_blacklisted", "have_tried", "updated_at")
    list_filter = ("is_blacklisted", "have_tried")
    search_fields = ("sponsor__organisation_name", "user__username")
    raw_id_fields = ("sponsor",)
