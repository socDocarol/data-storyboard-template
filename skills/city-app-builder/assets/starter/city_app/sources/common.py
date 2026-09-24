"""Shared validation for the small prepared-record contract."""

from __future__ import annotations

import math
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Mapping

from city_app.data import DIMENSIONS, MISSING_LABEL, Record, SourceInfo

FIELDS = ("record_id", "date", *DIMENSIONS, "value")
MAX_ROWS = 10_000
MAX_BYTES = 10_000_000


class SourceError(ValueError):
    """An actionable message that contains no source values or credentials."""


def row_limit(config: dict) -> int:
    value = config.get("max_rows", MAX_ROWS)
    if type(value) is not int or not 1 <= value <= MAX_ROWS:
        raise SourceError(f"max_rows must be between 1 and {MAX_ROWS}.")
    return value


def source_info(config: dict) -> SourceInfo:
    raw = config.get("source", {})
    if not isinstance(raw, dict):
        raise SourceError("source must be an object describing the data's meaning.")
    for key in ("name", "description", "value_label", "value_unit", "limitation"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise SourceError(f"source.{key} needs a nonempty description.")
    if type(raw.get("is_sample")) is not bool:
        raise SourceError("source.is_sample must explicitly be true or false.")
    try:
        snapshot = (
            date.fromisoformat(raw["updated_at"])
            if raw.get("updated_at")
            else date.today()
        )
        labels = raw.get("labels", {})
        if not isinstance(labels, dict) or any(
            not isinstance(v, str) or not v.strip() for v in labels.values()
        ):
            raise ValueError
        return SourceInfo(
            **{
                key: raw[key]
                for key in (
                    "name",
                    "description",
                    "value_label",
                    "value_unit",
                    "limitation",
                    "is_sample",
                )
            },
            aggregation=raw.get("aggregation"),
            updated_at=snapshot,
            labels=labels,
        )
    except (ValueError, TypeError, KeyError) as error:
        raise SourceError(
            "Check source aggregation (mean/sum), labels, and updated_at (YYYY-MM-DD)."
        ) from error


def validate_mapping(config: dict) -> dict:
    columns = config.get("columns")
    if not isinstance(columns, dict) or set(columns) != set(FIELDS):
        raise SourceError(
            "columns must map record_id, date, category, area, status, and value."
        )
    mode = config.get("value_mode", "column")
    if mode not in ("column", "count"):
        raise SourceError("value_mode must be column or count.")
    if mode == "count" and (
        columns["value"] is not None
        or config.get("source", {}).get("aggregation") != "sum"
    ):
        raise SourceError(
            "Row-count measures require columns.value null and source.aggregation sum."
        )
    for key, value in columns.items():
        if value is None and key not in ("record_id", "date"):
            continue
        if not isinstance(value, str) or not value.strip():
            raise SourceError(
                f"columns.{key} must name a column, or null for an optional field."
            )
    if config.get("date_format", "iso") not in ("iso", "unix_ms") and not isinstance(
        config.get("date_format"), str
    ):
        raise SourceError("date_format must be iso, unix_ms, or a strptime format.")
    row_limit(config)
    return columns


def calendar_date(value, format: str = "iso") -> date:
    if isinstance(value, datetime):
        return value.date()
    if type(value) is date:
        return value
    if format == "unix_ms":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError
        return datetime.fromtimestamp(value / 1000, timezone.utc).date()
    if not isinstance(value, str) or not value.strip():
        raise ValueError
    value = value.strip()
    if format == "iso":
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    return datetime.strptime(value, format).date()


def map_records(rows, config: dict) -> tuple[Record, ...]:
    columns = validate_mapping(config)
    result = []
    ids = set()
    for number, row in enumerate(rows, 1):
        if number > row_limit(config):
            raise SourceError(
                "The source exceeds max_rows. Narrow the source query or file; no partial totals were loaded."
            )
        if not isinstance(row, Mapping):
            raise SourceError(f"Row {number} must be a record object.")
        if any(column is not None and column not in row for column in columns.values()):
            raise SourceError(
                f"Row {number} is missing a mapped column. Check the field mapping."
            )
        values = {
            key: row[column] if column is not None else None
            for key, column in columns.items()
        }
        try:
            identifier = values["record_id"]
            if isinstance(identifier, bool) or not isinstance(identifier, (str, int)):
                raise ValueError
            identifier = str(identifier).strip()
            labels = {}
            for key in DIMENSIONS:
                value = values[key]
                if isinstance(value, (dict, list, bool)):
                    raise ValueError
                labels[key] = str(value).strip() if value is not None else MISSING_LABEL
                labels[key] = labels[key] or MISSING_LABEL
            value = 1 if config.get("value_mode") == "count" else values["value"]
            if value is None or (isinstance(value, str) and not value.strip()):
                value = None
            elif isinstance(value, bool) or not isinstance(
                value, (str, int, float, Decimal)
            ):
                raise ValueError
            else:
                value = float(value)
                if not math.isfinite(value):
                    raise ValueError
            result.append(
                Record(
                    identifier,
                    calendar_date(values["date"], config.get("date_format", "iso")),
                    **labels,
                    value=value,
                )
            )
        except (ValueError, TypeError, OverflowError, OSError) as error:
            raise SourceError(
                f"Row {number} has an invalid ID, date, grouping label, or numeric value. No rows were loaded."
            ) from error
        if identifier in ids:
            raise SourceError(f"Row {number} repeats a record ID. No rows were loaded.")
        ids.add(identifier)
    return tuple(result)
