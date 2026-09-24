"""Bounded, read-only CSV/JSON inspection; no connector or application import."""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

MAX_BYTES = 1_000_000
MAX_ROWS = 100
MAX_FIELDS = 40
TIMEOUT = 8


def kind(value):
    if value is None or value == "":
        return "missing"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (dict, list)):
        return "nested"
    try:
        date.fromisoformat(str(value))
        return "date-like"
    except ValueError:
        pass
    try:
        float(value)
        return "number-like"
    except (ValueError, TypeError):
        return "text"


def inspect(path: Path) -> dict:
    if str(path).startswith(("\\\\", "//")) or path.suffix.lower() not in (
        ".csv",
        ".json",
    ):
        raise ValueError(
            "Provide a local CSV or JSON example, not a URL, network share, or spreadsheet."
        )
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError(
            "This file exceeds the 1 MB inspection budget. Provide a smaller sample; do not retry with a larger limit."
        )
    text = raw.decode("utf-8-sig")
    if path.suffix.lower() == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        all_fields = reader.fieldnames or []
        rows = []
        for index, row in enumerate(reader):
            if index == MAX_ROWS:
                break
            if None in row:
                raise ValueError(
                    "The CSV has more values than headers. Provide a corrected small sample."
                )
            rows.append(row)
    else:
        payload = json.loads(text)
        if not isinstance(payload, list) or any(
            not isinstance(row, dict) for row in payload[:MAX_ROWS]
        ):
            raise ValueError(
                "JSON must be an array of record objects; nested API responses are deferred."
            )
        rows = payload[:MAX_ROWS]
        all_fields = list(dict.fromkeys(key for row in rows for key in row))
    fields = all_fields[:MAX_FIELDS]
    columns = []
    for field in fields:
        values = [row.get(field) for row in rows]
        # Inspect structure without echoing example values that could contain personal information.
        columns.append(
            {
                "field": str(field)[:120],
                "observed_types": sorted({kind(value) for value in values}),
                "missing_in_sample": sum(kind(value) == "missing" for value in values),
            }
        )
    return {
        "scope": "Partial sample only; no whole-dataset claims",
        "rows_inspected": len(rows),
        "bytes_read": len(raw),
        "fields_omitted": max(0, len(all_fields) - MAX_FIELDS),
        "columns": columns,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        try:
            print(json.dumps(inspect(args.path), ensure_ascii=True))
        except (OSError, ValueError, csv.Error) as error:
            print(
                json.dumps(
                    {
                        "error": str(error),
                        "next_step": "Use the fictional example or supply a small corrected local sample.",
                    }
                )
            )
            sys.exit(1)
        return
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), str(args.path), "--worker"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        print(
            json.dumps(
                {
                    "error": "Inspection stopped at the 8-second budget. Continue with a fictional example."
                }
            )
        )
        sys.exit(1)
    print(result.stdout.strip())
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
