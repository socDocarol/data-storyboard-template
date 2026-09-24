"""Scaffold -> activate -> dashboard -> drill -> CSV for every runnable connector.

Default: deterministic local fixtures. --live also reads the public Sacramento
example through the real connector. No SQL Server is contacted.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from browser_regressions import free_port, wait_for_server
from test_package import module

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "skills/city-app-builder/assets/starter"
EVIDENCE = ROOT / ".qa"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def run(live=False):
    EVIDENCE.mkdir(exist_ok=True)
    # Reuse the real paginated example and the protocol fixture from portable tests.
    sys.path.insert(0, str(STARTER))
    api = load_module("example_api", STARTER / "examples/serve_api.py")
    fixtures = load_module("connector_fixtures", STARTER / "tests/test_connectors.py")
    servers = [
        ThreadingHTTPServer(("127.0.0.1", 0), handler)
        for handler in (api.Handler, fixtures.ApiHandler)
    ]
    threads = [
        threading.Thread(target=server.serve_forever, daemon=True) for server in servers
    ]
    for thread in threads:
        thread.start()
    results = []
    try:
        with (
            tempfile.TemporaryDirectory() as temporary,
            sync_playwright() as playwright,
        ):
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            names = ("local-csv", "local-xlsx", "http-api", "arcgis-fixture") + (
                ("sacramento",) if live else ()
            )
            for name in names:
                app = module("scaffold").scaffold(
                    Path(temporary) / name,
                    title="Connector example",
                    sample="services",
                    future_source="file",
                    banner=True,
                )
                if name.startswith("local-"):
                    command = [sys.executable, "connect.py", "example", name]
                else:
                    configuration = json.loads(
                        (
                            app
                            / "examples"
                            / (
                                "http-api.json"
                                if name == "http-api"
                                else "sacramento.json"
                            )
                        ).read_text()
                    )
                    if name == "http-api":
                        configuration["url"] = (
                            f"http://127.0.0.1:{servers[0].server_port}/requests"
                        )
                    elif name == "arcgis-fixture":
                        configuration["url"] = (
                            f"http://127.0.0.1:{servers[1].server_port}/FeatureServer/0"
                        )
                        configuration["source"].update(
                            name="Synthetic ArcGIS protocol test",
                            description="Synthetic test records only; not actual City data.",
                            is_sample=True,
                        )
                        configuration["columns"] = {
                            "record_id": "id",
                            "date": "opened",
                            "category": "group",
                            "area": "district",
                            "status": "status",
                            "value": None,
                        }
                    (app / "example-config.json").write_text(json.dumps(configuration))
                    command = [
                        sys.executable,
                        "connect.py",
                        "activate",
                        "example-config.json",
                    ]
                result = subprocess.run(
                    command,
                    cwd=app,
                    capture_output=True,
                    text=True,
                    timeout=75,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if result.returncode:
                    raise RuntimeError(f"{name}: {result.stderr}")
                port = free_port()
                url = f"http://127.0.0.1:{port}"
                with (EVIDENCE / f"connector-{name}.log").open(
                    "w", encoding="utf-8"
                ) as log:
                    process = subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "shiny",
                            "run",
                            "--host",
                            "127.0.0.1",
                            "--port",
                            str(port),
                            "app.py",
                        ],
                        cwd=app,
                        stdout=log,
                        stderr=log,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    try:
                        wait_for_server(url, process)
                        context = browser.new_context(
                            viewport={"width": 1440, "height": 1000},
                            accept_downloads=True,
                        )
                        page = context.new_page()
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        page.goto(
                            url
                            + "#home?sample=spending&category=OldSampleLabel&record=OLD"
                        )
                        page.wait_for_function(
                            "location.hash.includes('sample=connected') && !location.hash.includes('OldSampleLabel')"
                        )
                        expect(page.locator(".stat-value").first).to_be_visible(
                            timeout=65000
                        )
                        count = int(
                            page.locator(".stat-value")
                            .first.inner_text()
                            .replace(",", "")
                        )
                        if name != "sacramento":
                            assert count == (2 if name == "arcgis-fixture" else 48), (
                                name,
                                count,
                            )
                        else:
                            assert count > 0
                        expect(page.locator("#heatmap")).to_be_visible()
                        expect(page.locator("#composition")).to_be_visible()
                        assert page.locator(".heatmap-table th").first.evaluate(
                            "node => node.getBoundingClientRect().width >= 80"
                        )
                        assert page.locator("#trend .axis-label").evaluate_all(
                            "nodes => nodes.every(node => node.getBBox().x >= 0)"
                        )
                        expect(page.locator(".preview-controls")).not_to_be_visible()
                        expect(page.locator(".hero-image")).to_be_visible()
                        if name == "sacramento":
                            expect(page.locator(".footer-meta")).not_to_contain_text(
                                "Fictional"
                            )
                        else:
                            expect(page.locator(".footer-meta")).to_contain_text(
                                "Fictional"
                            )
                        page.screenshot(
                            path=str(EVIDENCE / f"connector-{name}-desktop.png"),
                            full_page=True,
                        )
                        page.locator('.bar-label[data-drill="true"]').first.click()
                        page.wait_for_function("location.hash.includes('category=')")
                        page.locator('.city-nav a[data-page="explore"]').click()
                        expect(
                            page.locator(".table-scroll tbody tr").first
                        ).to_be_visible()
                        visible_ids = page.locator(
                            ".table-scroll tbody tr th"
                        ).all_text_contents()
                        with page.expect_download() as download:
                            page.locator("#download").click()
                        rows = list(
                            csv.DictReader(
                                io.StringIO(
                                    Path(download.value.path()).read_text(
                                        encoding="utf-8"
                                    )
                                )
                            )
                        )
                        assert len(rows) > 0 and len(rows) >= len(visible_ids)
                        assert [row["record_id"] for row in rows[:500]] == [
                            value.strip() for value in visible_ids
                        ]
                        assert {row["data_kind"] for row in rows} == {
                            "DATA" if name == "sacramento" else "FICTIONAL SAMPLE"
                        }
                        page.locator(".table-scroll a[data-record-id]").first.click()
                        expect(page.locator("#record-dialog")).to_be_visible()
                        page.keyboard.press("Escape")
                        page.reload()
                        expect(
                            page.locator(".table-scroll tbody tr").first
                        ).to_be_visible()
                        page.locator('.city-nav a[data-page="compare"]').click()
                        expect(page.locator(".comparison-scope")).to_be_visible()
                        page.locator('.city-nav a[data-page="about"]').click()
                        expect(page.locator("#about")).to_contain_text(
                            "Source and freshness"
                        )
                        page.locator('.city-nav a[data-page="home"]').click()
                        page.set_viewport_size({"width": 390, "height": 1000})
                        expect(page.locator("#heatmap")).to_be_visible()
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= innerWidth"
                        )
                        page.screenshot(
                            path=str(EVIDENCE / f"connector-{name}-mobile.png"),
                            full_page=True,
                        )
                        assert not errors, errors
                        results.append(
                            {
                                "source": name,
                                "records": count,
                                "filtered_export": len(rows),
                                "passed": "activation, charts, drill, records, details, CSV, refresh, compare, About, mobile",
                            }
                        )
                        context.close()
                    finally:
                        process.terminate()
                        process.wait(timeout=10)
            browser.close()
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    run(parser.parse_args().live)
