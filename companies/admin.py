from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path

from companies.admin_site import sponsor_admin_site
from companies.models import Sponsor
from companies.sponsor_register_sync import sync_register_from_xlsx


@admin.register(Sponsor, site=sponsor_admin_site)
class SponsorAdmin(admin.ModelAdmin):
    """View list, edit type & route (identity fields read-only), sync from Excel — no add/delete here."""

    change_list_template = "admin/companies/sponsor/change_list.html"
    list_display = ("organisation_name", "town_city", "county", "type_rating", "route")
    list_filter = ("county", "route")
    search_fields = ("organisation_name", "town_city", "county")
    readonly_fields = ("organisation_name", "town_city", "county")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "sync-xlsx/",
                self.admin_site.admin_view(self.sync_xlsx_view),
                name="%s_%s_sync_xlsx" % info,
            ),
        ] + super().get_urls()

    def sync_xlsx_view(self, request):
        if not request.user.is_staff:
            messages.error(request, "You do not have access to this page.")
            return redirect("admin:login")

        if request.method == "POST":
            import os
            import tempfile

            from django.core.files.uploadedfile import UploadedFile

            f = request.FILES.get("xlsx")
            if not f or not isinstance(f, UploadedFile):
                messages.error(request, "No file uploaded.")
                return redirect("admin:companies_sponsor_sync_xlsx")
            if not f.name.lower().endswith(".xlsx"):
                messages.error(request, "Please upload an .xlsx file.")
                return redirect("admin:companies_sponsor_sync_xlsx")

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            try:
                for chunk in f.chunks():
                    tmp.write(chunk)
                tmp.close()
                result = sync_register_from_xlsx(tmp.name)
                messages.success(
                    request,
                    "Sync finished. Excel rows: %(rows)s. Added: %(added)s. Updated: %(upd)s. "
                    "Skipped (already identical): %(skip)s."
                    % {
                        "rows": result.excel_rows,
                        "added": result.added,
                        "upd": result.updated_rows,
                        "skip": result.skipped_identical,
                    },
                )
            except Exception as exc:
                messages.error(request, "Sync failed: %s" % exc)
            finally:
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
            return redirect("admin:companies_sponsor_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": "Sync sponsor register from Excel",
            "opts": self.model._meta,
        }
        return render(request, "admin/companies/sponsor/sync_xlsx.html", context)
