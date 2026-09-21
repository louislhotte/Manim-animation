# Docling — chunking documents & plugging in OCR

A ~4:51, no-voiceover Manim explainer on how [Docling](https://github.com/docling-project/docling)
(open-source, IBM Research) turns a messy document — a PDF, a scan, a DOCX — into
one clean, structured `DoclingDocument`, and then into **RAG-ready chunks**. It
also shows how **OCR is a pluggable step** for pages whose text is trapped in
pixels.

It's built in the house dark style, LaTeX-free (all `Text`/Pango; code in Menlo),
and is a companion to the other inference/RAG explainers in this repo
(Transformer, KV Cache, Mixtral, Embedding Retrieval, LLM-as-a-Judge).

## What it teaches

- **Why naïve extraction fails.** `extract_text()` scrapes characters off the
  canvas — reading order scrambles, tables flatten, and scanned regions vanish.
  You get a "bag of words," which is garbage-in for RAG.
- **The Docling pipeline.** A document rides a conveyor through five stages:
  **Parse → Layout → OCR → Tables → Assemble**, and comes out as one
  `DoclingDocument` exportable to Markdown / JSON / HTML.
- **Understanding the page.** Docling detects and *types* every block (title,
  text, figure, caption, table), drops page furniture (headers/footers/page
  numbers), and recovers the **reading order** — down the left column, then the
  right — not blind top-to-bottom. Tables get their own model (TableFormer):
  cells, rows and spans rebuilt.
- **Plugging in OCR.** For a scanned image with no text layer, OCR is a
  swappable step — **EasyOCR, Tesseract, RapidOCR, ocrmac** all snap into the
  same socket. A scanning pass turns pixels into characters; the interface and
  output stay identical whichever engine you pick.
- **Chunking for RAG.** RAG retrieves *chunks*, not documents.
  - **HierarchicalChunker** splits along the document structure — each chunk keeps
    its heading trail as metadata.
  - **HybridChunker** is tokenizer-aware: it *merges* chunks that are too small
    and *splits* the ones that blow past the embedding model's token budget (at
    sentence boundaries), so every chunk fits `max_tokens` with its heading
    context preserved.
  - Chunks then embed into a vector store, ready for retrieval.

## Scenes

| Scene      | Class      | Beat |
|------------|------------|------|
| Intro      | `Intro`    | Title card |
| Problem    | `Problem`  | Naïve extraction → a jumbled "bag of words" |
| Pipeline   | `Pipeline` | The conveyor: Parse → Layout → OCR → Tables → Assemble → DoclingDocument |
| Layout     | `Layout`   | Typed bounding boxes, furniture dropped, reading-order path, TableFormer |
| OCR        | `OCR`      | Pluggable OCR socket, scanning beam, pixels → characters (engine swap) |
| Chunk      | `Chunk`    | HierarchicalChunker → HybridChunker (merge/split) → embed → vector store |
| Recap      | `Recap`    | One-breath takeaway |
| Outro      | `Outro`    | Thank-you card |

Full film class: **`DoclingFilm`** (all scenes, intro card to outro card).

## Render

```bash
./render.sh ocr --quick -q l    # fast sanity check of one scene (480p15)
./render.sh                     # whole film, 480p
./render.sh full -q h           # final 1080p60 (the HD deliverable)
./render.sh --stitch -q m       # render each scene and ffmpeg-concat to one file
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering / Fourier
/ CNN) if present, else bootstraps a local `.venv`. No LaTeX required.

### Pacing knobs

Reading holds and animation speed are separate:

- `DL_QUICK=1` (or `--quick`) collapses every hold for fast iteration.
- `DL_READ` (default `2.8`) — the absolute hold after a block of text lands.
- `DL_DELAY` (default `1.0`) — the between-step motion rhythm.

Measured runtime at default pacing: **4:51** (`ffprobe … format=duration`).

## Reference

- Docling — Auer et al., *"Docling Technical Report,"* IBM Research, 2024
  (arXiv:2408.09869); TableFormer — Nassar et al., 2022 (arXiv:2203.01017).
- OCR engines: EasyOCR, Tesseract, RapidOCR, ocrmac (all pluggable via
  `PdfPipelineOptions(do_ocr=True, ocr_options=…)`).
