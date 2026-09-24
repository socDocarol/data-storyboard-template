"""Build a portable ZIP from an explicit set of product folders."""

from __future__ import annotations

import hashlib
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.4.0"
EXCLUDE = {
    ".venv",
    ".cache",
    ".qa",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    ".git",
}
ROOT_FILES = (
    "README.md",
    "PRODUCT.md",
    "DESIGN.md",
    "Preview sample.cmd",
    ".gitignore",
)


def product_files():
    for name in ROOT_FILES:
        yield ROOT / name
    for folder in ("skills", "docs", "tests", "scripts"):
        for directory, dirs, files in os.walk(ROOT / folder):
            dirs[:] = sorted(
                name
                for name in dirs
                if name not in EXCLUDE and not (Path(directory) / name).is_symlink()
            )
            for name in sorted(files):
                path = Path(directory) / name
                if path.is_symlink():
                    raise ValueError(f"Do not package symbolic links: {path}")
                if name == ".gitignore" or (
                    not name.startswith(".")
                    and path.suffix
                    in (
                        ".py",
                        ".md",
                        ".json",
                        ".txt",
                        ".css",
                        ".js",
                        ".csv",
                        ".png",
                        ".woff2",
                        ".cmd",
                    )
                ):
                    yield path


def main():
    destination = ROOT / "dist" / f"city-app-kit-{VERSION}.zip"
    destination.parent.mkdir(exist_ok=True)
    files = list(product_files())
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(ROOT)
            archive.write(path, (Path("city-app-kit") / relative).as_posix())
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip():
            raise ValueError("Archive CRC validation failed.")
        for name in archive.namelist():
            if ".." in Path(name).parts or any(
                part in EXCLUDE for part in Path(name).parts
            ):
                raise ValueError(f"Unexpected archive path: {name}")
    checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
    print(
        f"Created {destination}\n{len(files)} files; {destination.stat().st_size:,} bytes\nSHA-256 {checksum}"
    )


if __name__ == "__main__":
    main()
