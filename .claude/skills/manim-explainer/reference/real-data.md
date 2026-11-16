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

## A laboratory on loopback: real network data with no network
`animations/Protocols` was built under "nothing leaves this machine". Two programs
on `127.0.0.1` still give real bytes, real handshakes and real errors (`lab.py`):
- **A relay between client and server** is the eavesdropper of the story and the
  recorder of the film: it logs every byte with a timestamp, cuts a TLS stream into
  records (5-byte header: type, version, length), and can rewrite what passes (a
  changed JSON value goes unnoticed on HTTP; one flipped bit of a TLS record gives
  the library's real error).
- **TLS without a browser**: `ssl` on both ends, certificates from the `openssl`
  command line (a root, an issuing authority, a leaf, and three that must be
  refused: self-signed, wrong name, expired). Private keys go *outside the
  repository* (`~/.cache/manimx/<film>-pki`); only what crossed the wire is baked.
- **The kernel answers without a packet capture** (which needs root): on macOS
  `getsockopt(IPPROTO_TCP, 0x106)` returns `tcp_connection_info` (first congestion
  window, timers, counters); a closed port refuses in under a millisecond; and
  `127.0.0.2` is a black hole: a connection attempt there shows the SYN retry timer
  and the 75 s the kernel takes to give up. `getaddrinfo(name, flags=AI_NUMERICHOST)`
  raises the exact error of a failed DNS lookup without sending a query.
- **What cannot be recorded is modelled, and says so**: TCP sequence numbers and loss
  come from a small simulation that follows the RFCs (`tcpsim.py`), fed with the real
  bytes; delays are the physical minimum (great circle, speed of light in fibre).
- A `manim.cfg` with `notify_outdated_version = False` in the film folder stops
  Manim's own version check, the last thing that touched the network at render time.
- **Say whose machine it is.** Error numbers, kernel timers and trust stores belong
  to the machine that baked the film: `[Errno 61]` / `[Errno 60]` and 75 s of SYN
  retries are macOS; the viewer's Linux server says 111 / 110 and gives up after
  about two minutes; "195 trusted authorities" was the bundle of one OpenSSL build,
  not the operating system's store. Say "here" in the narration, put the other
  system's values in the scene's note line and in a README table, and name the
  source of a count precisely or say a round figure that holds everywhere.
- **A model told as an event needs its label on screen**, not only in the README:
  "at best" under a stopwatch that shows a physical lower bound, "a model,
  exaggerated to be visible" under a loss rate chosen for the picture.
- **Read a chart at the timecode of the sentence said over it.** The congestion
  window was plotted as the RFC computes it; during fast recovery that value is
  inflated by one segment per duplicate ACK, so the curve climbed while the narrator
  said "and slows down". Correct and misleading: plot the quantity the sentence is
  about (the window the sender falls back to), and say in the README what the raw
  value does.
- **Say which product and which version.** "The balancer answers 502" is nginx and
  the cloud balancers; HAProxy and Envoy answer 503. "One more round trip" is TLS
  1.3; 1.2 costs two. One qualifier in the sentence ("with TLS 1.3", "or 503 with
  some products") keeps it true for the viewer whose stack differs.
- **A number about your own artifact is still a number: count it.** A note said "a
  40-line proxy" for a file with 53 lines of code. Count with a script, or say
  "small".
- **After moving a concept, re-read every sentence that counts.** Once DNS was taken
  out of the stack, "one request, four protocols" was wrong (five are named; there
  are four *layers*), and "each step speaks its own protocol" too (two steps share
  HTTP).

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
