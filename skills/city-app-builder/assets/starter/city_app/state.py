"""Bookmarkable dashboard selection and pure analytical operations."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, replace
from urllib.parse import urlencode

from city_app.data import (
    DIMENSIONS,
    ORDERS,
    PROVIDERS,
    STATES,
    Record,
    SourceInfo,
    filter_records,
    measure,
    monthly_groups,
)

PAGES = ("home", "explore", "compare", "about")
# Selection keys shown as removable chips, in display order, with labels.
FILTER_KEYS = (*DIMENSIONS, "month", "query")
FILTER_LABELS = {"month": "Month", "query": "Search"}


@dataclass(frozen=True)
class ViewState:
    """The single server-side selection. Every page, chart, table, and export uses it."""

    sample: str = "services"
    condition: str = "ready"
    category: str = ""
    area: str = ""
    status: str = ""
    month: str = ""
    query: str = ""
    order: str = "newest"
    compare_by: str = "category"
    left: str = ""
    right: str = ""
    record: str = ""

    @classmethod
    def from_payload(
        cls, payload: dict | None, default_sample: str = "services"
    ) -> ViewState:
        """Build a bounded, valid state from untrusted browser input."""
        payload = payload if isinstance(payload, dict) else {}
        values = {
            key: str(payload.get(key, default))[:160]
            for key, default in asdict(cls(sample=default_sample)).items()
        }
        if values["sample"] not in PROVIDERS:
            values["sample"] = default_sample
        if values["condition"] not in STATES:
            values["condition"] = "ready"
        if values["order"] not in ORDERS:
            values["order"] = "newest"
        if values["compare_by"] not in DIMENSIONS:
            values["compare_by"] = "category"
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", values["month"]):
            values["month"] = ""
        return cls(**values)

    def href(self, page: str = "home", **changes) -> str:
        """Encode this state (with changes) into a fragment link."""
        if page not in PAGES:
            raise ValueError("Unknown dashboard page.")
        updated = replace(self, **changes)
        defaults = asdict(ViewState())
        parameters = {
            key: value
            for key, value in asdict(updated).items()
            if value and (key == "sample" or value != defaults[key])
        }
        return f"#{page}?{urlencode(parameters)}"

    def clear(self) -> ViewState:
        """Remove every filter and the open record; keep the source, order, and comparison."""
        return replace(self, record="", **{key: "" for key in FILTER_KEYS})

    def without_record(self) -> ViewState:
        return replace(self, record="") if self.record else self

    def filters(
        self, *, labels: dict[str, str] | None = None
    ) -> list[tuple[str, str, str]]:
        """Active filters as (key, label, value) in display order."""
        labels = {**DIMENSIONS, **(labels or {}), **FILTER_LABELS}
        return [
            (key, labels[key], getattr(self, key))
            for key in FILTER_KEYS
            if getattr(self, key)
        ]

    def select(
        self, records: tuple[Record, ...], *, omit: str = ""
    ) -> tuple[Record, ...]:
        """The records this state selects. `omit` ignores one dimension (for comparisons)."""
        return filter_records(
            records,
            **{key: "" if key == omit else getattr(self, key) for key in DIMENSIONS},
            month=self.month,
            query=self.query,
            order=self.order,
        )

    def next_dimension(self) -> str | None:
        """The first unselected drill level, or None when the records are reached."""
        return next((key for key in DIMENSIONS if not getattr(self, key)), None)

    def drill(self, dimension: str, value: str) -> ViewState:
        """Select one level and clear every deeper level and the open record."""
        if dimension not in DIMENSIONS:
            raise ValueError("Only declared dimensions can be drilled.")
        keys = list(DIMENSIONS)
        changes = {deeper: "" for deeper in keys[keys.index(dimension) + 1 :]}
        return replace(self, record="", **{dimension: value}, **changes)


def grouped_counts(
    records: tuple[Record, ...], dimension: str
) -> list[tuple[str, int]]:
    """Record counts per group, largest first, ties alphabetical."""
    if dimension not in DIMENSIONS:
        raise ValueError("Unknown dimension.")
    return sorted(
        Counter(getattr(row, dimension) for row in records).items(),
        key=lambda entry: (-entry[1], entry[0]),
    )


@dataclass(frozen=True)
class GroupSummary:
    label: str
    records: int
    value: float | None
    contributors: int


@dataclass(frozen=True)
class Comparison:
    left: GroupSummary
    right: GroupSummary
    delta: float | None  # B − A
    percent: float | None  # (B − A) / |A| × 100; None when undefined


def compare_groups(
    records: tuple[Record, ...],
    source: SourceInfo,
    dimension: str,
    left: str,
    right: str,
) -> Comparison:
    """Each group's measure from its own contributors; never an average of averages."""
    if dimension not in DIMENSIONS:
        raise ValueError("Unknown comparison dimension.")

    def summary(label: str) -> GroupSummary:
        group = tuple(row for row in records if getattr(row, dimension) == label)
        value, contributors = measure(group, source)
        return GroupSummary(label, len(group), value, contributors)

    a, b = summary(left), summary(right)
    delta = b.value - a.value if a.value is not None and b.value is not None else None
    percent = delta / abs(a.value) * 100 if delta is not None and a.value else None
    return Comparison(a, b, delta, percent)


def compare_months(
    records: tuple[Record, ...], dimension: str, left: str, right: str
) -> list[tuple[str, int, int]]:
    """Monthly record counts for both groups over the months either group spans."""
    if dimension not in DIMENSIONS:
        raise ValueError("Unknown comparison dimension.")
    involved = tuple(row for row in records if getattr(row, dimension) in (left, right))
    return [
        (
            label,
            sum(getattr(row, dimension) == left for row in rows),
            sum(getattr(row, dimension) == right for row in rows),
        )
        for label, _, rows in monthly_groups(involved)
    ]
