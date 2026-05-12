from django.urls import include, path

from companies.admin_site import sponsor_admin_site

urlpatterns = [
    path("admin/", sponsor_admin_site.urls),
    path("", include("companies.urls")),
]
