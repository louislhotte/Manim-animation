"""Decision-making for the agents.

A *brain* looks at a ``World`` and returns, for the agents it controls, a
steering acceleration ``(K, 2)`` and a boolean lunge intent ``(K,)``.  Physics
lives elsewhere (see ``physics.py``); a brain only decides *where to push*.

Phase 1 ships two hand-coded brains:

* ``FishBrain``  — classic boids (separation / alignment / cohesion) plus shark
  evasion, wall avoidance and a lunge reflex.  Emergent schooling comes for
  free from the local rules.
* ``SharkBrain`` — greedy pursuit of the nearest fish with a lunge when close.

The RL engine (Phase 2) will add a ``NeuroFishBrain`` implementing the same
``fish_act`` signature, so it drops straight into ``Simulation``.
"""

from __future__ import annotations

import numpy as np

from config import SimConfig
from physics import World, unit


class FishBrain:
    """Hand-coded boids + evasion. Stateless; reads everything from the world."""

    def fish_act(self, world: World):
        cfg: SimConfig = world.cfg
        pos, vel, alive = world.pos, world.vel, world.alive
        n = pos.shape[0]

        # ---- pairwise fish-fish geometry (O(N^2), cheap for a few hundred) --
        diff = pos[None, :, :] - pos[:, None, :]          # (N, N, 2): i -> j
        dist2 = np.einsum("ijk,ijk->ij", diff, diff)
        np.fill_diagonal(dist2, np.inf)
        alive_j = alive[None, :]

        # Separation: push away from neighbours that are too close, ~1/d^2.
        sep_mask = (dist2 < cfg.separation_radius ** 2) & alive_j
        inv = np.where(sep_mask, 1.0 / np.maximum(dist2, 1e-6), 0.0)
        sep = unit(-np.einsum("ij,ijk->ik", inv, diff))

        # Perception neighbourhood for alignment + cohesion.
        per_mask = ((dist2 < cfg.perception_radius ** 2) & alive_j).astype(float)
        cnt = per_mask.sum(1, keepdims=True)
        have = cnt[:, 0] > 0

        mean_pos = np.einsum("ij,jk->ik", per_mask, pos) / np.maximum(cnt, 1.0)
        coh = unit(mean_pos - pos)
        coh[~have] = 0.0

        mean_vel = np.einsum("ij,jk->ik", per_mask, vel) / np.maximum(cnt, 1.0)
        ali = unit(mean_vel)
        ali[~have] = 0.0

        # ---- evade the nearest shark, harder the closer it is --------------
        sdiff = world.spos[None, :, :] - pos[:, None, :]  # (N, M, 2): fish -> shark
        sd2 = np.einsum("ijk,ijk->ij", sdiff, sdiff)
        nearest = np.argmin(sd2, axis=1)
        rows = np.arange(n)
        nd = np.sqrt(sd2[rows, nearest])
        to_shark = sdiff[rows, nearest]
        prox = np.clip(1.0 - nd / cfg.shark_sense_radius, 0.0, 1.0)[:, None]
        evade = unit(-to_shark) * prox

        # ---- steer away from walls when near them --------------------------
        wall = self._wall_force(pos, cfg)

        # ---- a little wander so calm schools still drift ------------------
        wander = unit(world.rng.normal(size=(n, 2)))

        steer = (
            cfg.w_separation * sep
            + cfg.w_alignment * ali
            + cfg.w_cohesion * coh
            + cfg.w_evade * evade
            + cfg.w_wall * wall
            + cfg.w_wander * wander
        )

        # Lunge (escape burst) when a shark breaches the trigger distance.
        lunge = nd < cfg.fish_lunge_trigger
        target_speed = np.where(lunge, cfg.fish_burst, cfg.fish_cruise)[:, None]
        desired = unit(steer) * target_speed
        accel = (desired - vel) * 4.0
        return accel, lunge

    @staticmethod
    def _wall_force(pos: np.ndarray, cfg: SimConfig) -> np.ndarray:
        m, s = cfg.wall_margin, cfg.size
        left = np.clip((m - pos[:, 0]) / m, 0.0, 1.0)
        right = np.clip((pos[:, 0] - (s - m)) / m, 0.0, 1.0)
        bottom = np.clip((m - pos[:, 1]) / m, 0.0, 1.0)
        top = np.clip((pos[:, 1] - (s - m)) / m, 0.0, 1.0)
        return np.stack([left - right, bottom - top], axis=1)


class SharkBrain:
    """Greedy hunter: chase the nearest fish, lunge when it gets close."""

    def act(self, world: World):
        cfg: SimConfig = world.cfg
        m = cfg.n_sharks
        accel = np.zeros((m, 2))
        lunge = np.zeros(m, dtype=bool)
        alive_idx = np.where(world.alive)[0]

        for k in range(m):
            spos, svel = world.spos[k], world.svel[k]
            if alive_idx.size == 0:
                # Nothing left to hunt: coast and avoid walls.
                accel[k] = -svel + cfg.shark_wall_weight * self._wall_force(spos, cfg)
                continue

            d = np.linalg.norm(world.pos[alive_idx] - spos, axis=1)
            order = np.argsort(d)
            # Confusion: occasionally lock onto a nearby (not nearest) fish.
            if world.rng.random() < cfg.shark_target_jitter and order.size > 1:
                pick = order[world.rng.integers(1, min(5, order.size))]
            else:
                pick = order[0]

            target = world.pos[alive_idx[pick]]
            to_target = target - spos
            dist = float(np.linalg.norm(to_target))
            lunge[k] = dist < cfg.shark_lunge_trigger

            speed = cfg.shark_burst if lunge[k] else cfg.shark_cruise
            desired = unit(to_target) * speed
            steer = (desired - svel) * 4.0
            steer += cfg.shark_wall_weight * cfg.shark_max_force * self._wall_force(spos, cfg)
            accel[k] = steer

        return accel, lunge

    @staticmethod
    def _wall_force(spos: np.ndarray, cfg: SimConfig) -> np.ndarray:
        m, s = cfg.wall_margin, cfg.size
        fx = np.clip((m - spos[0]) / m, 0.0, 1.0) - np.clip((spos[0] - (s - m)) / m, 0.0, 1.0)
        fy = np.clip((m - spos[1]) / m, 0.0, 1.0) - np.clip((spos[1] - (s - m)) / m, 0.0, 1.0)
        return np.array([fx, fy])
