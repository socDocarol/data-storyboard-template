"""Inspect, check, and activate a source without changing the dashboard design."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from city_app.sources import arcgis, local, sql_server
from city_app.sources.common import SourceError
from city_app.sources.configured import ConfiguredSource, read_config

ROOT = Path(__file__).resolve().parent


def activate(root: Path, config: dict) -> None:
    """Save only after a successful check; original sample configs stay available."""
    app_path = root / "app_config.json"
    app_config = json.loads(app_path.read_text(encoding="utf-8"))
    app_config.update(
        sample="connected",
        show_preview_controls=False,
        description=config["source"]["description"],
    )
    (root / "data_source.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    app_path.write_text(
        json.dumps(app_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def prepare_example(root: Path, name: str) -> dict:
    config = read_config(root / "examples" / f"{name}.json")
    if name in ("local-csv", "local-xlsx"):
        target = local.local_path(root, config["path"])
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            raise SourceError(
                "The example data file already exists. Use check/activate with its example JSON, or choose a fresh app folder."
            )
        source = root / "samples/services.csv"
        if name == "local-csv":
            target.write_bytes(source.read_bytes())
        else:
            from openpyxl import Workbook

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Requests"
            with source.open(encoding="utf-8", newline="") as stream:
                for row in csv.reader(stream):
                    worksheet.append(row)
            workbook.save(target)
            workbook.close()
    return config


def inspect_file(root: Path, name: str, sheet: str | None = None) -> dict:
    """Return structure only, bounded to 100 rows and 1 MB (no source values)."""
    path = local.local_path(root, name)
    if path.stat().st_size > 1_000_000:
        raise SourceError(
            "Inspection is limited to 1 MB. Supply a smaller sample; the connector itself accepts up to 10 MB."
        )
    # The local reader enforces shape and XLSX safety; only the first 100 rows are inspected.
    from itertools import islice

    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames or []
            rows = list(islice(reader, 100))
        sheets = None
    else:
        from openpyxl import load_workbook
        import zipfile

        with zipfile.ZipFile(path) as archive:
            if sum(item.file_size for item in archive.infolist()) > 5_000_000:
                raise SourceError(
                    "The expanded inspection sample exceeds 5 MB. Supply a smaller workbook."
                )
        workbook = load_workbook(
            path, read_only=True, data_only=False, keep_links=False
        )
        try:
            sheets = workbook.sheetnames
            if sheet is None and len(sheets) != 1:
                return {
                    "sheets": sheets,
                    "next_step": "Choose the relevant sheet before inspecting rows.",
                }
            if sheet is not None and sheet not in sheets:
                raise SourceError("The selected sheet does not exist.")
            worksheet = workbook[sheet or sheets[0]]
            worksheet.reset_dimensions()
            iterator = worksheet.iter_rows(values_only=True)
            fields = list(next(iterator, []))
            rows = [dict(zip(fields, values)) for values in islice(iterator, 100)]
        finally:
            workbook.close()
    return {
        "scope": "Structure from at most 100 rows; not a whole-dataset audit",
        "sheets": sheets,
        "rows_inspected": len(rows),
        "columns": [
            {
                "field": str(field)[:120],
                "missing_in_sample": sum(row.get(field) in (None, "") for row in rows),
                "types": sorted({type(row.get(field)).__name__ for row in rows}),
            }
            for field in fields[:40]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "activate", "doctor"):
        commands.add_parser(name).add_argument("config", type=Path)
    example = commands.add_parser("example")
    example.add_argument(
        "name", choices=("local-csv", "local-xlsx", "http-api", "sacramento")
    )
    inspect = commands.add_parser("inspect")
    inspect.add_argument("file", help="CSV/XLSX file relative to Data")
    inspect.add_argument("--sheet")
    metadata = commands.add_parser("arcgis-info")
    metadata.add_argument("url")
    metadata.add_argument("--layer-id", type=int)
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            print(json.dumps(inspect_file(ROOT, args.file, args.sheet), indent=2))
            return
        if args.command == "arcgis-info":
            print(
                json.dumps(
                    arcgis.inspect_layer({"url": args.url, "layer_id": args.layer_id}),
                    indent=2,
                )
            )
            return
        config = (
            prepare_example(ROOT, args.name)
            if args.command == "example"
            else read_config(args.config)
        )
        if args.command == "doctor":
            if config["kind"] != "sql-server":
                raise SourceError("doctor is the offline SQL Server preparation check.")
            print(json.dumps(sql_server.doctor(config), indent=2))
            return
        dataset = ConfiguredSource(ROOT, config).fetch()
        print(
            json.dumps(
                {
                    "state": dataset.state,
                    "records": len(dataset.records),
                    "source": dataset.source.name,
                    "is_sample": dataset.source.is_sample,
                    "snapshot": dataset.source.updated_at.isoformat(),
                },
                indent=2,
            )
        )
        if args.command in ("activate", "example"):
            activate(ROOT, config)
            print(
                "Source activated. Restart the app to open this snapshot. Source definitions are in About."
            )
    except (SourceError, OSError, ValueError) as error:
        message = (
            str(error)
            if isinstance(error, SourceError)
            else "Could not inspect or configure this source. Check the file, format, and permissions."
        )
        parser.exit(1, f"Source not activated: {message}\n")


if __name__ == "__main__":
    main()
