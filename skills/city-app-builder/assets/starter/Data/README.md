# Put local data here

Copy your CSV or XLSX into this folder, then tell your coding assistant the file
name and what you want to understand. The assistant checks a small sample and
maps its fields to the dashboard. It asks only about meanings that matter.

CSV files use UTF-8, one header row, and unique column names. XLSX files use one
header row and values rather than formulas. If a workbook has several sheets,
choose the relevant sheet. Keep one record per row and a unique record ID.

For any other format, the assistant should ask whether you want to convert it
to CSV/XLSX or add support for that specific format. It must not guess.

Input files in this folder are excluded from Git, scaffolds, and release ZIPs.
The connector reads only the configured file. Nothing here is uploaded.
The default limits are 10 MB and 10,000 rows; narrow larger extracts before use.
