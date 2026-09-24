# Your City data app

This is a working sample-data app. Every bundled record is fictional. CSV/XLSX, JSON HTTP, and public ArcGIS connectors are available when activated; SQL Server setup is prepared for a work computer.

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
5. Hover, focus, click, or tap the **information icon** beside the introduction. Open **Preview options** to see spending, missing fields, stale data, empty results, errors, or a paused loading view. Escape or clicking outside closes the panel.

Your selections persist across views and in bookmarks, refresh, and browser history. Compare keeps every filter except its chosen comparison dimension, with the scope displayed above its results.

Loading and error previews are simulations. Choose **Available data** to return to the working example.

## Optional image banner

The overview uses a wide desktop canvas, with supporting charts side by side. A banner image is optional: set `banner` in [app_config.json](app_config.json) to `null` for the plain introduction, or use an object with `image`, `alt`, and `credit` strings. The image path is relative to `www`, such as `assets/historic-city-hall.jpg`; local JPG, JPEG, PNG, and WebP files are supported. Keep any replacement image in `www/assets` and describe and credit it honestly. [ASSETS.md](ASSETS.md) records the example photograph's origin and usage boundary.

## Ask your AI for a change

> Read AGENTS.md and APP-BRIEF.md if present. Make this app more useful for [audience] by [change]. Keep source/sample labels truthful and preserve the City shell.

Basic wording and defaults live in [app_config.json](app_config.json). The selected or future source belongs in the app brief; do not paste credentials into either file. Put CSV/XLSX in [Data](Data/) and follow [CONNECTORS.md](CONNECTORS.md). For other local formats, ask whether to convert or add a reader.

The data interface is in [city_app/data.py](city_app/data.py). It represents prepared records and source information, and its `PROVIDERS` registry is shared by samples and configured connectors. The app's sample disclosures switch automatically when a source declares `is_sample=False`, but a working loader does not establish that field meanings, units, freshness, and row limits have been verified.

## Check a change

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Then open the app and check the affected interaction at desktop and phone widths. The unit tests check data correctness, filtering, missing values, credits, and safe exports; they do not prove a layout works or establish full accessibility conformance.

## Agent-run preview

```powershell
python start.py --no-browser
```

Use the app folder and exact URL printed by this launcher. It verifies the newly
started server before printing the URL, so another app at a familiar localhost
address cannot silently become this preview. Confirm the page title and source
match this app. Do not launch with a fixed-port command or stop an unrelated app.

See [ASSETS.md](ASSETS.md) for artwork and font provenance. This starter is a local
internal preview, with no authentication, public hosting, or publishing workflow.
