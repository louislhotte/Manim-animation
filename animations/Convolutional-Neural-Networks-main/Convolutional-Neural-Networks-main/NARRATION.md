# CNN Series — Narration Script (Parts 4–6)

This is the spoken-word script for the rendered video
(`media/CNN_parts_4-6_<res>.mp4`). Each scene has a *Visual* cue (what is on
screen) and numbered **narration** beats that line up with the animation's
`self.play(...)` steps. Feed the narration lines to a TTS/voice agent scene by
scene; timings in parentheses are the approximate target length so the voice
tracks the picture.

> Note: Parts 4–6 continue an existing series. Parts 1–3 already covered *how an
> image is represented*, *what a filter is*, and *the convolution operation*.
> The script below assumes the viewer has seen those.

---

## Flow at a glance (the arc)

1. **Part 4 – Activations:** after each convolution we apply a non-linearity.
2. **Part 5.1 – The network + the cost:** stack conv+activation blocks, flatten,
   add a classifier — and notice the classifier is already expensive.
3. **Part 5.2 – Pooling (the tool):** how pooling shrinks a feature map.
4. **Part 6.1 – Pooling pays off:** drop pooling into the network → far fewer
   parameters.
5. **Part 6.2 – Why conv, not dense:** conv vs fully-connected, and how the gap
   explodes on real-size images.
6. **Part 6.3 – Outro.**

**Is it a full flow?** The backbone is sound (extract features → they get big →
pool them down → this is why CNNs beat dense nets). But it is *not* self-contained
and has a few seams — see "Flow notes" at the bottom. The narration below is
written to paper over those seams; the animation-level fixes are optional.

---

## Scene 4.1 — Activation functions  (~33 s)

*Visual:* a ReLU graph is drawn, shrinks to the left; a digit → conv layer (blue)
→ activation layer (green) → output pipeline appears; the graph then cycles
through Sigmoid, Tanh, Leaky ReLU and ELU, and the output image updates each time.

**Narration**
1. *(ReLU graph appears)* "A convolution is a linear operation — so on its own, a
   stack of them can only ever learn linear patterns. To fix that, after every
   convolution we apply an *activation function*."
2. *(pipeline appears)* "The most common one is the ReLU: it simply keeps positive
   values and clamps everything negative to zero. Here it is applied to the feature
   map coming out of our convolutional layer."
3. *(cycles Sigmoid → Tanh)* "But it is not the only choice. The sigmoid squashes
   everything between zero and one; the hyperbolic tangent, between minus one and one."
4. *(cycles Leaky ReLU → ELU)* "Others, like the Leaky ReLU and the ELU, keep a
   small signal alive for negative inputs. Each one shapes the feature map a little
   differently — but they all do the same job: they make the network non-linear."

---

## Scene 5.1 — The network, and what it costs  (~30 s)

*Visual:* input image, then a stack of conv+activation blocks is built left to
right with braces (3, then 9, then 6, then 1 filters); an output image appears,
collapses to a single value, then is replaced by a *flatten + fully-connected*
layer to ten outputs. A box highlights "7840 parameters!".

**Narration**
1. *(stack builds)* "Now we can assemble a real network: convolution, activation,
   convolution, activation — each block extracting richer features than the last."
2. *(output → dense layer)* "Eventually we want an answer — which digit is this?
   So we flatten the final feature map into one long vector and connect it to an
   output layer, one neuron per class."
3. *(box: 7840 parameters)* "But look at the cost. This single fully-connected
   layer already needs almost eight thousand parameters — because the feature map
   feeding it is still twenty-eight by twenty-eight. If only we could make that map
   smaller…"

---

## Scene 5.2 — Pooling  (~33 s)

*Visual:* the digit under a 28×28 grid; a 2×2 kernel (Width 2, Stride 2) sweeps
the image row by row, building a 14×14 output on the right, one pixel per window.
Ends on "Width = 14, Height = 14".

**Narration**
1. *(kernel appears, Width 2 / Stride 2)* "…and that is exactly what *pooling*
   does. We slide a small window over the image — here two by two — with a stride
   of two, so the windows never overlap."
2. *(sweep across rows)* "For each window we keep a single summary value — the
   average, in this case. The window steps across the row, drops to the next, and
   sweeps again."
3. *(14×14 result, braces)* "The result is a smaller image that keeps the overall
   shape but throws away fine detail: twenty-eight by twenty-eight becomes fourteen
   by fourteen — a quarter of the data — and each new pixel now 'sees' a larger
   region of the original."

---

## Scene 6.1 — Pooling in the network  (~40 s)

*Visual:* the full CNN is rebuilt; pooling layers (red) are inserted between the
conv blocks; the output shrinks to 3×7×7; the flatten+dense head is shown again,
now only "1470 parameters!", ending on "5 times fewer parameters!".

**Narration**
1. *(network rebuilds, red pooling layers added)* "So let's put pooling to work.
   Between our convolutional blocks we add pooling layers — the red ones — that
   halve the width and height each time."
2. *(output now 3×7×7)* "By the end of the network the feature map has shrunk from
   twenty-eight by twenty-eight down to seven by seven."
3. *(box: 1470 parameters → 5× fewer)* "And now the same classifier needs only
   about fifteen hundred parameters — roughly five times fewer. Pooling made the
   network smaller, faster, and less prone to overfitting, almost for free."

---

## Scene 6.2 — Why convolution, not a dense net  (~18 s)

*Visual:* a convolutional network beside a fully-connected one on the same input;
"810" vs "15 880" parameters; the inputs then swap to a 256×256 photo (the
portrait) and its edge-map output; the dense count jumps to "1 million +".

**Narration**
1. *(conv vs dense, 810 vs 15 880)* "Which raises the question — why not just use a
   fully-connected network for everything? On this tiny digit, the dense network
   already needs twenty times more parameters than the convolutional one."
2. *(swap to 256×256 photo, 1 million+)* "And that gap explodes with image size.
   On a real, two-hundred-and-fifty-six-pixel image, the dense network blows past a
   million parameters — while the convolutional network barely grows, because it
   reuses the same small filters everywhere. *That* is why we use convolutions for
   images."

---

## Scene 6.3 — Outro  (~14 s)

*Visual:* "Thank you for watching!" with an underline, then "Created by Ptolémé".

**Narration (optional — can be left to music)**
1. "That's it for convolutional neural networks — from a single filter all the way
   to a full architecture. Thanks for watching, and see you in the next one."

---

## Flow notes (honest assessment + optional fixes)

These do not block voicing — the script above already bridges them — but they are
the reasons the raw animation "doesn't fully read" on its own:

1. **Not self-contained.** 4–6 lean on Parts 1–3 (image = pixels, filters,
   convolution). Fine if watched in order; add one bridging sentence if it must
   stand alone.
2. **Part 4 is a slight side-step.** Activations are important but sit outside the
   "features get big → pool them → CNNs scale" spine of 5–6. Beat 1 of 4.1 ties it
   back in.
3. **Pooling is set up, taught, and paid off across three scenes** (5.1 poses the
   cost → 5.2 teaches the tool → 6.1 delivers the saving). That's a good structure
   *with narration*, but silent it feels disjointed — which is likely why the flow
   was hard to follow.
4. **"Like and subscribe!" mid-series (end of 5.2).** It interrupts the arc right
   before the payoff. Recommend moving that call-to-action to the outro (6.3).
5. **"Receptive field" is named but never explained** in 5.2. Either develop it in
   one line (done in 5.2 beat 3: "each new pixel sees a larger region") or drop the
   on-screen label.
6. **Terse on-screen braces** ("9 (3x3x3)", "(3x7x7)") — the narration translates
   these into plain language so viewers aren't left decoding them.
