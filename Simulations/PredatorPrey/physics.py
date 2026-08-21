"""World state and physics for the predator / prey simulation.

``World`` owns *only* the state (positions, velocities, who is alive) and the
rules of motion / eating.  It knows nothing about *how* the fish or the shark
decide to move — those decisions arrive as acceleration vectors from a "brain"
(hand-coded in Phase 1, learned later).  Keeping physics and policy separate is
what lets the RL engine reuse this file untouched.

All state is stored as NumPy arrays and every update is vectorised, so a few
hundred fish over thousands of steps stays cheap.
"""

from __future__ import annotations

import numpy as np

from config import SimConfig

EPS = 1e-9


def unit(v: np.ndarray, eps: float = EPS) -> np.ndarray:
    """Return ``v`` scaled to unit length along the last axis (0 stays 0)."""
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, eps)


def clamp_speed(v: np.ndarray, vmin: float, vmax) -> np.ndarray:
    """Clamp the speed (row-wise magnitude) of an ``(N, 2)`` velocity array.

    ``vmax`` may be a scalar or a per-row array so lunging agents can be given a
    higher ceiling than cruising ones.
    """
    out = v.copy()
    sp = np.linalg.norm(out, axis=1)
    vmax = np.broadcast_to(np.asarray(vmax, float), (out.shape[0],))
    fast = sp > vmax
    out[fast] *= (vmax[fast] / sp[fast])[:, None]
    slow = (sp < vmin) & (sp > EPS)
    out[slow] *= (vmin / sp[slow])[:, None]
    return out


class World:
    """Mutable state of the tank plus the ``apply`` step that advances physics."""

    def __init__(self, cfg: SimConfig, rng: np.random.Generator):
        self.cfg = cfg
        self.rng = rng
        self.reset()

    # ------------------------------------------------------------------ reset
    def reset(self) -> None:
        cfg, rng, s = self.cfg, self.rng, self.cfg.size

        # Fish spawn as a loose crowd in the central area, heading randomly.
        self.pos = rng.uniform(0.2 * s, 0.8 * s, size=(cfg.n_fish, 2))
        ang = rng.uniform(0.0, 2 * np.pi, cfg.n_fish)
        self.vel = np.stack([np.cos(ang), np.sin(ang)], 1) * cfg.fish_cruise
        self.alive = np.ones(cfg.n_fish, dtype=bool)
        self.fish_bursting = np.zeros(cfg.n_fish, dtype=bool)
        self._lunge_timer = np.zeros(cfg.n_fish)   # >0 while bursting
        self._lunge_cd = np.zeros(cfg.n_fish)      # >0 while on cooldown
        self.death_step = np.full(cfg.n_fish, -1, dtype=int)

        # Sharks spawn on the edge so they have to swim in to hunt.
        edge = rng.uniform(0.0, s, size=(cfg.n_sharks, 2))
        edge[:, rng.integers(0, 2)] = rng.choice([0.05 * s, 0.95 * s], cfg.n_sharks)
        self.spos = edge
        sang = rng.uniform(0.0, 2 * np.pi, cfg.n_sharks)
        self.svel = np.stack([np.cos(sang), np.sin(sang)], 1) * cfg.shark_cruise
        self.shark_bursting = np.zeros(cfg.n_sharks, dtype=bool)
        self._s_lunge_timer = np.zeros(cfg.n_sharks)
        self._s_lunge_cd = np.zeros(cfg.n_sharks)

        self.t = 0.0
        self.step_idx = 0
        self.eat_events: list[tuple[float, float, int]] = []  # (x, y, step)

    # ------------------------------------------------------------- properties
    @property
    def n_alive(self) -> int:
        return int(self.alive.sum())

    # --------------------------------------------------------------- one step
    def apply(self, fish_accel, fish_lunge, shark_accel, shark_lunge) -> None:
        """Advance the world one ``dt`` given the agents' chosen accelerations."""
        cfg, dt = self.cfg, self.cfg.dt

        self._integrate(
            self.pos, self.vel, self.alive, fish_accel, fish_lunge,
            self._lunge_timer, self._lunge_cd,
            cfg.fish_max_force, cfg.fish_cruise, cfg.fish_burst, cfg.fish_min_speed,
            cfg.fish_lunge_time, cfg.fish_lunge_cooldown,
        )
        self.fish_bursting = self._lunge_timer > 0

        shark_alive = np.ones(cfg.n_sharks, dtype=bool)
        self._integrate(
            self.spos, self.svel, shark_alive, shark_accel, shark_lunge,
            self._s_lunge_timer, self._s_lunge_cd,
            cfg.shark_max_force, cfg.shark_cruise, cfg.shark_burst, cfg.shark_min_speed,
            cfg.shark_lunge_time, cfg.shark_lunge_cooldown,
        )
        self.shark_bursting = self._s_lunge_timer > 0

        self._eat()

        self.t += dt
        self.step_idx += 1

    # ---------------------------------------------------------- physics core
    def _integrate(self, pos, vel, alive, accel, lunge,
                   lunge_timer, lunge_cd,
                   max_force, cruise, burst, min_speed,
                   lunge_time, lunge_cd_time) -> None:
        cfg, dt, s = self.cfg, self.cfg.dt, self.cfg.size

        # --- lunge state machine: start new bursts that are off cooldown ---
        want = np.asarray(lunge, dtype=bool) & (lunge_cd <= 0) & (lunge_timer <= 0) & alive
        lunge_timer[want] = lunge_time
        bursting = lunge_timer > 0

        # --- integrate velocity with a capped steering force ---------------
        acc = clamp_speed(np.asarray(accel, float), 0.0, max_force)
        vel[alive] += acc[alive] * dt

        vmax = np.where(bursting, burst, cruise)
        vel[:] = clamp_speed(vel, min_speed, vmax)

        # --- integrate position (dead agents freeze) -----------------------
        pos[alive] += vel[alive] * dt

        # --- soft-ish walls: clamp inside the tank and bleed off outward speed
        for d in (0, 1):
            low = pos[:, d] < 0.0
            pos[low, d] = 0.0
            vel[low, d] *= -0.5
            high = pos[:, d] > s
            pos[high, d] = s
            vel[high, d] *= -0.5

        # --- advance timers -------------------------------------------------
        lunge_timer[:] = np.maximum(0.0, lunge_timer - dt)
        just_ended = bursting & (lunge_timer <= 0)
        lunge_cd[just_ended] = lunge_cd_time
        lunge_cd[:] = np.maximum(0.0, lunge_cd - dt)

    def _eat(self) -> None:
        cfg = self.cfg
        for m in range(cfg.n_sharks):
            if not self.alive.any():
                break
            d = np.linalg.norm(self.pos - self.spos[m], axis=1)
            hit = self.alive & (d <= cfg.eat_radius)
            for i in np.where(hit)[0]:
                self.eat_events.append((float(self.pos[i, 0]),
                                        float(self.pos[i, 1]),
                                        self.step_idx))
            self.alive[hit] = False
            self.death_step[hit] = self.step_idx
