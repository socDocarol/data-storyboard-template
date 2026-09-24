"""Install the local runtime once, then open this sample app on loopback only."""

from __future__ import annotations

import argparse
import hashlib
import os
import socket
import subprocess
import sys
import threading
import time
import venv
import webbrowser
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent


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
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", 8126))
        except OSError:
            listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    url = f"http://127.0.0.1:{port}"

    def open_when_ready():
        for _ in range(60):
            try:
                with urlopen(url, timeout=1) as response:
                    if response.status == 200:
                        webbrowser.open(url)
                        return
            except OSError:
                time.sleep(0.5)

    if not args.no_browser:
        threading.Thread(target=open_when_ready, daemon=True).start()
    print(
        f"\nOpen {url}\nCheck Data information for the active source and sample status. Keep this window open. Press Ctrl+C to stop.\n",
        flush=True,
    )
    subprocess.run(
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
        cwd=ROOT,
        check=True,
    )


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
