"""One explicitly configured provider, with a bounded in-memory snapshot cache."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from datetime import date
from pathlib import Path

from city_app.data import Dataset, Provider, PROVIDERS

from . import arcgis, http, local, sql_server
from .common import SourceError, map_records, source_info, validate_mapping

KINDS = ("local", "http", "arcgis", "sql-server")


def read_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(config, dict) or config.get("kind") not in KINDS:
            raise SourceError("Choose source kind local, http, arcgis, or sql-server.")
        source_info(config)
        validate_mapping(config)
        if config["kind"] == "sql-server":
            sql_server.select_query(config)
        seconds = config.get("refresh_seconds", 300)
        if type(seconds) is not int or not 30 <= seconds <= 86400:
            raise SourceError("refresh_seconds must be between 30 and 86400.")
        if config["kind"] == "local" and not config["source"].get("updated_at"):
            raise SourceError(
                "Local files need source.updated_at: the date of the supplied data snapshot."
            )
        return config
    except SourceError:
        raise
    except (OSError, ValueError, TypeError) as error:
        raise SourceError(
            "Cannot read the source configuration. Check the JSON file and required fields."
        ) from error


class ConfiguredSource:
    def __init__(self, root: Path, config: dict):
        self.root = root
        self.config = config
        self.source = source_info(config)
        self.cached = None
        self.checked_at = float("-inf")
        self.lock = threading.Lock()

    def fetch(self) -> Dataset:
        kind = self.config["kind"]
        try:
            if kind == "local":
                rows = local.read_rows(self.root, self.config)
            else:
                rows = {
                    "http": http.read_rows,
                    "arcgis": arcgis.read_rows,
                    "sql-server": sql_server.read_rows,
                }[kind](self.config)
            records = map_records(rows, self.config)
        except SourceError:
            raise
        except Exception as error:
            # Never surface raw driver responses, payloads, paths, or secrets in the UI.
            raise SourceError(
                "The source could not be loaded. Check its configuration and format with connect.py check."
            ) from error
        source = self.source
        if not self.config["source"].get("updated_at"):
            source = replace(
                source,
                updated_at=date.today(),
                limitation=source.limitation
                + " Snapshot date is the retrieval date, not the last edit date of the source records.",
            )
        return Dataset(records, source, "ready" if records else "empty")

    def load(self, condition="ready") -> Dataset:
        # Preview simulations never alter a configured source's real state.
        with self.lock:
            if time.monotonic() - self.checked_at < self.config.get(
                "refresh_seconds", 300
            ):
                return self.cached
            try:
                self.cached = self.fetch()
            except sql_server.ReadOnlyViolation as error:
                # A safety refusal must not look like a usable stale connection.
                self.cached = Dataset((), self.source, "error", message=str(error))
            except SourceError as error:
                if self.cached is not None and self.cached.records:
                    self.cached = replace(
                        self.cached, state="stale", message=str(error)
                    )
                else:
                    self.cached = Dataset((), self.source, "error", message=str(error))
            self.checked_at = time.monotonic()
            return self.cached


def register_source(root: Path) -> None:
    path = root / "data_source.json"
    if path.is_file():
        source = ConfiguredSource(root, read_config(path))
        PROVIDERS["connected"] = Provider(source.source, source.load)
