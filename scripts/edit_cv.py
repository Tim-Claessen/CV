#!/usr/bin/env python3
"""Serve one application CV with in-page text editing, and save back to lore.

    python scripts/edit_cv.py 2026-09-employer-role

Builds the private site, serves it, and opens /apply/<slug>/?edit=1. The page
makes its text editable; Save posts the changed values here, this writes them
into that record's application.yaml, and the site rebuilds so the page always
reflects the file rather than the browser.

Only values change. Comments, ordering and folded blocks in the record survive,
because the write is line-level (scripts/yaml_edit.py) rather than a reparse.
A save that produces a record the build rejects is rolled back.

This is a local tool: it binds to 127.0.0.1 and writes only inside the one
application folder named on the command line.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_pdf import PRIVATE_DIST, ROOT, applications_dir, free_port, npm  # noqa: E402
import yaml_edit  # noqa: E402


def build_private() -> None:
    subprocess.run(
        [npm(), "run", "build", "--", "--outDir", str(PRIVATE_DIST)],
        cwd=ROOT, check=True, env={**__import__("os").environ, "CV_MODE": "private"},
    )


def page_count(pdf: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


class EditHandler(SimpleHTTPRequestHandler):
    slug = ""

    def log_message(self, fmt: str, *args) -> None:  # quieter than the default
        if "api" in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - name fixed by the base class
        length = int(self.headers.get("content-length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad JSON"})

        # The slug is fixed at startup: a page cannot ask to write elsewhere.
        if payload.get("slug") != self.slug:
            return self._json(400, {"error": "wrong application"})

        if self.path == "/api/save":
            return self._save(payload.get("edits") or [])
        if self.path == "/api/export":
            return self._export()
        self._json(404, {"error": "no such route"})

    def _save(self, edits: list[dict]) -> None:
        record = applications_dir() / self.slug / "application.yaml"
        before = record.read_text(encoding="utf-8")
        text = before
        try:
            for edit in edits:
                path, value = edit["path"], edit["value"]
                if "index" in edit:
                    text = yaml_edit.set_sequence_item(text, path, int(edit["index"]), value)
                else:
                    text = yaml_edit.set_value(text, path, value)
        except (yaml_edit.RecordShapeError, KeyError, TypeError) as error:
            return self._json(400, {"error": f"{error}"})

        record.write_text(text, encoding="utf-8", newline="\n")
        try:
            build_private()
        except subprocess.CalledProcessError:
            record.write_text(before, encoding="utf-8", newline="\n")
            build_private()
            return self._json(400, {"error": "build rejected the change, record restored"})
        print(f"saved {len(edits)} edit(s) to {record}", flush=True)
        self._json(200, {"ok": True, "saved": len(edits)})

    def _export(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "export_pdf.py"),
             "--application", self.slug, "--no-build"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            return self._json(400, {"error": (result.stderr or "export failed").strip()[-200:]})
        pdf = applications_dir() / self.slug / "cv.pdf"
        self._json(200, {"ok": True, "pages": page_count(pdf)})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="application folder name in lore/job-applications/")
    parser.add_argument("--no-build", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    record = applications_dir() / args.slug / "application.yaml"
    if not record.exists():
        print(f"no application.yaml in {record.parent}", file=sys.stderr)
        return 1

    if not args.no_build:
        build_private()
    page = PRIVATE_DIST / "apply" / args.slug / "index.html"
    if not page.exists():
        print(f"{page} not built. Is the record's status 'drafting'?", file=sys.stderr)
        return 1

    EditHandler.slug = args.slug
    port = free_port()
    httpd = ThreadingHTTPServer(
        ("127.0.0.1", port), partial(EditHandler, directory=str(PRIVATE_DIST))
    )
    url = f"http://127.0.0.1:{port}/apply/{args.slug}/?edit=1"
    print(f"editing {args.slug}", flush=True)
    print(f"  {url}", flush=True)
    print(f"Ctrl+C to stop. Saves go into {record}", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("stopped")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
