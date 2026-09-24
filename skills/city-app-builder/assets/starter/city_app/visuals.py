"""Local, linked visual components. No chart service or JavaScript dependency."""

from __future__ import annotations

from collections import Counter
from math import pi

from htmltools import Tag
from shiny import ui

from city_app.data import DIMENSIONS, format_value, measure, monthly_groups

COLORS = ("#0077b6", "#a46128", "#397365", "#6951a3", "#4d637a")
# Known sample statuses keep a stable color; other labels take unused palette
# colors in alphabetical order, so two groups in one chart never share a color
# until the palette is exhausted.
STATUS_COLORS = {
    "Completed": COLORS[0],
    "Open": COLORS[1],
    "Posted": COLORS[0],
    "Credit": COLORS[1],
    "Not recorded": COLORS[4],
}
# Above this many recorded values the record plot asks for a narrower view
# instead of drawing one link per record.
MAX_PLOT_POINTS = 1000

PLOT_LEFT, PLOT_RIGHT, PLOT_TOP, PLOT_BOTTOM = 82, 592, 36, 220
PLOT_VIEW_BOX = "0 0 640 280"


def monthly_measures(records, source):
    """(label, key, measure, contributors, records) per month; absent months stay missing."""
    return [
        (label, key, *measure(rows, source), len(rows))
        for label, key, rows in monthly_groups(records)
    ]


def value_domain(values):
    """A signed axis domain that always includes zero and is never empty."""
    values = [value for value in values if value is not None]
    low, high = min([0, *values]), max([0, *values])
    return (low, high) if low != high else (0, 1)


def group_colors(labels) -> dict[str, str]:
    """Deterministic colors: known statuses first, then unused palette colors alphabetically."""
    colors = {label: STATUS_COLORS[label] for label in labels if label in STATUS_COLORS}
    unused = [color for color in COLORS if color not in colors.values()] or list(COLORS)
    for index, label in enumerate(
        sorted(label for label in labels if label not in colors)
    ):
        colors[label] = unused[index % len(unused)]
    return colors


def svg(*children, label, view_box=PLOT_VIEW_BOX, wrapper_class="plot-scroll"):
    """An accessible SVG in a focusable, horizontally scrollable region."""
    return ui.div(
        Tag(
            "svg",
            *children,
            xmlns="http://www.w3.org/2000/svg",
            viewBox=view_box,
            role="group",
            aria_label=label,
            class_="data-graphic",
        ),
        class_=wrapper_class,
        tabindex="0",
        role="region",
        aria_label=label,
    )


def exact_values(title, headers, rows):
    """A semantic table with the exact values behind a chart, collapsed by default."""
    return ui.tags.details(
        ui.tags.summary("View exact chart values"),
        ui.div(
            ui.tags.table(
                ui.tags.caption(title),
                ui.tags.thead(
                    ui.tags.tr(*[ui.tags.th(label, scope="col") for label in headers])
                ),
                ui.tags.tbody(
                    *[
                        ui.tags.tr(
                            *[
                                ui.tags.th(value, scope="row")
                                if index == 0
                                else ui.tags.td(value)
                                for index, value in enumerate(row)
                            ]
                        )
                        for row in rows
                    ]
                ),
                class_="data-table",
            ),
            class_="exact-scroll",
            tabindex="0",
            role="region",
            aria_label=f"{title} values",
        ),
        class_="chart-values",
    )


def visual_frame(title, hint, graphic, *, chart_id, values=None, scrollable=False):
    """Titled figure: heading, one-line hint, graphic, optional exact-value table."""
    return ui.tags.figure(
        ui.h2(title, id=f"{chart_id}-title"),
        ui.p(hint, class_="visual-hint"),
        graphic,
        ui.p(
            "Scroll across to see the full visual on a narrow screen.",
            class_="visual-scroll-hint",
        )
        if scrollable
        else None,
        values,
        class_="chart-frame visual-frame",
        aria_labelledby=f"{chart_id}-title",
        id=chart_id,
    )


def _axis(low, high, unit, y):
    """Three horizontal grid lines with formatted labels."""
    marks = []
    for value in (low, (low + high) / 2, high):
        marks.extend(
            (
                Tag(
                    "line",
                    x1=PLOT_LEFT,
                    x2=PLOT_RIGHT,
                    y1=y(value),
                    y2=y(value),
                    class_="plot-grid",
                ),
                Tag(
                    "text",
                    f"{value:,.1f}".removesuffix(".0")
                    if unit == "records"
                    else format_value(value, unit),
                    x=PLOT_LEFT - 10,
                    y=y(value) + 4,
                    text_anchor="end",
                    class_="axis-label",
                ),
            )
        )
    return marks


def _y_scale(low, high):
    span = PLOT_BOTTOM - PLOT_TOP

    def y(value):
        return PLOT_BOTTOM - (value - low) * span / (high - low)

    return y


def trend_chart(entries, source, links, *, area=False):
    """Line/area plot with zero-based signed scale; missing months break the path."""
    low, high = value_domain([row[2] for row in entries])
    y = _y_scale(low, high)
    width = PLOT_RIGHT - PLOT_LEFT

    def x(index):
        return PLOT_LEFT + index * width / max(1, len(entries) - 1)

    marks = _axis(low, high, source.value_unit, y)
    segments, segment = [], []
    for index, (_, _, value, _, _) in enumerate(entries):
        if value is None:
            if segment:
                segments.append(segment)
                segment = []
        else:
            segment.append((x(index), y(value)))
    if segment:
        segments.append(segment)
    for points in segments:
        path = "M " + " L ".join(f"{px:.2f},{py:.2f}" for px, py in points)
        if area and len(points) > 1:
            marks.append(
                Tag(
                    "path",
                    d=path
                    + f" L {points[-1][0]:.2f},{y(0):.2f} L {points[0][0]:.2f},{y(0):.2f} Z",
                    class_="trend-area",
                )
            )
        marks.append(Tag("path", d=path, class_="trend-line"))
    for index, (label, key, value, known, count) in enumerate(entries):
        if value is not None:
            accessible = f"{label}: {format_value(value, source.value_unit)}; {known} of {count} records. Select month"
            marks.append(
                Tag(
                    "a",
                    Tag("title", accessible),
                    Tag("circle", cx=x(index), cy=y(value), r=11, class_="point-hit"),
                    Tag(
                        "circle", cx=x(index), cy=y(value), r=4.5, class_="trend-point"
                    ),
                    href=links[key],
                    aria_label=accessible,
                    class_="trend-link",
                    data_drill="true",
                )
            )
        marks.append(
            Tag(
                "text",
                label.split()[0],
                x=x(index),
                y=PLOT_BOTTOM + 29,
                text_anchor="middle",
                class_="axis-label",
            )
        )
    plot = svg(
        *marks, label=f"{source.value_label} by month. Select a point to filter."
    )
    # Native links remain large and usable at phone widths, including missing months.
    controls = ui.div(
        *[
            ui.a(label, href=links[key], data_drill="true", class_="month-link")
            for label, key, *_ in entries
        ],
        class_="month-links",
    )
    return visual_frame(
        source.value_label + " over time",
        "Select a month · "
        + ("Monthly mean" if source.aggregation == "mean" else "Monthly net sum"),
        ui.TagList(plot, controls),
        chart_id="trend",
        scrollable=True,
        values=exact_values(
            "Monthly measures",
            ("Month", source.value_label, "Contributors", "Records"),
            [
                (label, format_value(value, source.value_unit), str(known), str(count))
                for label, _, value, known, count in entries
            ],
        ),
    )


def composition_chart(entries, links, *, label="Status"):
    """A small composition ring: arc length represents nonnegative record counts."""
    total = sum(count for _, count in entries)
    radius, center = 70, 110
    circumference, offset = 2 * pi * radius, 0
    colors = group_colors([name for name, _ in entries])
    arcs, legend = [], []
    for name, count in entries:
        fraction = count / total if total else 0
        color = colors[name]
        arcs.append(
            Tag(
                "circle",
                cx=center,
                cy=center,
                r=radius,
                fill="none",
                stroke=color,
                stroke_width=28,
                stroke_dasharray=f"{fraction * circumference:.4f} {circumference:.4f}",
                stroke_dashoffset=f"{-offset:.4f}",
                transform=f"rotate(-90 {center} {center})",
            )
        )
        offset += fraction * circumference
        legend.append(
            ui.tags.li(
                ui.a(
                    ui.span(
                        class_="legend-swatch",
                        style=f"background:{color}",
                        aria_hidden="true",
                    ),
                    ui.span(name),
                    ui.strong(f"{count} · {fraction:.0%}"),
                    href=links[name],
                    data_drill="true",
                )
            )
        )
    return visual_frame(
        f"{label} mix",
        f"Select a {label.lower()} · share of records",
        ui.div(
            svg(
                *arcs,
                Tag(
                    "text",
                    str(total),
                    x=center,
                    y=center - 2,
                    text_anchor="middle",
                    class_="ring-total",
                ),
                Tag(
                    "text",
                    "records",
                    x=center,
                    y=center + 22,
                    text_anchor="middle",
                    class_="axis-label",
                ),
                label=f"{label} share; counts and percentages in the linked legend",
                view_box="0 0 220 220",
                wrapper_class="ring-graphic",
            ),
            ui.tags.ul(*legend, class_="composition-legend"),
            class_="composition-body",
        ),
        chart_id="composition",
    )


def heatmap_chart(records, view, *, labels=DIMENSIONS):
    """Area × category record counts as a linked, color-graded table."""
    labels = {**DIMENSIONS, **labels}
    row_label, column_label = labels["area"], labels["category"]
    areas = sorted({row.area for row in records})
    categories = sorted({row.category for row in records})
    counts = Counter((row.area, row.category) for row in records)
    maximum = max(counts.values(), default=1)
    rows = []
    for area in areas:
        cells = []
        for category in categories:
            count = counts[(area, category)]
            level = 0 if not count else min(4, 1 + int(3 * count / maximum))
            cells.append(
                ui.tags.td(
                    ui.a(
                        str(count),
                        href=view.href(
                            "explore", area=area, category=category, record=""
                        ),
                        class_=f"heat-cell heat-{level}",
                        aria_label=f"{area}, {category}: {count} records; explore",
                    )
                )
            )
        rows.append(ui.tags.tr(ui.tags.th(area, scope="row"), *cells))
    return visual_frame(
        "Where records cluster",
        f"{row_label} × {column_label.lower()} · select a cell",
        ui.TagList(
            ui.div(
                ui.tags.table(
                    ui.tags.caption(
                        f"Record counts by {row_label.lower()} and {column_label.lower()}",
                        class_="sr-only",
                    ),
                    ui.tags.thead(
                        ui.tags.tr(
                            ui.tags.th(row_label, scope="col"),
                            *[
                                ui.tags.th(category, scope="col")
                                for category in categories
                            ],
                        )
                    ),
                    ui.tags.tbody(*rows),
                    class_="heatmap-table",
                ),
                class_="heatmap-scroll",
                tabindex="0",
                role="region",
                aria_label=f"{row_label} by {column_label.lower()} heatmap; scroll for all {column_label.lower()} groups",
            ),
            ui.p(
                "Lighter = fewer records · Darker = more · Numbers show exact counts"
                + (" · Scroll to see all groups" if len(categories) > 4 else ""),
                class_="visual-hint",
            ),
        ),
        chart_id="heatmap",
        scrollable=True,
    )


def record_plot(records, source, view):
    """Each recorded value against its date; every dot links to the record details."""
    known = [row for row in records if row.value is not None]
    if not known:
        return visual_frame(
            "Recorded values",
            "Individual records",
            ui.p("No recorded values in this selection. Missing values are excluded."),
            chart_id="record-plot",
        )
    if len(known) > MAX_PLOT_POINTS:
        return visual_frame(
            "Recorded values",
            "Individual records",
            ui.p(
                f"{len(known):,} recorded values is too many to plot individually. "
                f"Narrow the view to {MAX_PLOT_POINTS:,} or fewer to see each record."
            ),
            chart_id="record-plot",
        )
    low, high = value_domain([row.value for row in known])
    y = _y_scale(low, high)
    first, last = min(row.date for row in known), max(row.date for row in known)
    width = PLOT_RIGHT - PLOT_LEFT

    def x(day):
        return PLOT_LEFT + (day - first).days * width / max(1, (last - first).days)

    marks = _axis(low, high, source.value_unit, y)
    for row in known:
        label = f"{row.record_id}: {format_value(row.value, source.value_unit)}, {row.date.isoformat()}. Open details"
        marks.append(
            Tag(
                "a",
                Tag("title", label),
                Tag(
                    "circle", cx=x(row.date), cy=y(row.value), r=10, class_="point-hit"
                ),
                Tag(
                    "circle",
                    cx=x(row.date),
                    cy=y(row.value),
                    r=4.5,
                    class_="record-point",
                ),
                href=view.href("home", record=row.record_id),
                aria_label=label,
                data_record_id=row.record_id,
                class_="record-point-link",
            )
        )
    marks.extend(
        (
            Tag(
                "text",
                first.strftime("%d %b %Y"),
                x=PLOT_LEFT,
                y=PLOT_BOTTOM + 29,
                class_="axis-label",
            ),
            Tag(
                "text",
                last.strftime("%d %b %Y"),
                x=PLOT_RIGHT,
                y=PLOT_BOTTOM + 29,
                text_anchor="end",
                class_="axis-label",
            ),
        )
    )
    return visual_frame(
        "Recorded values",
        f"Each dot is a record · {len(known)} shown, {len(records) - len(known)} missing · select for details",
        svg(*marks, label=f"Individual values in {source.value_unit} by date"),
        chart_id="record-plot",
        scrollable=True,
        values=exact_values(
            "Individual recorded values",
            ("Record", "Date", f"Value ({source.value_unit})"),
            [
                (
                    ui.a(
                        row.record_id,
                        href=view.href("home", record=row.record_id),
                        data_record_id=row.record_id,
                    ),
                    row.date.isoformat(),
                    format_value(row.value, source.value_unit),
                )
                for row in known
            ],
        ),
    )
