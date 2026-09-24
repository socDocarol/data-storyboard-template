"""Startup and composition checks that need the Shiny runtime but no browser."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import app
from city_app.components import (
    disclosure,
    page_intro,
    selection_trail,
    state_panel,
    status_message,
    unavailable_panel,
)
from city_app.data import Dataset
from city_app.data import load_sample
from city_app.state import ViewState


class AppTests(unittest.TestCase):
    def test_page_composes_with_configured_title_and_default_source(self):
        html = str(app.app_ui)
        self.assertIn(app.CONFIG["title"], html)
        self.assertIn(f'data-default-sample="{app.CONFIG["sample"]}"', html)
        for route in ("home", "explore", "compare", "about"):
            self.assertIn(f'data-route="{route}"', html)
        self.assertIn('id="source_banner"', html)
        self.assertIn('id="source_footer"', html)

    def test_config_validation_fails_early_with_clear_messages(self):
        valid = json.loads((app.ROOT / "app_config.json").read_text(encoding="utf-8"))
        cases = (
            ({"sample": "production"}, "sample must be one of"),
            ({"title": ""}, "title of 1 to 60"),
            ({"portal_url": "ftp://x"}, "portal_url"),
            ({"portal_url": "https://user:pw@example.org"}, "portal_url"),
            ({"show_preview_controls": "yes"}, "show_preview_controls"),
            ({"audience": 3}, "'audience'"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "app_config.json"
            for change, message in cases:
                path.write_text(json.dumps({**valid, **change}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    app.read_config(path)
            path.write_text(json.dumps(valid), encoding="utf-8")
            self.assertEqual(app.read_config(path)["title"], valid["title"])

    def test_state_panel_rejects_states_that_show_records(self):
        for state in ("ready", "stale", "missing"):
            with self.assertRaises(ValueError):
                state_panel(state)
        self.assertIsNone(unavailable_panel(load_sample("services", "stale")))
        self.assertIn(
            "state-error", str(unavailable_panel(load_sample("services", "error")))
        )

    def test_banner_can_be_omitted_and_has_accessible_image_and_credit(self):
        plain = str(page_intro("Example", "Explore the data"))
        self.assertNotIn("hero-image", plain)
        self.assertEqual(plain.count("<h1"), 1)
        banner = {
            "image": "assets/historic-city-hall.jpg",
            "alt": "Historic City Hall",
            "credit": "City of Sacramento",
        }
        illustrated = str(page_intro("Example", "Explore the data", banner))
        self.assertIn('alt="Historic City Hall"', illustrated)
        self.assertIn("City of Sacramento", illustrated)
        self.assertEqual(illustrated.count("<h1"), 1)

    def test_banner_config_rejects_remote_outside_missing_and_invalid_images(self):
        valid = json.loads((app.ROOT / "app_config.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            for image in (
                "https://example.com/photo.jpg",
                "../samples/services.csv",
                "assets/missing.jpg",
                "assets/../../app.py",
                "//example.com/photo.jpg",
                "assets/fonts/Inter-LICENSE.txt",
            ):
                path.write_text(
                    json.dumps({**valid, "banner": {"image": image, "alt": "Example"}}),
                    encoding="utf-8",
                )
                with (
                    self.subTest(image=image),
                    self.assertRaisesRegex(ValueError, "banner image"),
                ):
                    app.read_config(path)
            for banner in (
                False,
                {},
                {"image": "assets/historic-city-hall.jpg", "alt": ""},
            ):
                path.write_text(
                    json.dumps({**valid, "banner": banner}), encoding="utf-8"
                )
                with (
                    self.subTest(banner=banner),
                    self.assertRaisesRegex(ValueError, "banner must"),
                ):
                    app.read_config(path)
            for banner in (
                None,
                {
                    "image": "assets/historic-city-hall.jpg",
                    "alt": "Historic City Hall",
                    "credit": "City of Sacramento",
                },
            ):
                path.write_text(
                    json.dumps({**valid, "banner": banner}), encoding="utf-8"
                )
                self.assertEqual(app.read_config(path)["banner"], banner)

    def test_live_states_never_mention_simulations(self):
        live = replace(load_sample("services").source, is_sample=False)
        for state in ("empty", "error", "loading"):
            panel = str(unavailable_panel(Dataset((), live, state)))
            self.assertNotIn("example", panel)
            self.assertNotIn("simulat", panel)
            self.assertNotIn("Available data", panel)
            self.assertNotIn("simulat", status_message(live, state))
        self.assertIn("simulated", str(state_panel("error")))
        self.assertIn("snapshot", status_message(live, "stale"))

    def test_disclosures_switch_together_on_is_sample(self):
        sample = load_sample("services").source
        live = replace(sample, is_sample=False, name="Live requests")
        for key in (
            "banner",
            "footer",
            "record_eyebrow",
            "table_caption",
            "download_note",
        ):
            self.assertIn("ictional", disclosure(sample, key))
            self.assertNotIn("ictional", disclosure(live, key))
        self.assertIn("Live requests", disclosure(live, "source_caption"))

    def test_selection_trail_uses_source_labels(self):
        view = ViewState(area="North", month="2026-01")
        html = str(selection_trail(view, 4, 48, labels={"area": "District"}))
        self.assertIn("District: North", html)
        self.assertIn("Month: 2026-01", html)
        self.assertIn("4 of 48 records", html)


if __name__ == "__main__":
    unittest.main()
