# Data Storyboard Template

**Turn a question about City work into a visual, local data app with a short conversation in your coding assistant.**

Data Storyboard Template is a Python Shiny starter for City colleagues who want to build an explorable, visuals-first data app without beginning from a blank page. It includes a guided app-building skill, reusable City-styled components, and clearly labeled fictional examples to make the first version concrete.

**v0.6.1 · Python Shiny · samples and opt-in data connectors**

## Create your own app

Copy this message into a coding assistant that has access to this repository:

```text
Help me build a data web app using this template:
https://github.com/socDocarol/data-storyboard-template

Before asking questions or writing code, read the repository's README.md and AGENTS.md, then follow skills/city-app-builder/SKILL.md.

Treat this as a new, isolated app. Reuse only the requirements I have given for this app. Do not use an earlier app's files, data, decisions, or running preview unless I explicitly ask you to.

Before building, help me clarify what the app should answer, which data and measures matter, and which dashboard views and drilldowns I need. Ask missing questions one at a time, with useful recommendations. Keep discovery short, but do not skip essentials to meet a question count. Save banner and other cosmetic choices until the scope is clear.

Summarize the agreed scope and any unconfirmed assumptions. Once the essentials are clear, create my app in a new folder inside this workspace using the bundled starter. Adapt the data and dashboard views to that scope, preserve existing apps, and begin with clearly labeled sample data. Do not present an unchanged starter with a new title as a tailored app.

Launch with the generated app's start.py, use its printed URL, and verify the page belongs to the new app before checking its views and interactions. Explain exactly how I can open it and what is still sample data. Keep explanations short and practical.
```

Your assistant will ask a few short questions and create your app in a new folder using clearly labeled sample data. When ready to connect data, put CSV/XLSX in the app's **Data** folder, or provide an HTTP API or Sacramento Open Data dataset link. Other local formats need a short choice about conversion or a specific reader.

**Coding agent: start here.** Read [AGENTS.md](AGENTS.md), then follow [the City App Builder instructions](skills/city-app-builder/SKILL.md) before asking discovery questions or building. Use the bundled starter and its existing workflow for the user's app.

![Data Storyboard Template overview: trends, rankings, composition, heatmap, and records](docs/images/overview.png)

## Optional: preview the sample yourself

You need **Windows and Python 3.12**. No manual package-install steps are needed.

1. Clone or download this kit into a normal development folder:

   ```powershell
   git clone https://github.com/socDocarol/data-storyboard-template.git
   cd data-storyboard-template
   ```

2. Open [Preview sample.cmd](Preview%20sample.cmd).
3. Keep its terminal window open while you explore. Press `Ctrl+C` there to stop the app.

The first launch creates a local virtual environment, installs the app runtime, and opens the app in your browser. Later launches reuse that setup. The sample runs locally at a loopback address.

Every included data record is fictional. The optional City Hall photograph supplies visual context, not source data. The preview does not connect to City systems, use credentials, or call an in-app AI service.

## What you can explore

The desktop-first Home view uses a wide canvas up to 1,920 pixels, with an optional image banner and a prominent trend. Ranked bars, status composition, a category-by-area heatmap, and selectable records share the space. Drill from a category, area, status, or month to the records behind it. Explore adds search, filters, record details, and a matching CSV download. Compare places two groups side by side and aligns their monthly patterns. About explains definitions and limits.

Selections stay with you as you move between views, refresh the page, or use browser Back and Forward. The preview also lets you switch between fictional service-request and spending examples, and show states such as missing, stale, empty, unavailable, and loading data.

Source notes and demo controls live behind the small **information icon** beside the introduction. Hover, focus, click, or tap it to reveal the details; open **Preview options** to switch examples. Escape or a click outside closes it. An amber icon flags data that needs attention.

![Record details drawer in the fictional service-request example](docs/images/record-details.png)

## Reusable pieces

| Included piece | What it gives you |
| --- | --- |
| [Guided app-building skill](skills/city-app-builder/SKILL.md) | A bounded discovery conversation, brief, build, and review workflow |
| [Working starter](skills/city-app-builder/assets/starter/) | Home, Explore, Compare, and About with linked visual drilldowns |
| [Component recipes](skills/city-app-builder/references/components.md) | Patterns for selections, details, comparisons, and visual compositions |
| [Data contract](skills/city-app-builder/references/data-contract.md) | The prepared record and metadata shape for every source |
| [Connector guide and examples](skills/city-app-builder/assets/starter/CONNECTORS.md) | CSV/XLSX in Data, JSON HTTP APIs, public ArcGIS, and SQL Server preparation |
| [Visual standard](skills/city-app-builder/references/city-visual-standard.md) | The bundled City visual rules used by the starter |
| [Scaffold command](skills/city-app-builder/scripts/scaffold.py) | A safe copy of the starter into a new app folder |

The included services sample has 48 invented requests. The spending sample has 48 invented entries, including credits. Sample labels remain visible in the app and every exported CSV row.

## Optional: scaffold from the command line

If you maintain the kit or prefer a direct starting point, run this from the kit root:

```powershell
python skills/city-app-builder/scripts/scaffold.py "C:/Projects/my-city-app" --title "My Data Explorer" --sample services --future-source sql-server
```

This creates a standalone copy only in a new folder. `--future-source` records the intended source; it does not create a connection. Available choices are `unknown`, `file`, `sql-server`, `api`, and `sacramento-open-data`. Open the new folder and run `python start.py`.

Add `--banner` to include the bundled image after choosing it. To use your own image, copy it into the new app's `www/assets` and set its `banner` image path, alt text, and credit in `app_config.json`. Set `banner` to `null` for the layout without an image. See the [build reference](skills/city-app-builder/references/building.md) for the exact format.

## Current scope

| Working now | Deferred in this release |
| --- | --- |
| Local preview; fictional samples; CSV/XLSX, paginated JSON HTTP, public ArcGIS connectors; linked visuals, drilldowns, filters, record details, comparison, and CSV | SQL Server live verification on a work computer; deployment/hosting; in-app AI/chat; unverified business definitions and performance claims |

Connectors use the existing dashboard and selections. Source errors and stale snapshots remain visible. Local data and active connection configuration are excluded from shared ZIPs. SQL Server uses Windows authentication and an existing table/view, reuses installed ODBC Driver 18 or 17, and has an offline prerequisite check. Mandatory guards reject unsafe SQL/configuration and writable or unverifiable permissions for the source; transactions are rolled back, never committed. IT-confirmed read-only access and live verification remain for the work computer.

The kit was tested on Windows with Python 3.12 and Microsoft Edge. Read the [verification record](docs/verification.md) for the checks performed and their limits. Read [maintenance instructions](docs/maintenance.md) to verify or package the kit.

## Assets and sharing

City branding and related assets are for internal use under the boundaries recorded in [ASSETS.md](skills/city-app-builder/assets/starter/ASSETS.md). This repository does not grant a public license for City identity artwork or imply one for City-specific code.
