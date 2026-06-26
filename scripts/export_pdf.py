#!/usr/bin/env python3
"""Render the built CV site to PDF.

- Always writes cv/cv-latest.pdf
- Archives cv/archive/cv-YYYY-MM-DD.pdf only when /data has changed since the
  last run, and at most one file per day.

Setup (once):
    pip install playwright
    playwright install chromium

Usage:
    python scripts/export_pdf.py                 # build + render 'all'
    python scripts/export_pdf.py --lens business # a persona-specific PDF
    python scripts/export_pdf.py --no-build      # skip 'npm run build'
"""
from __future__ import annotations
import argparse, datetime, functools, hashlib, http.server, os, socket
import socketserver, subprocess, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data"
CV = ROOT / "cv"
ARCHIVE = CV / "archive"
STATE = CV / ".last_data_hash"


def sh(cmd: list[str], env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def data_hash() -> str:
    h = hashlib.sha256()
    for f in sorted(DATA.glob("*.csv")):
        h.update(f.read_bytes())
    return h.hexdigest()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def serve(directory: Path, port: int) -> socketserver.TCPServer:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(directory))
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def render(url: str, out: Path) -> None:
    from playwright.sync_api import sync_playwright
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.emulate_media(media="print")
        page.pdf(path=str(out), format="A4",
                 print_background=True,
                 margin={"top": "14mm", "bottom": "14mm",
                         "left": "14mm", "right": "14mm"})
        browser.close()
    print("wrote", out.relative_to(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lens", default="all",
                    choices=["all", "business", "data"])
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    if not args.no_build:
        build_env = {**os.environ, "CV_LENS": args.lens}
        sh(["npm", "run", "build"], env=build_env)
    if not DIST.exists():
        print("dist/ not found — run a build first.", file=sys.stderr)
        return 1

    CV.mkdir(exist_ok=True)
    port = free_port()
    httpd = serve(DIST, port)
    try:
        url = f"http://127.0.0.1:{port}/"
        render(url, CV / "cv-latest.pdf")

        current = data_hash()
        previous = STATE.read_text().strip() if STATE.exists() else ""
        today = datetime.date.today().isoformat()
        dated = ARCHIVE / f"cv-{today}.pdf"
        if current != previous and not dated.exists():
            render(url, dated)
            STATE.write_text(current)
        elif current == previous:
            print("data unchanged since last run — no dated archive written")
        else:
            print(f"archive for {today} already exists — skipping")
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
