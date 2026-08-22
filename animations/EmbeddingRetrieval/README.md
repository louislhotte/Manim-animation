# Embeddings & Retrieval

A ~5-minute, house-style explainer on **vector search** — how an embedding model
turns a chunk of text into a point in a *latent space*, and how retrievers
(**OpenSearch**, **Azure AI Search**, **pgvector**) find the right chunks by
*similarity*. This is the machinery behind RAG. Boxes, arrows and small graphs;
no equations rendered as LaTeX, so it renders without a TeX install.

All on-screen text is rendered through a small crisp-`Text` wrapper (render at a
large base size, scale down) so letter/word spacing stays clean at every size —
Manim distorts spacing when `Text` is created at small font sizes.

## The film (`EmbeddingRetrieval`)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
six roughly one-minute scenes:

1. **Search by meaning** — keyword search (`heart attack`) misses a document that
   says `myocardial infarction`; semantic search finds it. Then the offline
   roadmap: `Documents → Chunks → Embedding model → Vectors → Vector index`.
2. **From chunk to vector** — a document splits into overlapping **chunks**; one
   chunk flows through the **embedding model** and comes out a **vector**
   (`d` numbers). The vector *is* a point in latent space; embed the whole corpus
   and topic **clusters** emerge — *similar meaning → nearby points*.
3. **The geometry of meaning** — closeness = similarity: **cosine** is the angle
   between two vectors (small angle → high `cos θ`); cosine vs dot-product vs
   Euclidean.
4. **Retrieval by similarity** — the query is embedded the *same way*, dropped
   into the space, and the **k-nearest neighbours** are returned as ranked,
   scored chunks.
5. **The retrievers** — OpenSearch (k-NN / HNSW), Azure AI Search (vector search /
   HNSW), pgvector (Postgres, IVFFlat / HNSW). Same core idea; **exact kNN** (scan
   everything, accurate/slow) vs **approximate NN** (hop through an HNSW graph,
   fast) — the `recall ↔ latency` knob.
6. **Why it matters (RAG)** — `Query → Retriever → top-k chunks → context → LLM →
   grounded answer`: retrieval fills the context window with the right facts.
   Punchline: *embeddings turn your data into the model's long-term memory.*

## Rendering

```bash
./render.sh embed --quick     # fast sanity check of one scene
./render.sh                   # the whole film, 480p
./render.sh full -q h         # final 1080p
./render.sh --stitch -q m     # render each scene and join into one 720p film
```

`render.sh` reuses the Harness / CNN / Fourier series' `.venv` if it finds one
(so Manim isn't reinstalled), otherwise it bootstraps a local `.venv` from
`requirements.txt`.

Individually renderable scenes: `intro` · `problem` · `embed` · `space` ·
`retrieve` · `systems` · `why` · `outro` (or `full`, the default).

`EMB_QUICK=1` (or `--quick`) shortens the on-screen holds while iterating.
Tunables (palette, timings, the tiny demo corpus) live at the top of
`embedding_retrieval.py`.
