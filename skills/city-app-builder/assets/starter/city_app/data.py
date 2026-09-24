"""The prepared-data boundary. This module performs no network or database calls.

Everything the rest of the app knows about the data shape lives here:
the record fields, the ordered drill dimensions, the data states, the sort
orders, and the registry of data providers. Change a fact once, here.
"""

from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

# Ordered drill hierarchy and default display labels. A source may relabel a
# dimension (for example category -> "Department") through SourceInfo.labels;
# it must not rename the underlying Record fields.
DIMENSIONS = {"category": "Category", "area": "Area", "status": "Status"}

DataState = Literal["ready", "missing", "stale", "empty", "error", "loading"]
STATES: tuple[DataState, ...] = (
    "ready",
    "missing",
    "stale",
    "empty",
    "error",
    "loading",
)
# States that carry no current records. "stale" and "missing" keep records.
UNAVAILABLE_STATES = ("empty", "error", "loading")

# Sort orders offered to the user, with their labels.
ORDERS = {
    "newest": "Newest first",
    "oldest": "Oldest first",
    "value-high": "Highest value first",
    "value-low": "Lowest value first",
}

MISSING_LABEL = "Not recorded"
SAMPLE_DIR = Path(__file__).resolve().parents[1] / "samples"


@dataclass(frozen=True)
class Record:
    record_id: str
    date: date
    category: str
    area: str
    status: str
    value: float | None

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ValueError("Each record needs a nonempty ID.")
        if type(self.date) is not date:
            raise ValueError("Each record needs a calendar date.")
        for name in DIMENSIONS:
            if (
                not isinstance(getattr(self, name), str)
                or not getattr(self, name).strip()
            ):
                raise ValueError(f"Use '{MISSING_LABEL}' for a missing {name}.")
        if self.value is not None and (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(self.value)
        ):
            raise ValueError(
                "Values must be finite numbers or None, never missing-as-zero."
            )

    @property
    def month(self) -> str:
        """The record's month as YYYY-MM, the key used for month selection."""
        return month_key(self.date)


@dataclass(frozen=True)
class SourceInfo:
    name: str
    description: str
    value_label: str
    value_unit: str  # "USD" formats as currency; any other unit is shown as text
    aggregation: Literal["mean", "sum"]
    updated_at: date
    limitation: str
    is_sample: bool = True
    labels: Mapping[str, str] = field(default_factory=lambda: dict(DIMENSIONS))

    def __post_init__(self) -> None:
        if self.aggregation not in ("mean", "sum"):
            raise ValueError("The measure needs an explicit mean or sum aggregation.")
        if type(self.updated_at) is not date:
            raise ValueError("updated_at must be a calendar date.")
        unknown = set(self.labels) - set(DIMENSIONS)
        if unknown:
            raise ValueError(f"labels may only relabel {list(DIMENSIONS)}: {unknown}")

    def label(self, dimension: str) -> str:
        """Display label for a dimension key, falling back to the default."""
        return self.labels.get(dimension, DIMENSIONS[dimension])


@dataclass(frozen=True)
class Dataset:
    records: tuple[Record, ...]
    source: SourceInfo
    state: DataState = "ready"
    message: str = ""
    is_preview: bool = False

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"Unknown data state: {self.state}")
        ids = [row.record_id for row in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError(
                "Record IDs must be unique; do not silently double-count rows."
            )
        if self.state in UNAVAILABLE_STATES and self.records:
            raise ValueError(
                "Unavailable states cannot contain current records. Use stale for fallback data."
            )


# --- Bundled fictional samples -------------------------------------------------

SOURCES = {
    "services": SourceInfo(
        name="Fictional service requests",
        description="One row represents one invented service request. Dates are request-opened dates.",
        value_label="Mean days to close",
        value_unit="days",
        aggregation="mean",
        updated_at=date(2026, 7, 1),
        limitation="Days to close applies only to completed requests with a recorded duration. Open requests have no duration. This does not measure overdue work or an official service target.",
    ),
    "spending": SourceInfo(
        name="Fictional spending entries",
        description="One row represents one invented spending entry. Dates are posting dates.",
        value_label="Net recorded spending",
        value_unit="USD",
        aggregation="sum",
        updated_at=date(2026, 7, 1),
        limitation="Negative values are fictional credits. The net total includes credits and excludes missing amounts. These are not adopted budgets, actual City expenditures, or a complete ledger.",
    ),
}


@lru_cache(maxsize=None)
def _read_sample(name: str) -> tuple[Record, ...]:
    """Parse a bundled CSV once per process; records are immutable, so sharing is safe."""
    with (SAMPLE_DIR / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
        return tuple(
            Record(
                record_id=row["record_id"],
                date=date.fromisoformat(row["date"]),
                category=row["category"] or MISSING_LABEL,
                area=row["area"] or MISSING_LABEL,
                status=row["status"] or MISSING_LABEL,
                value=float(row["value"]) if row["value"] else None,
            )
            for row in csv.DictReader(stream)
        )


def load_sample(name: str = "services", state: DataState = "ready") -> Dataset:
    """Load a bundled example, optionally simulating a preview data condition."""
    if name not in SOURCES:
        raise ValueError("Choose the services or spending sample.")
    if state not in STATES:
        raise ValueError("Choose a supported preview condition.")
    if state in UNAVAILABLE_STATES:
        return Dataset((), SOURCES[name], state, is_preview=True)
    records = _read_sample(name)
    if state == "missing":
        records = tuple(
            replace(row, value=None, area=MISSING_LABEL) if index % 4 == 0 else row
            for index, row in enumerate(records)
        )
    return Dataset(records, SOURCES[name], state, is_preview=True)


# --- Provider registry: the connector seam --------------------------------------


@dataclass(frozen=True)
class Provider:
    """A named data source: static metadata plus a loader that returns a Dataset.

    To add a live connector, write a loader `def load(condition) -> Dataset` in a
    new module (fetch, validate, map columns into Record, set is_sample=False on
    its SourceInfo), then register it here:

        PROVIDERS["requests"] = Provider(REQUESTS_SOURCE, load_requests)

    and set "sample": "requests" in app_config.json. The loader receives the
    preview condition; a live loader may ignore it and report its real state.
    """

    source: SourceInfo
    load: Callable[[DataState], Dataset]


def _sample_provider(name: str) -> Provider:
    return Provider(SOURCES[name], lambda condition: load_sample(name, condition))


PROVIDERS: dict[str, Provider] = {name: _sample_provider(name) for name in SOURCES}


def load_dataset(name: str, condition: DataState = "ready") -> Dataset:
    """Single entry point used by the app. Dispatches to the registered provider."""
    if name not in PROVIDERS:
        raise ValueError(
            f"Unknown data source '{name}'. Registered sources: {', '.join(PROVIDERS)}."
        )
    if condition not in STATES:
        raise ValueError("Choose a supported preview condition.")
    return PROVIDERS[name].load(condition)


# --- Pure operations on prepared records -----------------------------------------


def month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def month_label(key: str) -> str:
    return date(int(key[:4]), int(key[5:7]), 1).strftime("%b %Y")


def monthly_groups(
    records: tuple[Record, ...],
) -> list[tuple[str, str, tuple[Record, ...]]]:
    """Records grouped by month from first to last, keeping zero-record months.

    Returns (label, key, records) triples such as ("Jan 2026", "2026-01", (...)).
    """
    if not records:
        return []
    groups: dict[str, list[Record]] = defaultdict(list)
    for row in records:
        groups[row.month].append(row)
    first, last = min(groups), max(groups)
    year, month = int(first[:4]), int(first[5:7])
    result = []
    while (key := f"{year:04d}-{month:02d}") <= last:
        result.append((month_label(key), key, tuple(groups.get(key, ()))))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return result


def filter_records(
    records: tuple[Record, ...],
    *,
    category: str = "",
    area: str = "",
    status: str = "",
    month: str = "",
    query: str = "",
    order: str = "newest",
) -> tuple[Record, ...]:
    """Apply every selection in one pass, then sort. Empty strings mean no constraint."""
    if order not in ORDERS:
        raise ValueError(f"Unknown order '{order}'. Choose one of {list(ORDERS)}.")
    wanted = {"category": category, "area": area, "status": status}
    query = query.strip().casefold()
    selected = [
        row
        for row in records
        if all(not value or getattr(row, key) == value for key, value in wanted.items())
        and (not month or row.month == month)
        and (not query or query in _searchable(row))
    ]
    if order in ("value-high", "value-low"):
        sign = -1 if order == "value-high" else 1
        return tuple(
            sorted(
                selected,
                key=lambda row: (
                    row.value is None,
                    sign * (row.value or 0),
                    row.record_id,
                ),
            )
        )
    return tuple(
        sorted(
            selected,
            key=lambda row: (row.date, row.record_id),
            reverse=order == "newest",
        )
    )


def _searchable(row: Record) -> str:
    return " ".join(
        (row.record_id, row.category, row.area, row.status, row.date.isoformat())
    ).casefold()


def measure(
    records: tuple[Record, ...], source: SourceInfo
) -> tuple[float | None, int]:
    """The source's mean or sum over recorded values, with the contributor count."""
    values = [row.value for row in records if row.value is not None]
    if not values:
        return None, 0
    total = math.fsum(values)
    return (total / len(values) if source.aggregation == "mean" else total), len(values)


def format_value(value: float | None, unit: str) -> str:
    if value is None:
        return MISSING_LABEL
    if unit == "USD":
        return f"{'−' if value < 0 else ''}${abs(value):,.2f}"
    return f"{value:,.1f} {unit}"


def _safe_text(value: str) -> str:
    # Prevent text fields being interpreted as spreadsheet formulas on export.
    if value.startswith(("\t", "\r", "\n")) or value.lstrip().startswith(
        ("=", "+", "-", "@")
    ):
        return "'" + value
    return value


def export_csv(records: tuple[Record, ...], source: SourceInfo) -> str:
    """CSV with stable internal column names and a data-kind label on every row."""
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(
        ("data_kind", "source", "record_id", "date", *DIMENSIONS, "value", "unit")
    )
    for row in records:
        writer.writerow(
            (
                "FICTIONAL SAMPLE" if source.is_sample else "DATA",
                _safe_text(source.name),
                _safe_text(row.record_id),
                row.date.isoformat(),
                *[_safe_text(getattr(row, key)) for key in DIMENSIONS],
                row.value if row.value is not None else "",
                _safe_text(source.value_unit),
            )
        )
    return stream.getvalue()
