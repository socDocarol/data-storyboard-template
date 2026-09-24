"""Local fictional JSON API: python examples/serve_api.py (Ctrl+C to stop)."""

import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path != "/requests":
            self.send_error(404)
            return
        try:
            page = int(parse_qs(parsed.query).get("page", ["1"])[0])
            if page < 1:
                raise ValueError
        except ValueError:
            self.send_error(400)
            return
        with (ROOT / "samples/services.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            rows = list(csv.DictReader(stream))
        start = (page - 1) * 12
        body = json.dumps(
            {
                "records": rows[start : start + 12],
                "next": f"/requests?page={page + 1}"
                if start + 12 < len(rows)
                else None,
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(
        "Fictional API at http://127.0.0.1:8130/requests?page=1. Ctrl+C to stop.",
        flush=True,
    )
    with ThreadingHTTPServer(("127.0.0.1", 8130), Handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
