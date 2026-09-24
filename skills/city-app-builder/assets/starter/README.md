# Your City data app

This is a working sample-data app. Every included record is fictional; there are no live data connections.

## Open it

With Python 3.12 installed, open [Start app.cmd](Start%20app.cmd) on Windows, or run:

```text
python start.py
```

The first launch installs the locked app runtime into this folder's `.venv` and opens a browser. Keep the terminal open while using the app. Press Ctrl+C to stop. If port 8126 is already in use, the launcher chooses another local port and prints its address.

Install and run from a development folder, not a notes vault or Working Hub. The tested platform is Windows with Python 3.12 and Microsoft Edge.

## Try it

1. On the visual **Home** overview, select a trend point, status legend, heatmap cell, or record dot to explore. For hierarchical drilldown, select a category, then an area and status to reach the records. Select a month to narrow the view; use breadcrumbs or selection chips to broaden it.
2. Open **Explore**, choose filters, and search for a record. Open its ID for details; Escape closes the drawer. Use **Compare** for two groups, their measures, and monthly counts.
3. Download the matching rows. The CSV identifies every row as fictional.
4. Open **About** to see definitions, the example snapshot date, and limitations.
5. Use **Try another example or data condition** to see spending, missing fields, stale data, empty results, errors, or a paused loading view.

Your selections persist across views and in bookmarks, refresh, and browser history. Compare keeps every filter except its chosen comparison dimension, with the scope displayed above its results.

Loading and error previews are simulations. Choose **Available data** to return to the working example.

## Optional image banner

The overview uses a wide desktop canvas, with supporting charts side by side. A banner image is optional: set `banner` in [app_config.json](app_config.json) to `null` for the plain introduction, or use an object with `image`, `alt`, and `credit` strings. The image path is relative to `www`, such as `assets/historic-city-hall.jpg`; local JPG, JPEG, PNG, and WebP files are supported. Keep any replacement image in `www/assets` and describe and credit it honestly. [ASSETS.md](ASSETS.md) records the example photograph's origin and usage boundary.

## Ask your AI for a change

> Read AGENTS.md and APP-BRIEF.md if present. Make this app more useful for [audience] by [change]. Keep the data clearly fictional and preserve the City shell.

Basic wording and defaults live in [app_config.json](app_config.json). The future source belongs in the app brief; do not paste credentials into either file.

The data interface is in [city_app/data.py](city_app/data.py). It represents prepared records and source information, and its `PROVIDERS` registry is where a future SQL/API/Open Data connector is added. The app's sample disclosures switch automatically when a source declares `is_sample=False`, but a working loader does not establish that field meanings, units, freshness, and row limits have been verified.

## Check a change

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Then open the app and check the affected interaction at desktop and phone widths. The unit tests check data correctness, filtering, missing values, credits, and safe exports; they do not prove a layout works or establish full accessibility conformance.

## Manual startup

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
.venv/Scripts/python.exe -m shiny run --host 127.0.0.1 --port 8126 app.py
```

Open `http://127.0.0.1:8126`. See [ASSETS.md](ASSETS.md) for artwork and font provenance. This starter is a local internal preview, with no authentication, public hosting, or publishing workflow.
