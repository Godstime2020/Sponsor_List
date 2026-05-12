"""Read sponsor rows from the Home Office Worker / Temporary Worker xlsx (stdlib only)."""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NS_REL = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}


def col_ref_to_index(cell_ref: str) -> tuple[int, int]:
    m = re.match(r"^([A-Z]+)(\d+)$", cell_ref)
    if not m:
        return 0, 0
    letters, row_s = m.group(1), m.group(2)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1, int(row_s)


def load_shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    out: list[str] = []
    for si in root.findall(".//main:si", NS):
        parts: list[str] = []
        for t in si.findall(".//main:t", NS):
            if t.text:
                parts.append(t.text)
        out.append("".join(parts))
    return out


def first_sheet_path(z: zipfile.ZipFile) -> str:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    sheets = wb.findall(".//main:sheet", NS)
    if not sheets:
        raise RuntimeError("No sheets in workbook")
    rid = sheets[0].get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = None
    for rel in rels.findall(".//r:Relationship", NS_REL):
        if rel.get("Id") == rid:
            target = rel.get("Target")
            break
    if not target:
        raise RuntimeError("Could not resolve first sheet path")
    target = target.replace("xl/", "").lstrip("/")
    return "xl/" + target


def cell_text(c: ET.Element, shared: list[str]) -> str:
    t = c.get("t")
    v = c.find("main:v", NS)
    if v is not None and v.text is not None:
        if t == "s":
            return shared[int(v.text)]
        return v.text
    is_elem = c.find("main:is", NS)
    if is_elem is not None:
        return "".join((t.text or "") for t in is_elem.findall(".//main:t", NS))
    return ""


def iter_sheet_rows(z: zipfile.ZipFile, sheet_path: str, shared: list[str]):
    sheet = ET.fromstring(z.read(sheet_path))
    for row in sheet.findall(".//main:sheetData/main:row", NS):
        cells: dict[int, str] = {}
        for c in row.findall("main:c", NS):
            ref = c.get("r")
            if not ref:
                continue
            ci, _ = col_ref_to_index(ref)
            cells[ci] = cell_text(c, shared).strip()
        if not cells:
            continue
        width = max(cells) + 1
        yield [cells.get(i, "") for i in range(width)]


def iter_sponsor_records(xlsx_path: str | Path) -> Iterator[dict[str, str]]:
    """
    Yield one dict per data row (after header). Keys: organisation_name, town_city,
    county, type_rating, route.
    """
    path = Path(xlsx_path)
    with zipfile.ZipFile(path, "r") as z:
        shared = load_shared_strings(z)
        sheet_path = first_sheet_path(z)
        it = iter_sheet_rows(z, sheet_path, shared)
        header = next(it, None)
        if not header:
            return
        expected = ["Organisation Name", "Town/City", "County", "Type & Rating", "Route"]
        if [h.strip() for h in header[:5]] != expected:
            pass
        for row in it:
            while len(row) < 5:
                row.append("")
            org, town, county, typ, route = row[0], row[1], row[2], row[3], row[4]
            if county.upper() == "NULL":
                county = ""
            yield {
                "organisation_name": org,
                "town_city": town,
                "county": county,
                "type_rating": typ,
                "route": route,
            }
