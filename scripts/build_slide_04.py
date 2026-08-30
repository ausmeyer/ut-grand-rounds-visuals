#!/usr/bin/env python3
"""Build the self-contained slide-4 iframe page."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "slide-04.template.html"
SYSTEMS = ROOT / "data" / "slide-04-systems.json"
OUTPUT = ROOT / "docs" / "slide-04.html"
MARKER = "/*__SLIDE_04_SYSTEMS__*/"


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    systems = json.loads(SYSTEMS.read_text(encoding="utf-8"))
    if MARKER not in template:
        raise ValueError(f"Template marker {MARKER!r} was not found")
    rendered = template.replace(
        MARKER,
        json.dumps(systems, ensure_ascii=False, separators=(",", ":")),
    )
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(systems)} systems")


if __name__ == "__main__":
    main()
