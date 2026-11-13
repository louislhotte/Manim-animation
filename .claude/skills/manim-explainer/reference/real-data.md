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

## A real map (OpenStreetMap), without any GIS library
`animations/MIP` draws Paris from OpenStreetMap with the standard library, NumPy,
SciPy and Cairo only:
- **Fetch once, cache, be polite** (`osm.py`): Overpass QL over HTTPS, one query per
  layer, roads in tiles, every answer gzipped in `~/.cache/manimx/`. The main
  instance (`overpass-api.de`) was at capacity (HTTP 502) and two mirrors hung;
  the instance of OpenStreetMap France answered in seconds. `out geom` returns each
  way with its coordinates and node ids, which is all a street graph needs.
- **Bake small** (`city.py`): project to metres around a reference point, store
  integer decimetres in one `.npz` (4.5 MB for the whole city); rasterise windows on
  demand with Cairo and cache the textures outside the repo.
- **Ride times are shortest paths** (`routing.py`): `scipy.sparse.csgraph.dijkstra`
  on the street graph, restricted to its largest strongly connected component; say
  which rules were kept (one-ways, speeds) and which were not (lights, slopes).
- Credit on screen and in the README: "Map data © OpenStreetMap contributors" (ODbL).

## A solver's run is data too
Run the real solver in the baking script and keep its log verbatim; show an excerpt
picked by matching line starts, never retyped. The model shown on screen is the
block of a real file that the bake `exec`s (`animations/MIP/demo/course.py`), so the
code and the numbers cannot drift apart. Cross-check the headline number with a
second method (another solver, brute force) and assert it.

What an independent review and the last checks found in the MIP film, most of it
invisible on screen:
- **Export exactly what you solved.** The bake solved the instance at full precision
  and wrote it rounded (4 decimals). A search is sensitive to the last digit: from
  the committed file our own branch and bound took 93 nodes, not the 129 the film
  states, and Gurobi's root bound read 32.78635 instead of 32.78638. Store the
  instance unrounded (JSON floats round-trip exactly) and check it the way a reader
  would: reload the file, solve again, compare tree and log.
- **Read a log only after the solver has closed it.** Switching Gurobi's `LogFile`
  off before a second run dropped everything the first run had not flushed: the
  kept log stopped at a 9 % gap, without its "Explored ... nodes" and "Optimal"
  lines. Silence the second run with `OutputFlag = 0`, dispose model and
  environment, then copy the file; assert that the summary line is in it.
- **A rule shown as a solver's trick must be derived, not looked up.** The first
  version justified a cutting plane with brute force (the very enumeration the film
  rules out). The same rule follows from the data in one line (six deliveries take
  at least 61 minutes, the last deadline is at 59): bake that derivation, keep brute
  force as the cross-check.
- Show a clock floored to the minute and compute "N min later" from what is on
  screen: 20:22 and 20:34 with "13 min later" is an error a viewer can see.
- Round in the direction the sentence needs: 60.9 minutes is "more than 60", not
  "at least 61"; 31,577 nodes is "more than thirty-one thousand". `assert` the
  inequality the line states (`need > 60 > deadline`), not a rounded equality.
- After the last render, check that every clip was rendered with the narration now
  in the code: compare each trace's `note` lines with the `vo` strings of the scene
  (a clip rendered before a late wording fix looks fine and says the old line).

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
