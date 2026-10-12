"""Draws every image of the profile into OUT_DIR (default: dist).

    GITHUB_TOKEN=... python -m extras.build

First the four galaxy-profile plates from config.yml, then the open-source plate.
Any error stops the build, so the workflow publishes nothing and the images of
the last good run stay online.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor" / "galaxy-profile"))

from generator.config import validate_config  # noqa: E402
from generator.main import run  # noqa: E402
from generator.plates import VARIANTS  # noqa: E402
from generator.themes import get_theme  # noqa: E402

from extras import opensource, pulls  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    out = Path(os.environ.get("OUT_DIR", "dist"))
    token = os.environ.get("GITHUB_TOKEN", "")
    config_path = ROOT / "config.yml"

    run(config_path, out, demo=False, token=token, today=date.today())

    with open(config_path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    extra = raw.get("open_source", {})
    config = validate_config(raw)
    found = pulls.fetch(config["username"], token, extra.get("min_stars", 500), extra.get("exclude", []),
                        extra.get("limit", 6))
    for suffix, mode, mobile in VARIANTS:
        theme = get_theme(config["themes"][mode], mode, config["themes"]["overrides"])
        (out / f"open-source{suffix}.svg").write_text(opensource.render(found, theme, mobile, config["motion"]),
                                                      encoding="utf-8")
    logging.info("Open source: %d pull requests drawn.", len(found))


if __name__ == "__main__":
    main()
