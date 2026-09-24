# Build a preview

All paths here are relative to the skill folder. Keep the package outside a notes vault or synchronized Working Hub. Use a normal development folder such as the Desktop Data Storyboard workspace.

## Create an app

```powershell
python scripts/scaffold.py "C:/Projects/my-city-app" --title "Service Explorer" --sample services --future-source sql-server --banner
```

The destination must not exist. The script refuses to overwrite an app or write inside its own starter. It copies the complete starter and writes a short `APP-BRIEF.md`; update that brief with the actual conversation. Supported sample names: services, spending. Future-source choices: unknown, file, sql-server, api, sacramento-open-data. This flag records intent only. The default is no banner; use `--banner` only after the person chooses the bundled example image.

`app_config.json` controls the banner. Use `"banner": null` for no banner, or a local asset object such as:

```json
"banner": {
  "image": "assets/historic-city-hall.jpg",
  "alt": "Historic City Hall in Sacramento",
  "credit": "City of Sacramento · Historic City Hall"
}
```

The image path is relative to the starter `www` directory and must point to an existing local PNG, JPG, JPEG, or WEBP inside that directory. Do not use URLs or paths outside `www`. For a supplied image, copy it into the generated app's `www/assets` directory and set this object; if it is not yet available, keep `banner` as `null` and note it as pending in `APP-BRIEF.md`.

The generated app runs with `python start.py`, or by opening `Start app.cmd` on Windows with Python 3.12 installed. First launch installs the pinned runtime into that app's own `.venv`; subsequent launches reuse it. The launcher opens a local browser and keeps its terminal running. Stop with Ctrl+C. Never install packages in the user's notes vault.

For manual setup:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
.venv/Scripts/python.exe -m shiny run --host 127.0.0.1 --port 8126 app.py
```

## Editing map

| Change | Owner |
| --- | --- |
| Title, introduction, audience, default example, portal URL, banner image/alt/credit | `app_config.json` |
| Page composition, reactive wiring, table row cap (`MAX_TABLE_ROWS`) | `app.py` |
| Reusable header/footer, metric, state, chart presentation, and every sample/live wording (`disclosure`) | `city_app/components.py` |
| Record fields, drill `DIMENSIONS`, data `STATES`, sort `ORDERS`, sample sources, `PROVIDERS` registry, filtering, month grouping, calculation, export | `city_app/data.py` |
| Shared selection (`ViewState`), encoded links, drill hierarchy, group comparisons | `city_app/state.py` |
| Line/area trends, composition ring, heatmaps, record plots, plot point cap (`MAX_PLOT_POINTS`) | `city_app/visuals.py` |
| Display labels for category/area/status (relabel, never rename) | `SourceInfo.labels` in `city_app/data.py` |
| Sample rows | `samples/services.csv`, `samples/spending.csv` |
| City geometry, tokens, responsive behavior | `www/city.css` |
| Bookmarkable selection, control bindings, record dialog, focus, menu, sticky behavior | `www/shell.js` |
| Findings and user choices | `APP-BRIEF.md` |

Choose services for count/trend/record-lookup examples and spending for amounts/credits/group comparisons. Keep the actual sample domain visible. If neither fits, explain the mismatch; don't relabel a duration as a currency or claim the source was analyzed.

## Component recipes

- `site_header(title, portal_url)` and `site_footer()` provide the shared shell. The parent portal address is different from the app's `#home` destination.
- `stat_card(label, value, detail)` displays a formatted measure with its scope and denominator.
- `bar_chart(title, entries, description=..., chart_id=...)` renders labeled counts and a semantic exact-value table. Use a distinct chart ID for each instance.
- `unavailable_panel(dataset)` returns the right state panel when a dataset has no current records, else `None`; `state_panel(state, filtered=True)` covers a no-results search. Both, and `status_message(source, state)`, use preview wording for samples and plain wording for a live source.
- `disclosure(source, key)` supplies every sample-versus-live sentence, keyed on `SourceInfo.is_sample`. Never write "fictional" into a component directly.
- `format_value`, `measure`, `filter_records`, `monthly_groups`, and `export_csv` keep missing values, calculations, months, and downloads consistent.
- `source.label("area")` is the display name for a dimension. Pass `labels=source.labels` to `selection_trail` and `heatmap_chart`, and `label=source.label("status")` to `composition_chart`.

Read [components.md](components.md) for the complete connected-component catalog and recipes: linked drill charts, ancestor breadcrumbs, removable selection chips, record drawers, paired group comparisons, and persistent view state. Prefer those compositions over new abstractions. Visual-first overview recipes include trends, rankings, status composition, heatmaps, individual values, and source-defined means/sums; arbitrary charting, maps, and statistical inference are outside this version.

## Focused verification

Run the generated project's unit tests:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Then inspect the running app in one batch:

1. Home, Explore, Compare, and About, including direct hashes and browser Back/Forward.
2. Category + area + status + month + text search, Reset filters, ordering, and a CSV matching the filtered results.
3. Category → area → status → records, ancestor breadcrumbs, month selection, record drawer keyboard/refresh/Escape, and comparison scope/group links.
4. Both examples and missing, stale, empty, error, and loading previews.
5. Desktop 1440px and 1920px, tablet 800px, mobile 390px, and narrow 320px. Inspect wide 2048px when shell/layout changes. Confirm the City header keeps its height and identity, desktop gutters stay near 32px, the primary trend remains dominant, and a banner (if enabled) does not bury charts or sample labels.
6. Keyboard navigation, skip link, mobile menu selection/Escape, chart exact-value tables, and absence of horizontal page overflow.

Fix observed problems and confirm those fixes. Do not claim live-source validation, production readiness, or full accessibility conformance. For release-oriented work, the full visual guide's accessibility acceptance requirements still apply.
