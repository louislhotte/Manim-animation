# PubTables-1M: the paper, animated

A short house-style explainer of one paper:

> Brandon Smock, Rohith Pesala, Robin Abraham.
> **"PubTables-1M: Towards comprehensive table extraction from unstructured
> documents."** CVPR 2022. [arXiv:2110.00061](https://arxiv.org/abs/2110.00061).
> Paper licensed **CC BY 4.0**; released as
> [microsoft/table-transformer](https://github.com/microsoft/table-transformer).

The paper's own figures are reused **verbatim** (as the license permits, with
on-screen attribution): they are extracted at native resolution from the arXiv
PDF by `fetch_assets.py` and baked into `assets/` as JPEGs, so rendering needs
no network access.

## What it teaches

1. A presented table's logical structure (what spans what, which cells are
   headers) is implicit; recovering it is **table extraction** (paper Fig. 1).
2. Its three subtasks: **table detection**, **table structure recognition**,
   **functional analysis** (Fig. 2).
3. Where a million labeled tables come from: aligning the PDF and XML versions
   of PubMed Central Open Access articles, character by character -
   **947,642 tables**, nearly 2x the largest prior dataset (Table 1).
4. **Oversegmentation**: markup stores one spanning header as several blank
   cells, giving one table many "valid" ground truths (Fig. 3a; among tables
   with a projected row header, 58.65% oversegmented in PubTabNet, 98.87% in
   FinTabNet: Table 2). The fix is **canonicalization** (Algorithm 1), which
   adjusted 34.7% of all tables and leaves zero oversegmented headers (Fig. 3b).
5. Modeling: all three tasks as plain object detection with **six dilated box
   classes** (Fig. 4) and an off-the-shelf **DETR**: TD 0.966 AP, TSR+FA
   0.912 AP (Table 3), and exact content match on complex tables jumping
   **0.536 → 0.694** from canonical labels alone (Table 4).

Takeaway: clean ground truth is a model upgrade.

## Scenes

| # | Scene (`render.sh` name) | Class          | Content                                  |
|---|--------------------------|----------------|------------------------------------------|
| 0 | `intro`                  | `Intro`        | House title card                         |
| 1 | `paper`                  | `Paper`        | Citation card, Fig. 1, implicit structure|
| 2 | `tasks`                  | `Tasks`        | Fig. 2 spotlight: TD / TSR / FA          |
| 3 | `scale`                  | `Scale`        | PDF+XML alignment, dataset-size bars     |
| 4 | `canonical`              | `Canonical`    | Fig. 3 oversegmentation → Algorithm 1 fix|
| 5 | `model`                  | `ModelResults` | Fig. 4 six classes, DETR, results bars   |
| 6 | `outro`                  | `Outro`        | Thanks + full citation                   |
|   | `full`                   | `PubTables1M`  | The whole film                           |

Measured runtime (full film, default pacing): **4:23**.

## Rendering

```bash
./render.sh paper --quick        # fast layout check of one scene (480p15)
./render.sh                      # whole film, 480p
./render.sh full -q h            # final 1080p60 (slow)
./render.sh --stitch -q h        # render each scene and concat to one file
```

Media renders to `/private/tmp/pt-media` (override with `PT_MEDIA_DIR`);
writing straight into the OneDrive-synced repo stalls on I/O. Reading-hold
pacing: `PT_QUICK=1` collapses holds, `PT_DELAY=<x>` overrides the multiplier
(default 2.2).

## Assets / provenance

`fetch_assets.py` (one-time, needs network + `pymupdf`) downloads the pinned
arXiv **v3** PDF and extracts:

- `fig1_example.jpg`, `fig2_tasks.jpg`, `fig3a_overseg.jpg`,
  `fig3b_canonical.jpg`, `fig4_dilated.jpg`: the paper's embedded raster
  figures, pulled verbatim at native resolution via their PDF xrefs;
- `page1.jpg`: page 1 rendered at 3x (the citation card);
- `alg1_canon.jpg`: the Algorithm 1 box, clipped from page 5 at 4x.

All figures © the paper's authors, CC BY 4.0, credited on screen.
