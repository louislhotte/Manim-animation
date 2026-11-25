"""Glue that ties the world, the fish brain and the shark brain together.

``Simulation`` is the object the visualiser and (later) the RL trainer both
drive.  Swap ``fish_brain`` for a learned policy and everything else — physics,
rendering, bookkeeping — stays the same.
"""

from __future__ import annotations

import numpy as np

from brains import FishBrain, SharkBrain
from config import SimConfig
from physics import World


class Simulation:
    def __init__(self, cfg: SimConfig | None = None, fish_brain=None, shark_brain=None):
        self.cfg = cfg or SimConfig()
        self.rng = np.random.default_rng(self.cfg.seed)
        self.world = World(self.cfg, self.rng)
        self.fish_brain = fish_brain or FishBrain()
        self.shark_brain = shark_brain or SharkBrain()

        # Time series of survivors, for the "collective intelligence" panel.
        self.time_history = [0.0]
        self.alive_history = [self.world.n_alive]

    # ------------------------------------------------------------------ step
    def step(self) -> None:
        w = self.world
        fish_accel, fish_lunge = self.fish_brain.fish_act(w)
        shark_accel, shark_lunge = self.shark_brain.act(w)
        w.apply(fish_accel, fish_lunge, shark_accel, shark_lunge)
        self.time_history.append(w.t)
        self.alive_history.append(w.n_alive)

    def done(self) -> bool:
        return self.world.n_alive == 0 or self.world.t >= self.cfg.max_seconds

    # --------------------------------------------------------------- headless
    def run(self, verbose: bool = False):
        """Run a whole episode with no rendering; return a small summary dict."""
        while not self.done():
            self.step()
        summary = {
            "survivors": self.world.n_alive,
            "eaten": self.cfg.n_fish - self.world.n_alive,
            "duration_s": self.world.t,
            "survival_rate": self.world.n_alive / self.cfg.n_fish,
        }
        if verbose:
            print(
                f"t={summary['duration_s']:.1f}s  "
                f"survivors={summary['survivors']}/{self.cfg.n_fish}  "
                f"eaten={summary['eaten']}  "
                f"survival_rate={summary['survival_rate']:.0%}"
            )
        return summary
