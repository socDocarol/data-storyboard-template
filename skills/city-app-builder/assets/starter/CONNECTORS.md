# Connect data to this app

Keep using the same Home, Explore, Compare, About, drilldowns, and downloads.
Your coding assistant configures the source and confirms what its fields mean.
The default preview still uses fictional data.

## Local files: the easiest starting point

1. Put a CSV or XLSX in [Data](Data/).
2. Tell your assistant the file name and what you want to understand.
3. The assistant inspects a small sample, maps the columns, checks the connector,
   and activates it. Restart the app to use the new source.

Other formats require a short choice: convert to CSV/XLSX, or add a reader for
that format. Do not silently treat JSON, XLS, XLSM, or another file as supported.
For XLSX, choose a sheet when there is more than one; use a values-only copy if
the sheet contains formulas. The app never calculates Excel formulas.

## Try a complete connector example

Run these commands **inside a generated app**, using its Python environment after
the first launch has installed dependencies. The template itself stays a sample.

```powershell
.venv/Scripts/python.exe connect.py example local-csv
python start.py
```

The example copies the bundled 48 fictional requests into `Data/example-services.csv`,
validates them, and selects the file provider. `local-xlsx` does the same with an
Excel workbook. Existing example files are never overwritten. To reuse one, run
`connect.py activate examples/local-csv.json` or its XLSX equivalent.

For a paginated HTTP example, keep this running in a second terminal:

```powershell
.venv/Scripts/python.exe examples/serve_api.py
```

Then run `connect.py example http-api` and restart the app. This reads all four
pages from the local example API. Its records remain clearly labeled fictional.
The endpoint uses port 8130 and no credentials.

For real public data, run `connect.py example sacramento`, then restart. It reads
the published Sacramento 311 layer for January 1 through January 7, 2025, using
UTC dates. It selects no geometry, addresses, or narrative descriptions. The numeric measure counts published rows: each incident contributes one. No
duration, lateness, or performance measure is inferred. About states the scope and limitations.

## Configure another source

Copy the closest JSON in [examples](examples/) to a private configuration file.
Keep the six internal column keys; change only their source column names. The
`category`, `area`, `status`, and `value` mappings can be `null`: grouping labels
become **Not recorded**, and values stay missing. IDs and dates are required.
Labels can change via `source.labels`; bookmark keys and CSV columns stay stable.
For an explicit row-count measure, set `value_mode: "count"`, `columns.value: null`,
and `source.aggregation: "sum"`. Each row then contributes one. Otherwise leave
`value_mode` as `column` (the default); a missing numeric value remains missing.

Set `source.is_sample` honestly. Confirm the row definition, date meaning,
measure, unit, and `mean` or `sum` aggregation. Do not turn invented data into
real data by switching the flag. Local snapshots require `source.updated_at`.
For a remote source without it, the displayed snapshot date is retrieval date,
explicitly described in About. It is not a claim that all records are current.

```powershell
.venv/Scripts/python.exe connect.py inspect my-file.xlsx --sheet Requests
.venv/Scripts/python.exe connect.py check my-source.json
.venv/Scripts/python.exe connect.py activate my-source.json
```

`inspect` shows field names and missing/type counts from at most 100 rows of a
1 MB file, without printing record values. `check` loads and validates but does
not activate. `activate` checks first, writes `data_source.json`, and selects
`connected` in `app_config.json`, hiding preview simulation controls. Do not put
credentials in either JSON file. Keep personal configurations in `Data` or use
the ignored active `data_source.json`; only generic examples belong in Git.

Supported dates: ISO dates/timestamps (calendar date as written), Excel date
cells, `date_format: "unix_ms"` (UTC), or an explicit Python strptime format such
as `%m/%d/%Y`. Never guess a day/month convention. Numbers must be finite plain
numbers, without currency symbols or thousands separators. Missing values are
never zero. Invalid dates/IDs/values, missing mapped columns, and duplicate IDs
reject the entire load.

### HTTP JSON APIs

Set `kind: "http"`, `url`, and `records_path` (empty for a top-level array,
`data.items` for a nested array). HTTP is allowed only for loopback examples;
external endpoints require HTTPS. Requests are GETs. Choose pagination explicitly:

| Mode | Configuration and completion rule |
| --- | --- |
| `none` | One complete response. Use only for an endpoint documented to be unpaginated. |
| `next` | `next_path` identifies the next URL; a null or empty URL ends the result. Links must stay on the same origin. |
| `page` | `parameter` (default `page`), `start` (default 1), `size_parameter` (default `limit`), `page_size` (default 500). Stops at an empty page. |
| `offset` | Same options, default `offset` parameter and start 0. Advances by rows received; stops at an empty page. |

APIs using POST, GraphQL, OAuth token acquisition, non-URL cursors, or custom
signing need a source-specific adapter. The assistant should explain the gap
and ask about the source's supported access method, not claim universal support.
For header authentication, add `"auth": {"env": "MY_API_TOKEN"}` for a Bearer
header. API keys can use `"header": "X-API-Key", "prefix": ""`. Set secrets in
the operating-system environment. URLs cannot contain credentials. Redirects
fail with a request for the final URL; credentials are never forwarded across
redirects or to a different next-page origin.

### Sacramento and other ArcGIS Open Data

The [City's portal](https://www.cityofsacramento.gov/information-technology/gis/data)
publishes ArcGIS resources. Use `kind: "arcgis"` with a Hub dataset URL containing
an item ID, an ArcGIS item URL, or a numbered FeatureServer/MapServer layer URL.
An item with multiple layers needs an explicit `layer_id`. Inspect before mapping:

```powershell
.venv/Scripts/python.exe connect.py arcgis-info "https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/SalesForce311_View/FeatureServer/0"
```

The connector reads layer metadata, checks mapped fields, applies the configured
`where` filter, counts rows, captures all matching object IDs, then fetches them
in batches no larger than the service's record limit. It checks every returned
ID and rejects incomplete downloads. Coded-value domains are decoded for grouping
labels. ArcGIS errors inside a successful HTTP response are still failures.
The download is a best-effort snapshot, not a database transaction; concurrent
edits can require a retry. Queries are read-only and geometry is not downloaded.

This supports public queryable ArcGIS layers and tables. Catalog pages without
a dataset ID, dashboards, maps, documents, raster/image services, attachments,
related tables, and authenticated ArcGIS services are not automatically flattened
into records. Use the underlying public layer or a supplied CSV/XLSX. No source
can create a meaningful time-series dashboard without a verified date field.

The [311 example layer](https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/SalesForce311_View/FeatureServer/0)
uses `DateCreated`, `CategoryLevel1`, `CouncilDistrictNumber`, `PublicStatus`, and `OBJECTID`. Its ArcGIS publisher is `Applications_SacCity`; the exact dataset is linked from the official City page. The current view retains calls last updated on or after January 1, 2023, so a historical date filter does not establish completeness.
The [City's 311 maps page](https://www.cityofsacramento.gov/information-technology/311/incident-maps)
describes the published incidents. Follow the portal's dataset terms and
limitations. [Esri documents ID-based querying](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/).

### SQL Server: Windows authentication with minimal setup

The adapter uses the Windows account running this local app. There is no SQL
username/password prompt and no connection-string environment variable. Use
[examples/sql-server.json](examples/sql-server.json) as the starting point.
No work database has been accessed here.

1. Run `connect.py doctor examples/sql-server.json` on the work computer. This
   checks local prerequisites only. Reuse an installed Microsoft ODBC Driver 18
   or 17; 18 is preferred when both are present. The app does not install or
   upgrade system drivers or create an ODBC DSN. If neither is available to this
   Python environment, ask IT about the approved driver.
2. If the optional Python adapter is missing, install it only in the app's
   environment: `.venv/Scripts/python.exe -m pip install -r requirements-sql.txt`.
   The sample app and other connectors do not require it.
3. Set `server`, `database`, and `table` in a private copy of the example JSON.
   `table` is the schema-qualified name of an **existing table or view** your
   Windows account is already allowed to read. Map its actual columns and set
   a useful date range. No dedicated view, new login, or schema change is made by the app. Existing
   access must pass the strict read-only checks below; SELECT access alone is
   insufficient if the account also has write or administrative permissions. Confirm the row
   definition, dates, units, and aggregation as usual.
4. Run `connect.py check` with that configuration, then `connect.py activate`
   when it succeeds. Keep using the normal Windows work account and work
   network/VPN. The example starts with a 1,000-row cap; narrow the date range
   if it is exceeded rather than silently accepting a partial result.

Only nonsecret connection details belong in configuration. The adapter builds
`Trusted_Connection=yes` itself and does not accept raw connection strings or
SQL credentials. It requests read-only access, retains encrypted transport and
certificate validation with either driver, and queries only the configured
object and columns. Driver selection can be pinned with `driver` when IT
requires one of the supported installed versions.

Reads use a bounded `SELECT TOP`, parameterized date filters, short timeouts,
normal SQL read consistency, and prompt cursor/connection cleanup. Autocommit
is disabled; the connector never commits and always attempts rollback before
closing, on both success and failure. The code does not use a connection context
manager that might implicitly commit.

#### Strict SQL guardrails

These protections are mandatory; there is no configuration switch to bypass them.

- **Restricted configuration and execution:** unknown settings, raw SQL,
  procedures, hooks, custom WHERE clauses, credentials, and connection options
  are rejected. Server/database names cannot contain connection-string options.
  The only statements the execution boundary accepts are three fixed metadata
  SELECTs and the generated single-object, selected-column SELECT. It rejects
  writes, DDL, `EXEC`, `SELECT INTO`, sequences, comments, extra statements, and
  direct linked-server/cross-database references. This is a narrow template
  boundary, not a general-purpose SQL sanitizer.
- **Checks before reading source rows:** verify the selected database and a named
  user table/view in its catalog, reject sysadmin/database-owner sessions, then
  examine effective permissions at server, database, configured schema, and
  configured object scopes. A conservative read-permission allowlist rejects
  write, execute, control/ownership, impersonation, and any unknown permission.
  It includes permissions inherited through Windows groups and database roles.
- **Column checks:** require SELECT on each mapped column and no UPDATE permission
  on any column of the target, including unmapped columns. This matters because
  SQL Server column grants can override an object-level DENY. Missing, NULL,
  incomplete, or failed checks stop before the data SELECT. Newly introduced
  harmless permissions can also be refused until explicitly reviewed.
- **Failure handling:** a safety refusal clears the provider's cached snapshot
  and shows an error; it cannot silently continue with a stale SQL result. The
  offline `doctor` never connects and explicitly reports that permissions have
  not been verified. `check`, `activate`, and every subsequent database fetch
  run the same guards. Ordinary cached reads issue no SQL.

No permissions, roles, database objects, logins, drivers, or server settings are
changed automatically. The permission check inspects the configured target; it
is not an audit of every object, module, or impersonation path on the server.
A local table/view name does not prove local storage: external tables, computed
columns, and views/functions can depend on other objects or systems. Use only
DBA-approved targets; their definitions and dependencies remain a trust boundary.

**Application guards are not a database-enforced guarantee.** `readonly=True`
and `ApplicationIntent=ReadOnly` are requests/hints, and rollback does not undo
all possible external effects. For a guarantee enforced independently of this
editable application, IT must confirm SELECT-only access for the Windows
identity, or provide an existing read-only reporting database/readable secondary
that rejects writes. Permissions can change after a preflight. Do not weaken
checks, alter production permissions, or change a production database to
read-only automatically. If the ordinary Windows account is too privileged,
ask IT for an approved read-only access arrangement. Actual SQL verification
still waits for the work computer. SacMarina SQL remains separate.

See Microsoft's [effective-permission function](https://learn.microsoft.com/en-us/sql/relational-databases/system-functions/sys-fn-my-permissions-transact-sql?view=sql-server-ver17),
[ODBC read-only attribute limits](https://learn.microsoft.com/en-us/sql/odbc/reference/syntax/sqlsetconnectattr-function?view=sql-server-ver17),
and [Windows authentication guidance](https://learn.microsoft.com/en-us/sql/odbc/reference/develop-app/driver-specific-connection-information?view=sql-server-ver17).

## Limits, refresh, and sharing

Loads are capped at 10,000 rows (`max_rows` can lower this), 10 MB of file/network
input, 100 API pages, 15 seconds per HTTP request, and 60 seconds per HTTP load.
XLSX expansion is capped at 50 MB. A limit failure never produces partial totals.
The existing table shows at most 500 rows; a filtered CSV includes all loaded
matching records. Narrow larger sources upstream.

Successful snapshots are cached in memory for 300 seconds by default
(`refresh_seconds`, minimum 30). The next interaction after expiry attempts a
refresh. There is no background polling. Restart to reload immediately. A failed
refresh retains the last good in-process snapshot as **stale**, with a visible
reason, except a SQL safety refusal, which clears it and shows an error. With no good snapshot, it shows an error. No snapshots persist to disk.

The app runs on loopback. Local `Data` contents, active source configuration,
and `.env` files are excluded from scaffolds and the release ZIP. Never place
private input files in `samples` or `examples`. Those folders are distributed.
Remote source calls run on the Python server; the browser receives only prepared
dashboard records. Downloads contain the current source/sample label on every row.
