# Transformer Inference

A ~3-minute, house-style explainer on how a trained Transformer language model
turns a prompt into text — **one token at a time**. Boxes, arrows, vectors and
small matrices; no equations that need LaTeX, so it renders anywhere.

Grounded in the original architecture from **"Attention Is All You Need"**
(Vaswani et al., NeurIPS 2017, [arXiv:1706.03762](https://arxiv.org/abs/1706.03762)).
We follow the **decoder stack with masked self-attention** — the basis of
GPT-style autoregressive inference.

## The film (`TransformerInference`)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
six scenes walk the full forward path:

1. **Inference = next-token prediction** — given the tokens so far, the model
   emits a probability distribution over the whole vocabulary; you pick one,
   append it, and repeat. Weights are frozen — no learning happens at inference.
2. **From text to vectors** — a tokenizer splits text into sub-word tokens with
   integer IDs (BPE); each ID looks up a 512-dim **embedding**; a fixed
   **sinusoidal positional encoding** is added because attention is order-agnostic.
3. **The decoder stack** — bottom-to-top: `Embeddings ⊕ PosEnc → N × (Masked
   Multi-Head Self-Attention → Add & Norm → Feed-Forward → Add & Norm) → Final
   Linear → Softmax → next-token probabilities`, with residual/skip connections
   and the paper's hyperparameters (N = 6, d = 512, h = 8, d_ff = 2048).
4. **Self-attention** — each token is projected into **Query, Key, Value**;
   `Attention(Q,K,V) = softmax(QKᵀ / √dₖ) · V`; the **causal mask** blocks every
   token from attending to the future (what makes generation autoregressive);
   **multi-head** runs h = 8 attentions in parallel and concatenates them.
5. **Choosing the next token** — the last position's vector → `Linear` →
   **logits** over ~50 k tokens → `softmax` → probabilities; then a decoding
   strategy (greedy · temperature · top-k / top-p) picks one ("are").
6. **Autoregressive generation** — append the token, feed the sequence back in,
   repeat; the **KV cache** stores past keys & values so each new step adds just
   one column and stays fast; stop at `<eos>` or a length limit. The running
   example is J.R.R. Tolkien's *"Not all those who wander are lost."*

## Rendering

```bash
./render.sh attention --quick   # fast sanity check of one scene
./render.sh                     # the whole film, 480p
./render.sh full -q h           # final 1080p
./render.sh --stitch -q m       # render each scene and join into one 720p film
```

`render.sh` reuses the HarnessEngineering / Fourier / CNN series' `.venv` if it
finds one (so Manim isn't reinstalled), otherwise it bootstraps a local `.venv`
from `requirements.txt`.

Individually renderable scenes: `intro` · `task` · `embed` · `arch` ·
`attention` · `sample` · `generate` · `outro` (or `full`, the default).

`TF_QUICK=1` (or `--quick`) shortens the on-screen holds while iterating.
`TF_DELAY=<seconds>` overrides the pacing knob; the default (`1.8`) lands the
whole film at ~3:00. Tunables (palette, timings) live at the top of
`transformer_inference.py`.
