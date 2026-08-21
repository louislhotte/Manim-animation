"""Tunable parameters for the predator / prey simulation.

Everything the simulator does is driven by one ``SimConfig`` instance so that the
(coming) RL engine can sweep parameters without touching the physics code.
Units are arbitrary "tank units"; think of the arena as a square pool of side
``size`` and time advancing in steps of ``dt`` seconds.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimConfig:
    # ---- Arena -----------------------------------------------------------
    size: float = 120.0          # side length of the (square) tank
    dt: float = 1.0 / 30.0       # seconds per simulation step
    seed: int | None = 5         # RNG seed (None -> random); 5 = calibrated 2-min demo

    # ---- Population ------------------------------------------------------
    n_fish: int = 160
    n_sharks: int = 1

    # ---- Fish kinematics (units per second) ------------------------------
    fish_cruise: float = 15.0    # comfortable swimming speed
    fish_burst: float = 36.0     # top speed while lunging (escape burst)
    fish_min_speed: float = 4.0  # fish never fully stop
    fish_max_force: float = 95.0 # cap on steering acceleration (units/s^2)

    # ---- Fish perception -------------------------------------------------
    perception_radius: float = 11.0   # neighbours used for align / cohesion
    separation_radius: float = 4.5    # neighbours that feel "too close"
    shark_sense_radius: float = 28.0  # how far a fish can see a shark

    # ---- Fish behaviour weights (hand-coded brain, Phase 1) --------------
    w_separation: float = 1.7
    w_alignment: float = 1.0
    w_cohesion: float = 0.85
    w_evade: float = 3.7
    w_wander: float = 0.35
    w_wall: float = 2.4
    wall_margin: float = 11.0    # start turning away this far from a wall

    # ---- Fish lunge (escape burst) --------------------------------------
    fish_lunge_trigger: float = 16.0  # burst when a shark is this close
    fish_lunge_time: float = 0.45     # seconds a burst lasts
    fish_lunge_cooldown: float = 0.9  # seconds before the fish can burst again

    # ---- Shark kinematics ------------------------------------------------
    shark_cruise: float = 18.0
    shark_burst: float = 44.0         # a fast, hard lunge
    shark_min_speed: float = 3.0
    shark_max_force: float = 100.0    # very manoeuvrable, stays on target

    # ---- Shark behaviour -------------------------------------------------
    shark_sight: float = 70.0         # will hunt fish within this range
    shark_lunge_trigger: float = 20.0 # lunge when target is this close
    shark_lunge_time: float = 0.55
    shark_lunge_cooldown: float = 1.15
    eat_radius: float = 2.8           # fish within this of a shark is eaten
    shark_target_jitter: float = 0.18 # chance to pick a non-nearest target
    shark_wall_weight: float = 1.5

    # ---- Episode ---------------------------------------------------------
    max_seconds: float = 120.0

    @property
    def steps_per_episode(self) -> int:
        return int(round(self.max_seconds / self.dt))
