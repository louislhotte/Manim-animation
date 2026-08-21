"""Title / rules / outro cards that bookend the simulation.

House style (shared with the repo's Manim explainers): dark background, warm-white
bold title, a GOLD rule that runs past both ends of the title, a muted subtitle
and a "Created by Ptolémé" byline; the film ends on "Thank you for watching!".
Rendered here in matplotlib (1920×1080) so they stitch seamlessly onto the
matplotlib simulation with ffmpeg (see film.py).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from viz import BG, PANEL

# House palette (matches animations/*/*.py: INK / MUTED / GOLD).
INK = "#F5F3EF"
MUTED = "#8A93A6"
GOLD = "#FFD166"
TEAL = "#39c5bb"     # fish
RED = "#ff6b6b"      # shark
BYLINE = "#39c5bb"


def _canvas():
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)
    return fig, ax


def _title_rule(fig, ax, title, y, fs, color=INK, rule=GOLD, pad=0.035, gap=0.05):
    """Centred bold title with a gold underline that extends past both ends."""
    t = ax.text(0.5, y, title, ha="center", va="center",
                color=color, fontsize=fs, weight="bold")
    fig.canvas.draw()  # need a renderer to measure the text
    bb = t.get_window_extent()
    inv = ax.transData.inverted()
    (x0, y0), (x1, _) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
    ax.plot([x0 - pad, x1 + pad], [y0 - gap, y0 - gap],
            color=rule, lw=3.0, solid_capstyle="round")


def _save(fig, path, dpi):
    fig.savefig(path, dpi=dpi, facecolor=BG)
    plt.close(fig)
    print(f"saved {path}")


def intro_card(cfg, path, dpi=120):
    fig, ax = _canvas()
    _title_rule(fig, ax, "Predator & Prey", 0.60, 66)
    ax.text(0.5, 0.45, "A school outruns a shark — with nothing but local rules",
            ha="center", va="center", color=MUTED, fontsize=25)
    ax.text(0.5, 0.30, "Created by Ptolémé", ha="center", va="center",
            color=BYLINE, fontsize=21)
    _save(fig, path, dpi)


def _stat_panel(ax, cx, name, name_color, lines):
    top = 0.75
    line_gap = 0.062
    w = 0.40
    bottom = top - 0.085 - line_gap * (len(lines) - 1) - 0.045
    box = FancyBboxPatch(
        (cx - w / 2, bottom), w, top + 0.045 - bottom,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        fc=PANEL, ec=name_color, lw=1.8, alpha=0.95, mutation_aspect=1.0,
    )
    ax.add_patch(box)
    ax.text(cx, top, name, ha="center", va="top", color=name_color,
            fontsize=29, weight="bold")
    for i, ln in enumerate(lines):
        ax.text(cx, top - 0.085 - i * line_gap, ln, ha="center", va="top",
                color=INK, fontsize=20)


def rules_card(cfg, path, dpi=120):
    fig, ax = _canvas()
    _title_rule(fig, ax, "The Rules", 0.925, 46, gap=0.04)

    _stat_panel(ax, 0.28, f"FISH  ×{cfg.n_fish}", TEAL, [
        f"cruise {cfg.fish_cruise:.0f} · burst {cfg.fish_burst:.0f}",
        "Lunges (bursts) to flee",
        "Turns gold while lunging",
    ])
    _stat_panel(ax, 0.72, f"SHARK  ×{cfg.n_sharks}", RED, [
        f"cruise {cfg.shark_cruise:.0f} · burst {cfg.shark_burst:.0f}",
        "Lunges (bursts) to strike",
        f"Eats any fish within r = {cfg.eat_radius:.1f}",
    ])

    ax.text(0.5, 0.435,
            "Every fish steers in the direction opposite the nearest shark",
            ha="center", va="center", color=INK, fontsize=27, weight="bold")
    ax.text(0.5, 0.375, "— unless a wall is in the way.",
            ha="center", va="center", color=INK, fontsize=27, weight="bold")
    ax.text(0.5, 0.285,
            "Repeat that one rule across the whole school and a lifelike, "
            "mesmerizing dance emerges.",
            ha="center", va="center", color=MUTED, fontsize=21)

    ax.text(0.5, 0.145, "This is math, not magic.",
            ha="center", va="center", color=GOLD, fontsize=40, weight="bold")
    _save(fig, path, dpi)


def outro_card(cfg, path, dpi=120):
    fig, ax = _canvas()
    _title_rule(fig, ax, "Thank you for watching!", 0.58, 50)
    ax.text(0.5, 0.42, "Created by Ptolémé", ha="center", va="center",
            color=BYLINE, fontsize=22)
    ax.text(0.5, 0.30, f"{cfg.n_fish} fish · {cfg.n_sharks} shark · one simple rule",
            ha="center", va="center", color=MUTED, fontsize=20)
    _save(fig, path, dpi)
