"""Diff uploaded Home Office–style xlsx against Sponsor rows; insert new; update changed fields."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.db import transaction

from companies.models import Sponsor

from xlsx_utils import iter_sponsor_records


def _norm(s: str | None) -> str:
    return (s or "").strip()


def _row_tuple(rec: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        _norm(rec.get("organisation_name")),
        _norm(rec.get("town_city")),
        _norm(rec.get("county")),
        _norm(rec.get("type_rating")),
        _norm(rec.get("route")),
    )


@dataclass
class RegisterSyncResult:
    added: int
    skipped_identical: int
    updated_rows: int
    excel_rows: int


def sync_register_from_xlsx(xlsx_path: str | Path) -> RegisterSyncResult:
    """
    Compare each spreadsheet row to the DB:
    - Exact match on all five fields → skip.
    - Same organisation + town + county as an existing row but type/route (or town/county text)
      differs → update matching Sponsor rows from the file row.
    - Otherwise → insert a new Sponsor.
    """
    path = Path(xlsx_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    existing_exact: set[tuple[str, str, str, str, str]] = set()
    for s in Sponsor.objects.iterator(chunk_size=5000):
        existing_exact.add(
            (
                _norm(s.organisation_name),
                _norm(s.town_city),
                _norm(s.county),
                _norm(s.type_rating),
                _norm(s.route),
            )
        )

    added = 0
    skipped_identical = 0
    updated_rows = 0
    excel_rows = 0
    batch: list[Sponsor] = []
    batch_size = 3000
    pending_keys: set[tuple[str, str, str, str, str]] = set()

    def flush_batch() -> None:
        nonlocal batch, added, pending_keys
        if not batch:
            return
        with transaction.atomic():
            Sponsor.objects.bulk_create(batch, batch_size=batch_size)
        for obj in batch:
            existing_exact.add(
                (
                    _norm(obj.organisation_name),
                    _norm(obj.town_city),
                    _norm(obj.county),
                    _norm(obj.type_rating),
                    _norm(obj.route),
                )
            )
        added += len(batch)
        batch.clear()
        pending_keys.clear()

    for rec in iter_sponsor_records(path):
        excel_rows += 1
        t = _row_tuple(rec)
        org, town, county, typ, route = t

        if t in existing_exact or t in pending_keys:
            skipped_identical += 1
            continue

        qs = Sponsor.objects.filter(
            organisation_name=org,
            town_city=town,
            county=county,
        )
        if qs.exists():
            old_tuples = [
                tuple(_norm(x) for x in row)
                for row in qs.values_list(
                    "organisation_name",
                    "town_city",
                    "county",
                    "type_rating",
                    "route",
                )
            ]
            with transaction.atomic():
                n = qs.update(
                    organisation_name=org,
                    town_city=town,
                    county=county,
                    type_rating=typ,
                    route=route,
                )
            for ot in old_tuples:
                existing_exact.discard(ot)
            existing_exact.add(t)
            updated_rows += n
            continue

        batch.append(
            Sponsor(
                organisation_name=org,
                town_city=town,
                county=county,
                type_rating=typ,
                route=route,
            )
        )
        pending_keys.add(t)
        if len(batch) >= batch_size:
            flush_batch()

    flush_batch()

    return RegisterSyncResult(
        added=added,
        skipped_identical=skipped_identical,
        updated_rows=updated_rows,
        excel_rows=excel_rows,
    )
