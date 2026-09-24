"""Batched functional and responsive checks. Requires playwright and local Edge."""

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
)
EVIDENCE = ROOT / ".qa"


def run():
    EVIDENCE.mkdir(exist_ok=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    log = (EVIDENCE / "browser-server.log").open("w", encoding="utf-8")
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
        cwd=STARTER,
        stdout=log,
        stderr=log,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    checks = []
    try:
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError("Shiny exited; inspect .qa/browser-server.log")
            try:
                with urlopen(url, timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.25)
        else:
            raise RuntimeError("Shiny did not start")
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 1000}, accept_downloads=True
            )
            page = context.new_page()
            errors = []
            remote = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "request",
                lambda request: (
                    remote.append(request.url)
                    if request.url.startswith(("http:", "https:"))
                    and not request.url.startswith(url)
                    else None
                ),
            )
            page.goto(url)
            expect(page.locator(".stat-value").first).to_have_text("48")
            expect(page.locator(".stat-value").nth(1)).to_have_text("9.4 days")
            page.locator(".chart-values summary").first.click()
            expect(page.locator(".chart-values table").first).to_be_visible()
            page.locator(".chart-values summary").first.click()
            checks.append("home metrics and accessible exact-value table")
            expect(page.locator("#overview figure")).to_have_count(5)
            expect(page.locator("#trend svg")).to_be_visible()
            expect(page.locator("#composition")).to_contain_text("36 · 75%")
            assert (
                sum(
                    int(value)
                    for value in page.locator(".heat-cell").all_text_contents()
                )
                == 48
            )
            expect(page.locator(".record-point-link")).to_have_count(36)
            expect(page.locator(".selection-notes")).not_to_have_attribute("open", "")
            page.screenshot(
                path=str(EVIDENCE / "visual-overview-1440.png"), full_page=True
            )
            assert page.locator("#trend").bounding_box()["y"] < 550, page.locator(
                "#trend"
            ).bounding_box()
            point = page.locator(".record-point-link").first
            point_id = point.get_attribute("data-record-id")
            point.focus()
            page.keyboard.press("Enter")
            expect(page.locator("#record-dialog")).to_be_visible()
            expect(page.locator("#record-title")).to_have_text(point_id)
            page.keyboard.press("Escape")
            expect(page.locator("#record-dialog")).not_to_be_visible()
            page.locator(".heat-cell").first.click()
            expect(page.locator("#page-explore")).to_be_visible()
            expect(page.locator(".table-scroll tbody tr")).to_have_count(2)
            page.click("#reset")
            page.locator('.city-nav a[data-page="home"]').click()
            expect(page.locator("#overview .stat-value").first).to_have_text("48")
            page.locator(".composition-legend a").filter(has_text="Open").click()
            expect(page.locator("#overview .stat-value").first).to_have_text("12")
            expect(page.locator("#record-plot")).to_contain_text("No recorded values")
            page.locator(".selection-trail a").first.click()
            expect(page.locator("#overview .stat-value").first).to_have_text("48")
            checks.append(
                "five visual families, compact first viewport, linked heatmap/status, keyboard record dots, all-missing plot"
            )

            # A linked journey: chart -> group -> status -> record, then restore history.
            page.locator("#overview a.bar-label").filter(
                has_text="Street maintenance"
            ).click()
            expect(page.locator("#overview .stat-value").first).to_have_text("19")
            expect(page.locator("#drill-title")).to_have_text("Drill into area")
            expect(page.locator("#drill-title")).to_be_focused()
            page.locator("#overview a.bar-label").filter(has_text="North").click()
            expect(page.locator("#overview .stat-value").first).to_have_text("4")
            page.locator(".drill-breadcrumbs a").filter(
                has_text="Street maintenance"
            ).click()
            expect(page.locator("#overview .stat-value").first).to_have_text("19")
            expect(page.locator("#drill-title")).to_have_text("Drill into area")
            page.locator("#overview a.bar-label").filter(has_text="North").click()
            expect(page.locator("#drill-title")).to_have_text("Drill into status")
            page.locator("#overview a.bar-label").filter(has_text="Completed").click()
            expect(page.locator("#overview .stat-value").first).to_have_text("4")
            page.get_by_role("link", name="Open 4 records", exact=True).click()
            expect(page.locator(".table-scroll tbody tr")).to_have_count(4)
            record_link = page.locator(".table-scroll tbody th a").first
            record_id = record_link.inner_text()
            record_link.focus()
            page.keyboard.press("Enter")
            expect(page.locator("#record-dialog")).to_be_visible()
            expect(page.locator("#record-title")).to_have_text(record_id)
            expect(page.locator("#record-title")).to_be_focused()
            page.screenshot(path=str(EVIDENCE / "record-1440.png"), full_page=True)
            page.set_viewport_size({"width": 320, "height": 1000})
            assert page.locator("#record-dialog").evaluate(
                "e => e.scrollWidth <= e.clientWidth"
            )
            page.screenshot(path=str(EVIDENCE / "record-320.png"), full_page=True)
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.reload()
            expect(page.locator("#record-dialog")).to_be_visible()
            expect(page.locator("#record-title")).to_have_text(record_id)
            page.keyboard.press("Escape")
            expect(page.locator("#record-dialog")).not_to_be_visible()
            expect(page.locator(f'[data-record-id="{record_id}"]')).to_be_focused()
            page.go_back()
            expect(page.locator("#record-dialog")).to_be_visible()
            page.get_by_role("button", name="Close details").click()
            expect(page.locator("#record-dialog")).not_to_be_visible()
            page.locator('.city-nav a[data-page="compare"]').click()
            expect(page.locator(".comparison-scope")).to_contain_text("North")
            expect(page.locator(".comparison-grid .stat-card")).to_have_count(2)
            expect(page.locator(".paired-chart")).to_be_visible()
            page.get_by_role(
                "link", name="Remove area filter: North", exact=True
            ).click()
            page.select_option("#compare_by", "status")
            expect(page.locator(".comparison-scope")).to_contain_text("19 records")
            expect(page.locator(".comparison-grid")).to_contain_text("Not recorded")
            page.get_by_text("View exact comparison values", exact=True).click()
            expect(page.locator("#comparison .chart-values table")).to_be_visible()
            page.reload()
            expect(page.locator("#compare_by")).to_have_value("status")
            page.set_viewport_size({"width": 320, "height": 1000})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(EVIDENCE / "compare-320.png"), full_page=True)
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.locator(".selection-trail a").first.click()
            page.locator('.city-nav a[data-page="home"]').click()
            expect(page.locator("#overview .stat-value").first).to_have_text("48")
            page.locator("#overview a.month-link").filter(has_text="Jan 2026").click()
            expect(page.locator("#overview .stat-value").first).to_have_text("8")
            page.locator('.city-nav a[data-page="explore"]').click()
            expect(page.locator(".table-scroll tbody tr")).to_have_count(8)
            page.reload()
            expect(page.locator("#month")).to_have_value("2026-01")
            page.click("#reset")
            expect(page.locator(".table-scroll tbody tr")).to_have_count(48)
            checks.append(
                "linked hierarchy and monthly drill, persistent selection, keyboard record drawer, refreshed deep link, comparison scope and missing means, mobile comparison"
            )

            page.locator('.city-nav a[data-page="explore"]').click()
            expect(page.locator("#page-explore")).to_be_visible()
            expect(page.locator(".table-scroll tbody tr")).to_have_count(48)
            page.select_option("#category", "Street maintenance")
            page.select_option("#area", "North")
            page.fill("#search", "completed")
            expect(page.locator(".selection-context")).to_contain_text(
                "Street maintenance"
            )
            expect(page.locator(".table-scroll tbody tr")).to_have_count(4)
            expect(page.locator("#search")).to_be_focused()
            with page.expect_download() as download_info:
                page.get_by_text("Download these sample records", exact=True).click()
            download = download_info.value
            exported = list(
                csv.DictReader(
                    io.StringIO(Path(download.path()).read_text(encoding="utf-8"))
                )
            )
            assert len(exported) == 4
            assert all(
                r["category"] == "Street maintenance"
                and r["area"] == "North"
                and r["data_kind"] == "FICTIONAL SAMPLE"
                for r in exported
            )
            visible_ids = page.locator(".table-scroll tbody th a").all_text_contents()
            assert [r["record_id"] for r in exported] == visible_ids
            page.fill("#search", "no-such-record")
            expect(
                page.get_by_role("heading", name="No matching records")
            ).to_be_visible()
            expect(page.locator("#download")).to_have_count(0)
            page.click("#reset")
            expect(page.locator(".table-scroll tbody tr")).to_have_count(48)
            checks.append("combined filters, matching CSV, empty search, reset")

            page.locator('.city-nav a[data-page="about"]').click()
            expect(
                page.get_by_role("heading", name="About this data", exact=True)
            ).to_be_visible()
            page.go_back()
            expect(page.locator("#page-explore")).to_be_visible()
            page.go_forward()
            expect(page.locator("#page-about")).to_be_visible()
            page.reload()
            expect(
                page.get_by_role("heading", name="How the numbers are calculated")
            ).to_be_visible()
            checks.append("addressable routes, refresh, Back and Forward")

            page.locator('.city-nav a[data-page="home"]').click()
            page.locator(".preview-controls > summary").click()
            for condition, expected in (
                ("empty", "No records to show"),
                ("error", "The example data is unavailable"),
                ("loading", "Loading the example"),
            ):
                page.select_option("#condition", condition)
                expect(
                    page.get_by_role("heading", name=expected, exact=True)
                ).to_be_visible()
                expect(page.locator("#overview .stat-card")).to_have_count(0)
            page.select_option("#condition", "stale")
            expect(page.locator(".source-status")).to_contain_text("last available")
            expect(page.locator(".stat-value").first).to_have_text("48")
            page.select_option("#condition", "missing")
            expect(page.locator(".source-status")).to_contain_text(
                "intentionally missing"
            )
            page.select_option("#sample", "spending")
            expect(page.locator("#introduction")).to_contain_text("spending entry")
            expect(page.locator(".stat-card").nth(1)).to_contain_text("36 of 48")
            page.select_option("#condition", "ready")
            expect(page.locator(".stat-value").nth(1)).to_have_text("$851,949.00")
            page.locator('.city-nav a[data-page="explore"]').click()
            page.select_option("#order", "value-low")
            expect(page.locator(".table-scroll tbody tr").first).to_contain_text(
                "−$7,500.00"
            )
            checks.append("all six data conditions, spending credits and ordering")

            # Test long category labels in the spending sample at every required width.
            page.locator(".preview-controls > summary").click()
            for width in (2048, 1440, 800, 390, 320):
                page.set_viewport_size({"width": width, "height": 1000})
                page.evaluate("location.hash = 'home?sample=spending'")
                expect(page.locator("#page-home")).to_be_visible()
                expect(page.locator(".stat-value").first).to_have_text("48")
                geometry = page.evaluate(
                    """() => { const header = document.querySelector('.city-header').getBoundingClientRect(); const brand = document.querySelector('.city-brand-link').getBoundingClientRect(); return {overflow:document.documentElement.scrollWidth > innerWidth, height:header.height, center:(brand.left+brand.right)/2, width:innerWidth, main:document.querySelectorAll('main').length, visibleH1:[...document.querySelectorAll('h1')].filter(e=>e.getClientRects().length).length}; }"""
                )
                assert not geometry["overflow"], (width, geometry)
                assert geometry["height"] == (60 if width < 768 else 64), (
                    width,
                    geometry,
                )
                assert abs(geometry["center"] - width / 2) <= 1, (width, geometry)
                assert geometry["main"] == geometry["visibleH1"] == 1
                assert page.locator(".portal-arrow").inner_text() == "↖"
                if width in (1440, 390):
                    page.wait_for_function(
                        "!document.documentElement.classList.contains('shiny-busy') && !document.querySelector('#overview.recalculating')"
                    )
                    page.screenshot(
                        path=str(EVIDENCE / f"home-{width}.png"), full_page=True
                    )
                if width < 1280:
                    page.locator(".city-menu-button").click()
                    page.locator('.city-mobile-nav a[data-page="explore"]').click()
                    expect(page.locator("#city-menu")).not_to_have_attribute("open", "")
                else:
                    page.locator('.city-nav a[data-page="explore"]').click()
                expect(page.locator(".table-scroll tbody tr")).to_have_count(48)
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                ), width
                if width in (1440, 390):
                    page.screenshot(
                        path=str(EVIDENCE / f"explore-{width}.png"), full_page=True
                    )
            checks.append(
                "2048/1440/800/390/320 geometry, long labels, table overflow, menu selection"
            )

            page.locator(".city-menu-button").focus()
            page.keyboard.press("Enter")
            expect(page.locator("#city-menu")).to_have_attribute("open", "")
            page.keyboard.press("Escape")
            expect(page.locator(".city-menu-button")).to_be_focused()
            expect(page.locator("#city-menu")).not_to_have_attribute("open", "")
            page.locator(".skip-link").focus()
            page.keyboard.press("Enter")
            expect(page.locator("#main")).to_be_focused()
            expect(page.locator("#page-explore")).to_be_visible()
            page.emulate_media(reduced_motion="reduce")
            assert (
                page.locator(".city-header").evaluate(
                    "e=>getComputedStyle(e).transitionDuration"
                )
                == "0s"
            )
            checks.append(
                "keyboard menu, Escape focus, skip link preserves route, reduced motion"
            )
            assert not errors, errors
            assert not remote, remote
            checks.append("no JavaScript errors and no external HTTP requests")
            browser.close()
        print(json.dumps({"passed": checks}, indent=2))
        (EVIDENCE / "browser-results.json").write_text(
            json.dumps({"passed": checks}, indent=2), encoding="utf-8"
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
