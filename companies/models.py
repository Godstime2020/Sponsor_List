from django.conf import settings
from django.db import models


class Sponsor(models.Model):
    """A row from the published sponsor register."""

    organisation_name = models.CharField(max_length=512, db_index=True)
    town_city = models.CharField(max_length=256, blank=True, db_index=True)
    county = models.CharField(
        max_length=256,
        blank=True,
        db_index=True,
        help_text="Treated as region for filtering (UK county or similar).",
    )
    type_rating = models.CharField(max_length=256, blank=True)
    route = models.CharField(max_length=256, blank=True)

    class Meta:
        ordering = ["organisation_name"]
        indexes = [
            models.Index(fields=["county", "organisation_name"]),
        ]

    def __str__(self) -> str:
        return self.organisation_name

    @property
    def region_label(self) -> str:
        return self.county.strip() or "Unknown"


class UserSponsorEntry(models.Model):
    """Per-user tracking, blacklist, and notes for one sponsor."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sponsor_entries",
    )
    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.CASCADE,
        related_name="user_entries",
    )
    is_blacklisted = models.BooleanField(default=False)
    have_tried = models.BooleanField(
        default=False,
        help_text="Mark if you have already approached or applied here.",
    )
    tried_at = models.DateTimeField(null=True, blank=True)
    what_i_know = models.TextField(
        blank=True,
        help_text="Your notes: context, contacts, reputation, etc.",
    )
    what_they_do = models.TextField(
        blank=True,
        help_text="What the company does (sector, products, hiring patterns).",
    )
    extra_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "sponsor"], name="unique_user_sponsor_entry"),
        ]
        ordering = ["-updated_at"]
        verbose_name_plural = "User sponsor entries"

    def __str__(self) -> str:
        flags = []
        if self.is_blacklisted:
            flags.append("blacklist")
        if self.have_tried:
            flags.append("tried")
        suffix = f" ({', '.join(flags)})" if flags else ""
        return f"{self.user.username} → {self.sponsor.organisation_name}{suffix}"

    def has_any_notes(self) -> bool:
        def nz(s: str | None) -> bool:
            return bool((s or "").strip())

        return nz(self.what_i_know) or nz(self.what_they_do) or nz(self.extra_notes)
