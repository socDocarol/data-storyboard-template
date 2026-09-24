# Data connector implementation plan

Build on handoff `4d3f2e8`. Preserve dashboard composition, shared drilldowns,
source disclosures, and the three-question discovery target. SacMarina SQL
work is outside this repository change.

- [x] Add bounded CSV/XLSX loading from `Data`, explicit field mapping, source
  metadata, safe validation errors, and registration through `Provider`.
- [x] Add JSON HTTP pagination and ArcGIS Hub/item/layer resolution with complete
  ID-based downloads. Add a SQL Server adapter using a reviewed view and environment
  credentials, tested without a work database.
- [x] Add runnable examples, source inspection/check/activation commands, private
  data exclusions, and update the builder's short discovery instructions.
- [x] Verify portable/scaffold tests, local/API/ArcGIS end-to-end examples,
  existing browser interactions, packaging, and one focused connector review.

Keep the sample preview as the default. A configured connector is opt-in. Reject
invalid records and over-budget results rather than silently omitting rows.
Never infer business semantics or substitute zero for missing values. Keep
secrets and local input files out of Git and distributions. Use openpyxl for XLSX;
the HTTP client uses Python's standard library. SQL support is optional.

Key checks: duplicate IDs, malformed dates/numbers, ambiguous workbook sheets,
formula cells, pagination loops and truncation, authentication/redirect handling,
source error/stale states, sample labeling, portable examples, and filtered CSVs.
