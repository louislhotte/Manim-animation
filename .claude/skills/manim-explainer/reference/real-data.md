# Real data beats a synthetic stand-in

On GeoDetect the same story was cut twice: v1 from procedural stand-ins (a hand-coded
pixel grid, a Gaussian "NDVI" curve) was called "lazy"; v2 from real Sentinel-2 /
Landsat imagery was "much better". Scale is part of the evidence: hundreds of real
irrigation circles convince where a 7x13 toy grid does not.

## Rules
- **Reach for a real, open dataset or API before inventing one.** Government and
  research open-data APIs are usually free, keyless and one HTTP GET away
  (e.g. Microsoft Planetary Computer's titiler renders band math like NDVI as a PNG
  server-side, no GDAL needed).
- **Bake once, render offline.** A `fetch_assets.py` / `generate_assets.py` writes into
  `assets/`; declare the files in `render.sh` (`ASSETS=(...)`) so the driver rebuilds
  them only when missing or with `--assets`. Seed every random generator.
- **Compute and assert, don't type numbers in.** A trained toy network, a real
  benchmark run, a real `rustc` error: run it in the baking script, store the result,
  and `assert` the facts the film states (counts, totals, which item wins).
- **Verify a highlighted data point against the source** before circling it: overlay a
  coordinate grid on the full-resolution source, read the pixel, convert to scene space
  (GeoDetect's `image_point()`).
- **Synthetic is fine when no real thing exists** or the subject is a pure algorithm or
  data structure (a B-tree, a loss surface). "Real" then means computed, not vibes.

## A paper's table or figure: show the real thing
A cell-by-cell rebuild of a results table was rejected as "not professional" even
with every number exact. Crop the PDF instead:

```python
import pymupdf
page = doc[page_no]
hits = [r for r in page.search_for("Table 3") if y_lo < r.y0 < y_hi]   # filter by y, not [0]
clip = pymupdf.Rect(x0, hits[0].y0 - 4, x1, y_end)
page.get_pixmap(matrix=pymupdf.Matrix(5, 5), clip=clip).save("assets/table3.jpg", jpg_quality=95)
```

- Anchor the clip on the table's own caption / header text (`search_for`); when a
  string appears twice on a page, pick the match by y-range (results are in document
  order, `[0]`/`[-1]` silently picks the wrong one).
- Show it with an `ImageMobject` plus a border; animate highlight boxes at *relative*
  image coordinates `(u, v)` in `[0, 1]` computed from the cell's text rect
  (`u = (x - clip.x0) / clip.width`), and check every coordinate on a 20x20 grid
  overlay of the saved image before trusting it.
- Worked examples: `animations/PubTables` (embedded figures), `animations/OmniDocBench`
  (vector tables cropped at zoom), `animations/GeoDetect` (`image_card`, `country_map`).
