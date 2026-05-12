from typing import Any

from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import UserSponsorEntryForm
from .models import Sponsor, UserSponsorEntry


def build_qs(request, **overrides: Any) -> str:
    p = request.GET.copy()
    p.pop("page", None)
    for key, val in overrides.items():
        if val is None:
            p.pop(key, None)
        else:
            p[key] = str(val)
    return urlencode({k: v for k, v in p.items() if str(v) != ""})


def page_href(request, page_num: int) -> str:
    """Absolute path so pagination works from any URL shape."""
    qd = request.GET.copy()
    qd["page"] = str(page_num)
    return f"{reverse('dashboard')}?{qd.urlencode()}"


def _htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Account created. You are now signed in.")
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "companies/signup.html", {"form": form})


@login_required
def dashboard(request):
    q = request.GET.get("q", "").strip()
    region = request.GET.get("region", "")
    tab = request.GET.get("tab", "all")

    sponsors = Sponsor.objects.all()

    if region == "__UNKNOWN__":
        sponsors = sponsors.filter(county="")
    elif region:
        sponsors = sponsors.filter(county=region)

    if q:
        sponsors = sponsors.filter(
            Q(organisation_name__icontains=q)
            | Q(town_city__icontains=q)
            | Q(county__icontains=q)
        )

    if tab == "blacklisted":
        sponsors = sponsors.filter(
            user_entries__user=request.user,
            user_entries__is_blacklisted=True,
        ).distinct()
    elif tab == "tried":
        sponsors = sponsors.filter(
            user_entries__user=request.user,
            user_entries__have_tried=True,
        ).distinct()
    elif tab == "saved":
        saved_ids = (
            UserSponsorEntry.objects.filter(user=request.user)
            .filter(
                ~Q(what_i_know="") | ~Q(what_they_do="") | ~Q(extra_notes=""),
            )
            .values_list("sponsor_id", flat=True)
        )
        sponsors = sponsors.filter(id__in=saved_ids)

    sponsors = sponsors.order_by("organisation_name")

    paginator = Paginator(sponsors, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    ids = [s.id for s in page_obj.object_list]
    entries = {
        e.sponsor_id: e
        for e in UserSponsorEntry.objects.filter(user=request.user, sponsor_id__in=ids)
    }
    rows = [(s, entries.get(s.id)) for s in page_obj.object_list]

    region_rows = (
        Sponsor.objects.values("county")
        .annotate(c=Count("id"))
        .order_by("-c")[:48]
    )
    region_list = []
    for r in region_rows:
        name = (r["county"] or "").strip()
        label = name if name else "Unknown"
        key = name if name else "__UNKNOWN__"
        region_list.append({"key": key, "label": label, "count": r["c"]})

    stats = {
        "blacklisted": UserSponsorEntry.objects.filter(
            user=request.user, is_blacklisted=True
        ).count(),
        "tried": UserSponsorEntry.objects.filter(user=request.user, have_tried=True).count(),
        "with_notes": UserSponsorEntry.objects.filter(user=request.user)
        .filter(~Q(what_i_know="") | ~Q(what_they_do="") | ~Q(extra_notes=""))
        .count(),
    }

    all_regions_qs = build_qs(request, region=None)
    region_hrefs = [
        {
            "label": "All regions",
            "url": "?" + all_regions_qs if all_regions_qs else "?",
            "count": Sponsor.objects.count(),
            "active": not region,
        }
    ]
    for r in region_list:
        qs_s = build_qs(request, region=r["key"])
        region_hrefs.append(
            {
                "label": r["label"],
                "url": "?" + qs_s if qs_s else "?",
                "count": r["count"],
                "active": region == r["key"],
            }
        )

    tab_hrefs = {
        name: ("?" + build_qs(request, tab=name)) if build_qs(request, tab=name) else "?"
        for name in ("all", "blacklisted", "tried", "saved")
    }

    page_prev = (
        page_href(request, page_obj.previous_page_number())
        if page_obj.has_previous()
        else None
    )
    page_next = (
        page_href(request, page_obj.next_page_number()) if page_obj.has_next() else None
    )

    ctx = {
        "rows": rows,
        "page_obj": page_obj,
        "q": q,
        "region": region,
        "tab": tab,
        "region_hrefs": region_hrefs,
        "tab_hrefs": tab_hrefs,
        "page_prev": page_prev,
        "page_next": page_next,
        "stats": stats,
        "total_sponsors": Sponsor.objects.count(),
    }
    return render(request, "companies/dashboard.html", ctx)


@login_required
@require_http_methods(["GET", "POST"])
def sponsor_detail(request, pk: int):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    entry, _ = UserSponsorEntry.objects.get_or_create(
        user=request.user,
        sponsor=sponsor,
        defaults={},
    )
    if request.method == "POST":
        form = UserSponsorEntryForm(request.POST, instance=entry)
        if form.is_valid():
            inst = form.save(commit=False)
            was_tried = entry.have_tried
            if inst.have_tried and not was_tried:
                inst.tried_at = timezone.now()
            if not inst.have_tried:
                inst.tried_at = None
            inst.save()
            messages.success(request, "Saved your notes.")
            return redirect("sponsor_detail", pk=pk)
    else:
        form = UserSponsorEntryForm(instance=entry)
    return render(
        request,
        "companies/sponsor_detail.html",
        {"sponsor": sponsor, "entry": entry, "form": form},
    )


@login_required
@require_POST
def toggle_blacklist(request, pk: int):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    entry, _ = UserSponsorEntry.objects.get_or_create(user=request.user, sponsor=sponsor)
    entry.is_blacklisted = not entry.is_blacklisted
    entry.save(update_fields=["is_blacklisted", "updated_at"])
    if _htmx(request):
        return render(
            request,
            "companies/partials/sponsor_row.html",
            {"sponsor": sponsor, "entry": entry},
        )
    messages.info(
        request,
        f"Blacklist {'on' if entry.is_blacklisted else 'off'} for {sponsor.organisation_name}.",
    )
    return redirect(_next_dashboard(request))


@login_required
@require_POST
def toggle_tried(request, pk: int):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    entry, _ = UserSponsorEntry.objects.get_or_create(user=request.user, sponsor=sponsor)
    entry.have_tried = not entry.have_tried
    if entry.have_tried and entry.tried_at is None:
        entry.tried_at = timezone.now()
    if not entry.have_tried:
        entry.tried_at = None
    entry.save(update_fields=["have_tried", "tried_at", "updated_at"])
    if _htmx(request):
        return render(
            request,
            "companies/partials/sponsor_row.html",
            {"sponsor": sponsor, "entry": entry},
        )
    messages.info(
        request,
        f"Tried flag {'on' if entry.have_tried else 'off'} for {sponsor.organisation_name}.",
    )
    return redirect(_next_dashboard(request))


def _next_dashboard(request):
    n = request.POST.get("next")
    if n and n.startswith("/"):
        return n
    return "dashboard"
