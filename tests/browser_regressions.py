"""Focused browser regressions for source metadata and the table row cap.

Run with ``.venv\\Scripts\\python.exe tests\\browser_regressions.py``.  The
test server registers its synthetic provider in its own process, leaving the
starter application and its fixture registry untouched.
"""

from __future__ import annotations

import csv
import io
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STARTER = Path(
    os.getenv("CITY_TEST_APP", str(ROOT / "skills/city-app-builder/assets/starter"))
).resolve()
EVIDENCE = ROOT / ".qa"

# This code runs only in the spawned server process. It deliberately imports
# the provider registry before app.py so the preview selector sees this source.
SERVER_BOOTSTRAP = r"""
from datetime import date, timedelta
from pathlib import Path
import os
import sys

starter = Path(os.environ["CITY_TEST_APP"]).resolve()
os.chdir(starter)
sys.path.insert(0, str(starter))

from city_app.data import Dataset, Provider, PROVIDERS, Record, SourceInfo, UNAVAILABLE_STATES

source = SourceInfo(
    name="Synthetic 501-record regression source",
    description="Entirely fictional records created only for browser regression coverage.",
    value_label="Mean synthetic days",
    value_unit="days",
    aggregation="mean",
    updated_at=date(2026, 9, 1),
    limitation="This synthetic fixture is not a real connector or City dataset.",
    is_sample=False,
    labels={"area": "District"},
)
records = tuple(
    Record(
        record_id=f"REG-{index:03d}",
        date=date(2026, 1, 1) + timedelta(days=index % 90),
        category=("Permits" if index % 2 else "Inspections"),
        area=("North" if index % 3 else "Central"),
        status=("Open" if index % 4 else "Completed"),
        value=float((index % 12) + 1),
    )
    for index in range(1, 502)
)

def load_regression(condition):
    return Dataset((), source, condition) if condition in UNAVAILABLE_STATES else Dataset(records, source, condition)

PROVIDERS["regression"] = Provider(source, load_regression)

import app
from shiny import run_app

run_app(app.app, host="127.0.0.1", port=int(os.environ["CITY_TEST_PORT"]), reload=False)
"""


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_server(url: str, process: subprocess.Popen[str]) -> None:
    for _ in range(80):
        if process.poll() is not None:
            raise RuntimeError(
                "Regression Shiny server exited; inspect .qa/browser-regressions.log"
            )
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("Regression Shiny server did not start")


def select_source(page, source: str) -> None:
    if not page.locator(".preview-controls").get_attribute("open") == "":
        page.locator(".preview-controls > summary").click()
    page.select_option("#sample", source)
    page.wait_for_function(f"location.hash.includes('sample={source}')")
    expect(page.locator("#sample")).to_have_value(source)


def run() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    log = (EVIDENCE / "browser-regressions.log").open("w", encoding="utf-8")
    environment = {
        **os.environ,
        "CITY_TEST_APP": str(STARTER),
        "CITY_TEST_PORT": str(port),
    }
    process = subprocess.Popen(
        [sys.executable, "-c", SERVER_BOOTSTRAP],
        cwd=STARTER,
        env=environment,
        stdout=log,
        stderr=log,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        text=True,
    )
    checks: list[str] = []
    try:
        wait_for_server(url, process)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 1000}, accept_downloads=True
            )
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url)
            expect(page.locator("#page-home")).to_be_visible()

            select_source(page, "regression")
            expect(page.locator("#overview figure").first).to_be_visible()
            expect(page.locator(".heatmap-table thead")).to_contain_text("District")
            expect(page.locator(".heatmap-table caption")).to_contain_text("category")
            checks.append("partial source labels preserve Home heatmap charts")

            page.locator('.city-nav a[data-page="explore"]').click()
            expect(page.locator(".table-scroll tbody tr")).to_have_count(500)
            limit_message = page.locator(".table-limit-note, .table-hint").filter(
                has_text="Showing the first 500 of 501 records"
            )
            expect(limit_message).to_be_visible()
            page.set_viewport_size({"width": 390, "height": 1000})
            expect(limit_message).to_be_visible()
            with page.expect_download() as download_info:
                page.locator("#download").click()
            exported = list(
                csv.DictReader(
                    io.StringIO(
                        Path(download_info.value.path()).read_text(encoding="utf-8")
                    )
                )
            )
            assert len(exported) == 501
            assert {row["data_kind"] for row in exported} == {"DATA"}
            checks.append(
                "desktop and mobile expose the 500-row limit while CSV retains 501"
            )

            page.set_viewport_size({"width": 1440, "height": 1000})
            page.locator('.city-nav a[data-page="home"]').click()
            select_source(page, "services")
            expect(page.locator(".sample-notice")).to_contain_text("Sample data")
            expect(page.locator(".footer-meta")).to_contain_text(
                "Fictional sample data"
            )
            select_source(page, "regression")
            page.reload()
            page.wait_for_function("location.hash.includes('sample=regression')")
            expect(page.locator(".sample-notice")).to_contain_text(
                "Synthetic 501-record regression source"
            )
            expect(page.locator(".footer-meta")).to_contain_text(
                "Synthetic 501-record regression source"
            )
            expect(page.locator(".footer-meta")).not_to_contain_text("Fictional sample")
            page.locator('.city-nav a[data-page="explore"]').click()
            expect(page.locator(".table-scroll caption")).to_contain_text(
                "Synthetic 501-record regression source"
            )
            expect(page.locator(".table-scroll caption")).not_to_contain_text(
                "fictional"
            )
            expect(page.locator("#download")).to_have_text("Download these records")
            select_source(page, "services")
            expect(page.locator(".sample-notice")).to_contain_text("Sample data")
            expect(page.locator(".footer-meta")).to_contain_text(
                "Fictional sample data"
            )
            checks.append(
                "source changes refresh banner, footer, table, and download disclosure"
            )

            assert not errors, errors
            browser.close()

        result = {"passed": checks}
        print(json.dumps(result, indent=2))
        (EVIDENCE / "browser-regressions-results.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        log.close()


if __name__ == "__main__":
    run()
