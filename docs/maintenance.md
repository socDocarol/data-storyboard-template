# Maintain and verify the kit

The skill's `assets/starter` is the single source for new apps. Fix it there, run checks, then rebuild the ZIP. Existing generated apps are independent copies; they do not receive automatic upgrades. Version 0.6.1 intentionally has no shared-package upgrade service or MCP.

Keep temporary plans, session journals, and handoff/QA notes in the ignored `.internal/` folder. They stay local and are excluded from scaffolds and ZIPs. Legacy plan/journal paths under `docs` are also excluded. Stable product guidance, reusable tests, and these maintenance instructions belong in the repository.

## Setup

Use Python 3.12 from the kit root:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r skills/city-app-builder/assets/starter/requirements-lock.txt
.venv/Scripts/python.exe -m pip install playwright==1.58.0 ruff==0.15.0 PyYAML==6.0.3
```

Microsoft Edge must be installed for the browser checks. These development tools are not needed by generated apps.

## Checks

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py" -v
.venv/Scripts/python.exe tests/browser_check.py
.venv/Scripts/python.exe tests/browser_regressions.py
.venv/Scripts/python.exe tests/browser_connectors.py
.venv/Scripts/python.exe -m ruff check skills tests scripts
```

The package suite also launches a freshly scaffolded app while another HTTP server owns its preferred port, verifies the new instance identity/title, and confirms the original server still responds.

The package test suite also runs the portable data, connector, selection, visual-data, and startup tests from a freshly scaffolded app. To run those tests directly, use `python -m unittest discover -s tests -v` from the starter directory with the app's environment.

If the Codex Skill Creator validator is available, run it with Python's `-X utf8` flag on Windows. It validates the skill's frontmatter/shape, not actual model behavior.

The browser check starts an isolated local server, checks interactions and all required widths, saves screenshots under `.qa`, and stops that server. It fails on JavaScript errors or external HTTP requests. Run it twice before a release; a single pass does not rule out a timing race. Set `CITY_TEST_APP` to another scaffolded app directory to exercise a clean copy using the same test environment. The supplied test uses the default services sample and expects its known fixture totals.

The focused browser regression script starts a separate local server with a synthetic provider registered only in that child process. It checks partial dimension labels, the visible 500-row notice at desktop and phone widths, a complete 501-row CSV, and source disclosures through switching and refresh. That regression remains synthetic. `browser_connectors.py` separately scaffolds and activates real adapters against deterministic fixtures; add `--live` for the public Sacramento example. It never connects to SQL Server.

## Conversations to review

Review [conversation cases](conversation-cases.md) whenever changing the skill. These are acceptance scenarios, not a completed model benchmark. A real smaller-model trial should measure discovery turns, unsupported source claims, completed workflows, repairs, time, and cost on matched tasks, including a follow-up edit.

## Dependencies and assets

`requirements.txt` pins Shiny, openpyxl, and defusedxml for XLSX with protected XML parsing. `requirements-sql.txt` is optional and outside the default runtime. `requirements-lock.txt` pins the resolved runtime and is used by the launcher. When deliberately updating dependencies, regenerate the lock with `uv pip compile requirements.txt --universal --output-file requirements-lock.txt` from the starter folder and rerun checks. Do not copy an existing virtual environment into a distribution.

The included visual guide is a snapshot of the source guide at kit creation. Update that snapshot and its starter implementation together when the City contract changes. Keep font licenses and the City signature provenance in the package.

## Create the ZIP

```powershell
python scripts/package.py
```

The output is `dist/data-storyboard-template-0.6.1.zip`. The packager selects the product files explicitly, excludes environments/caches/logs, private Data contents, active data_source.json, and environment files, verifies archive paths and CRCs, and prints a checksum. Extract it into a new development folder to share it. No global skill installation, repository push, or deployment occurs.
