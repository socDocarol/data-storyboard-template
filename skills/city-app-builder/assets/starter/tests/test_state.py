"""Selection, drill and comparison semantics independent of the browser."""

import unittest
from dataclasses import replace
from datetime import date
from urllib.parse import parse_qs, urlsplit

from city_app.data import Record, load_sample
from city_app.state import ViewState, compare_groups, compare_months


class StateTests(unittest.TestCase):
    def test_selection_and_comparison_scope(self):
        rows = load_sample().records
        view = ViewState(
            category="Street maintenance", area="North", status="Completed"
        )
        self.assertEqual(len(view.select(rows)), 4)
        self.assertTrue(
            all(
                row.area == "North" and row.status == "Completed"
                for row in view.select(rows, omit="category")
            )
        )
        self.assertGreater(len(view.select(rows, omit="category")), 4)

    def test_month_search_and_order_apply_together(self):
        rows = load_sample().records
        result = ViewState(month="2026-01", query="completed", order="oldest").select(
            rows
        )
        self.assertTrue(result)
        self.assertTrue(
            all(row.date.month == 1 and row.status == "Completed" for row in result)
        )
        self.assertEqual(
            list(result), sorted(result, key=lambda row: (row.date, row.record_id))
        )

    def test_drill_replaces_descendants_and_clear_keeps_source(self):
        view = ViewState(
            sample="spending",
            category="old",
            area="North",
            status="Posted",
            month="2026-01",
            record="id",
        )
        drilled = view.drill("category", "new")
        self.assertEqual(
            (drilled.category, drilled.area, drilled.status, drilled.record),
            ("new", "", "", ""),
        )
        self.assertEqual(drilled.month, "2026-01")
        self.assertEqual(view.clear().sample, "spending")
        self.assertEqual(view.clear().next_dimension(), "category")
        self.assertEqual(view.without_record(), replace(view, record=""))
        self.assertIs(drilled.without_record(), drilled)

    def test_active_filters_follow_display_order_and_labels(self):
        view = ViewState(status="Open", category="Lighting", query="x", month="2026-02")
        self.assertEqual(
            [
                (key, label)
                for key, label, _ in view.filters(labels={"status": "Stage"})
            ],
            [
                ("category", "Category"),
                ("status", "Stage"),
                ("month", "Month"),
                ("query", "Search"),
            ],
        )
        self.assertEqual(ViewState().filters(), [])

    def test_urls_roundtrip_special_characters(self):
        view = ViewState(
            category="Parks & trees / North?", query="#tag + text", record="ABC"
        )
        fragment = urlsplit(view.href("explore")).fragment
        values = {
            key: value[0] for key, value in parse_qs(fragment.split("?", 1)[1]).items()
        }
        self.assertEqual(ViewState.from_payload(values), view)

    def test_invalid_state_is_bounded(self):
        state = ViewState.from_payload(
            {
                "sample": "unknown",
                "condition": "oops",
                "month": "2026-13",
                "compare_by": "secret",
                "query": "a" * 2000,
            }
        )
        self.assertEqual(
            (state.sample, state.condition, state.month, state.compare_by),
            ("services", "ready", "", "category"),
        )
        self.assertEqual(len(state.query), 160)

    def test_missing_zero_negative_baselines(self):
        source = load_sample("spending").source
        a = Record("a", date(2026, 1, 1), "A", "North", "Posted", -10)
        b = replace(a, record_id="b", category="B", value=5)
        result = compare_groups((a, b), source, "category", "A", "B")
        self.assertEqual((result.delta, result.percent), (15, 150))
        for value in (0, None):
            result = compare_groups(
                (replace(a, value=value), b), source, "category", "A", "B"
            )
            self.assertIsNone(result.percent)
        self.assertIsNone(result.delta)
        self.assertEqual(result.left.contributors, 0)

    def test_comparison_means_use_individual_contributors(self):
        source = load_sample().source
        a = Record("a", date(2026, 1, 1), "A", "North", "Completed", 10)
        rows = (
            a,
            replace(a, record_id="b", value=None),
            replace(a, record_id="c", category="B", value=20),
            replace(a, record_id="d", category="B", value=40),
        )
        result = compare_groups(rows, source, "category", "A", "B")
        self.assertEqual(
            (
                result.left.value,
                result.left.contributors,
                result.right.value,
                result.delta,
            ),
            (10, 1, 30, 20),
        )

    def test_comparison_months_fill_gaps_and_empty_groups(self):
        a = Record("a", date(2026, 1, 1), "A", "North", "Posted", 1)
        b = replace(a, record_id="b", date=date(2026, 3, 1), category="B")
        self.assertEqual(
            compare_months((a, b), "category", "A", "B"),
            [("Jan 2026", 1, 0), ("Feb 2026", 0, 0), ("Mar 2026", 0, 1)],
        )
        self.assertEqual(compare_months((), "category", "A", "B"), [])


if __name__ == "__main__":
    unittest.main()
