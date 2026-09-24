# Prepared data, independent of its connection

The app supports one deliberately small analytical shape. It is not a universal database schema. A connector maps an approved source into this shape; the rest of the app never changes for a new source.

`assets/starter/city_app/data.py` is the single home for every data fact: the `Record` fields, the ordered drill `DIMENSIONS`, the data `STATES`, the sort `ORDERS`, the bundled sample `SOURCES`, and the `PROVIDERS` registry. Presentation modules import these; they never redefine them.

| Record field | Required meaning |
| --- | --- |
| record_id | Unique, nonempty text identifier; no silent duplicate counting |
| date | Python calendar date; the source description explains what date it is |
| category | Nonempty grouping label; use Not recorded for missing labels |
| area | Nonempty location/group label; use Not recorded when missing |
| status | Nonempty descriptive state; no inferred overdue/closed semantics |
| value | Finite number or None; never substitute zero for missing information |

**Relabel, never rename.** If the real data calls these "Department", "District", and "Stage", keep the field names and set `SourceInfo.labels={"category": "Department", "area": "District", "status": "Stage"}`. Every control, chip, heading, table header, and record drawer reads labels from the source. CSV exports keep the internal column names so downstream users get a stable file.

`SourceInfo` carries the source name, row definition, measure label, unit, explicit mean/sum aggregation, snapshot date, limitations, `is_sample`, and optional `labels`. Unit `USD` formats as currency; any other unit string is shown after the number (`9.4 days`, `1,500.0 hours`).

`Dataset.state` is ready, missing, stale, empty, error, or loading. Missing and stale can retain records. Empty, error, and loading contain no current records. Stale means an older usable snapshot, not a successful refresh.

## Working rules

- Home counts every record in the active source. Explore filters and its download share the same filtered records and ordering. Home is intentionally not affected by Explore filters; the UI states this.
- `filter_records` applies every selection (three dimensions, month, search, order) in one pass. `ViewState.select` is the only caller in the app; use it rather than filtering by hand.
- `monthly_groups` is the one month-by-month iterator. Trends, comparisons, and counts all use it, so zero-record months and year boundaries behave identically everywhere.
- Mean and sum use recorded values only, with the contributor count visible. No recorded values produces Not recorded, not zero.
- CSV text fields are protected against formula interpretation; numeric values remain numeric. Rows are labeled `FICTIONAL SAMPLE` when `is_sample` is true and `DATA` otherwise.
- The sample providers parse each CSV once per process and reuse the immutable records. Simulated conditions never mutate the cached base.
- The records table shows at most `MAX_TABLE_ROWS` rows (app.py) and the record plot at most `MAX_PLOT_POINTS` values (visuals.py); the CSV always contains every filtered record. Raise these only with a measured reason.

## Adding a connector

`load_dataset(name, condition)` in `data.py` is the only place the app asks for data. It dispatches to `PROVIDERS[name]`, a `Provider(source, load)` pair. The bundled samples are registered this way; a live source is added the same way.

1. Create `city_app/sources/<name>.py` (new folder) with a `SOURCE = SourceInfo(..., is_sample=False, labels={...})` and a `def load(condition: DataState) -> Dataset`. Fetch outside the UI, validate, map columns into `Record` (dates as `date`, missing values as `None`, missing labels as `Not recorded`), and return `Dataset(records, SOURCE, state)`. Report a real `state`: `error` on a failed fetch, `stale` with the last good snapshot if you keep one, otherwise `ready`. Ignore the preview `condition` or map it deliberately.
2. Register it in `data.py`: `PROVIDERS["<name>"] = Provider(SOURCE, load)`. Do not edit `load_sample`.
3. Set `"sample": "<name>"` in `app_config.json` and set `"show_preview_controls": false` unless the sample switcher should remain.
4. Decide row limits: page or cap the query before building records. The app is not a substitute for pagination on a 100k-row table.
5. Run `python -m unittest discover -s tests -v` and open the app. The fictional-sample banner, footer, captions, record drawer, download label, About text, and CSV label all switch automatically because they read `disclosure(source, key)` in `components.py`, keyed on `is_sample`. Nothing else in the app decides whether data is fictional.
6. Update the About wording and `APP-BRIEF.md` with the verified row definition, unit, aggregation, freshness, and limitations. A working loader does not establish that the field meanings are right.

Never put credentials in `app_config.json`, the brief, or source code. Read them from the environment inside the loader and document the variable names in the brief.
