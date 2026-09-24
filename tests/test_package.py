import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen
from unittest.mock import patch
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
    def test_new_preview_uses_its_own_server_when_preferred_port_is_occupied(self):
        class ExistingApp(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<title>Previous budget app</title>")

            def log_message(self, *args):
                pass

        previous = ThreadingHTTPServer(("127.0.0.1", 0), ExistingApp)
        thread = threading.Thread(target=previous.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                destination = module("scaffold").scaffold(
                    Path(temporary) / "New isolated budget app",
                    title="New isolated budget app",
                    sample="spending",
                    future_source="unknown",
                )
                script = """
import sys
from pathlib import Path
from urllib.request import urlopen
from start import start_server, stop_server

process, url = start_server(Path(sys.executable), Path.cwd(), preferred_port=int(sys.argv[1]))
try:
    assert not url.endswith(':' + sys.argv[1]), url
    with urlopen(url, timeout=5) as response:
        body = response.read().decode('utf-8')
    assert '<title>New isolated budget app</title>' in body
    assert 'storyboard-preview-id' in body
    assert process.poll() is None
    print('Verified separate preview:', url)
finally:
    stop_server(process)
"""
                result = subprocess.run(
                    [sys.executable, "-c", script, str(previous.server_port)],
                    cwd=destination,
                    capture_output=True,
                    text=True,
                    timeout=40,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("Verified separate preview:", result.stdout)
                with urlopen(
                    f"http://127.0.0.1:{previous.server_port}", timeout=2
                ) as response:
                    self.assertIn(b"Previous budget app", response.read())
        finally:
            previous.shutdown()
            previous.server_close()
            thread.join(timeout=2)

    def test_private_inputs_and_active_config_are_not_scaffolded_or_packaged(self):
        create = module("scaffold")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            starter = root / "skills/city-app-builder/assets/starter"
            data = starter / "Data"
            data.mkdir(parents=True)
            (data / "private.csv").write_text("secret")
            (data / "nested").mkdir()
            (data / "nested/private.csv").write_text("secret")
            (data / "README.md").write_text("Put files here")
            (data / ".gitignore").write_text("*")
            (starter / "data_source.json").write_text("{}")
            (starter / ".env.local").write_text("secret")
            (starter / "app_config.json").write_text(
                (create.STARTER / "app_config.json").read_text()
            )
            with patch.object(create, "STARTER", starter):
                app = create.scaffold(
                    root / "app",
                    title="Private test",
                    sample="services",
                    future_source="file",
                )
            self.assertEqual(
                {path.name for path in (app / "Data").iterdir()},
                {"README.md", ".gitignore"},
            )
            self.assertFalse((app / "data_source.json").exists())
            self.assertFalse((app / ".env.local").exists())
            spec = importlib.util.spec_from_file_location(
                "package_privacy", ROOT / "scripts/package.py"
            )
            package = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(package)
            with patch.object(package, "ROOT", root):
                files = list(package.product_files())
            self.assertIn(data / "README.md", files)
            self.assertNotIn(data / "private.csv", files)
            self.assertNotIn(data / "nested/private.csv", files)
            self.assertNotIn(starter / "data_source.json", files)
            self.assertNotIn(starter / ".env.local", files)

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
