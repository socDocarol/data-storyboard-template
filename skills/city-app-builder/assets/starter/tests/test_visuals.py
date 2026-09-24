"""Check the quantities and edge cases used by visual encodings."""

import unittest
from dataclasses import replace
from datetime import date

from city_app.data import Record, load_sample
from city_app.state import ViewState
from city_app.visuals import (
    MAX_PLOT_POINTS,
    composition_chart,
    group_colors,
    heatmap_chart,
    monthly_measures,
    record_plot,
    trend_chart,
    value_domain,
)


class VisualTests(unittest.TestCase):
    def test_monthly_means_reconcile_with_record_contributors(self):
        sample = load_sample()
        entries = monthly_measures(sample.records, sample.source)
        self.assertEqual(sum(row[3] for row in entries), 36)
        self.assertEqual(sum(row[4] for row in entries), 48)
        self.assertAlmostEqual(sum(row[2] * row[3] for row in entries), 338)

    def test_monthly_sums_include_credits(self):
        sample = load_sample("spending")
        self.assertEqual(
            sum(row[2] for row in monthly_measures(sample.records, sample.source)),
            851949,
        )

    def test_missing_month_is_a_gap_not_zero(self):
        source = load_sample("spending").source
        first = Record("a", date(2026, 1, 1), "A", "North", "Posted", -10)
        last = replace(first, record_id="b", date=date(2026, 3, 1), value=20)
        entries = monthly_measures((first, last), source)
        self.assertEqual([row[2] for row in entries], [-10, None, 20])
        self.assertEqual(entries[1][3:], (0, 0))
        chart = str(
            trend_chart(
                entries, source, {row[1]: "#home" for row in entries}, area=True
            )
        )
        self.assertEqual(chart.count('class="trend-line"'), 2)
        self.assertNotIn('class="trend-area"', chart)

    def test_scale_includes_zero_negative_values_and_constant_data(self):
        self.assertEqual(value_domain([-20, 5, None]), (-20, 5))
        self.assertEqual(value_domain([0, 0]), (0, 1))
        self.assertEqual(value_domain([None]), (0, 1))
        self.assertEqual(value_domain([-20, -10]), (-20, 0))

    def test_all_missing_records_have_no_fabricated_dots(self):
        sample = load_sample()
        rows = tuple(replace(row, value=None) for row in sample.records)
        chart = str(record_plot(rows, sample.source, ViewState()))
        self.assertIn("No recorded values", chart)
        self.assertNotIn("record-point-link", chart)

    def test_too_many_points_asks_for_a_narrower_view(self):
        sample = load_sample()
        base = sample.records[0]
        rows = tuple(
            replace(base, record_id=f"R{index}", value=1.0)
            for index in range(MAX_PLOT_POINTS + 1)
        )
        chart = str(record_plot(rows, sample.source, ViewState()))
        self.assertIn("too many to plot", chart)
        self.assertNotIn("record-point-link", chart)

    def test_group_colors_never_collide_within_a_chart(self):
        colors = group_colors(["Completed", "Open", "Zeta", "Alpha", "Mid"])
        self.assertEqual(len(set(colors.values())), 5)
        self.assertEqual(colors["Completed"], group_colors(["Completed"])["Completed"])
        chart = str(
            composition_chart(
                [("Alpha", 3), ("Zeta", 1)],
                {"Alpha": "#a", "Zeta": "#z"},
                label="Stage",
            )
        )
        self.assertIn("Stage mix", chart)
        self.assertIn("3 · 75%", chart)

    def test_heatmap_uses_source_labels(self):
        sample = load_sample()
        chart = str(
            heatmap_chart(
                sample.records,
                ViewState(),
                labels={"area": "District", "category": "Service"},
            )
        )
        self.assertIn("District × service", chart)
        self.assertEqual(chart.count("heat-cell"), 16)

    def test_labels_are_escaped_in_svg_and_tables(self):
        sample = load_sample()
        row = replace(
            sample.records[0], record_id="<script>alert(1)</script>", value=10
        )
        chart = str(record_plot((row,), sample.source, ViewState()))
        self.assertNotIn("<script>", chart)
        self.assertIn("&lt;script&gt;", chart)

    def test_heatmap_preserves_defaults_for_partial_source_labels(self):
        sample = load_sample()
        for labels, expected in (
            ({"area": "District"}, "District × category"),
            ({"category": "Service"}, "Area × service"),
            ({"status": "Stage"}, "Area × category"),
            ({}, "Area × category"),
        ):
            with self.subTest(labels=labels):
                source = replace(sample.source, labels=labels)
                chart = str(
                    heatmap_chart(sample.records, ViewState(), labels=source.labels)
                )
                self.assertIn(expected, chart)
                self.assertEqual(chart.count("heat-cell"), 16)
                self.assertEqual(dict(source.labels), labels)


if __name__ == "__main__":
    unittest.main()
