"""Run with `python -m shiny run --host 127.0.0.1 --port 8126 app.py`.

Page composition and reactive wiring only. Data shape and providers live in
city_app/data.py, selection in city_app/state.py, presentation in
city_app/components.py and city_app/visuals.py.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

from shiny import App, Inputs, Outputs, Session, reactive, render, ui

from city_app.components import (
    bar_chart,
    comparison_chart,
    disclosure,
    drill_breadcrumbs,
    information_icon,
    page_intro,
    record_panel,
    sample_banner,
    select_control,
    selection_trail,
    site_footer,
    site_header,
    stat_card,
    state_panel,
    status_message,
    unavailable_panel,
)
from city_app.data import (
    DIMENSIONS,
    MISSING_LABEL,
    ORDERS,
    PROVIDERS,
    STATES,
    export_csv,
    format_value,
    load_dataset,
    measure,
)
from city_app.state import ViewState, compare_groups, compare_months, grouped_counts
from city_app.visuals import (
    composition_chart,
    heatmap_chart,
    monthly_measures,
    record_plot,
    trend_chart,
)

ROOT = Path(__file__).resolve().parent
# The records table shows at most this many rows; the CSV always has them all.
MAX_TABLE_ROWS = 500
PREVIEW_CONDITIONS = {
    "ready": "Available data",
    "missing": "Some information missing",
    "stale": "Last available snapshot",
    "empty": "Empty dataset",
    "error": "Data unavailable",
    "loading": "Loading",
}
assert set(PREVIEW_CONDITIONS) == set(STATES), (
    "PREVIEW_CONDITIONS must label every STATE"
)


def read_config(path: Path) -> dict:
    """Validate app_config.json early so a bad edit fails at startup, not on a click."""
    config = json.loads(path.read_text(encoding="utf-8"))
    for key in ("title", "description", "audience", "sample", "portal_url"):
        if not isinstance(config.get(key), str):
            raise ValueError(f"app_config.json: '{key}' must be a text value.")
    if config["sample"] not in PROVIDERS:
        raise ValueError(
            f"app_config.json: sample must be one of {', '.join(PROVIDERS)}."
        )
    if not 1 <= len(config["title"].strip()) <= 60:
        raise ValueError(
            "app_config.json: use an application title of 1 to 60 characters."
        )
    portal = urlsplit(config["portal_url"])
    if (
        portal.scheme not in ("http", "https")
        or not portal.netloc
        or portal.username
        or portal.password
    ):
        raise ValueError(
            "app_config.json: portal_url must be an HTTP(S) portal address without credentials."
        )
    config.setdefault("show_preview_controls", True)
    if not isinstance(config["show_preview_controls"], bool):
        raise ValueError(
            "app_config.json: show_preview_controls must be true or false."
        )
    config.setdefault("banner", None)
    banner = config["banner"]
    if banner is not None:
        if (
            not isinstance(banner, dict)
            or any(
                not isinstance(banner.get(key), str) or not banner[key].strip()
                for key in ("image", "alt")
            )
            or not isinstance(banner.get("credit", ""), str)
        ):
            raise ValueError(
                "app_config.json: banner must be null or an object with image, alt, and optional credit text."
            )
        asset_root = (ROOT / "www").resolve()
        asset = (asset_root / banner["image"]).resolve()
        if (
            urlsplit(banner["image"]).scheme
            or banner["image"].startswith(("/", "\\"))
            or not asset.is_relative_to(asset_root)
            or asset.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp")
            or not asset.is_file()
        ):
            raise ValueError(
                "app_config.json: banner image must be an existing local JPG, PNG, or WebP file inside www."
            )
        config["banner"] = {**banner, "image": asset.relative_to(asset_root).as_posix()}
    return config


CONFIG = read_config(ROOT / "app_config.json")


def preview_controls():
    return ui.tags.details(
        ui.tags.summary("Preview options"),
        ui.div(
            ui.input_select(
                "sample",
                "Example dataset",
                {name: provider.source.name for name, provider in PROVIDERS.items()},
                selected=CONFIG["sample"],
            ),
            ui.input_select("condition", "Show data as", PREVIEW_CONDITIONS),
            class_="preview-grid",
        ),
        ui.p(
            "These controls change fictional examples only. No database or API is contacted."
        ),
        class_="preview-controls",
        hidden=not CONFIG["show_preview_controls"],
    )


def page(route: str, heading: str, lede, *outputs, hidden: bool = True, banner=None):
    return ui.tags.section(
        page_intro(heading, lede, banner),
        *outputs,
        id=f"page-{route}",
        data_route=route,
        hidden=hidden,
    )


app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.meta(name="robots", content="noindex, nofollow"),
        ui.tags.link(rel="stylesheet", href="city.css"),
        ui.tags.script(src="shell.js", defer=True),
    ),
    site_header(CONFIG["title"], CONFIG["portal_url"]),
    ui.tags.main(
        ui.div(
            ui.tags.details(
                ui.tags.summary(
                    ui.output_ui("info_icon", inline=True),
                    id="data-info-trigger",
                    aria_label="Data information and preview options",
                ),
                ui.div(
                    ui.output_ui("source_banner"),
                    ui.output_ui("source_status"),
                    preview_controls(),
                    ui.a("Sources and definitions", href="#about"),
                    class_="data-info-panel",
                ),
                id="data-info",
                class_="data-info",
            ),
            ui.output_ui("selection_summary"),
            page(
                "home",
                CONFIG["title"],
                ui.output_text("introduction", inline=True),
                ui.output_ui("overview"),
                hidden=False,
                banner=CONFIG["banner"],
            ),
            page(
                "explore",
                "Explore the records",
                "Narrow the view, inspect individual records, and download what you find.",
                ui.output_ui("filters"),
                ui.output_ui("explorer"),
                ui.output_ui("download_control"),
            ),
            page(
                "compare",
                "Compare groups",
                "Keep the context. See how two groups differ.",
                ui.output_ui("comparison_controls"),
                ui.output_ui("comparison"),
            ),
            page(
                "about",
                "About this data",
                "Understand what the numbers represent before using them.",
                ui.output_ui("about"),
            ),
            class_="city-container",
        ),
        id="main",
        tabindex="-1",
        data_default_sample=CONFIG["sample"],
    ),
    ui.tags.dialog(
        ui.tags.button(
            "Close details",
            type="button",
            data_close_record="true",
            class_="secondary-button",
        ),
        ui.output_ui("record_details"),
        id="record-dialog",
        aria_labelledby="record-title",
    ),
    ui.output_ui("source_footer"),
    title=CONFIG["title"],
    lang="en",
)


def server(input: Inputs, output: Outputs, session: Session):
    # `view` is the complete browser state. `selection` is the same state without
    # the open record, and only changes when something other than the record
    # changes, so opening or closing a record never redraws charts or tables.
    initial = ViewState(sample=CONFIG["sample"])
    view = reactive.value(initial)
    selection = reactive.value(initial)

    @reactive.effect
    @reactive.event(input.dashboard_state)
    def receive_state():
        incoming = ViewState.from_payload(input.dashboard_state(), CONFIG["sample"])
        view.set(incoming)
        if incoming.without_record() != selection():
            selection.set(incoming.without_record())

    @reactive.calc
    def dataset():
        return load_dataset(selection().sample, selection().condition)

    @reactive.calc
    def filtered():
        return selection().select(dataset().records)

    @render.text
    def introduction():
        if selection().sample == CONFIG["sample"]:
            return CONFIG["description"]
        return "Previewing another example. " + dataset().source.description

    @render.ui
    def selection_summary():
        return selection_trail(
            selection(),
            len(filtered()),
            len(dataset().records),
            labels=dataset().source.labels,
        )

    @render.ui
    def filters():
        current = selection()
        source = dataset().source
        controls = []
        for key in DIMENSIONS:
            values = sorted(
                {getattr(row, key) for row in dataset().records}
                | ({getattr(current, key)} if getattr(current, key) else set())
            )
            controls.append(
                select_control(
                    key,
                    source.label(key),
                    {
                        "": f"All {source.label(key).lower()} groups",
                        **{value: value for value in values},
                    },
                    getattr(current, key),
                )
            )
        months = sorted(
            {row.month for row in dataset().records}
            | ({current.month} if current.month else set())
        )
        return ui.div(
            *controls,
            select_control(
                "month",
                "Month",
                {"": "All months", **{month: month for month in months}},
                current.month,
            ),
            ui.div(
                ui.tags.label("Search records", for_="search"),
                ui.tags.input(
                    id="search",
                    type="search",
                    value=current.query,
                    data_state="query",
                    placeholder="ID, "
                    + ", ".join(source.label(key).lower() for key in DIMENSIONS)
                    + ", or date",
                ),
                class_="state-control",
            ),
            select_control("order", "Order", ORDERS, current.order),
            ui.a(
                "Reset filters",
                href=current.clear().href("explore", order="newest"),
                id="reset",
                class_="secondary-button",
            ),
            class_="filter-bar",
        )

    @output(suspend_when_hidden=False)
    @render.ui
    def source_banner():
        return sample_banner(dataset().source)

    @output(suspend_when_hidden=False)
    @render.ui
    def info_icon():
        return information_icon(dataset().state)

    @output(suspend_when_hidden=False)
    @render.ui
    def source_footer():
        return site_footer(dataset().source)

    @render.ui
    def source_status():
        current = dataset()
        return ui.div(
            ui.strong(current.source.name),
            ui.span(status_message(current.source, current.state)),
            class_=f"source-status status-{current.state}",
            role="status",
        )

    @render.ui
    def overview():
        current = dataset()
        if panel := unavailable_panel(current):
            return panel
        rows = filtered()
        if not rows:
            return state_panel("empty", filtered=True)
        state = selection()
        source = current.source
        value, known = measure(rows, source)
        months = monthly_measures(rows, source)
        dimension = state.next_dimension()
        categories = grouped_counts(rows, "category")
        groups = grouped_counts(rows, dimension) if dimension else []
        statuses = grouped_counts(rows, "status")
        return ui.TagList(
            drill_breadcrumbs(state),
            ui.div(
                stat_card("Records in this view", f"{len(rows):,}", "Selected records"),
                stat_card(
                    source.value_label,
                    format_value(value, source.value_unit),
                    f"{known} of {len(rows)} values recorded",
                ),
                stat_card(
                    f"{source.label('category')} groups represented",
                    str(len(categories)),
                    f"{min(row.date for row in rows):%b %Y} to {max(row.date for row in rows):%b %Y}",
                ),
                stat_card(
                    f"{source.label('area')} groups represented",
                    str(len({row.area for row in rows if row.area != MISSING_LABEL})),
                    "Missing labels excluded",
                ),
                class_="stats-grid overview-stats",
            ),
            ui.div(
                trend_chart(
                    months,
                    source,
                    {key: state.href("home", month=key) for _, key, *_ in months},
                    area=source.aggregation == "sum",
                ),
                bar_chart(
                    f"Drill into {source.label(dimension).lower()}",
                    groups,
                    description="Select a group · record counts",
                    chart_id="drill",
                    links={
                        label: state.drill(dimension, label).href()
                        for label, _ in groups
                    },
                    caption=disclosure(source, "source_caption")
                    + " Counts are not City performance figures.",
                )
                if dimension
                else ui.div(
                    ui.h2(
                        "You have reached the records", id="drill-title", tabindex="-1"
                    ),
                    ui.p("Open the selected records to inspect individual details."),
                    ui.a(
                        f"Open {len(rows)} records",
                        href=state.href("explore"),
                        class_="primary-link",
                    ),
                    class_="chart-frame",
                ),
                class_="charts-grid visual-primary",
            ),
            ui.div(
                heatmap_chart(rows, state, labels=source.labels),
                composition_chart(
                    statuses,
                    {label: state.href("home", status=label) for label, _ in statuses},
                    label=source.label("status"),
                ),
                record_plot(rows, source, state),
                class_="visual-secondary",
            ),
            ui.tags.details(
                ui.tags.summary("Insights and definitions for this selection"),
                ui.p(
                    f"This view contains {len(rows)} records across {len(categories)} "
                    f"{source.label('category').lower()} groups. {known} records contribute to {source.value_label.lower()}."
                ),
                ui.p(source.limitation),
                ui.a(
                    "Explore the records",
                    href=state.href("explore"),
                    class_="primary-link",
                ),
                class_="selection-notes",
                open=bool(state.filters()),
            ),
            ui.p(
                f"Source: {source.name} · Snapshot {source.updated_at.isoformat()} · Missing values excluded from measures.",
                class_="visual-source",
            ),
        )

    @render.ui
    def explorer():
        current = dataset()
        if panel := unavailable_panel(current):
            return panel
        rows = filtered()
        if not rows:
            return state_panel("empty", filtered=True)
        source = current.source
        state = selection()
        shown = rows[:MAX_TABLE_ROWS]
        return ui.TagList(
            ui.p(
                "Scroll across the table to see every column.",
                class_="table-hint muted",
            ),
            ui.p(
                f"Showing the first {len(shown):,} of {len(rows):,} records; "
                "narrow the view or download the CSV for all of them.",
                class_="table-limit-note muted",
                role="status",
            )
            if len(rows) > len(shown)
            else None,
            ui.div(
                ui.tags.table(
                    ui.tags.caption(disclosure(source, "table_caption")),
                    ui.tags.thead(
                        ui.tags.tr(
                            *[
                                ui.tags.th(label, scope="col")
                                for label in (
                                    "Record",
                                    "Date",
                                    *[source.label(key) for key in DIMENSIONS],
                                    f"Value ({source.value_unit})",
                                )
                            ]
                        )
                    ),
                    ui.tags.tbody(
                        *[
                            ui.tags.tr(
                                ui.tags.th(
                                    ui.a(
                                        row.record_id,
                                        href=state.href(
                                            "explore", record=row.record_id
                                        ),
                                        data_record_id=row.record_id,
                                    ),
                                    scope="row",
                                ),
                                ui.tags.td(row.date.isoformat()),
                                *[ui.tags.td(getattr(row, key)) for key in DIMENSIONS],
                                ui.tags.td(
                                    format_value(row.value, source.value_unit),
                                    class_="numeric",
                                ),
                            )
                            for row in shown
                        ]
                    ),
                    class_="data-table",
                ),
                class_="table-scroll",
                tabindex="0",
                role="region",
                aria_label="Scrollable records table",
            ),
        )

    @render.ui
    def download_control():
        if not filtered():
            return ui.p(
                "Downloads are available when there are matching records.",
                class_="muted",
            )
        source = dataset().source
        return ui.div(
            ui.download_button(
                "download",
                disclosure(source, "download_button"),
                class_="secondary-button",
            ),
            ui.p(disclosure(source, "download_note"), class_="muted"),
            class_="download-row",
        )

    @render.download(
        filename=lambda: (
            f"{disclosure(dataset().source, 'download_prefix')}-{selection().sample}-records.csv"
        ),
        media_type="text/csv; charset=utf-8",
    )
    def download():
        yield export_csv(filtered(), dataset().source)

    @reactive.calc
    def comparison_context():
        current = selection()
        rows = current.select(dataset().records, omit=current.compare_by)
        groups = sorted({getattr(row, current.compare_by) for row in rows})
        left = current.left if current.left in groups else (groups[0] if groups else "")
        right = (
            current.right
            if current.right in groups
            else next((group for group in groups if group != left), left)
        )
        return rows, groups, left, right

    @render.ui
    def comparison_controls():
        rows, groups, left, right = comparison_context()
        source = dataset().source
        return ui.div(
            select_control(
                "compare_by",
                "Compare by",
                {key: source.label(key) for key in DIMENSIONS},
                selection().compare_by,
            ),
            select_control("left", "Group A", {group: group for group in groups}, left),
            select_control(
                "right", "Group B", {group: group for group in groups}, right
            ),
            class_="filter-bar",
        )

    @render.ui
    def comparison():
        current = dataset()
        rows, groups, left, right = comparison_context()
        if panel := unavailable_panel(current):
            return panel
        if len(groups) < 2:
            return ui.div(
                ui.h2("Choose a broader view to compare"),
                ui.p(
                    "Fewer than two groups remain. Remove a selection or choose another comparison dimension."
                ),
                class_="state-panel",
            )
        state = selection()
        source = current.source
        dimension = state.compare_by
        result = compare_groups(rows, source, dimension, left, right)
        scope = [
            f"{label}: {value}"
            for key, label, value in state.filters(labels=source.labels)
            if key != dimension
        ]
        return ui.TagList(
            ui.p(
                f"Scope: {len(rows)} records. Comparing {source.label(dimension).lower()} ignores its current selection; all other filters remain. "
                + (" · ".join(scope) if scope else "No other filters."),
                class_="comparison-scope",
                role="status",
            ),
            ui.p(
                "Both sides show the same group. Choose another Group B to see a difference."
            )
            if left == right
            else None,
            ui.div(
                *[
                    ui.div(
                        stat_card(
                            f"{letter}: {group.label}",
                            format_value(group.value, source.value_unit),
                            f"{group.records} records; {group.contributors} contribute to the {source.aggregation}",
                        ),
                        ui.a(
                            "Explore these records",
                            href=replace(state, **{dimension: group.label}).href(
                                "explore"
                            ),
                            class_="primary-link",
                        ),
                    )
                    for letter, group in (("A", result.left), ("B", result.right))
                ],
                class_="comparison-grid",
            ),
            comparison_chart(
                compare_months(rows, dimension, left, right),
                left,
                right,
                caption=disclosure(source, "source_caption")
                + " These are record counts, not amounts.",
            ),
            ui.tags.details(
                ui.tags.summary("Difference and interpretation"),
                ui.div(
                    ui.h2("Difference: B minus A"),
                    ui.p(
                        format_value(result.delta, source.value_unit),
                        class_="comparison-delta",
                    ),
                    ui.p(
                        f"{result.percent:+.1f}% relative to the absolute value of A."
                        if result.percent is not None
                        else "Percentage is not defined when A is zero or either measure is missing."
                    ),
                    ui.p(
                        "This is a descriptive difference, not a performance judgment or a test of statistical significance. Averages use each group's recorded values."
                    ),
                    class_="comparison-note",
                ),
                class_="comparison-explanation",
            ),
        )

    @output(suspend_when_hidden=False)
    @render.ui
    def record_details():
        record_id = view().record
        if not record_id:
            return None
        row = next((row for row in filtered() if row.record_id == record_id), None)
        if row is None:
            return ui.div(
                ui.h2(
                    "Record unavailable in this view", id="record-title", tabindex="-1"
                ),
                ui.p(
                    "The record may be outside your selection or unavailable in this sample. Close details and broaden the view."
                ),
                data_record_content=record_id,
            )
        return record_panel(row, dataset().source, view())

    @render.ui
    def about():
        source = dataset().source
        return ui.div(
            ui.h2(disclosure(source, "about_heading")),
            ui.p(
                f"This preview is intended for {CONFIG['audience']}. "
                + disclosure(source, "about_origin")
            ),
            ui.h2("Source and freshness"),
            ui.p(source.name + ". " + source.description),
            ui.p(disclosure(source, "about_snapshot")),
            ui.h2("How the numbers are calculated"),
            ui.p(
                "Record totals count rows. Shared selections apply to charts, records, details, and downloads. Compare retains all filters except the dimension being compared; its scope is stated above the results."
            ),
            ui.p(
                source.value_label
                + (
                    " is the arithmetic mean of recorded values."
                    if source.aggregation == "mean"
                    else " is the sum of recorded values, including negative credits."
                )
            ),
            ui.p(
                "Missing values display as Not recorded and are excluded from the measure. The metric states how many records contribute."
            ),
            ui.h2(disclosure(source, "about_limits_heading")),
            ui.p(source.limitation),
            ui.h2("Connecting your data later") if source.is_sample else None,
            ui.p(
                "Your future source may be a file, SQL Server, an API, or Sacramento Open Data. This version does not connect to those sources. Keep the preview fictional until a connection and its field meanings have been verified."
            )
            if source.is_sample
            else None,
            class_="prose",
        )


app = App(app_ui, server, static_assets=ROOT / "www")
