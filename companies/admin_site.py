from django.contrib.admin import AdminSite


class SponsorTrackerAdminSite(AdminSite):
    """Admin area limited to sponsor register operations (no user/group management here)."""

    site_header = "Sponsor tracker admin"
    site_title = "Sponsor tracker"
    index_title = "Sponsor register"


sponsor_admin_site = SponsorTrackerAdminSite(name="admin")
