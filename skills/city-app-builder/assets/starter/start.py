"""Install the local runtime once, then open this sample app on loopback only."""

from __future__ import annotations

import argparse
import hashlib
import os
import secrets
import socket
import subprocess
import sys
import time
import venv
import webbrowser
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent


def choose_port(preferred: int = 8126) -> int:
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", preferred))
        except OSError:
            listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_preview(
    process, url: str, preview_id: str, *, timeout: float = 30
) -> None:
    """Verify this launched instance, not merely any server returning HTTP 200."""
    from html.parser import HTMLParser

    class Identity(HTMLParser):
        def __init__(self):
            super().__init__()
            self.matches = []

        def handle_starttag(self, tag, attrs):
            values = dict(attrs)
            if tag == "meta" and values.get("name") == "storyboard-preview-id":
                self.matches.append(values.get("content"))

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "This app's server exited before its preview was ready. Check the startup error above."
            )
        try:
            with urlopen(url, timeout=1) as response:
                body = response.read(1_000_000).decode("utf-8")
                parser = Identity()
                parser.feed(body)
                if response.status == 200:
                    if parser.matches != [preview_id]:
                        raise RuntimeError(
                            "Another or unverified app responded at the selected URL. This preview was not opened; retry the launcher without stopping other apps."
                        )
                    if process.poll() is None:
                        return
        except (OSError, UnicodeError):
            pass
        time.sleep(0.1)
    raise RuntimeError("This app's preview did not become ready within 30 seconds.")


def stop_server(process) -> None:
    """Clean up only the child started by this launcher."""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def start_server(python: Path, root: Path, *, preferred_port: int = 8126):
    port = choose_port(preferred_port)
    url = f"http://127.0.0.1:{port}"
    preview_id = secrets.token_hex(16)
    process = subprocess.Popen(
        [
            str(python),
            "-m",
            "shiny",
            "run",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "app.py",
        ],
        cwd=root,
        env={**os.environ, "STORYBOARD_PREVIEW_ID": preview_id},
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        wait_for_preview(process, url, preview_id)
    except BaseException:
        stop_server(process)
        raise
    return process, url


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 12):
        raise RuntimeError(
            "Install Python 3.12 or newer, then open Start app.cmd again."
        )
    environment = ROOT / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        print("Preparing this app's local Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    requirements = ROOT / "requirements-lock.txt"
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = environment / ".city-requirements"
    if not marker.exists() or marker.read_text().strip() != digest:
        print(
            "Installing the app runtime. First launch needs internet access; later launches reuse it.",
            flush=True,
        )
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-r",
                str(requirements),
            ],
            check=True,
            cwd=ROOT,
        )
        marker.write_text(digest)
    process, url = start_server(python, ROOT)
    try:
        print(
            f"\nApp folder: {ROOT}\nOpen {url}\nCheck Data information for the active source and sample status. Keep this window open. Press Ctrl+C to stop.\n",
            flush=True,
        )
        if not args.no_browser:
            webbrowser.open(url)
        if process.wait() != 0:
            raise RuntimeError("This app's server stopped with an error.")
    finally:
        stop_server(process)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApp stopped.")
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(
            f"Could not start the app: {error}\nShare this message with your coding assistant; do not include credentials.",
            file=sys.stderr,
        )
        sys.exit(1)
