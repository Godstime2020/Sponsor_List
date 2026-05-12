from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="companies/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("sponsor/<int:pk>/", views.sponsor_detail, name="sponsor_detail"),
    path(
        "sponsor/<int:pk>/toggle-blacklist/",
        views.toggle_blacklist,
        name="toggle_blacklist",
    ),
    path("sponsor/<int:pk>/toggle-tried/", views.toggle_tried, name="toggle_tried"),
]
