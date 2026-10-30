# OmniDocBench — can AI actually read a document?

A no-voiceover Manim explainer on [OmniDocBench](https://github.com/opendatalab/OmniDocBench)
(Ouyang, Qu, Zhou, Zhu, Zhang et al., Shanghai AI Laboratory, arXiv:[2412.07626](https://arxiv.org/abs/2412.07626)),
a benchmark for evaluating how well document-parsing systems (classic pipelines
and vision-language models) recover a PDF page's text, tables, formulas and
reading order.

Built in the house dark style, LaTeX-free (all `Text`/Pango), and a companion
to this repo's other document-parsing explainer, Docling (chunking + OCR) —
where Docling shows *how* a parser turns a PDF into structured chunks, this
film is about *how do we know if it did that well*.

## What it teaches

- **Why existing benchmarks fall short.** Most cover only one document domain
  (usually academic papers) and score everything with generic text-similarity
  metrics (Edit Distance, BLEU) that can't fairly judge a table or formula
  written in a different but equally valid syntax. OmniDocBench's Table 1
  (shown as a real screenshot of the paper) is the only benchmark that checks
  every box: 9 document domains, every annotation type, every evaluation level.
- **How the dataset was built.** 200,000+ PDFs collected from the web, visual
  features clustered with ResNet-50 + Faiss down to 6,000 diverse pages,
  manually balanced to a final **981 pages across 9 real document types**
  (academic papers, textbooks, exam papers, slides, books, magazines, notes,
  newspapers, financial reports).
- **How rich the annotations are.** Layout boxes across 19 region categories,
  per-box attributes (language, background, rotation for text; language,
  frame type, special issues for tables), reading order, and affiliation —
  over 100,000 annotations total, built via a 3-stage automatic-annotate /
  human-correct / PhD-review pipeline.
- **What OCR actually looks like.** A scanned page with no text layer, a
  scanning pass turning pixels into characters line by line, and a real
  single-character misread ("in" → "ln") to motivate why a naive string
  match can't fairly score a parser.
- **How scoring is made fair.** A model's raw Markdown output is Extracted
  (LaTeX/HTML tables, formulas, code, text, in a fixed order), then Matched
  against ground truth with an "Adjacency Search Match" that merges/splits
  paragraphs to find the best alignment, then scored with the *right* metric
  per element: Text → Edit Distance, Tables → TEDS + Edit Distance,
  Formulas → CDM + BLEU + Edit Distance, Reading Order → Edit Distance.
- **The results, verbatim.** Table 2 (the full comprehensive scoreboard) and
  Table 3 (broken down by document type) are shown as real screenshots of the
  paper's own pages, with highlight boxes drawn at the image's own pixel
  coordinates — no rebuilt/reconstructed table. The twist: MinerU (a pipeline
  tool) wins six of nine individual document types outright, but Qwen2-VL-72B
  (a general VLM) posts the best *overall* average, 0.179 vs. 0.206, because
  MinerU catastrophically fails on one category (handwritten Notes, 0.984)
  while Qwen2-VL-72B never does. The system with the most wins isn't the
  system with the best overall score.

## Scenes

| Scene       | Class         | Beat |
|-------------|---------------|------|
| Intro       | `Intro`       | Title card |
| Problem     | `Problem`     | Why existing benchmarks fall short; Table 1 (real screenshot) |
| Dataset     | `Dataset`     | 200k → 6k → 981 pages across 9 real document types |
| Annotation  | `Annotation`  | Layout boxes, attributes, reading order; the 3-stage annotation pipeline |
| Contenders  | `Contenders`  | Pipeline Tools vs. Expert VLMs vs. General VLMs (8 real systems) |
| Ocr         | `Ocr`         | What OCR actually does: pixels → scanning beam → recognized text → a real misread |
| Evaluation  | `Evaluation`  | Extract → Match (Adjacency Search) → per-type Metric → Overall |
| Results1    | `Results1`    | Table 2 (real screenshot), highlight boxes walk through every metric group |
| Results2    | `Results2`    | Table 3 (real screenshot), the "no single system wins everywhere" twist |
| Takeaway    | `Takeaway`    | Closing recap |
| Outro       | `Outro`       | Thank-you card |

Full film class: **`OmniDocBenchFilm`** (all scenes, intro card to outro card).

## Render

```bash
./render.sh results2 --quick -q l   # fast sanity check of one scene (480p15)
./render.sh                         # whole film, 480p
./render.sh full -q h               # final 1080p60 (the HD deliverable)
./render.sh --stitch -q m           # render each scene and ffmpeg-concat to one file
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN / Docling) if present, else bootstraps a local `.venv`. No LaTeX
required.

### Pacing knobs

- `ODB_QUICK=1` (or `--quick`) collapses every hold for fast iteration.
- `ODB_DELAY` (default `1.8`) — the reading-hold multiplier.

Measured runtime at default pacing: **6:53** (`ffprobe … format=duration`).

## Tables are real screenshots, not rebuilt mobjects

`assets/table{1,2,3}_shot.jpg` are crops of the actual PDF pages (via
`pymupdf`, rendered at 5x zoom for crispness, clip rectangles anchored on the
table's own header/caption text so nothing else on the page bleeds in). The
film displays them with `image_card()`/`credit()` and draws highlight boxes
with `uv_rect()`/`uv_point()` at *relative image coordinates* computed from
the same PDF text-box positions (cross-checked against a coordinate-gridded
render of each screenshot) — so a highlight always lands on the real cell,
never a re-typeset approximation. Table 1 (p.3), Tables 2-3 (p.6) of
arXiv:2412.07626v2.

## Reference

- OmniDocBench — Ouyang, Qu, Zhou, Zhu, Zhang et al., *"OmniDocBench:
  Benchmarking Diverse PDF Document Parsing with Comprehensive Annotations,"*
  Shanghai AI Laboratory, 2024 (arXiv:2412.07626). Dataset and code:
  https://github.com/opendatalab/OmniDocBench
- Companion film in this repo: `animations/Docling` (chunking + OCR).
