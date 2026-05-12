#!/usr/bin/env python3
"""
Convert the Worker and Temporary Worker sponsor xlsx into a SQLite database.
Uses only the Python standard library (sqlite3 + xlsx_utils).
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from xlsx_utils import iter_sponsor_records  # noqa: E402


def main() -> int:
    xlsx = ROOT / "Companies_With_COS.xlsx"
    out_db = ROOT / "public" / "sponsors.db"

    if not xlsx.is_file():
        print(f"Missing xlsx: {xlsx}", file=sys.stderr)
        return 1

    out_db.parent.mkdir(parents=True, exist_ok=True)
    if out_db.is_file():
        out_db.unlink()

    conn = sqlite3.connect(out_db)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE sponsors (
            id INTEGER PRIMARY KEY,
            organisation_name TEXT NOT NULL,
            town_city TEXT,
            county TEXT,
            type_rating TEXT,
            route TEXT
        );
        """
    )
    cur.execute(
        "CREATE INDEX idx_sponsors_org ON sponsors (organisation_name COLLATE NOCASE);"
    )
    cur.execute(
        "CREATE INDEX idx_sponsors_town ON sponsors (town_city COLLATE NOCASE);"
    )
    cur.execute("CREATE INDEX idx_sponsors_county ON sponsors (county COLLATE NOCASE);")

    batch: list[tuple[str, str, str, str, str]] = []
    BATCH = 5000

    for rec in iter_sponsor_records(xlsx):
        batch.append(
            (
                rec["organisation_name"],
                rec["town_city"],
                rec["county"],
                rec["type_rating"],
                rec["route"],
            )
        )
        if len(batch) >= BATCH:
            cur.executemany(
                "INSERT INTO sponsors (organisation_name, town_city, county, type_rating, route) VALUES (?,?,?,?,?)",
                batch,
            )
            batch.clear()
            conn.commit()
    if batch:
        cur.executemany(
            "INSERT INTO sponsors (organisation_name, town_city, county, type_rating, route) VALUES (?,?,?,?,?)",
            batch,
        )
        batch.clear()

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM sponsors")
    (total,) = cur.fetchone()
    conn.execute("ANALYZE sponsors;")
    conn.close()

    print(f"Wrote {out_db} with {total} rows ({out_db.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
