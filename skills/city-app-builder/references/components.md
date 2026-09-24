# Connected dashboard recipes

Use these tested behaviors as a unit. A useful app connects summary, context, comparison, and records; adding more independent charts does not create that experience. Do not promise superiority to another BI platform or assume every app needs every component.

## Visual selection and screen hierarchy

The first screen is a visual overview: an optional civic banner, compact headline numbers, a prominent primary plot, then a few complementary views. Use short titles/units and one-line hints. Full tables, methods, interpretation, and longer explanations belong in drilldowns, expandable notes, and About. Source/sample status and meaningful stale/missing warnings remain visible. At desktop size the primary chart should begin within the first viewport.

Use a banner only when the person selected it. It is local civic imagery with meaningful alt text and an honest credit, never a simulated chart or source evidence. Keep it visually subordinate to the main analytical task: it must not cover the primary trend, sample disclosure, warnings, or controls. Lay out desktop screens first through 1920px with roughly 32px outer gutters, a dominant trend, and compact supporting charts; retain the shared City header height/identity and responsive mobile behavior.

| Data/question | Working component | Behavior |
| --- | --- | --- |
| How does a measure change by month? | `trend_chart(entries, source, links, area=False)` | SVG line; optional area fill for sums; month-point links, native month links, exact table |
| Which group has more records? | `bar_chart(..., links=...)` | Ranked bars; linked hierarchy |
| What is the status mix? | `composition_chart(entries, links, label=...)` | Ring by count with linked count/percentage legend; known statuses keep stable colors, other groups never share one within a chart |
| Where do groups concentrate? | `heatmap_chart(records, view, labels=...)` | Area × category counts; numbered, linked cells; contained scrolling on phones |
| What do individual values look like? | `record_plot(records, source, view)` | Value against date; linked points open record details; exact linked table; above `MAX_PLOT_POINTS` values it asks for a narrower view |
| How do two groups differ? | `comparison_chart(...)` | Paired monthly count bars; same scale and exact table |

These components are implemented in [visuals.py](../assets/starter/city_app/visuals.py) and [components.py](../assets/starter/city_app/components.py). They render locally with native HTML/SVG; no chart service or additional runtime library is needed.

The sample overview demonstrates five complementary forms. Choose fewer when the task is simpler. Do not use a donut for many categories or signed amounts; this one encodes nonnegative record counts. Heatmaps supplement exact values rather than relying on color alone. Record plots show values over dates, not correlation between two independent measures. Large datasets require an explicit aggregation or sampling policy before reusing the record plot; the current examples have 48 rows.

`monthly_measures` applies the declared source aggregation per month through the shared `monthly_groups` iterator, includes contributor counts, and retains missing months as gaps. An absent sum is missing, not zero. Trend paths break at gaps. All numeric axes include zero and preserve negative values. Native exact tables and links remain available to keyboard and assistive-technology users. Do not invent findings from the chart's shape.

Maps, treemaps, histograms, calendar grids, target/bullet charts, and forecasting are not bundled implementations. Use a map only after geographic fields or boundaries are verified, and a target chart only after a target is defined. Add a specialized component for an actual task, without asking the person a long chart-design questionnaire.

## Choose a recipe without another interview

| The person's main task | Assemble | Sensible starting choice |
| --- | --- | --- |
| Understand a change or pattern | Primary trend + ranking + complementary composition/heatmap + record drawer | Category → area → status → records |
| Compare groups | Two-group comparison + explicit scope + difference + paired monthly chart + links to each group's records | First two available groups; user can change either |
| Find and inspect something | Search + categorical/month filters + sortable record table + drawer + matching CSV | Newest records first |
| Move from a summary to an explanation | Breadcrumbs + removable selections + source/definition notes | Retain context across pages and in the URL |

Recommend the recipe from the existing purpose and inspected fields. Keep the skill's three-question discovery budget; do not ask separately about every chart, filter, drill level, and interaction. If the person has not supplied verified field meanings, use the named fictional example and record tentative mappings in the brief.

## Working component catalog

All paths below are relative to the starter. Components accept prepared values; they do not fetch data.

| Component | Contract and use |
| --- | --- |
| `site_header`, `site_footer` | Shared City shell, responsive menu, source link |
| `stat_card(label, value, detail)` | Measure with explicit selection scope and contributor count |
| `selection_trail(view, count, total, labels=...)` | Visible filter chips in display order, independent removal, reset; shared across every page |
| `drill_breadcrumbs(view)` | Ancestor links remove deeper hierarchy levels while retaining month/search |
| `bar_chart(..., links={label: href})` | Labeled count bars, keyboard-operable group/month links, exact-value table |
| `select_control(key, label, choices, selected)` | Native accessible control connected to URL selection through `data-state` |
| `record_panel(row, source, view)` | Record fields, missing-value explanation, source snapshot, related-category and comparison links inside the modal drawer |
| `comparison_chart(entries, left, right, caption=...)` | Paired monthly counts on one scale; A/B text labels and exact-value table |
| `state_panel(state, filtered=..., sample=...)`, `unavailable_panel(dataset)`, `status_message(source, state)` | Loading, empty, no matches, and unavailable states with preview or live wording; other states raise so a mistake is visible |
| `disclosure(source, key)` | Every sample-versus-live sentence; keyed on `is_sample` |

Presentation lives in [components.py](../assets/starter/city_app/components.py); composition is in [app.py](../assets/starter/app.py). Selection and analytics are in [state.py](../assets/starter/city_app/state.py); browser navigation, dialog focus, and native control bindings are in [shell.js](../assets/starter/www/shell.js).

## Selection contract

`ViewState` is the single server-side selection. `select(records)` applies category, area, status, month, search, and order in one pass through `filter_records`. Use that result for overview measures, drill charts, the table, detail lookup, and CSV. Never recalculate a chart against the full dataset accidentally. `filters()` lists the active constraints in display order for chips and scope text; `without_record()` strips the open record.

The server keeps two reactive values: `view` (everything the browser sent) and `selection` (the same without the open record, updated only when it differs). Charts, tables, and downloads read `selection`, so opening or closing a record drawer never redraws them and focus returns to the originating link. Only `record_details` reads `view`.

`drill(dimension, value)` sets a level and clears its descendants. The current sample hierarchy is defined by the ordered `DIMENSIONS` mapping: category → area → status. This is an analytical grouping path, not a claim that every area's real organizational parent is a category. Keep names and hierarchy aligned to the verified data model when adapting the starter.

`href(page, **changes)` encodes a complete view into the fragment, including the sample, selections, comparison groups, order, and open record. Route-only navigation preserves context. Links are reproducible against the same bundled sample; they do not grant access to a remote source. Search terms and record IDs are visible in the address, so do not put credentials or confidential free text there.

The browser sends `dashboard_state` only after Shiny initialization. Server-generated links and native controls use the same state. Hash navigation restores selections on Back, Forward, and refresh. Do not add a separate set of independent chart filters or AI calls on clicks.

## Comparison semantics

Comparison uses `view.select(records, omit=view.compare_by)`: retain every constraint except the dimension being compared. State this scope above the results. If fewer than two groups remain, suggest broadening the view. Each card links to its own records under the same remaining constraints.

Use `compare_groups` to return each group's record count, contributor count, and measure. The source defines **mean** or **sum**. Means are calculated independently from contributing records, never by averaging already aggregated groups. Missing is not zero. Negative amounts remain negative.

Difference is **B − A**. Percentage is **(B − A) / abs(A) × 100**; it is undefined for a zero A or missing measure. Present neutral differences, not red/green performance judgments. Monthly comparison bars are **counts**, regardless of the measure's unit.

## Detail behavior

Record IDs link to a native modal dialog. It supports keyboard activation, Escape, trapped focus, return focus to the originating row, refreshed record links, and an unavailable-record message. Resolve the record within the active filtered rows; never silently show a record outside the selected scope. Do not insert data using raw HTML.

## Verification when composing

Check one complete journey: select category → area → status → open records → inspect a record → close it → compare groups → follow one group's records → download. Confirm counts, identifiers, and calculations agree at each step. Check an ancestor breadcrumb, independent chip removal, month selection, refresh, and Back/Forward. Include missing means, a zero/negative comparison baseline, long labels, and phone-width comparison/detail layouts.

This library supplies five visual forms plus paired comparison bars, drilldowns, and record inspection over two bundled samples. Maps, editing, writeback, forecasting, saved accounts, access control, and live connectors are not implemented. Add a specialized component only for an actual user task; keep the shared selection/source contract intact.
