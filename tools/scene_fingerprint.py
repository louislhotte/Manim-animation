"""Fingerprint Manim scenes without rendering a single frame.

A fingerprint is the sequence of Manim's own per-``play()`` cache keys: a hash of
the camera, the animations and every mobject on screen at each call. Two
fingerprints that match mean the two runs would produce identical frames, which
makes this the cheapest proof that a refactor (e.g. a change to ``manimx``) left a
film's output untouched.

How it works: every ``play()`` is reported as "already cached", so Manim computes
the hash, fast-forwards the animation to its final state, and never rasterises
anything. Scenes that take minutes to render fingerprint in seconds.

Usage (run with the Manim interpreter; see tools/render_lib.sh for MX_PYTHON):

    python tools/scene_fingerprint.py animations/KVCache/kv_cache.py            # every scene class
    python tools/scene_fingerprint.py animations/KVCache/kv_cache.py Waste Reuse
    python tools/scene_fingerprint.py --json out.json animations/KVCache/kv_cache.py

Output: one line per scene, ``<Class> <n_plays> <digest>``. Compare two runs
with ``diff``. The pacing env vars (``MX_QUICK`` / ``<PREFIX>_QUICK`` ...) change
wait lengths and therefore the fingerprint; keep them identical across runs.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))  # so films can `from manimx import *`


def _patch_file_writer() -> None:
    from manim.scene.scene_file_writer import SceneFileWriter

    SceneFileWriter.is_already_cached = lambda self, h: True  # never rasterise
    SceneFileWriter.finish = lambda self: None  # nothing to combine
    SceneFileWriter.save_image = lambda self, image: None


def _ignore_function_source() -> None:
    """Hash functions by name only, not by their source text.

    Manim serialises updater closures together with the source of every
    function they reference, so moving a helper into a library (same behaviour,
    different docstring) changes the hash. Updaters still run, and their effect
    lands in the next play's mobject state, which is still compared.
    """
    import types

    from manim.utils import hashing

    original = hashing._CustomEncoder.default

    def default(self, obj):
        if isinstance(obj, types.MethodType | types.FunctionType):
            return f"<fn {getattr(obj, '__qualname__', getattr(obj, '__name__', '?'))}>"
        return original(self, obj)

    hashing._CustomEncoder.default = default


def _scene_classes(module) -> list[str]:
    from manim import Scene

    names = []
    for name, obj in vars(module).items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, Scene)
            and obj.__module__ == module.__name__
            and not name.startswith("_")
        ):
            names.append(name)
    return names


def fingerprint(path: Path, classes: list[str], verbose: bool = False) -> dict:
    from manim import config
    from manim.utils.module_ops import get_module

    os.chdir(path.parent)  # films load assets relative to their own folder
    config.media_dir = tempfile.mkdtemp(prefix="mx-fp-")
    config.verbosity = "ERROR"
    config.progress_bar = "none"
    config.disable_caching = False
    config.seed = 0  # Manim reseeds random/np.random per scene; None = OS entropy
    config.pixel_width, config.pixel_height, config.frame_rate = 854, 480, 15

    module = get_module(Path(path.name))
    results = {}
    for name in classes or sorted(_scene_classes(module)):
        t0 = time.perf_counter()
        scene = getattr(module, name)()
        scene.render()
        hashes = [h or "-" for h in scene.renderer.animations_hashes]
        digest = hashlib.sha256("\n".join(hashes).encode()).hexdigest()[:16]
        results[name] = {
            "plays": len(hashes),
            "digest": digest,
            "seconds": round(time.perf_counter() - t0, 1),
        }
        if verbose:
            results[name]["hashes"] = hashes
    return results


def _pin_hash_seed() -> None:
    """Re-exec once with PYTHONHASHSEED=0.

    Python's per-process hash salt changes set/dict-of-str iteration order, which
    can change mobject order and therefore the fingerprint.
    """
    if os.environ.get("PYTHONHASHSEED") != "0":
        os.environ["PYTHONHASHSEED"] = "0"
        os.execv(sys.executable, [sys.executable, *sys.argv])


def main() -> int:
    _pin_hash_seed()
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("file", type=Path, help="film .py file")
    ap.add_argument("classes", nargs="*", help="scene classes (default: all public)")
    ap.add_argument("--json", type=Path, help="also write results to this JSON file")
    ap.add_argument("-v", "--verbose", action="store_true", help="keep every hash")
    ap.add_argument(
        "--ignore-code",
        action="store_true",
        help="hash functions (updaters) by name, not source: use when helpers moved",
    )
    args = ap.parse_args()

    _patch_file_writer()
    if args.ignore_code:
        _ignore_function_source()
    results = fingerprint(args.file.resolve(), args.classes, args.verbose)
    for name, r in results.items():
        print(f"{name} {r['plays']} {r['digest']}  ({r['seconds']}s)")
    if args.json:
        args.json.write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
