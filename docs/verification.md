# Verification record

Date: 2026-09-21. Package version: 0.3.0. Tested on Windows, Python 3.12, Shiny 1.7.0, and headless Microsoft Edge through Playwright 1.58.0.

## Passed

- **29 portable data/selection/visual tests:** sample identity, explicit missing values, service mean and denominator, spending credits/net sum, zero-count months, combined filters, ordering, invalid/duplicate records, sample-labeled exports, spreadsheet-formula protection, selection scope, drill ancestor behavior, URL encoding, invalid state bounds, comparison means/denominators, missing/zero/negative baselines, aligned months, monthly measure reconciliation, gaps rather than zero, signed chart scales, all-missing plots, and escaped visual labels.
- **6 package tests:** standalone scaffold and its portable test run, source preservation, refusal to overwrite existing folders or write inside the skill, input validation, bounded CSV/JSON profiling, no example-value echo, size limits, and rejection of network paths.
- **Browser checks:** visual-first overview and five chart families; linked heatmap/status/record dots; keyboard chart-to-record flow; all-missing plot; Home/Explore/Compare/About; linked category/area/status and month drill; record drawer keyboard, Escape, return focus, refresh and history; comparison scope, exact table, and missing means; direct hashes and refresh; Back/Forward; matching filtered CSV and row order; reset/no-results behavior; both examples; all six data conditions; credits and ordering; exact-value chart tables; menu selection and Escape; skip link; reduced motion.
- **Responsive geometry:** 2048, 1440, 800, 390, and 320 pixels; header heights and centered identity; one main landmark and one visible H1; long category labels; contained table scrolling; no horizontal page overflow.
- **Runtime behavior:** no JavaScript errors and no external HTTP requests during the browser test. The optional Portal link was not followed.
- **Fresh first launch (v0.1 runtime, unchanged dependencies in v0.2):** a newly scaffolded app installed its locked dependencies into its own virtual environment, served successfully, and passed all 15 portable tests using that new environment. The test server was stopped afterward.
- **Skill shape and code quality:** Skill Creator's validator passed using UTF-8 mode on Windows; Ruff checks passed. The skill's CSV inspector was also run through its time-limited command entrypoint.
- **Visual review:** desktop and phone layouts were inspected, including the new comparison page at 320 pixels and record-detail drawer. Shared selections and drill controls retain the City visual standard.

The Impeccable detector flagged only the generic use of Inter in this visual pass. Inter is explicitly required by the inherited City guide, so it was retained. Mobile charts and heatmaps retain readable scales through contained horizontal scrolling, with a visible scroll hint and exact-value alternatives.

## 0.4.0 refactor check (2026-09-21)

Same environment as above. The starter was refactored for reliability and efficiency without changing its behavior; these are the checks actually run afterwards.

- **44 portable tests** from the starter (was 29): the earlier cases plus one-pass filtering by status and month, month grouping across a year boundary, any-unit value formatting, cached sample immutability, live-source export labeling, source label validation, the provider registry, state-panel misuse, live-source state and status wording, the plot point cap, non-colliding group colors, source-labeled heatmaps and chips, startup config validation, and page composition.
- **6 package tests**, unchanged, including the portable suite run inside a fresh scaffold.
- **Browser check passed twice in a row** on the refactored starter. On the unmodified 0.3.0 code the same check failed once and passed once at the step where closing the record drawer returns focus to the originating table link: closing the drawer changed the shared state, which redrew the whole table and replaced the focused element. The server now keeps a record-free `selection` value that charts and tables depend on, so a drawer open or close redraws nothing else.
- **Ruff** lint and format pass.

Boundaries above still apply. No connector was added; the provider registry, label relabeling, disclosure switch, and row/point caps were exercised only by unit tests and the sample data.

## Review fixes verified (2026-09-22)

- Partial dimension label overrides now retain the default labels in the heatmap. An area-only `District` override renders Home successfully, and the new unit test also covers category-only, status-only, and empty overrides without mutating the supplied mapping.
- The row-limit notice is separate from the mobile scroll hint. A synthetic 501-row dataset shows the 500-row limit at 1440px and 390px; its CSV contains all 501 records.
- Banner and footer disclosures now render from the active dataset. Switching samples → a synthetic provider with `is_sample=False` → samples, and refreshing the nondefault source URL, preserves consistent banner/footer/table/download wording.
- **Passed:** 45 portable tests through a fresh scaffold, 6 package tests, the existing complete browser check, the focused browser regression script, and Ruff lint/format checks.
- These checks use local fictional fixtures only. No live connector, deployment, or credential handling was added.

## Desktop layout and optional banner verified (2026-09-24)

- **47 portable tests and 7 package tests passed**, including the plain introduction, accessible banner markup, local-image configuration validation, opt-in scaffolding, and inclusion of the JPEG in the distribution.
- **Browser check passed:** the City Hall photo loads with attribution; all five visual families and existing drilldowns remain functional. At 1440px and 2048px, the content uses at least 90% of the viewport and the three supporting visuals share a row. Tablet, phone, and 320px layouts have no page overflow; keyboard, history, filtered downloads, and the six data conditions still pass.
- Desktop and phone screenshots were inspected. Heatmap columns were adjusted to accommodate full words, and the affected browser checks passed afterward.
- The builder's banner choice is within the three-question conversation budget. New scaffolds omit the banner unless explicitly requested with `--banner`; missing user-supplied images do not block a preview.
- Ruff lint/format and the skill validator passed. The visual detector's only finding was Inter, retained because it is required by the City guide.
- City Hall photography is inherited unchanged from Budget Atlas as contextual imagery; asset attribution and the inherited usage boundary are recorded in the starter's asset notes. No live connection was added.

## Compact information disclosure verified (2026-09-24)

- The two full-width sample/preview rows were replaced by one information control beside the introduction. The source notice, state explanation, and preview selectors remain inside its panel; nonready data gets an amber indicator and unavailable chart views retain their messages.
- Browser checks passed for hover into the panel, pointer exit, keyboard focus, Escape with focus return, click pinning, click-away dismissal, phone-width controls, route changes, and preserving open controls through state changes. Existing chart, record, filter, download, history, and responsive checks still pass.
- The focused source/row-limit regression suite passed, including consistent disclosures through source switches and refresh. Closed-overview and expanded-panel screenshots were inspected.
- The 47 portable tests, 7 package tests, Ruff, and skill validation passed. No dependencies or live connections were added.

## KPI alignment verified (2026-09-24)

The borderless KPI group now stays within 800px, uses the same left content inset as the hero and charts, and aligns values through wrapped labels. Focused browser checks passed for both datasets at 2048, 1440, 800, 620, 390, and 320px: content edges align within one pixel, KPI values share a row, and neither page nor values overflow. Desktop and phone screenshots were inspected; the layout detector reported no findings. This was a CSS-only refinement; calculation and data tests were not rerun.

## Four centered KPIs verified (2026-09-24)

The overview now centers four borderless KPIs and their text; the hero and charts retain their existing alignment. The new area-group metric follows the selection and excludes unrecorded area labels. Focused browser checks passed for both samples at 2048, 1440, 1024, 800, 620, 390, and 320px: four visible metrics, centered group/text, desktop row and smaller-screen 2×2 layout, aligned values, and no overflow or JavaScript errors. Filtered North counts one area; an unrecorded-only selection counts zero. Desktop and phone screenshots were inspected. The 47 portable tests through the scaffold, 7 package tests, and layout detector also passed.

## Boundaries

- The question bank and conversation cases were reviewed against the requested workflow. No independent smaller-model trial has been performed, and no model-performance improvement is claimed yet.
- SQL Server, APIs, Sacramento Open Data, credentials, real-source interpretation, and deployment are not implemented or verified.
- The local inspector describes a bounded CSV/JSON sample; it is not a data connector, importer, or whole-dataset audit.
- Keyboard and responsive checks do not establish full accessibility conformance. A comprehensive accessibility audit, contrast-tool sweep, assistive-technology testing, and release review remain separate work.
- Windows/Edge is the tested launch environment. Other operating systems and browsers have not been validated.
- The included guide is a snapshot. Generated apps are independent copies and do not receive future kit fixes automatically.

Reproduction commands and packaging instructions are in [maintenance.md](maintenance.md).

## Data connectors verified (0.6.0, 2026-09-24)

- **67 portable tests and 8 package tests passed**, including CSV/XLSX parsing,
  missing/zero/negative values, explicit row counts, date formats, duplicate IDs,
  file/row/network limits, formula rejection, styled blank Excel columns, real
  empty/error/stale states, HTTP pagination/authentication/redirect handling,
  ArcGIS ID completeness, mocked read-only SQL, and private-data exclusions.
  The portable suite also ran inside a fresh scaffold.
- **Connector browser checks passed** for CSV, XLSX, a four-page local JSON API,
  and an ArcGIS protocol fixture. They cover activation, stale sample bookmarks,
  charts, drilldowns, details, filtered exports, refresh, Compare, About, and
  phone rendering. Fictional fixtures retain sample labels.
- **Real Sacramento browser check passed:** the official City's incident-maps
  page links Hub item `5b9a9448663f41b1898643b6d91201c4`, owned by
  `Applications_SacCity`, resolving to `SalesForce311_View/FeatureServer/0` in
  ArcGIS organization `54falWtcpty3V47Z`. The January 1-7, 2025 UTC query loaded
  9,386 rows; a category drill exported 2,937 matching rows. Geometry, addresses,
  and free-text descriptions were not requested. Counts are observations from
  this check, not fixed future expectations. The current view's retention rule
  and retrieval-date semantics are disclosed in the example.
- **Existing browser and source/row-limit regression checks passed.** A preexisting
  chart-layout test race reproduced before implementation and during checking:
  separate DOM measurements could straddle a reactive replacement. The test now
  waits for one visible render and captures its chart positions atomically.
- Desktop/phone screenshots were inspected. Real data exposed squeezed heatmap
  columns and clipped record-count axis labels; minimum heatmap column width,
  contained scrolling, and numeric count-axis labels fixed both. Layout, City
  identity, banner, shared selection, and drilldowns remain intact. The design
  detector reports only the inherited Inter font, required by the City guide.
- Ruff lint/format checks and an independent connector review passed. Review
  fixes cover old sample bookmarks after activation, credential-bearing query
  URLs, formatted workbook trailing blanks, and truthful first-load errors.
- A saved standalone CSV example installed its own locked runtime, started on loopback, and passed all 67 portable tests with the connector active. Its Data folder contains equivalent fictional CSV/XLSX examples.
- SQL Server was tested with a fake ODBC connection and the offline doctor only.
  No work database, VPN, authentication, certificate, permissions, or actual view
  was verified. No SacMarina SQL files were changed. See the work-computer steps
  in the connector guide.

## SQL setup simplified (2026-09-24)

- SQL setup now uses Windows integrated authentication from the account running
  the local app. Server/database names are safely quoted into a generated
  connection string; raw connection strings and SQL credentials are not accepted.
- Reuses installed Microsoft ODBC Driver 18 or 17, preferring 18. No system
  driver install/upgrade, DSN, database objects, new login, or automatic permission
  change is performed. The optional Python adapter stays in the app environment.
- Uses an existing approved table or view with existing read access. The SQL
  example starts at 1,000 rows, with bounded selected-column queries and date
  filters. Encryption, certificate validation, timeouts, and cleanup remain.
- All 70 portable tests passed, including driver reuse, forced Windows auth,
  connection-string quoting, rejection of raw credentials, an offline-only
  prerequisite check, and mocked read-only queries. SQL remains unverified
  against a work computer/database. No UI behavior changed in this follow-up.

## Strict SQL read-only guardrails (2026-09-24)

- All 80 portable tests passed, including unsafe settings/identifier/ODBC-option
  rejection; a single execution boundary for fixed metadata SELECTs and generated
  data SELECT; rejection of writes, DDL, EXEC, SELECT INTO, sequences, comments,
  and extra statements; admin/wrong-database/object-type checks; effective
  server/database/schema/object permission checks; column UPDATE exceptions;
  and refusal when checks fail or return unknown/NULL results.
- Mocked connections verify autocommit=False, no commit calls, explicit rollback
  on success and failure, closed cursors/connections, and failure when cleanup
  cannot be confirmed. SQL safety refusals
  clear cached data. The offline doctor remains disconnected and reports that
  permissions have not been verified.
- An independent focused SQL review found no blocking write path. This is not
  live SQL verification or proof of all permissions/dependencies in an actual
  database. Views/external targets remain DBA-approved trust boundaries. A true
  database-enforced guarantee requires IT-confirmed SELECT-only access or a
  read-only reporting database/endpoint. No database or permissions were changed.

## New-app scope and preview isolation (0.6.1, 2026-09-24)

- Reviewed the two budget-template test sessions. They created separate app
  folders, but the discovery flow treated a broad budget topic/source plus a
  banner choice as sufficient. The completed test used a fixed-port manual
  launch. The live page later identified itself as Approved Budget Explorer;
  the available evidence does not prove prior budget-app content was reused or
  that the wrong app was actually served during that test.
- Replaced the rigid question cap/banner reservation with required coverage of
  purpose, important data/measures and period, business dashboard views, and a
  concrete first-version task. Decisions from other apps are not inherited.
  Starter briefs now explicitly mark scope as unfinished instead of presenting
  generic sample pages as agreed requirements. Complete briefs proceed without
  repetitive discovery or another approval gate.
- Removed the documented fixed-port manual launch. The launcher assigns each
  child a fresh preview identity and prints/opens its URL only after the server
  returns that identity. It detects a dead child or unrelated HTTP 200 response
  and cleans up only its own child. Other running apps stay untouched.
- **9 package tests passed**, including a real new Shiny server started with an
  occupied preferred port and verification that both old and new servers served
  their own pages. The suite runs **84 portable tests** from a fresh scaffold,
  including occupied-port fallback, instance matching, dead-child rejection,
  and startup-failure cleanup. Ruff and the skill shape validator passed.
- A separate agent performed a bounded four-case discovery simulation against
  the updated skill. Vague/partial budget requests remained in discovery;
  complete requirements proceeded to build; preview steps used the printed URL
  and verified the new app. This is a focused behavioral check, not a benchmark
  or a guarantee of compliance by every assistant/model.
- Existing budget/test apps, their data, and their running processes were not
  modified. No SQL Server access or SacMarina changes were involved.
