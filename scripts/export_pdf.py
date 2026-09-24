#!/usr/bin/env python3
"""Render the built CV page to PDF.

- Renders /cv (the printable one-pager), not / (the browsable portfolio)
- Always writes cv/cv-latest.pdf
- Archives cv/archive/cv-YYYY-MM-DD.pdf (one file per day; overwrites today's)

These PDFs are committed to a public repo, so this refuses to run against a
private-mode build. A CV with real client names is produced locally from /build
and never checked in.

--application is the exception, because its output never enters this repo: it
builds private into dist-private/ (leaving dist/ public), renders /apply/<slug>/
and writes cv.pdf into that application's own folder in lore.

Setup (once):
    pip install -r requirements.txt
    python -m playwright install chromium

Usage:
    python scripts/export_pdf.py                 # build + render 'all'
    python scripts/export_pdf.py --lens business # a persona-specific PDF
    python scripts/export_pdf.py --no-build      # skip 'npm run build'
    python scripts/export_pdf.py --application 2026-09-employer-role
"""
from __future__ import annotations
import argparse, datetime, functools, http.server, os, shutil, socket
import socketserver, subprocess, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PRIVATE_DIST = ROOT / "dist-private"
CV = ROOT / "cv"
ARCHIVE = CV / "archive"


def npm() -> str:
    exe = "npm.cmd" if sys.platform == "win32" else "npm"
    path = shutil.which(exe)
    if not path:
        raise RuntimeError("npm not found — install Node.js and ensure npm is on PATH")
    return path


def sh(cmd: list[str], env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


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
    # An application PDF lands in lore, outside this repo.
    print("wrote", out.relative_to(ROOT) if out.is_relative_to(ROOT) else out)


def applications_dir() -> Path:
    """Mirrors applicationsDir() in src/lib/applications.ts."""
    configured = os.environ.get("CV_APPLICATIONS")
    return Path(configured).resolve() if configured else (ROOT.parent / "lore" / "job-applications")


def export_application(slug: str, build: bool) -> int:
    folder = applications_dir() / slug
    if not (folder / "application.yaml").exists():
        print(f"no application.yaml in {folder}", file=sys.stderr)
        return 1

    if build:
        build_env = {**os.environ, "CV_MODE": "private"}
        sh([npm(), "run", "build", "--", "--outDir", str(PRIVATE_DIST)], env=build_env)
    page = PRIVATE_DIST / "apply" / slug / "index.html"
    if not page.exists():
        print(f"{page} not built. Is the application's status 'drafting'?", file=sys.stderr)
        return 1

    port = free_port()
    httpd = serve(PRIVATE_DIST, port)
    try:
        render(f"http://127.0.0.1:{port}/apply/{slug}/", folder / "cv.pdf")
    except PermissionError:
        # Windows locks an open PDF, and the viewer is usually the one holding it.
        print(f"cannot write {folder / 'cv.pdf'} - close it in your PDF viewer and retry",
              file=sys.stderr)
        return 1
    finally:
        httpd.shutdown()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lens", default="all",
                    choices=["all", "business", "data"])
    ap.add_argument("--application", metavar="SLUG",
                    help="render one drafting application into its lore folder")
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    if args.application:
        return export_application(args.application, build=not args.no_build)

    if os.environ.get("CV_MODE") == "private":
        print(
            "refusing to export: CV_MODE=private names real clients, and these PDFs are "
            "committed to a public repo. Print from /build instead.",
            file=sys.stderr,
        )
        return 1

    if not args.no_build:
        build_env = {**os.environ, "CV_LENS": args.lens}
        sh([npm(), "run", "build"], env=build_env)
    if not DIST.exists():
        print("dist/ not found — run a build first.", file=sys.stderr)
        return 1

    CV.mkdir(exist_ok=True)
    port = free_port()
    httpd = serve(DIST, port)
    try:
        url = f"http://127.0.0.1:{port}/cv/"
        render(url, CV / "cv-latest.pdf")

        today = datetime.date.today().isoformat()
        dated = ARCHIVE / f"cv-{today}.pdf"
        render(url, dated)
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
