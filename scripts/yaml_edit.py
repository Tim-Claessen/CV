#!/usr/bin/env python3
"""Replace scalar values in an application record, line by line.

The in-page editor sends back the text of one field at a time. Rewriting the
YAML with a parser would lose the comments that say where wording came from, so
this locates the value's lines and replaces only those, leaving every other byte
of the file alone.

It understands the shapes /tailor writes and nothing else. Anything it does not
recognise raises, so a record is never half-written or mangled: the caller can
restore its backup and say what happened.

A path is a list of keys and indices, e.g.
    ["profile"]
    ["roles", "EY Director, Risk Analytics", "bullets", 0, "text"]
    ["projects", 2, "summary"]
    ["projects", 2, "technologies", 1]
"""
from __future__ import annotations

import json
import re
from typing import Sequence

WRAP_AT = 78


class RecordShapeError(ValueError):
    """The record isn't shaped the way this editor knows how to edit."""


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_blank(line: str) -> bool:
    return line.strip() == "" or line.lstrip().startswith("#")


def _key_pattern(key: str) -> re.Pattern[str]:
    escaped = re.escape(key)
    # A key is bare or quoted; role names carry commas and are quoted.
    # A key may also open a sequence item, as in "- text: ...".
    return re.compile(
        rf'^(?P<indent> *)(?P<dash>- )?(?P<key>"{escaped}"|\'{escaped}\'|{escaped})\s*:(?P<rest>.*)$'
    )


def _find_key(lines: list[str], start: int, end: int, key: str, indent: int | None) -> int:
    pattern = _key_pattern(key)
    for i in range(start, end):
        if _is_blank(lines[i]):
            continue
        match = pattern.match(lines[i])
        if match and (indent is None or len(match.group("indent")) == indent):
            return i
    raise RecordShapeError(f"key {key!r} not found")


def _block_end(lines: list[str], first: int, owner_indent: int) -> int:
    """Line after the block owned by a key or item at `owner_indent`."""
    i = first + 1
    last_content = first + 1
    while i < len(lines):
        if _is_blank(lines[i]):
            i += 1
            continue
        if _indent_of(lines[i]) <= owner_indent:
            break
        i += 1
        last_content = i
    return last_content


def _find_item(lines: list[str], start: int, end: int, index: int) -> tuple[int, int]:
    """Locate the nth `- ` item of the sequence beginning at `start`."""
    seen = -1
    item_indent: int | None = None
    for i in range(start, end):
        if _is_blank(lines[i]):
            continue
        indent = _indent_of(lines[i])
        stripped = lines[i].lstrip()
        if not stripped.startswith("- "):
            if item_indent is not None and indent <= item_indent:
                break
            continue
        if item_indent is None:
            item_indent = indent
        elif indent != item_indent:
            continue
        seen += 1
        if seen == index:
            return i, item_indent
    raise RecordShapeError(f"sequence item {index} not found")


def _resolve(lines: list[str], path: Sequence[object]) -> tuple[int, int, int]:
    """Return (key_line, region_end, owner_indent) for the value at `path`."""
    start, end, indent = 0, len(lines), 0
    key_line = -1
    for step in path:
        if isinstance(step, int):
            item_line, item_indent = _find_item(lines, start, end, step)
            key_line, indent = item_line, item_indent
            start, end = item_line, _block_end(lines, item_line, item_indent)
        else:
            key_line = _find_key(lines, start, end, str(step), None)
            # "- text:" opens both the item and the key, so the value it owns
            # ends where the item's next key starts, not where the item does.
            # Without this, editing a bullet would swallow its evidence lines.
            dash = lines[key_line].lstrip().startswith("- ")
            indent = _indent_of(lines[key_line]) + (2 if dash else 0)
            start, end = key_line, _block_end(lines, key_line, indent)
    if key_line < 0:
        raise RecordShapeError("empty path")
    return key_line, end, indent


def _wrap(text: str, indent: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) + indent > WRAP_AT:
            lines.append(" " * indent + current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(" " * indent + current)
    return lines or [" " * indent]


def _quote_inline(value: str) -> str:
    if value == "" or value[0] in "[{&*#?|-<>=!%@`\"'" or ": " in value or value.endswith(":"):
        return json.dumps(value)
    return value


def set_value(text: str, path: Sequence[object], value: str) -> str:
    """Return `text` with the scalar at `path` replaced by `value`."""
    value = " ".join(value.split())
    lines = text.splitlines()
    key_line, region_end, indent = _resolve(lines, path)

    line = lines[key_line]
    match = re.match(r"^(?P<head>\s*(?:- )?(?:\"[^\"]*\"|'[^']*'|[^:]+)\s*:)(?P<rest>.*)$", line)

    # A flow sequence element: technologies: [a, b, c]
    if isinstance(path[-1], int) and match is None:
        raise RecordShapeError("cannot edit that sequence item")
    if isinstance(path[-1], int):
        raise RecordShapeError("sequence element edits go through set_sequence_item")

    if match is None:
        raise RecordShapeError(f"line {key_line + 1} is not a key")

    head, rest = match.group("head"), match.group("rest").strip()
    if rest.startswith("|"):
        raise RecordShapeError("literal blocks are not edited here")

    if rest.startswith(">"):
        folded = rest  # keep the exact chomping indicator, e.g. ">-"
        body_indent = indent + 2
        for probe in range(key_line + 1, region_end):
            if not _is_blank(lines[probe]):
                body_indent = _indent_of(lines[probe])
                break
        new = [f"{head} {folded}"] + _wrap(value, body_indent)
    elif len(value) + len(head) + 1 > WRAP_AT and rest != "" and not rest.startswith("["):
        # Grown too long for one line: fold it, matching how /tailor writes prose.
        new = [f"{head} >-"] + _wrap(value, indent + 2)
    else:
        new = [f"{head} {_quote_inline(value)}"]

    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(lines[:key_line] + new + lines[region_end:]) + trailing


def set_sequence_item(text: str, path: Sequence[object], index: int, value: str) -> str:
    """Replace one element of an inline sequence, e.g. technologies: [a, b, c]."""
    value = " ".join(value.split())
    lines = text.splitlines()
    key_line, _end, _indent = _resolve(lines, path)
    match = re.match(r"^(?P<head>.*?:)\s*\[(?P<items>.*)\]\s*$", lines[key_line])
    if match is None:
        raise RecordShapeError(f"line {key_line + 1} is not an inline sequence")
    items = [item.strip() for item in match.group("items").split(",")] if match.group("items").strip() else []
    if not 0 <= index < len(items):
        raise RecordShapeError(f"sequence index {index} out of range")
    items[index] = _quote_inline(value)
    lines[key_line] = f"{match.group('head')} [{', '.join(items)}]"
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(lines) + trailing
