"""Bake the PubTables-1M paper's own figures into assets/ for the film.

One-time bake step (needs network + pymupdf; the render itself stays offline).

Source paper (all figures reused verbatim, as the film states on screen):

    Brandon Smock, Rohith Pesala, Robin Abraham.
    "PubTables-1M: Towards comprehensive table extraction from
    unstructured documents." CVPR 2022. arXiv:2110.00061 (v3).
    Licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/),
    which permits redistribution with attribution.

The paper's figures are embedded in the PDF as raster images; we pull them
out at native resolution via their xrefs (verbatim, no re-rendering), plus a
3x render of page 1 (the citation card) and a 4x clip of the Algorithm 1 box.

Run with any Python that has pymupdf:

    python3 -m venv /tmp/ptenv && /tmp/ptenv/bin/pip install pymupdf
    /tmp/ptenv/bin/python fetch_assets.py

Assets are saved as quality-95 JPEGs (the repo gitignores *.png).
"""
from __future__ import annotations

import os
import urllib.request

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

# Pin the exact revision so the image xrefs below stay valid.
PDF_URL = "https://arxiv.org/pdf/2110.00061v3"
PDF_LOCAL = "/tmp/pubtables_2110.00061v3.pdf"

# Embedded raster figures, by xref in the v3 PDF.
FIGS = [
    ("fig1_example.jpg", 54),     # Fig 1: a presentation table (structure implicit)
    ("fig2_tasks.jpg", 61),       # Fig 2: detection / structure / functional analysis
    ("fig3a_overseg.jpg", 98),    # Fig 3a: oversegmented structure annotation
    ("fig3b_canonical.jpg", 99),  # Fig 3b: canonical structure annotation
    ("fig4_dilated.jpg", 203),    # Fig 4: dilated boxes for the six object classes
]


def ensure_pdf() -> pymupdf.Document:
    if not os.path.exists(PDF_LOCAL):
        print(f">> downloading {PDF_URL}")
        req = urllib.request.Request(
            PDF_URL, headers={"User-Agent": "pubtables-explainer-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(PDF_LOCAL, "wb") as f:
            f.write(r.read())
    return pymupdf.open(PDF_LOCAL)


def save(pix: pymupdf.Pixmap, name: str) -> None:
    out = os.path.join(ASSETS, name)
    pix.save(out, jpg_quality=95)
    print(f">> {name}  {pix.width}x{pix.height}")


def main() -> None:
    doc = ensure_pdf()

    # 1) The figures themselves, verbatim at native resolution.
    for name, xref in FIGS:
        pix = pymupdf.Pixmap(doc, xref)
        if pix.colorspace and pix.colorspace.n > 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        save(pix, name)

    # 2) Page 1, rendered as the "this is the actual paper" citation card.
    save(doc[0].get_pixmap(matrix=pymupdf.Matrix(3, 3)), "page1.jpg")

    # 3) The Algorithm 1 box on page 5, clipped from its title to its LAST
    #    line (the phrase below appears twice; [-1] takes line 14, not 11).
    p5 = doc[4]
    title = p5.search_for("PubTables-1M Canonicalization")[0]
    bottom = p5.search_for("with any adjacent blank cells below")[-1]
    clip = pymupdf.Rect(48, title.y0 - 10, 298, bottom.y1 + 8)
    save(p5.get_pixmap(matrix=pymupdf.Matrix(4, 4), clip=clip), "alg1_canon.jpg")


if __name__ == "__main__":
    main()
