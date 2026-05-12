from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from companies.models import Sponsor

from xlsx_utils import iter_sponsor_records


class Command(BaseCommand):
    help = "Import sponsors from the configured XLSX file into the Sponsor table."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all Sponsor rows before import.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Import at most N rows (for testing).",
        )

    def handle(self, *args, **options) -> None:
        path = settings.SPONSOR_XLSX
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"Missing file: {path}"))
            return

        clear: bool = options["clear"]
        limit: int | None = options["limit"]

        if clear:
            deleted, _ = Sponsor.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} sponsor rows."))

        batch: list[Sponsor] = []
        batch_size = 3000
        total = 0
        imported = 0

        for rec in iter_sponsor_records(path):
            if limit is not None and imported >= limit:
                break
            batch.append(
                Sponsor(
                    organisation_name=rec["organisation_name"],
                    town_city=rec["town_city"],
                    county=rec["county"],
                    type_rating=rec["type_rating"],
                    route=rec["route"],
                )
            )
            imported += 1
            if len(batch) >= batch_size:
                with transaction.atomic():
                    Sponsor.objects.bulk_create(batch, batch_size=batch_size)
                total += len(batch)
                self.stdout.write(f"Imported {total}…")
                batch.clear()

        if batch:
            with transaction.atomic():
                Sponsor.objects.bulk_create(batch, batch_size=batch_size)
            total += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Done. Imported in this run: {total}."))
        self.stdout.write(f"Database total: {Sponsor.objects.count()}.")
