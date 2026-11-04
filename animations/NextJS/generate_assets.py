#!/usr/bin/env python3
"""Bake REAL Next.js artifacts for the explainer (house rule: real data).

Copies demo/ (a genuine, minimal Next.js app backed by node:sqlite) into a
local temp dir — never into this OneDrive-synced repo — then actually:

    1. npm-installs Next.js and seeds the SQLite database,
    2. runs `next build` and captures its route table verbatim,
    3. starts `next start` and curls real responses:
         GET /            (static page)
         GET /books       (dynamic server-rendered page, twice — the two
                           "rendered at" timestamps prove per-request SSR)
         GET /api/books   (route handler returning JSON, with headers)
    4. scaffolds + builds a real Vite React SPA and captures its built
       dist/index.html — the famous "empty div" the SPA server sends.

Everything is written to assets/next.json and assets/spa.json so renders stay
offline. Network-dependent; run manually, not at render time.
"""
from __future__ import annotations

import json
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE / "demo"
ASSETS = HERE / "assets"
PORT = 3123

ENV = {"NO_COLOR": "1", "FORCE_COLOR": "0", "CI": "1",
       "NEXT_TELEMETRY_DISABLED": "1"}


def run(cmd, cwd, timeout=600):
    print(f"  $ {' '.join(cmd)}  (cwd={cwd})")
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       timeout=timeout, env={**dict(__import__('os').environ), **ENV})
    if p.returncode != 0:
        print(p.stdout[-4000:])
        print(p.stderr[-4000:])
        raise SystemExit(f"command failed: {cmd}")
    return p.stdout + p.stderr


def strip_ansi(s):
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def fetch(path, with_headers=False):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}")
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()
        if with_headers:
            status = f"HTTP/1.1 {r.status} {r.reason}"
            headers = {k.lower(): v for k, v in r.headers.items()}
            return status, headers, body
        return body


def wait_ready():
    for _ in range(120):
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise SystemExit("next start never came up")


def build_table(build_out):
    """The verbatim `next build` route table + legend lines."""
    lines = strip_ansi(build_out).splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Route (app)"))
    out = []
    for l in lines[start:]:
        out.append(l.rstrip())
        if l.strip().startswith(("ƒ", "f ")) and "(Dynamic)" in l:
            break
    return out


def body_excerpt(html):
    """The page's <main>...</main> region of Next's single-line HTML, split at
    tag boundaries for display. Text stays verbatim; only the framework's
    scripts/boilerplate outside <main> are dropped (whole tags)."""
    m = re.search(r"<main>.*</main>", html, re.S)
    parts = re.sub(r">\s*<", ">\n<", m.group(0)).splitlines()
    dropped = html.count("<script")
    return [p for p in parts if p.strip()], dropped


def main():
    ASSETS.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="nextjs_assets_"))
    print(f">> working in {tmp}")

    # ---- the Next.js app ---------------------------------------------------- #
    app = tmp / "next-demo"
    shutil.copytree(DEMO, app, ignore=shutil.ignore_patterns(
        "node_modules", ".next", "data", ".gitignore"))
    run(["npm", "install", "--no-audit", "--no-fund"], app, timeout=900)
    node_ver = run(["node", "--version"], app).strip()
    next_ver = json.loads((app / "node_modules/next/package.json").read_text())["version"]
    print(f">> next {next_ver} on node {node_ver}")

    run(["node", "seed.mjs"], app)
    build_out = run(["npx", "next", "build"], app, timeout=900)
    table = build_table(build_out)

    srv = subprocess.Popen(["npx", "next", "start", "-p", str(PORT)], cwd=app,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_ready()
        time.sleep(1.0)
        home_html = fetch("/")
        books_html_1 = fetch("/books")
        time.sleep(1.3)
        books_html_2 = fetch("/books")
        status, headers, api_body = fetch("/api/books", with_headers=True)
    finally:
        srv.terminate()
        srv.wait(timeout=15)

    books_rows, books_dropped = body_excerpt(books_html_1)
    home_rows, home_dropped = body_excerpt(home_html)
    # React SSR interleaves "<!-- -->" between text nodes; match the ISO stamp.
    # (It shows up twice per response: once in the HTML, once in the embedded
    # RSC payload — take the first per response.)
    iso = r"\d{4}-\d{2}-\d{2}T[\d:.]+Z"
    ts = [re.search(iso, h).group(0) for h in (books_html_1, books_html_2)]
    assert len(ts) == 2 and ts[0] != ts[1], ts  # proof of per-request SSR
    api_books = json.loads(api_body)
    assert len(api_books) == 5 and api_books[0]["year"] == 1975, api_books

    next_asset = {
        "next_version": next_ver,
        "node_version": node_ver,
        "build_table": table,
        "home_rows": home_rows, "home_scripts_dropped": home_dropped,
        "books_rows": books_rows, "books_scripts_dropped": books_dropped,
        "books_ts": ts,
        "api_status": status,
        "api_content_type": headers.get("content-type", ""),
        "api_body": api_body,
    }
    (ASSETS / "next.json").write_text(json.dumps(next_asset, indent=2))
    print(f">> wrote assets/next.json ({len(table)} table rows, ts {ts})")

    # ---- the Vite React SPA (the "empty div" contrast) ----------------------- #
    run(["npm", "create", "-y", "vite@latest", "spa", "--", "--template", "react"],
        tmp, timeout=600)
    spa = tmp / "spa"
    run(["npm", "install", "--no-audit", "--no-fund"], spa, timeout=900)
    run(["npm", "run", "build"], spa, timeout=600)
    index = (spa / "dist/index.html").read_text()
    vite_ver = json.loads((spa / "node_modules/vite/package.json").read_text())["version"]
    (ASSETS / "spa.json").write_text(json.dumps(
        {"vite_version": vite_ver, "index_html": index}, indent=2))
    print(f">> wrote assets/spa.json (vite {vite_ver}, {len(index)} bytes)")

    shutil.rmtree(tmp, ignore_errors=True)
    print(">> done")


if __name__ == "__main__":
    sys.exit(main())
