#!/usr/bin/env python3
"""Fail the build if a non-public client name reaches the public output.

The anonymisation rules live in three places -- lore's `public:` flags, cv-sync's
leak detection, and this repo's overrides -- and a mistake in any one of them puts
a real client name on the open web. This is the backstop: it reads the built HTML
and looks for names that should never be there, whatever the upstream logic said.

Checks the rendered output, not the source, because that's what actually ships.

Usage:
    python scripts/check_public.py            # scan dist/
    python scripts/check_public.py --dir out  # scan somewhere else
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CAREER = REPO_ROOT / "content" / "career.json"

# Aliases short enough to collide with ordinary words are skipped: "VIA" would
# match the word "via", and a false alarm that can't be silenced gets ignored.
MIN_ALIAS = 4

# Hyphens and underscores are word separators in a URL, so "south32-leave" has to
# be seen as the words it contains.
SEPARATORS = re.compile(r"[-_/]+")


def searchable(text: str) -> str:
    """Everything a client name could hide in: prose, attributes, URLs, JSON."""
    return SEPARATORS.sub(" ", text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=REPO_ROOT / "dist")
    args = parser.parse_args()

    if not CAREER.exists():
        print(f"{CAREER} not found — run /cv-sync first", file=sys.stderr)
        return 1
    if not args.dir.is_dir():
        print(f"{args.dir} not found — run `npm run build` first", file=sys.stderr)
        return 1

    payload = json.loads(CAREER.read_text(encoding="utf-8"))
    forbidden: dict[str, str] = {}
    for client in payload["clients"]:
        if client["public"]:
            continue
        for identifier in (client["name"], *client.get("aliases", [])):
            if len(identifier) >= MIN_ALIAS:
                forbidden[identifier] = client["name"]

    pages = sorted(args.dir.rglob("*.html"))
    if not pages:
        print(f"no HTML found under {args.dir}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for page in pages:
        rel = page.relative_to(args.dir)
        # The whole file, not just visible text: a client name in an href, a slug,
        # or an embedded JSON payload is just as public as one in a paragraph.
        # The path itself counts too — the URL is visible in the address bar.
        haystacks = {
            "path": searchable(str(rel)),
            "content": searchable(page.read_text(encoding="utf-8", errors="replace")),
        }
        for identifier, client in forbidden.items():
            pattern = r"(?<![A-Za-z0-9])" + re.escape(searchable(identifier)) + r"(?![A-Za-z0-9])"
            for where, haystack in haystacks.items():
                if re.search(pattern, haystack, re.IGNORECASE):
                    failures.append(
                        f"{rel} [{where}]: '{identifier}' (client {client!r} is public: false)"
                    )

    if failures:
        print(f"FAIL — {len(failures)} client name(s) leaked into the public build:\n")
        for failure in sorted(set(failures)):
            print(f"  {failure}")
        print(
            "\nFix by anonymising the wording in overrides/, or set public: true on the "
            "client in lore if it may genuinely be named."
        )
        return 1

    print(f"OK — scanned {len(pages)} page(s), no non-public client names found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
