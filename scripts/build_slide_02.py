#!/usr/bin/env python3
"""Build the self-contained slide-2 iframe page."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "src" / "slide-02.template.html"
EVENTS = ROOT / "data" / "slide-02-events.json"
OUTPUT = ROOT / "docs" / "slide-02.html"
MARKER = "/*__SLIDE_02_EVENTS__*/"


def main() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    events = json.loads(EVENTS.read_text(encoding="utf-8"))
    if MARKER not in template:
        raise ValueError(f"Template marker {MARKER!r} was not found")
    rendered = template.replace(
        MARKER,
        json.dumps(events, ensure_ascii=False, separators=(",", ":")),
    )
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(events)} events")


if __name__ == "__main__":
    main()
