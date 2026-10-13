#!/usr/bin/env python3
"""Bake the REAL data the film shows (run manually; the render itself is offline).

1. assets/bench.json — a real, measured benchmark: the same prime-counting
   algorithm, line for line, in CPython (bench/count_primes.py) and in Rust
   compiled with `rustc -O` (bench/count_primes.rs). Single thread each, best
   of 3 runs, on this machine. Also records versions, the chip, and asserts
   both languages return the identical prime count.

2. assets/errors.json — rustc's REAL stderr for the two snippets the film
   shows: bench/move_demo.rs (E0382, use after move) and bench/borrow_demo.rs
   (E0502, mutate while borrowed). Captured verbatim.

Usage:  python3 generate_assets.py
"""
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(ROOT, "bench")
ASSETS = os.path.join(ROOT, "assets")
LIMIT = 1_000_000
REPS = 3


def find_rustc():
    p = shutil.which("rustc")
    if p:
        return p
    cand = os.path.expanduser(
        "~/.rustup/toolchains/stable-aarch64-apple-darwin/bin/rustc")
    if os.path.exists(cand):
        return cand
    sys.exit("rustc not found — install Rust (rustup or `brew install rust`)")


def chip_name():
    try:
        out = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except OSError:
        pass
    return platform.machine()


def main():
    os.makedirs(ASSETS, exist_ok=True)
    rustc = find_rustc()
    rustc_ver = subprocess.run([rustc, "--version"], capture_output=True,
                               text=True).stdout.strip()
    py_ver = f"CPython {platform.python_version()}"

    # ---- 1. the benchmark (compile + run outside the OneDrive-synced tree) --
    with tempfile.TemporaryDirectory() as tmp:
        binpath = os.path.join(tmp, "count_primes")
        print(f">> compiling bench/count_primes.rs with -O  ({rustc_ver})")
        subprocess.run(
            [rustc, "-O", "--edition=2021",
             os.path.join(BENCH, "count_primes.rs"), "-o", binpath],
            check=True)

        print(f">> running Rust bench  (limit={LIMIT:,}, best of {REPS})")
        rs = json.loads(subprocess.run(
            [binpath, str(LIMIT), str(REPS)],
            capture_output=True, text=True, check=True).stdout)

        print(f">> running Python bench ({py_ver}, same limit, best of {REPS})"
              " — takes a few seconds...")
        py = json.loads(subprocess.run(
            [sys.executable, os.path.join(BENCH, "count_primes.py"),
             str(LIMIT), str(REPS)],
            capture_output=True, text=True, check=True).stdout)

    assert py["count"] == rs["count"], (py["count"], rs["count"])
    bench = {
        "limit": LIMIT,
        "count": py["count"],
        "py_s": round(py["best_s"], 4),
        "rs_s": round(rs["best_s"], 5),
        "speedup": round(py["best_s"] / rs["best_s"], 1),
        "py_ver": py_ver,
        "rs_ver": rustc_ver,
        "chip": chip_name(),
        "reps": REPS,
    }
    with open(os.path.join(ASSETS, "bench.json"), "w") as fh:
        json.dump(bench, fh, indent=2)
    print(f">> bench.json: python {bench['py_s']} s vs rust {bench['rs_s']} s"
          f"  =  {bench['speedup']}x   (both count {bench['count']:,} primes)")

    # ---- 2. the real compiler errors ----------------------------------------
    errors = {}
    for key, src in (("move", "move_demo.rs"), ("borrow", "borrow_demo.rs")):
        with tempfile.TemporaryDirectory() as tmp:
            # cwd=bench so the error's `-->` line cites the bare filename
            r = subprocess.run(
                [rustc, "--edition=2021", src, "-o", os.path.join(tmp, "demo")],
                capture_output=True, text=True, cwd=BENCH)
        assert r.returncode != 0, f"{src} unexpectedly compiled"
        errors[key] = r.stderr
        first = r.stderr.splitlines()[0]
        print(f">> errors.json [{key}]: {first}")
    errors["rs_ver"] = rustc_ver
    with open(os.path.join(ASSETS, "errors.json"), "w") as fh:
        json.dump(errors, fh, indent=2)
    print(">> done.")


if __name__ == "__main__":
    main()
