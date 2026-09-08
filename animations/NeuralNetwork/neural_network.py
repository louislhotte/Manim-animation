"""How a Neural Network Learns — the full ~10-minute film.

An end-to-end, house-style (no-voiceover) explainer on supervised image
classification: teaching a network to tell a **car** from a **plane** from a
**ship**, from raw pixels, start to finish. Five ~2-minute scenes:

    1. The Task        -- the supervised paradigm + labelled data (intro card)
    2. The Network     -- flatten to 144 inputs, build the (untrained) net, a
                          forward pass that guesses wrong
    3. Training        -- forward → loss → backpropagation → weight update, then
                          scaled up (real loss/accuracy curves)
    4. Tuning          -- hyper-parameters: sweep the number of neurons, measure
                          validation accuracy, pick the best size
    5. The Verdict     -- three sizes head-to-head, a dezoom to all 2,400 test
                          images, and the real global accuracy (outro card)

Every number on screen is real — the dataset, the trained models, the curves and
the accuracies are computed by ``generate_assets.py`` into
``assets/nn_learn.npz``. Everything is drawn with Manim ``Text`` (Pango), never
``Tex`` — no LaTeX toolchain.

Scenes render individually from their own files (``scene1_task.py`` …
``scene5_verdict.py``: classes ``Task``, ``Arch``, ``Train``, ``Tune``,
``Verdict``) or as this one continuous film (``NeuralNetworkLearns``).

Env knobs:
    NN_QUICK=1   collapse every reading hold for a fast sanity render
    NN_DELAY=..  reading-rhythm multiplier;  NN_READ=..  caption hold (seconds)
"""
from __future__ import annotations

from nn_common import NNBase
from scene1_task import build_task
from scene2_arch import build_arch
from scene3_train import build_train
from scene4_tune import build_tune
from scene5_verdict import build_verdict


class NeuralNetworkLearns(NNBase):
    """The whole film, intro card to outro card."""

    def construct(self):
        build_task(self)      # opens with the house intro card
        build_arch(self)
        build_train(self)
        build_tune(self)
        build_verdict(self)   # closes with the house outro card


if __name__ == "__main__":
    NeuralNetworkLearns().render()
