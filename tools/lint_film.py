"""Static checks for the explainer house rules (no rendering needed).

    python3 tools/lint_film.py animations/KVCache/kv_cache.py
    python3 tools/lint_film.py animations/*/[a-z]*.py --summary

Errors (exit 1) break a hard rule; warnings are smells worth a look:

  E101  Tex / MathTex / DecimalNumber / Integer: needs LaTeX (the repo is LaTeX-free)
  E102  em-dash in rendered text (reads as an "AI tell"; use . : or ,)
  E103  arr()/Arrow() endpoint is a bare name: pass box.get_right(), not box
  W201  font size < 16: unreadable on a phone at 1080p
  W202  rendered string > 100 chars: Pango soft-wraps it; split the sentence
  W203  slide-deck smell: "in one card/breath", bullet glyphs, tick-lists
  W204  no on-screen cite() although the docstring names a paper / dataset
  W205  CurvedArrow: verify the bow direction in a rendered frame
  W206  scene method has no visual besides text (a slide, not a picture)
"""

from __future__ import annotations

import argparse
import ast
import re
from collections import Counter
from pathlib import Path

TEXT_FUNCS = {
    "Text",
    "BaseText",
    "MarkupText",
    "Paragraph",
    "txt",
    "mono",
    "say",
    "caption",
    "swap_cap",
    "takeaway",
    "cite",
    "chip",
    "pill",
    "stamp",
    "bottomcap",
    "section_header",
    "show_say",
    "replace_say",
    "set_cap",
    "tok_box",
    "dot_label",
}
LATEX = {
    "Tex",
    "MathTex",
    "SingleStringMathTex",
    "DecimalNumber",
    "Integer",
    "Variable",
}
TEXT_ONLY_OK = {"play_intro", "play_outro", "introduction", "play_all"}
MOBJECT_CTORS = {
    "VGroup",
    "Group",
    "Rectangle",
    "RoundedRectangle",
    "Square",
    "Circle",
    "Dot",
    "Text",
    "BaseText",
    "txt",
    "mono",
    "chip",
    "pill",
    "stamp",
    "plate",
    "tok_box",
    "Polygon",
    "SurroundingRectangle",
    "ImageMobject",
    "Ellipse",
    "Star",
    "RegularPolygon",
    "Triangle",
    "image_card",
    "node_box",
    "person",
    "padlock",
    "browser",
}
# calls that only place text or run plumbing: a scene made of nothing else is a slide
TEXTY = TEXT_FUNCS | {
    "play",
    "wait",
    "beat",
    "read",
    "settle",
    "wipe",
    "card_wait",
    "clear_cap",
    "add",
    "remove",
    "FadeIn",
    "FadeOut",
    "Write",
    "Transform",
    "ReplacementTransform",
    "TransformMatchingStrings",
    "AddTextLetterByLetter",
    "Indicate",
    "Circumscribe",
    "LaggedStart",
    "AnimationGroup",
    "Succession",
    "VGroup",
    "Group",
    "arrange",
    "next_to",
    "move_to",
    "to_edge",
    "to_corner",
    "shift",
    "scale",
    "set_color",
    "align_to",
    "set_opacity",
    "scale_to_fit_width",
    "animate",
    "get_center",
    "get_top",
    "get_bottom",
    "get_left",
    "get_right",
    "clamp_width",
    "range",
    "len",
    "zip",
    "enumerate",
    "min",
    "max",
    "set",
    "copy",
    "Line",
    "Underline",
    "make_tick",
    "make_cross",
    "dot_label",
    "set_width",
    "set_stroke",
    "set_fill",
}
PAPER = re.compile(r"arXiv|et al\.|NeurIPS|ICLR|ICML|CVPR|ACL|dataset|benchmark", re.I)


def call_name(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def strings_in(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n
        elif isinstance(n, ast.JoinedStr):
            yield n


def lint(path: Path):
    src = path.read_text()
    tree = ast.parse(src)
    out = []

    def add(node, code, msg):
        out.append((path, getattr(node, "lineno", 0), code, msg))

    doc = ast.get_docstring(tree) or ""
    has_cite = "cite(" in src
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name in LATEX and isinstance(node.func, ast.Name):
            add(node, "E101", f"{name}() needs LaTeX; build it from Text / mtext()")
        if name in TEXT_FUNCS:
            for s in strings_in(node):
                val = s.value if isinstance(s, ast.Constant) else ast.unparse(s)
                if "—" in val:
                    add(s, "E102", f"em-dash in rendered text: {val[:50]!r}")
                if isinstance(s, ast.Constant) and len(val) > 100 and "\n" not in val:
                    add(s, "W202", f"{len(val)}-char line will soft-wrap: split it")
                if re.search(r"in one (card|breath)|^\s*[•●▪]", val):
                    add(s, "W203", f"slide-deck phrasing/bullets: {val[:50]!r}")
            for kw in node.keywords:
                if (
                    kw.arg in ("font_size", "fs")
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, int | float)
                    and kw.value.value < 16
                ):
                    add(
                        kw.value,
                        "W201",
                        f"{kw.arg}={kw.value.value} is too small to read",
                    )
        if name == "CurvedArrow":
            add(
                node, "W205", "CurvedArrow: check the bow direction in a rendered frame"
            )

    # E103: arrow endpoints that are names bound to a mobject in the same function
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        mobs = set()
        for st in ast.walk(fn):
            if (
                isinstance(st, ast.Assign)
                and isinstance(st.value, ast.Call)
                and call_name(st.value) in MOBJECT_CTORS
            ):
                mobs |= {t.id for t in st.targets if isinstance(t, ast.Name)}
        for c in ast.walk(fn):
            if isinstance(c, ast.Call) and call_name(c) in (
                "arr",
                "Arrow",
                "harrow",
                "DoubleArrow",
            ):
                for a in c.args[:2]:
                    if isinstance(a, ast.Name) and a.id in mobs:
                        add(
                            a,
                            "E103",
                            f"{call_name(c)}({a.id}, ...): {a.id} is a mobject; "
                            f"pass an edge point such as {a.id}.get_right()",
                        )

    if PAPER.search(doc) and not has_cite:
        add(
            tree,
            "W204",
            "docstring cites a paper/dataset but nothing calls cite() on screen",
        )

    # text-only scene methods (slides)
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        for fn in [m for m in cls.body if isinstance(m, ast.FunctionDef)]:
            if not fn.name.startswith("scene_") or fn.name in TEXT_ONLY_OK:
                continue
            calls = {call_name(c) for c in ast.walk(fn) if isinstance(c, ast.Call)} - {
                ""
            }
            if calls and calls <= TEXTY:
                add(
                    fn,
                    "W206",
                    f"{fn.name}() draws no visual besides text: make the picture carry it",
                )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--summary", action="store_true", help="per-file counts only")
    ap.add_argument("--errors-only", action="store_true")
    args = ap.parse_args()
    errors = 0
    for f in args.files:
        if f.name.startswith(("generate", "fetch", "bake", "verify", "_")):
            continue
        try:
            found = lint(f)
        except SyntaxError as e:
            print(f"{f}:{e.lineno}: E000 syntax error: {e.msg}")
            errors += 1
            continue
        if args.errors_only:
            found = [x for x in found if x[2].startswith("E")]
        errors += sum(1 for x in found if x[2].startswith("E"))
        if args.summary:
            c = Counter(code for *_, code, _ in found)
            if c:
                print(f"{f}: " + " ".join(f"{k}x{v}" for k, v in sorted(c.items())))
        else:
            for p, line, code, msg in found:
                print(f"{p}:{line}: {code} {msg}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
