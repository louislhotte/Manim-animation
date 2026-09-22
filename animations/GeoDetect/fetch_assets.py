"""Fetch real, open satellite imagery + a real vector base map for GeoDetect.

One-time bake step (needs network). Pulls real Sentinel-2 / Landsat 5 crops
from Microsoft's Planetary Computer data API (a public titiler deployment,
free, no auth/API key) and a real Natural Earth country-boundary map, then
compresses/saves everything into assets/ so the render itself never needs
network access.

Run once (or whenever the AOIs change):

    <manim-venv>/bin/python fetch_assets.py

Sources (all public, open data -- see README.md for full citations):
  - Sentinel-2 L2A (ESA/Copernicus Open Access), collection "sentinel-2-l2a"
  - Landsat 5 Collection 2 Level 2 (USGS/NASA), collection "landsat-c2-l2"
  - Natural Earth 1:110m Admin 0 Countries (public domain)

Both raster collections are served (band math + colormap rendered
server-side) via https://planetarycomputer.microsoft.com/api/data/v1 --
this is a real computation on real satellite reflectance bands, not a
locally-faked heatmap.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

PC_BBOX = "https://planetarycomputer.microsoft.com/api/data/v1/item/bbox"
UA = {"User-Agent": "geodetect-fetch/1.0 (educational manim explainer)"}


def _get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def crop_url(bbox, w, h, collection, item, params):
    q = {"collection": collection, "item": item, **params}
    return f"{PC_BBOX}/{bbox}/{w}x{h}.png?{urllib.parse.urlencode(q, doseq=True)}"


def fetch_jpeg(url, name, quality=88):
    """Download a PNG crop and re-save as a compressed JPEG asset."""
    out = os.path.join(ASSETS, name)
    print(f">> {name}")
    raw = _get(url)
    tmp_png = out + ".tmp.png"
    with open(tmp_png, "wb") as f:
        f.write(raw)
    im = Image.open(tmp_png).convert("RGB")
    im.save(out, "JPEG", quality=quality)
    os.remove(tmp_png)


# ---- Rondônia, Brazil: real deforestation AOI (checkerboard/fishbone) ----- #
# NASA Earth Observatory and INPE have long documented this exact style of
# clearing along BR-364 in Rondônia. AOI picked to avoid the Landsat scene's
# diagonal swath edge.
RO_BBOX = "-62.9,-10.0,-62.45,-9.6"
S2_ITEM = "S2B_MSIL2A_20231116T142709_R053_T20LNQ_20231116T201659"   # 2023-11-16, ~3% cloud
L5_ITEM = "LT05_L2SP_231067_19900618_02_T1"                          # 1990-06-18, 0% cloud

fetch_jpeg(crop_url(RO_BBOX, 1200, 1066, "sentinel-2-l2a", S2_ITEM,
                     {"assets": "visual", "dst_crs": "epsg:4326"}),
           "rondonia_2023_tci.jpg")

fetch_jpeg(crop_url(RO_BBOX, 1200, 1066, "sentinel-2-l2a", S2_ITEM,
                     {"assets": ["B08", "B04"], "asset_as_band": "true",
                      "expression": "(B08-B04)/(B08+B04)", "rescale": "-0.2,0.95",
                      "colormap_name": "rdylgn", "dst_crs": "epsg:4326"}),
           "rondonia_2023_ndvi.jpg")

fetch_jpeg(crop_url(RO_BBOX, 1200, 1066, "landsat-c2-l2", L5_ITEM,
                     {"assets": ["red", "green", "blue"], "rescale": "7000,17000",
                      "color_formula": "Gamma RGB 1.6 Saturation 1.4 Sigmoidal RGB 3 0.4",
                      "dst_crs": "epsg:4326"}),
           "rondonia_1990_tci.jpg")

# Landsat C2 L2 assets are raw scaled DN; NDVI needs the true surface
# reflectance (DN * 0.0000275 - 0.2) or the offset distorts the ratio.
L5_NDVI_EXPR = ("(((nir08*0.0000275)-0.2)-((red*0.0000275)-0.2))/"
                "(((nir08*0.0000275)-0.2)+((red*0.0000275)-0.2))")
fetch_jpeg(crop_url(RO_BBOX, 1200, 1066, "landsat-c2-l2", L5_ITEM,
                     {"assets": ["nir08", "red"], "asset_as_band": "true",
                      "expression": L5_NDVI_EXPR, "rescale": "-0.2,0.95",
                      "colormap_name": "rdylgn", "dst_crs": "epsg:4326"}),
           "rondonia_1990_ndvi.jpg")

# ---- Kansas, USA: real center-pivot irrigation AOI ------------------------ #
KS_ITEM = "S2A_MSIL2A_20230830T171901_R012_T14SLG_20230831T022350"   # 2023-08-30, ~0% cloud
KS_WIDE_BBOX = "-100.85,37.45,-100.45,37.8"
KS_CLOSE_BBOX = "-100.78,37.55,-100.62,37.68"

fetch_jpeg(crop_url(KS_WIDE_BBOX, 1200, 939, "sentinel-2-l2a", KS_ITEM,
                     {"assets": "visual", "dst_crs": "epsg:4326"}),
           "kansas_wide_tci.jpg")

fetch_jpeg(crop_url(KS_WIDE_BBOX, 1200, 939, "sentinel-2-l2a", KS_ITEM,
                     {"assets": ["B08", "B04"], "asset_as_band": "true",
                      "expression": "(B08-B04)/(B08+B04)", "rescale": "-0.2,0.9",
                      "colormap_name": "rdylgn", "dst_crs": "epsg:4326"}),
           "kansas_wide_ndvi.jpg")

fetch_jpeg(crop_url(KS_CLOSE_BBOX, 1200, 975, "sentinel-2-l2a", KS_ITEM,
                     {"assets": "visual", "dst_crs": "epsg:4326"}),
           "kansas_close_tci.jpg")

fetch_jpeg(crop_url(KS_CLOSE_BBOX, 1200, 975, "sentinel-2-l2a", KS_ITEM,
                     {"assets": ["B08", "B04"], "asset_as_band": "true",
                      "expression": "(B08-B04)/(B08+B04)", "rescale": "-0.2,0.9",
                      "colormap_name": "rdylgn", "dst_crs": "epsg:4326"}),
           "kansas_close_ndvi.jpg")

# ---- Natural Earth 1:110m country boundaries (public domain) -------------- #
# Trimmed to just the ring coordinates we need (drop the ~140 metadata
# columns) and saved compactly so the render step has no network dependency.
print(">> world map (Natural Earth 110m countries)")
raw = _get("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
           "master/geojson/ne_110m_admin_0_countries.geojson", timeout=30)
gj = json.loads(raw)
countries = []
for feat in gj["features"]:
    geom = feat["geometry"]
    name = feat["properties"].get("NAME", "")
    if geom["type"] == "Polygon":
        rings = [geom["coordinates"][0]]
    elif geom["type"] == "MultiPolygon":
        rings = [poly[0] for poly in geom["coordinates"]]
    else:
        continue
    countries.append({"name": name, "rings": rings})
with open(os.path.join(ASSETS, "world_map.json"), "w") as f:
    json.dump(countries, f)
print(f"   {len(countries)} country outlines saved")

print("done.")
