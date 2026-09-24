import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "city-app-builder"


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, SKILL / "scripts" / f"{name}.py"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class PackageTests(unittest.TestCase):
    def test_scaffold_is_standalone_and_preserves_source(self):
        create = module("scaffold")
        original = (create.STARTER / "app_config.json").read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "My app with spaces"
            create.scaffold(
                destination,
                title='Spending "Review"',
                sample="spending",
                future_source="sql-server",
            )
            config = json.loads((destination / "app_config.json").read_text())
            self.assertEqual(config["title"], 'Spending "Review"')
            self.assertEqual(config["sample"], "spending")
            self.assertIsNone(config["banner"])
            self.assertIn("sql-server", (destination / "APP-BRIEF.md").read_text())
            self.assertTrue(
                (
                    destination / "www/assets/city-of-sacramento-signature-white.png"
                ).is_file()
            )
            self.assertFalse((destination / ".venv").exists())
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                cwd=destination,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((create.STARTER / "app_config.json").read_bytes(), original)

    def test_scaffold_banner_is_opt_in_and_included_in_distribution(self):
        create = module("scaffold")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "With banner"
            create.scaffold(
                destination,
                title="Example",
                sample="services",
                future_source="unknown",
                banner=True,
            )
            config = json.loads(
                (destination / "app_config.json").read_text(encoding="utf-8")
            )
            self.assertTrue((destination / "www" / config["banner"]["image"]).is_file())
            self.assertIn(
                "Bundled City Hall image selected",
                (destination / "APP-BRIEF.md").read_text(encoding="utf-8"),
            )
        spec = importlib.util.spec_from_file_location(
            "package", ROOT / "scripts/package.py"
        )
        package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(package)
        self.assertIn(
            create.STARTER / "www/assets/historic-city-hall.jpg",
            list(package.product_files()),
        )

    def test_scaffold_refuses_existing_folder_and_does_not_touch_contents(self):
        create = module("scaffold")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            sentinel = destination / "keep.txt"
            sentinel.write_text("user work")
            with self.assertRaises(ValueError):
                create.scaffold(
                    destination, title="App", sample="services", future_source="unknown"
                )
            self.assertEqual(sentinel.read_text(), "user work")

    def test_scaffold_refuses_own_package_and_invalid_input(self):
        create = module("scaffold")
        with self.assertRaises(ValueError):
            create.scaffold(
                SKILL / "never-created",
                title="App",
                sample="services",
                future_source="unknown",
            )
        with tempfile.TemporaryDirectory() as temporary:
            for title, sample in (
                ("", "services"),
                ("x" * 61, "services"),
                ("Bad\nTitle", "services"),
                ("App", "live"),
            ):
                with self.assertRaises(ValueError):
                    create.scaffold(
                        Path(temporary) / "new",
                        title=title,
                        sample=sample,
                        future_source="unknown",
                    )
                self.assertFalse((Path(temporary) / "new").exists())

    def test_inspector_respects_row_budget_and_does_not_echo_values(self):
        inspect = module("inspect_sample")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "sample.csv"
            source.write_text(
                "date,amount,person\n" + "2026-01-01,12,PRIVATE_VALUE\n" * 120
            )
            result = inspect.inspect(source)
            self.assertEqual(result["rows_inspected"], 100)
            self.assertNotIn("PRIVATE_VALUE", json.dumps(result))
            self.assertEqual(result["columns"][0]["observed_types"], ["date-like"])

    def test_inspector_rejects_large_files_and_network_paths(self):
        inspect = module("inspect_sample")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "large.csv"
            source.write_bytes(b"a" * (inspect.MAX_BYTES + 1))
            with self.assertRaises(ValueError):
                inspect.inspect(source)
        with self.assertRaises(ValueError):
            inspect.inspect(Path("//server/share/data.csv"))

    def test_inspector_json_shapes_and_missing_values(self):
        inspect = module("inspect_sample")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "sample.json"
            source.write_text('[{"amount":null},{"amount":0},{"amount":-10}]')
            result = inspect.inspect(source)
            self.assertEqual(result["columns"][0]["missing_in_sample"], 1)
            source.write_text('{"nested":[]}')
            with self.assertRaises(ValueError):
                inspect.inspect(source)


if __name__ == "__main__":
    unittest.main()
