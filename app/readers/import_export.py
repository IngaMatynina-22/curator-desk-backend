"""Low-level export helpers (CSV / Excel / PDF)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Sequence

from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_csv(path: Path, headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(list(headers))
        for row in rows:
            writer.writerow(list(row))
            count += 1
    return count


def export_xlsx(path: Path, headers: Sequence[str], rows: Iterable[Sequence[Any]], sheet_name: str = "Report") -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(list(headers))
    count = 0
    for row in rows:
        ws.append(list(row))
        count += 1
    wb.save(path)
    return count


def read_tabular(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Read CSV or XLSX into (headers, list of row dicts)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            headers = list(reader.fieldnames or [])
            rows = [dict(row) for row in reader]
            return headers, rows
    if suffix in {".xlsx", ".xlsm"}:
        from openpyxl import load_workbook

        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        raw = list(ws.iter_rows(values_only=True))
        if not raw:
            return [], []
        headers = [str(h).strip() if h is not None else "" for h in raw[0]]
        rows = []
        for values in raw[1:]:
            row = {
                headers[i]: ("" if values[i] is None else str(values[i]).strip())
                for i in range(len(headers))
                if headers[i]
            }
            if any(row.values()):
                rows.append(row)
        return headers, rows
    raise ValueError(f"unsupported import format: {suffix}")


def export_pdf(path: Path, title: str, lines: Sequence[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, title[:90])
    y -= 24
    c.setFont("Helvetica", 10)
    count = 0
    for line in lines:
        if y < 40:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 40
        c.drawString(40, y, line[:110])
        y -= 14
        count += 1
    c.save()
    return count
