#!/usr/bin/env python3
"""Draft public-facing wording for projects that can't publish under their lore name.

lore names projects after their client ("Silverchain Payroll Analytics & Remediation"),
so a project title leaks the client even when the client node is anonymised. cv-sync
withholds those from the public build until an override supplies replacement wording.

This seeds those overrides with a first draft, so the starting point is 46 editable
lines rather than a blank file. Drafts are marked `draft: true` — the CV build treats
a draft exactly like a finished override, so review is about quality, not correctness.

Never overwrites wording that already exists. Re-run it after adding projects to lore
and it only appends the new ones.

Usage:
    python scripts/seed_overrides.py            # top up overrides/projects.yaml
    python scripts/seed_overrides.py --dry-run  # print what it would add
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CAREER = REPO_ROOT / "content" / "career.json"
OVERRIDES = REPO_ROOT / "overrides" / "projects.yaml"

# Joining words that shouldn't start a title once the client name is stripped off
# the front ("Fortescue UiPath..." -> "UiPath...", but "... & Reporting" -> "Reporting").
LEADING_JUNK = re.compile(r"^(?:and|&|of|for|the|a)\s+", re.IGNORECASE)

# Once the client name is stripped, a trailing corporate word can be left stranded
# at the front: "Endeavour Group Delegation..." -> "Group delegation...".
STRANDED = frozenset(
    {
        "group", "resources", "enterprises", "corporation", "limited", "ltd", "university",
        "department", "victorian", "australian", "federal", "commission", "of", "wa",
    }
)

# Removing client words can leave connector debris: "Victorian Department of & Risk
# Analytics" once "Jobs" and "Skills" are gone.
DEBRIS = [
    (re.compile(r"\s*&\s*&\s*"), " & "),
    (re.compile(r"^\s*[&,]\s*"), ""),
    (re.compile(r"\s+(?:of|and|&|for)\s*$", re.IGNORECASE), ""),
    (re.compile(r"\s{2,}"), " "),
]

# Descriptors read mid-sentence ("... for a global energy major"), so the leading
# capital has to go — except where the first word is genuinely a proper noun.
KEEP_CAPITALISED = frozenset({"victorian", "australian", "group", "wa", "queensland"})


def article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def lead_lower(phrase: str) -> str:
    """Lowercase a descriptor's first word unless it's a proper noun or acronym."""
    first, _, rest = phrase.partition(" ")
    if first.lower().strip("-") in KEEP_CAPITALISED:
        return phrase
    if any(c.isupper() for c in first[1:]):  # ASX-listed, IT, LNG
        return phrase
    return first[:1].lower() + first[1:] + (" " + rest if rest else "")


def strip_client_tokens(title: str, tokens: list[str]) -> str:
    """Drop the client's identifying words from a project title."""
    kept = []
    for word in title.split():
        bare = re.sub(r"[^A-Za-z0-9]", "", word).lower()
        if bare in tokens:
            continue
        kept.append(word)
    while kept and re.sub(r"[^A-Za-z0-9]", "", kept[0]).lower() in STRANDED:
        kept.pop(0)
    stem = " ".join(kept).strip()
    for pattern, replacement in DEBRIS:
        stem = pattern.sub(replacement, stem)
    return LEADING_JUNK.sub("", stem.strip()) or title


def product_phrases(payload: dict) -> list[str]:
    """Product names from lore's technologies, longest first.

    Matched as whole phrases, not tokens. Token matching pulls ordinary words out
    of multi-word product names -- "SAP Analytics Cloud" would capitalise every
    "Analytics", and "Employee Central Payroll" every "Payroll". Only technologies
    are used, never skills: skill names are ordinary words that should lowercase
    normally mid-sentence.
    """
    phrases = {
        source
        for technology in payload["technologies"]
        for source in (technology["name"], *technology.get("aliases", []))
        if source
    }
    return sorted(phrases, key=len, reverse=True)


def restore_products(text: str, phrases: list[str]) -> str:
    """Put canonical product casing back after sentence-casing flattened it."""
    for phrase in phrases:
        text = re.sub(
            r"(?<![A-Za-z0-9])" + re.escape(phrase) + r"(?![A-Za-z0-9])",
            phrase,
            text,
            flags=re.IGNORECASE,
        )
    return text


def sentence_case(text: str) -> str:
    """Lowercase words that are plainly not proper nouns or acronyms.

    Kept crude on purpose: these are drafts for a human to fix, and over-clever
    casing rules produce worse output than an obvious rule plus review.
    """
    out = []
    for i, word in enumerate(text.split()):
        # Compare on letters only, so trailing punctuation ("Quality,") doesn't
        # make an ordinary word look like a product name.
        bare = re.sub(r"[^A-Za-z0-9]", "", word)
        # Acronyms, product names and anything mixed-case stay as written.
        if not bare or bare.isupper() or any(c.isupper() for c in bare[1:]):
            out.append(word)
        elif i == 0:
            out.append(word[0].upper() + word[1:])
        else:
            out.append(word.lower())
    return " ".join(out)


def yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not CAREER.exists():
        print(f"{CAREER} not found — run /cv-sync first")
        return 1

    payload = json.loads(CAREER.read_text(encoding="utf-8"))
    clients = {c["name"]: c for c in payload["clients"]}
    phrases = product_phrases(payload)

    existing = OVERRIDES.read_text(encoding="utf-8") if OVERRIDES.exists() else ""

    blocks: list[str] = []
    for project in payload["projects"]:
        if project["publicSafe"]:
            continue
        # `"<name>":` is how each block is keyed; presence means hands off.
        if yaml_quote(project["name"]) + ":" in existing:
            continue

        client = clients.get(project["client"])
        descriptor = client["publicName"] if client else "an undisclosed client"
        tokens = sorted(
            {*project["leaks"]["title"], *project["leaks"]["outcome"], *project["leaks"]["body"]}
        )

        stem = restore_products(sentence_case(strip_client_tokens(project["name"], tokens)), phrases)
        phrase = lead_lower(descriptor)
        public_title = f"{stem} for {article(phrase)} {phrase}"

        lines = [
            f"  {yaml_quote(project['name'])}:",
            f"    publicTitle: {yaml_quote(public_title)}",
        ]
        if project["leaks"]["outcome"]:
            outcome = project["outcome"]
            for token in tokens:
                outcome = re.sub(
                    rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])",
                    descriptor,
                    outcome,
                    flags=re.IGNORECASE,
                )
            lines.append(f"    publicOutcome: {yaml_quote(outcome)}")
        lines.append("    draft: true")
        blocks.append("\n".join(lines))

    if not blocks:
        print("nothing to seed — every withheld project already has an override")
        return 0

    if args.dry_run:
        print("\n".join(blocks))
        return 0

    OVERRIDES.parent.mkdir(parents=True, exist_ok=True)
    if not existing.strip():
        header = (
            "# Project overrides — CV presentation layer.\n"
            "#\n"
            "# lore owns the facts (client, dates, technologies, outcome). This file owns how\n"
            "# they READ. Keys are lore project names; re-running /cv-sync never touches it.\n"
            "#\n"
            "#   publicTitle    replaces the lore name on public surfaces (required where the\n"
            "#                  lore name quotes a client that isn't public)\n"
            "#   publicOutcome  same, for the outcome line\n"
            "#   headline       short label for the CV builder, any surface\n"
            "#   bullet         CV wording, overriding outcome:\n"
            "#   weight         higher sorts earlier; default 0\n"
            "#   draft          true = auto-drafted, not yet reviewed by Tim\n"
            "\n"
            "projects:\n"
        )
        existing = header
    elif not existing.endswith("\n"):
        existing += "\n"

    OVERRIDES.write_text(existing + "\n".join(blocks) + "\n", encoding="utf-8")
    print(f"seeded {len(blocks)} project overrides into {OVERRIDES.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
