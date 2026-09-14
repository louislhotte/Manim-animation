# Stealing a Model's Reasoning

A ~4-minute, no-voiceover Manim explainer of the 2026 result
**"Stealing Reasoning Traces from Proprietary LLM APIs"** — how researchers pulled
the hidden chain-of-thought out of locked, top-tier LLM APIs, and used it to
distill a small model.

It builds the whole attack from the ground up, in the shared dark house style
(hand-drawn glyphs, `Text`/Pango only, no LaTeX):

1. **The chain of thought** — a reasoning model thinks in steps, then the provider
   seals that reasoning away and returns only the answer. The reasoning is the
   densest possible teaching signal, so it is exactly what a rival wants to copy.
2. **The lockbox** — the hidden reasoning comes back as an encrypted AEAD envelope
   (header, nonce, auth tag, ciphertext). The server stores nothing; you hand the
   box back every turn. Only the provider's key should ever open it.
3. **One key fits every lock** — the flaw: one global key. A block minted in one
   session, by another user, or by a *different model* is accepted everywhere.
4. **The bank shot** — you cannot make the strong model reveal its reasoning (it
   refuses). So you hand its locked box to a weaker sibling that shares the same
   key and ask it to transcribe verbatim. Out pours the plaintext chain of thought.
   The strong model is never touched.
5. **The harvest** — run at scale: 6,708 public trajectories → 315,320
   reconstructed reasoning blocks, plus 704 real secrets (API keys, passwords,
   tokens, emails), some never shown in the visible chat.
6. **Distilling the theft** — train a small open model on the stolen reasoning.
   On MATH500 it jumps from 68.4% (answer-only distillation) to 76.0%, for a few
   hundred dollars of API calls.
7. **The fix** — bind each box to its user, session and model; store reasoning
   server-side behind an opaque id; refusal-train the transcription trick. Every
   major provider has since patched it. The deeper lesson: reasoning you must
   decrypt to use can only ever be *semi*-hidden.

The numbers, the mechanism (cross-model interchangeable AEAD blocks, a weak
sibling as the decoder) and the distillation result are all from the paper.

## Render

```bash
./render.sh bankshot --quick        # fast layout check of one scene (480p15)
./render.sh full                    # whole film, 480p
./render.sh full -q h               # final 1080p60 (slow; run in background)
./render.sh --stitch -q m           # render each scene and concat to one file
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) if present, else bootstraps a local `.venv`. No LaTeX required.

## Scenes

`Intro`, `CoT`, `Lockbox`, `OneKey`, `BankShot`, `Harvest`, `Distill`, `Fix`,
`Outro`, and the full film `StealingReasoning`.

### Pacing knobs

- `RT_QUICK=1` collapses every hold for a fast sanity render.
- `RT_DELAY` scales the small inter-step pauses.
- `RT_READ` is the absolute hold (seconds) after a caption lands.

## Runtime

Measured full-film duration (StealingReasoning, real cadence): **4m12s** (253 s).
