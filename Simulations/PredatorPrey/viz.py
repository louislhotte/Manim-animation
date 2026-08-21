"""Matplotlib visualisation of the tank plus a live survivors panel.

Two views share the figure:

* ``ArenaView``  — the tank: fish as heading arrows (gold while lunging), the
  shark as a red arrow ringed by its kill radius, and expanding flashes where
  fish were eaten.
* ``StatsView``  — survivors over time, i.e. the "# of surviving fish" curve
  the RL engine will grow across generations.

Nothing here imports ``pyplot`` at module load beyond the standard alias, so the
caller can pick the backend (Agg for saving, an interactive one for a window)
before importing this module.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.patches import Circle, Rectangle

from physics import World

# --- palette ------------------------------------------------------------------
BG = "#0b1020"
PANEL = "#121a33"
GRID = "#243056"
TEXT = "#dfe6ff"
MUTED = "#7f8bbf"
FISH_CMAP = LinearSegmentedColormap.from_list("fish", ["#39c5bb", "#ffd23f"])
SHARK_CMAP = LinearSegmentedColormap.from_list("shark", ["#c0303a", "#ff7a45"])
EAT = "#ff5a5f"


class ArenaView:
    """Draws the tank and updates every frame from the world state."""

    def __init__(self, ax, world: World):
        self.ax = ax
        cfg = world.cfg
        s = cfg.size
        self.fish_len = 0.022 * s
        self.shark_len = 0.045 * s
        self.flash_life = int(round(0.6 / cfg.dt))
        self._flash_ptr = 0
        self._flashes: list[tuple[float, float, int]] = []

        ax.set_xlim(0, s)
        ax.set_ylim(0, s)
        ax.set_aspect("equal")
        ax.set_facecolor(BG)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.add_patch(Rectangle((0, 0), s, s, fill=False, ec=GRID, lw=1.5))

        n = world.pos.shape[0]
        z = np.zeros(n)
        self.fish_q = ax.quiver(
            z, z, z, z, z, cmap=FISH_CMAP, clim=(0, 1),
            angles="xy", scale_units="xy", scale=1.0,
            width=0.004, headwidth=3.5, headlength=4.5, pivot="mid", zorder=3,
        )

        m = world.spos.shape[0]
        zm = np.zeros(m)
        self.shark_q = ax.quiver(
            zm, zm, zm, zm, zm, cmap=SHARK_CMAP, clim=(0, 1),
            angles="xy", scale_units="xy", scale=1.0,
            width=0.011, headwidth=3.0, headlength=3.5, pivot="mid", zorder=5,
        )
        self.kill_rings = [
            Circle((0, 0), cfg.eat_radius, fill=False, ec=EAT, lw=1.4, alpha=0.55, zorder=4)
            for _ in range(m)
        ]
        self.sense_rings = [
            Circle((0, 0), cfg.shark_lunge_trigger, fill=False, ec="#ff7a45",
                   lw=0.8, ls=(0, (3, 3)), alpha=0.25, zorder=4)
            for _ in range(m)
        ]
        for c in self.kill_rings + self.sense_rings:
            ax.add_patch(c)

        self.flash = ax.scatter([], [], s=[], facecolors="none", zorder=6)

        self.hud = ax.text(
            0.02, 0.975, "", transform=ax.transAxes, va="top", ha="left",
            color=TEXT, fontsize=15, family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", fc=PANEL, ec=GRID, alpha=0.85),
        )

    def update(self, world: World):
        cfg = world.cfg

        # --- fish arrows (dead ones parked off-screen) ---------------------
        pos = world.pos.copy()
        dir_ = _dir(world.vel) * self.fish_len
        pos[~world.alive] = -1e4
        self.fish_q.set_offsets(pos)
        self.fish_q.set_UVC(dir_[:, 0], dir_[:, 1], world.fish_bursting.astype(float))

        # --- shark arrow + rings -------------------------------------------
        sdir = _dir(world.svel) * self.shark_len
        self.shark_q.set_offsets(world.spos)
        self.shark_q.set_UVC(sdir[:, 0], sdir[:, 1], world.shark_bursting.astype(float))
        for k, (kr, sr) in enumerate(zip(self.kill_rings, self.sense_rings)):
            kr.center = tuple(world.spos[k])
            sr.center = tuple(world.spos[k])

        # --- eat flashes (expand + fade) -----------------------------------
        while self._flash_ptr < len(world.eat_events):
            self._flashes.append(world.eat_events[self._flash_ptr])
            self._flash_ptr += 1
        now = world.step_idx
        self._flashes = [f for f in self._flashes if now - f[2] < self.flash_life]
        if self._flashes:
            age = np.array([(now - f[2]) / self.flash_life for f in self._flashes])
            xy = np.array([[f[0], f[1]] for f in self._flashes])
            sizes = 40.0 + age * 520.0
            colors = np.tile(to_rgba(EAT), (len(self._flashes), 1))
            colors[:, 3] = (1.0 - age) * 0.65
            self.flash.set_offsets(xy)
            self.flash.set_sizes(sizes)
            self.flash.set_facecolor("none")
            self.flash.set_edgecolor(colors)
        else:
            self.flash.set_offsets(np.empty((0, 2)))
            self.flash.set_sizes([])

        eaten = cfg.n_fish - world.n_alive
        self.hud.set_text(
            f"t {world.t:5.1f}s\n"
            f"alive {world.n_alive:3d}/{cfg.n_fish}\n"
            f"eaten {eaten:3d}"
        )


class StatsView:
    """Survivors-over-time line — the seed of the Phase-2 learning curve."""

    def __init__(self, ax, world: World):
        cfg = world.cfg
        self.ax = ax
        self.xmax = cfg.max_seconds
        ax.set_facecolor(PANEL)
        ax.set_xlim(0, cfg.max_seconds)
        ax.set_ylim(0, cfg.n_fish * 1.04)
        ax.set_title("surviving fish", color=TEXT, fontsize=17, pad=12, weight="bold")
        ax.set_xlabel("time (s)", color=MUTED, fontsize=12)
        ax.tick_params(colors=MUTED, labelsize=11)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        ax.grid(True, color=GRID, lw=0.5, alpha=0.5)

        # Reference line for the "half the population" target.
        ax.axhline(cfg.n_fish / 2, color=MUTED, ls=(0, (5, 4)), lw=1.1, alpha=0.7)
        # Kept on the LEFT so it never collides with the survivors tip label,
        # which travels along the right as time advances.
        ax.text(cfg.max_seconds * 0.015, cfg.n_fish / 2 + 1.5, "½ population",
                color=MUTED, fontsize=11, va="bottom", ha="left")

        (self.line,) = ax.plot([], [], color="#39c5bb", lw=2.6)
        self.tip = ax.scatter([], [], s=64, color="#ffd23f", zorder=5)
        self.tip_txt = ax.text(0, 0, "", color=TEXT, fontsize=13, weight="bold",
                               va="center", ha="left")
        self.fill = None

    def update(self, times, alive):
        self.line.set_data(times, alive)
        if self.fill is not None:
            self.fill.remove()
        self.fill = self.ax.fill_between(times, alive, color="#39c5bb", alpha=0.16)
        tx, ty = times[-1], alive[-1]
        self.tip.set_offsets([[tx, ty]])
        near_edge = tx > 0.85 * self.xmax
        self.tip_txt.set_position((tx - 0.015 * self.xmax if near_edge else tx + 0.015 * self.xmax,
                                   ty + 4))
        self.tip_txt.set_ha("right" if near_edge else "left")
        self.tip_txt.set_text(f"{int(ty)}")


def make_figure(world: World, figsize=(16, 9)):
    cfg = world.cfg
    fig = plt.figure(figsize=figsize, facecolor=BG)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.32, 1.0], wspace=0.12,
                          left=0.025, right=0.975, top=0.875, bottom=0.12)
    ax_arena = fig.add_subplot(gs[0, 0])
    ax_stats = fig.add_subplot(gs[0, 1])
    fig.suptitle("Predator & Prey  —  a school learns to survive",
                 color=TEXT, fontsize=22, y=0.965, weight="bold")

    # Persistent rules/stats key along the bottom — the rules, always on screen.
    fig.text(0.025, 0.037,
             f"Fish  cruise {cfg.fish_cruise:.0f} · burst {cfg.fish_burst:.0f}"
             " · flee the nearest shark",
             color="#39c5bb", ha="left", va="bottom", fontsize=13, family="monospace")
    fig.text(0.5, 0.037, "gold = lunging (burst)", color="#ffd23f",
             ha="center", va="bottom", fontsize=12.5, family="monospace")
    fig.text(0.975, 0.037,
             f"Shark  cruise {cfg.shark_cruise:.0f} · burst {cfg.shark_burst:.0f}"
             f" · eats within r = {cfg.eat_radius:.1f}",
             color="#ff6b6b", ha="right", va="bottom", fontsize=13, family="monospace")
    return fig, ArenaView(ax_arena, world), StatsView(ax_stats, world)


def animate(sim, seconds=None, save=None, show=False, fps=None, dpi=120):
    """Build the figure and run the episode as an animation."""
    fig, arena, stats = make_figure(sim.world)
    seconds = seconds if seconds is not None else sim.cfg.max_seconds
    total = int(round(seconds / sim.cfg.dt))
    fps = fps or int(round(1.0 / sim.cfg.dt))

    def frame(_):
        if not sim.done():
            sim.step()
        arena.update(sim.world)
        stats.update(sim.time_history, sim.alive_history)
        return ()

    anim = FuncAnimation(fig, frame, frames=total, interval=1000 * sim.cfg.dt, blit=False)
    if save:
        # High-quality H.264: crf 18 is visually near-lossless; yuv420p plays everywhere.
        writer = FFMpegWriter(
            fps=fps, codec="libx264",
            extra_args=["-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium"],
            metadata={"artist": "PredatorPrey"},
        )
        anim.save(save, writer=writer, dpi=dpi)
        print(f"saved {save}")
    if show:
        plt.show()
    plt.close(fig)
    return anim


def snapshot(sim, steps, path, dpi=120):
    """Advance ``steps`` steps and save a single PNG (for previews / checks)."""
    fig, arena, stats = make_figure(sim.world)
    for _ in range(steps):
        if sim.done():
            break
        sim.step()
    arena.update(sim.world)
    stats.update(sim.time_history, sim.alive_history)
    fig.savefig(path, dpi=dpi, facecolor=BG)
    plt.close(fig)
    print(f"saved {path}")


def _dir(v, eps=1e-9):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, eps)
