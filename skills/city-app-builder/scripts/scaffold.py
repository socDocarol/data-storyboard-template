"""Copy the bundled app to a new directory. Never merge into an existing app."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
STARTER = SKILL_ROOT / "assets" / "starter"
SAMPLES = {
    "services": "Explore patterns in fictional service requests, then find the records behind the numbers.",
    "spending": "Explore fictional spending entries, compare categories, and inspect the entries behind the totals.",
}


def scaffold(
    destination: Path,
    *,
    title: str,
    sample: str,
    future_source: str,
    audience: str = "City colleagues",
    banner: bool = False,
) -> Path:
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise ValueError(
            "Choose a new folder. Existing folders are never overwritten, even if empty."
        )
    if destination.is_relative_to(SKILL_ROOT):
        raise ValueError("Create the app outside the skill package.")
    if not title.strip() or len(title) > 60 or any(ord(char) < 32 for char in title):
        raise ValueError("Use a title of 1 to 60 characters on one line.")
    if sample not in SAMPLES:
        raise ValueError("Choose the services or spending example.")
    if future_source not in (
        "unknown",
        "file",
        "sql-server",
        "api",
        "sacramento-open-data",
    ):
        raise ValueError("Choose a supported future source.")
    shutil.copytree(
        STARTER,
        destination,
        ignore=shutil.ignore_patterns(
            ".venv", "__pycache__", "*.pyc", ".pytest_cache", "*.log", ".qa"
        ),
    )
    config_file = destination / "app_config.json"
    config = json.loads(config_file.read_text(encoding="utf-8"))
    config.update(
        title=title.strip(),
        sample=sample,
        audience=audience,
        description=SAMPLES[sample],
        banner=config.get("banner") if banner else None,
    )
    config_file.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (destination / "APP-BRIEF.md").write_text(
        f"# {title.strip()}\n\n"
        f"Audience: {audience}\n\n"
        "Main question: Explore the example's patterns and supporting records; refine from the conversation.\n\n"
        f"Intended future source: {future_source}. No connection has been attempted.\n\n"
        "Actually inspected: bundled fictional sample only.\n\n"
        "Confirmed: sample-data prototype; real source definitions are not verified.\n\n"
        f"Defaults: Home, Explore, Compare, and About using the {sample} example; shared selection, drilldowns, record details, and group comparison.\n\n"
        f"Banner: {'Bundled City Hall image selected.' if banner else 'No banner image selected; keep the layout without an image unless the user opts in.'}\n\n"
        "Unresolved meanings: the real source's row definition, measures, and freshness.\n\n"
        "Deferred: live data connectors, credentials, deployment, and further analyses.\n",
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--title", default="Data Explorer")
    parser.add_argument("--sample", choices=tuple(SAMPLES), default="services")
    parser.add_argument(
        "--future-source",
        choices=("unknown", "file", "sql-server", "api", "sacramento-open-data"),
        default="unknown",
    )
    parser.add_argument("--audience", default="City colleagues")
    parser.add_argument(
        "--banner",
        action="store_true",
        help="Include the bundled example banner after the user opts in.",
    )
    args = parser.parse_args()
    try:
        destination = scaffold(
            args.destination,
            title=args.title,
            sample=args.sample,
            future_source=args.future_source,
            audience=args.audience,
            banner=args.banner,
        )
    except (ValueError, OSError) as error:
        parser.exit(1, f"App not created: {error}\n")
    print(
        f"Created: {destination}\nOpen that folder and run: python start.py\nAll included data is fictional. Live connectors are deferred."
    )


if __name__ == "__main__":
    main()
