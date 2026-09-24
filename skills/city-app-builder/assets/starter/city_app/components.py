"""Presentation components accepting plain values or Shiny tags, never data connections."""

from __future__ import annotations

from dataclasses import replace

from shiny import ui

from city_app.data import (
    DIMENSIONS,
    UNAVAILABLE_STATES,
    Dataset,
    Record,
    SourceInfo,
    format_value,
)
from city_app.state import ViewState

NAVIGATION = (
    ("home", "Home"),
    ("explore", "Explore"),
    ("compare", "Compare"),
    ("about", "About"),
)


def disclosure(source: SourceInfo, key: str) -> str:
    """Every sample-versus-live wording, keyed on SourceInfo.is_sample.

    Add a live provider with is_sample=False and these switch together; nothing
    elsewhere in the app decides whether data is fictional.
    """
    sample = source.is_sample
    texts = {
        "banner_title": "Sample data" if sample else "Source data",
        "banner": (
            "Fictional records · Select a visual to explore."
            if sample
            else f"{source.name} · Select a visual to explore."
        ),
        "footer": (
            "Fictional sample data · Local preview · No live data connection"
            if sample
            else f"{source.name} · Local preview"
        ),
        "record_eyebrow": "Fictional sample record" if sample else "Record",
        "source_caption": (
            "Source: bundled fictional sample." if sample else f"Source: {source.name}."
        ),
        "table_caption": f"{source.name}. Values shown in {source.value_unit}."
        + (" All records are fictional." if sample else ""),
        "download_button": (
            "Download these sample records" if sample else "Download these records"
        ),
        "download_note": (
            "CSV includes a fictional-sample label on every row."
            if sample
            else "CSV includes the source name on every row."
        ),
        "download_prefix": "fictional" if sample else "records",
        "about_origin": (
            "Every record was created for this starter. It does not describe actual City activity."
            if sample
            else f"Records come from {source.name}. Check its definitions before drawing conclusions."
        ),
        "about_heading": (
            "A working example, ready for your ideas"
            if sample
            else f"About {source.name}"
        ),
        "about_limits_heading": (
            "What this example cannot tell you"
            if sample
            else "What this data cannot tell you"
        ),
        "about_snapshot": (
            f"The fictional snapshot is dated {source.updated_at:%B %d, %Y}. It is bundled with the app and is not refreshed from a live source."
            if sample
            else f"The data snapshot is dated {source.updated_at:%B %d, %Y}."
        ),
    }
    return texts[key]


def site_header(title: str, portal_url: str):
    def links(mobile: bool = False):
        return [
            ui.a(
                label,
                href=f"#{key}",
                class_="city-mobile-link" if mobile else "city-nav-link",
                data_page=key,
            )
            for key, label in NAVIGATION
        ]

    return ui.tags.header(
        ui.a("Skip to content", href="#main", class_="skip-link"),
        ui.div(
            ui.a(
                ui.span("↖", aria_hidden="true", class_="portal-arrow"),
                "Portal",
                href=portal_url,
                aria_label="Return to portal",
                class_="portal-link",
            ),
            ui.a(
                ui.img(
                    src="assets/city-of-sacramento-signature-white.png",
                    width="210",
                    height="51",
                    alt="City of Sacramento",
                    class_="city-brand-logo",
                ),
                ui.span(class_="city-brand-separator", aria_hidden="true"),
                ui.span(title, class_="city-app-identity", title=title),
                href="#home",
                class_="city-brand-link",
                aria_label=f"City of Sacramento {title} home",
            ),
            ui.tags.nav(*links(), class_="city-nav", aria_label="Application sections"),
            ui.tags.details(
                ui.tags.summary(
                    ui.span("☰", aria_hidden="true"),
                    ui.span("Open page menu", class_="sr-only"),
                    class_="city-menu-button",
                ),
                ui.tags.nav(
                    *links(True),
                    class_="city-mobile-nav",
                    aria_label="Application sections",
                ),
                class_="city-menu",
                id="city-menu",
            ),
            class_="city-header-inner",
        ),
        class_="city-header",
        id="city-header",
    )


def site_footer(source: SourceInfo):
    return ui.tags.footer(
        ui.img(
            src="assets/city-of-sacramento-signature-white.png",
            width="210",
            height="51",
            alt="City of Sacramento",
        ),
        ui.p("Built for understanding. Grounded in the data."),
        ui.a("Sources, definitions & limitations", href="#about"),
        ui.p(disclosure(source, "footer"), class_="footer-meta"),
        class_="city-footer",
    )


def sample_banner(source: SourceInfo):
    return ui.div(
        ui.strong(disclosure(source, "banner_title")),
        ui.span(disclosure(source, "banner")),
        class_="sample-notice",
    )


def stat_card(label: str, value: str, detail: str):
    return ui.div(
        ui.h2(label),
        ui.p(value, class_="stat-value"),
        ui.p(detail, class_="muted"),
        class_="stat-card",
    )


def selection_trail(view: ViewState, count: int, total: int, *, labels=DIMENSIONS):
    """Every active constraint is visible and independently removable."""
    chips = [
        ui.a(
            f"{label}: {value} ×",
            href=view.href("home", **{key: "", "record": ""}),
            data_keep_page="true",
            aria_label=f"Remove {label.lower()} filter: {value}",
            class_="selection-chip",
        )
        for key, label, value in view.filters(labels=labels)
    ]
    return ui.div(
        ui.p(
            f"{count:,} of {total:,} records" + (" · All records" if not chips else ""),
            class_="filter-summary",
            role="status",
        ),
        ui.tags.nav(
            ui.a("All records", href=view.clear().href(), data_keep_page="true"),
            *chips,
            aria_label="Current selection",
            class_="selection-trail",
        ),
        class_="selection-context" + (" unfiltered" if not chips else ""),
    )


def drill_breadcrumbs(view: ViewState):
    """Ancestor links remove deeper levels while retaining month and search."""
    if not any(getattr(view, key) for key in DIMENSIONS):
        return None
    root = replace(view, record="", **{key: "" for key in DIMENSIONS})
    links = [ui.tags.li(ui.a("Overview", href=root.href()))]
    for key in DIMENSIONS:
        value = getattr(view, key)
        if value:
            links.append(ui.tags.li(ui.a(value, href=view.drill(key, value).href())))
    return ui.tags.nav(
        ui.tags.ol(*links, class_="drill-breadcrumbs"), aria_label="Drill path"
    )


def select_control(key: str, label: str, choices: dict[str, str], selected: str):
    """Native control, bound to the single bookmarkable selection by shell.js."""
    return ui.div(
        ui.tags.label(label, for_=key),
        ui.tags.select(
            *[
                ui.tags.option(text, value=value, selected=value == selected)
                for value, text in choices.items()
            ],
            id=key,
            data_state=key,
        ),
        class_="state-control",
    )


def comparison_chart(
    entries: list[tuple[str, int, int]],
    left: str,
    right: str,
    *,
    caption: str = "Source: bundled fictional sample. These are record counts, not amounts.",
):
    """Paired monthly count bars on one scale, with an exact-value table."""
    maximum = max((max(a, b) for _, a, b in entries), default=1) or 1
    return ui.tags.figure(
        ui.h2("Monthly record counts"),
        ui.p(
            f"A: {left} · B: {right}. Both series use the same scale.", class_="muted"
        ),
        ui.tags.ul(
            *[
                ui.tags.li(
                    ui.strong(month),
                    ui.div(
                        *[
                            ui.div(
                                ui.span(label, class_="series-label"),
                                ui.span(
                                    ui.span(
                                        class_=f"bar-fill series-{index}",
                                        style=f"width:{100 * value / maximum:.4f}%",
                                    ),
                                    class_="bar-track",
                                    aria_hidden="true",
                                ),
                                ui.span(str(value), class_="bar-value"),
                                class_="paired-row",
                            )
                            for index, (label, value) in enumerate((("A", a), ("B", b)))
                        ]
                    ),
                )
                for month, a, b in entries
            ],
            class_="paired-chart",
        ),
        ui.tags.details(
            ui.tags.summary("View exact comparison values"),
            ui.tags.table(
                ui.tags.caption("Monthly counts for both comparison groups"),
                ui.tags.thead(
                    ui.tags.tr(
                        *[
                            ui.tags.th(label, scope="col")
                            for label in ("Month", left, right)
                        ]
                    )
                ),
                ui.tags.tbody(
                    *[
                        ui.tags.tr(
                            ui.tags.th(month, scope="row"),
                            ui.tags.td(str(a)),
                            ui.tags.td(str(b)),
                        )
                        for month, a, b in entries
                    ]
                ),
                class_="data-table",
            ),
            class_="chart-values",
        ),
        ui.tags.figcaption(caption),
        class_="chart-frame",
    )


def record_panel(row: Record, source: SourceInfo, view: ViewState):
    """Record fields, missing-value explanation, source snapshot, and related links."""
    return ui.div(
        ui.p(disclosure(source, "record_eyebrow"), class_="eyebrow"),
        ui.h2(row.record_id, id="record-title", tabindex="-1"),
        ui.tags.dl(
            *[
                ui.div(ui.tags.dt(label), ui.tags.dd(value))
                for label, value in (
                    ("Date", row.date.isoformat()),
                    *[(source.label(key), getattr(row, key)) for key in DIMENSIONS],
                    (
                        f"Recorded value ({source.value_unit})",
                        format_value(row.value, source.value_unit),
                    ),
                )
            ]
        ),
        ui.p("Not recorded means missing, never zero. " + source.limitation),
        ui.a(
            f"Explore this {source.label('category').lower()}",
            href=view.clear().href("explore", category=row.category),
            class_="primary-link",
        ),
        ui.a(
            f"Compare this {source.label('category').lower()}",
            href=view.href(
                "compare", compare_by="category", left=row.category, right="", record=""
            ),
            class_="secondary-button",
        ),
        ui.p(
            f"Source: {source.name}. Snapshot {source.updated_at.isoformat()}.",
            class_="muted",
        ),
        data_record_content=row.record_id,
    )


def state_panel(state: str, *, filtered: bool = False, sample: bool = True):
    """Explain an empty, loading, or unavailable view. Other states show data instead.

    `sample` selects preview wording (simulated conditions) or live wording.
    """
    if sample:
        messages = {
            "empty": (
                "No matching records" if filtered else "No records to show",
                "Try a different search or use Reset filters."
                if filtered
                else "This example is intentionally empty. Choose Available data in the preview controls to continue.",
            ),
            "error": (
                "The example data is unavailable",
                "This is a simulated error, not a failed connection. Choose Available data to restore the example.",
            ),
            "loading": (
                "Loading the example",
                "This is a paused loading preview. Choose Available data to continue.",
            ),
        }
    else:
        messages = {
            "empty": (
                "No matching records" if filtered else "No records to show",
                "Try a different search or use Reset filters."
                if filtered
                else "The source returned no records.",
            ),
            "error": (
                "The data is unavailable",
                "The source could not be read. Try again later; if it persists, contact the app maintainer.",
            ),
            "loading": ("Loading", "The data is being loaded."),
        }
    if state not in messages:
        raise ValueError(
            f"state_panel handles {list(messages)}; '{state}' shows records instead."
        )
    title, message = messages[state]
    return ui.div(
        ui.div(class_="loading-placeholder", aria_hidden="true")
        if state == "loading"
        else None,
        ui.h2(title),
        ui.p(message),
        class_=f"state-panel state-{state}",
        role="alert" if state == "error" else "status",
    )


def unavailable_panel(dataset: Dataset):
    """The state panel for a dataset with no current records, else None."""
    if dataset.records:
        return None
    return state_panel(
        dataset.state if dataset.state in UNAVAILABLE_STATES else "empty",
        sample=dataset.source.is_sample,
    )


def status_message(source: SourceInfo, state: str) -> str:
    """One sentence for the source-status line, keyed on the data state and is_sample."""
    if source.is_sample:
        messages = {
            "stale": "Showing the last available sample snapshot. A newer snapshot is unavailable in this simulation.",
            "missing": "Some fields are intentionally missing. Missing amounts are excluded from calculations, never counted as zero.",
            "error": "Data-unavailable preview. No connection attempt was made.",
            "loading": "Loading preview is paused until you choose another condition.",
            "empty": "Empty-data preview.",
        }
        return messages.get(state, "Bundled example; no automatic refresh.")
    messages = {
        "stale": f"Showing the last available snapshot from {source.updated_at:%B %d, %Y}; a newer read failed.",
        "missing": "Some fields are missing in the source. Missing values are excluded from calculations, never counted as zero.",
        "error": "The source could not be read.",
        "loading": "Loading data from the source.",
        "empty": "The source returned no records.",
    }
    return messages.get(state, f"Snapshot {source.updated_at:%B %d, %Y}.")


def bar_chart(
    title: str,
    entries: list[tuple[str, int]],
    *,
    description: str,
    chart_id: str,
    links: dict[str, str] | None = None,
    caption: str = "Source: bundled fictional sample. Counts are not City performance figures.",
):
    """Counts remain visible as text. A semantic table supplies the same exact values."""
    maximum = max((count for _, count in entries), default=1) or 1
    return ui.tags.figure(
        ui.h2(title, id=f"{chart_id}-title", tabindex="-1"),
        ui.p(description, class_="muted"),
        ui.tags.ul(
            *[
                ui.tags.li(
                    ui.a(
                        label, href=links[label], class_="bar-label", data_drill="true"
                    )
                    if links and label in links
                    else ui.span(label, class_="bar-label"),
                    ui.span(
                        ui.span(
                            style=f"width:{100 * count / maximum:.4f}%",
                            class_="bar-fill",
                        ),
                        class_="bar-track",
                        aria_hidden="true",
                    ),
                    ui.span(f"{count:,}", class_="bar-value"),
                )
                for label, count in entries
            ],
            class_="bar-chart",
            aria_label=f"{title}, record counts",
        ),
        ui.tags.details(
            ui.tags.summary("View exact chart values"),
            ui.tags.table(
                ui.tags.caption(f"{title}: record counts"),
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("Group", scope="col"),
                        ui.tags.th("Records", scope="col"),
                    )
                ),
                ui.tags.tbody(
                    *[
                        ui.tags.tr(
                            ui.tags.th(label, scope="row"), ui.tags.td(str(count))
                        )
                        for label, count in entries
                    ]
                ),
                class_="data-table",
            ),
            class_="chart-values",
        ),
        ui.tags.figcaption(caption),
        class_="chart-frame",
        aria_labelledby=f"{chart_id}-title",
    )
