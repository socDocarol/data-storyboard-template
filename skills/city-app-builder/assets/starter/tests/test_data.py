"""Portable correctness checks: run python -m unittest discover -s tests -v."""

import csv
import io
import unittest
from dataclasses import replace
from datetime import date

from city_app.data import (
    DIMENSIONS,
    PROVIDERS,
    Dataset,
    Provider,
    Record,
    export_csv,
    filter_records,
    format_value,
    load_dataset,
    load_sample,
    measure,
    monthly_groups,
)


class DataTests(unittest.TestCase):
    def setUp(self):
        self.services = load_sample("services")
        self.spending = load_sample("spending")

    def test_samples_have_distinct_ids_and_truthful_metadata(self):
        for sample in (self.services, self.spending):
            self.assertEqual(len(sample.records), 48)
            self.assertEqual(len({r.record_id for r in sample.records}), 48)
            self.assertTrue(sample.source.is_sample)

    def test_service_mean_excludes_open_requests(self):
        value, count = measure(self.services.records, self.services.source)
        self.assertEqual(count, 36)
        self.assertAlmostEqual(value, 338 / 36)
        self.assertTrue(
            all(
                row.value is None
                for row in self.services.records
                if row.status == "Open"
            )
        )

    def test_spending_total_includes_negative_credits(self):
        value, count = measure(self.spending.records, self.spending.source)
        self.assertEqual(count, 48)
        self.assertEqual(value, 851949)
        self.assertEqual(
            sum(r.value for r in self.spending.records if r.value < 0), -26250
        )

    def test_missing_values_are_not_zero(self):
        rows = tuple(replace(row, value=None) for row in self.spending.records)
        self.assertEqual(measure(rows, self.spending.source), (None, 0))
        self.assertEqual(format_value(None, "USD"), "Not recorded")
        self.assertEqual(format_value(0, "USD"), "$0.00")

    def test_format_value_handles_any_unit(self):
        self.assertEqual(format_value(-1234.5, "USD"), "−$1,234.50")
        self.assertEqual(format_value(9.44, "days"), "9.4 days")
        self.assertEqual(format_value(1500, "hours"), "1,500.0 hours")

    def test_missing_preview_retains_rows(self):
        missing = load_sample("spending", "missing")
        self.assertEqual(len(missing.records), 48)
        self.assertEqual(sum(r.value is None for r in missing.records), 12)
        self.assertEqual(sum(r.area == "Not recorded" for r in missing.records), 12)
        # The cached base sample is never mutated by a simulated condition.
        self.assertEqual(load_sample("spending").records, self.spending.records)

    def test_stale_preview_retains_snapshot(self):
        stale = load_sample("services", "stale")
        self.assertEqual(stale.records, self.services.records)
        self.assertEqual(stale.state, "stale")
        self.assertEqual(stale.source.updated_at, self.services.source.updated_at)

    def test_unavailable_states_have_no_rows(self):
        for state in ("empty", "error", "loading"):
            self.assertEqual(load_sample("services", state).records, ())
            with self.assertRaises(ValueError):
                Dataset(self.services.records, self.services.source, state)

    def test_filter_intersection_and_case_insensitive_search(self):
        rows = filter_records(
            self.services.records,
            category="Street maintenance",
            area="North",
            query="COMPLETED",
        )
        self.assertTrue(rows)
        self.assertTrue(
            all(
                r.category == "Street maintenance"
                and r.area == "North"
                and r.status == "Completed"
                for r in rows
            )
        )
        self.assertEqual(
            filter_records(self.services.records, query="does not exist"), ()
        )

    def test_filter_applies_status_and_month_directly(self):
        rows = filter_records(self.services.records, status="Open", month="2026-01")
        self.assertTrue(rows)
        self.assertTrue(all(r.status == "Open" and r.month == "2026-01" for r in rows))
        with self.assertRaises(ValueError):
            filter_records(self.services.records, order="random")

    def test_ordering_handles_negative_and_missing_values(self):
        rows = (
            replace(self.spending.records[0], value=None),
            *self.spending.records[1:],
        )
        low = filter_records(rows, order="value-low")
        high = filter_records(rows, order="value-high")
        self.assertLess(low[0].value, 0)
        self.assertIsNone(low[-1].value)
        self.assertIsNone(high[-1].value)
        self.assertEqual(
            [r.value for r in high[:-1]],
            sorted((r.value for r in rows if r.value is not None), reverse=True),
        )
        newest = filter_records(rows, order="newest")
        self.assertEqual(newest[0].date, max(r.date for r in rows))

    def test_monthly_groups_keep_zero_months(self):
        record = self.services.records[0]
        rows = (
            replace(record, date=date(2026, 1, 1)),
            replace(record, record_id="second", date=date(2026, 3, 1)),
        )
        groups = monthly_groups(rows)
        self.assertEqual(
            [(label, key, len(group)) for label, key, group in groups],
            [
                ("Jan 2026", "2026-01", 1),
                ("Feb 2026", "2026-02", 0),
                ("Mar 2026", "2026-03", 1),
            ],
        )
        self.assertEqual(monthly_groups(()), [])
        # Year boundaries roll over correctly.
        rows = (
            replace(record, date=date(2025, 12, 15)),
            replace(record, record_id="second", date=date(2026, 1, 2)),
        )
        self.assertEqual(
            [key for _, key, _ in monthly_groups(rows)], ["2025-12", "2026-01"]
        )

    def test_csv_matches_filtered_order_and_labels_every_record(self):
        rows = filter_records(self.services.records, area="North", order="oldest")
        exported = list(
            csv.DictReader(io.StringIO(export_csv(rows, self.services.source)))
        )
        self.assertEqual(
            [r["record_id"] for r in exported], [r.record_id for r in rows]
        )
        self.assertTrue(all(r["data_kind"] == "FICTIONAL SAMPLE" for r in exported))
        self.assertEqual(
            list(exported[0]),
            ["data_kind", "source", "record_id", "date", *DIMENSIONS, "value", "unit"],
        )

    def test_csv_preserves_numeric_credits_and_blanks(self):
        row = replace(self.spending.records[0], value=-12.5)
        blank = replace(row, record_id="blank", value=None)
        exported = list(
            csv.DictReader(io.StringIO(export_csv((row, blank), self.spending.source)))
        )
        self.assertEqual(exported[0]["value"], "-12.5")
        self.assertEqual(exported[1]["value"], "")

    def test_csv_protects_formula_text(self):
        for unsafe in ("=1+1", "+cmd", " -cmd", "@sum", "\tformula"):
            row = replace(self.services.records[0], category=unsafe)
            exported = list(
                csv.DictReader(io.StringIO(export_csv((row,), self.services.source)))
            )
            self.assertEqual(exported[0]["category"], "'" + unsafe)

    def test_live_source_export_is_not_labeled_fictional(self):
        live = replace(self.services.source, is_sample=False, name="Requests")
        exported = list(
            csv.DictReader(io.StringIO(export_csv(self.services.records[:1], live)))
        )
        self.assertEqual(exported[0]["data_kind"], "DATA")
        self.assertEqual(exported[0]["source"], "Requests")

    def test_contract_rejects_duplicate_and_invalid_values(self):
        row = self.services.records[0]
        with self.assertRaises(ValueError):
            Dataset((row, row), self.services.source)
        for value in (float("nan"), float("inf"), True, "12"):
            with self.assertRaises(ValueError):
                replace(row, value=value)
        with self.assertRaises(ValueError):
            Record("", date.today(), "Category", "Area", "Open", None)
        with self.assertRaises(ValueError):
            replace(row, date="2026-01-01")
        with self.assertRaises(ValueError):
            replace(self.services.source, labels={"district": "District"})
        with self.assertRaises(ValueError):
            replace(self.services.source, aggregation="median")

    def test_source_labels_relabel_without_renaming_fields(self):
        source = replace(self.services.source, labels={"area": "District"})
        self.assertEqual(source.label("area"), "District")
        self.assertEqual(source.label("category"), "Category")

    def test_unknown_sample_and_state_fail_clearly(self):
        with self.assertRaises(ValueError):
            load_sample("production")
        with self.assertRaises(ValueError):
            load_sample("services", "fresh")
        with self.assertRaises(ValueError):
            load_dataset("production")

    def test_provider_registry_is_the_connector_seam(self):
        self.assertEqual(set(PROVIDERS), {"services", "spending"})
        self.assertEqual(load_dataset("spending", "stale").state, "stale")
        self.assertIs(PROVIDERS["spending"].source, self.spending.source)
        live_source = replace(self.services.source, is_sample=False, name="Live")
        registered = dict(PROVIDERS)
        registered["live"] = Provider(
            live_source, lambda condition: Dataset(self.services.records, live_source)
        )
        self.assertFalse(registered["live"].load("ready").source.is_sample)


if __name__ == "__main__":
    unittest.main()
