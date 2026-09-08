"""Scene 4 — Hyperparameter tuning: choosing the network's size.

Training sets the *weights* automatically (Scene 3). But WE choose the network's
*size* — a hyperparameter. This scene draws the distinction (parameters vs
hyperparameters), frames tuning as a loop (choose a size → train → measure →
adapt → repeat), then runs the real sweep: validation accuracy vs hidden width on
a log x-axis. The curve rises steeply, plateaus, and the train curve races to
100% — the growing train–val gap is overfitting. We read off three sizes (Tiny 2,
Medium 8, Large 64) that sit exactly on the sweep, to carry into the finale.

Every number is real (``DATA.sweep_*``, ``DATA.params``, ``DATA.val_acc``).
"""
from nn_common import *

# ---- curve colours -------------------------------------------------------- #
VAL_C = GOLD          # validation-accuracy curve — the metric we select on
TR_C = GOOD           # train-accuracy curve — a reference

# the three sizes carried into the finale (indices into the sweep arrays):
#   width 2 -> Tiny, width 8 -> Medium, width 64 -> Large
SEL_IDX = [1, 3, 6]


# ========================================================================== #
# local helpers
# ========================================================================== #
def _fit(m, maxw):
    if m.width > maxw:
        m.scale(maxw / m.width)
    return m


def _info_panel(title, lines, accent, width=5.75):
    """A titled, colour-accented panel of short body lines."""
    head = chip(title, accent, fs=21, h=0.5, weight="BOLD")
    body = VGroup(*[_fit(txt(t, fs=20, color=INK), width - 0.6) for t in lines])
    body.arrange(DOWN, aligned_edge=LEFT, buff=0.24)
    inner = VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
    box = RoundedRectangle(width=width, height=inner.height + 0.66, corner_radius=0.16,
                           stroke_color=accent, stroke_width=2.4,
                           fill_color=accent, fill_opacity=0.05)
    inner.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.3)
    g = VGroup(box, inner)
    g.head = head
    g.body = body
    return g


def _curve(ax, xs, ys, color, sw=5):
    """A straight-segment polyline over data points (no overshoot)."""
    m = VMobject()
    m.set_points_as_corners([ax.c2p(x, y) for x, y in zip(xs, ys)])
    m.set_stroke(color=color, width=sw)
    return m


def _legend_row(color, label):
    ln = Line(ORIGIN, RIGHT * 0.55, stroke_color=color, stroke_width=5)
    return VGroup(ln, txt(label, fs=19, color=INK)).arrange(RIGHT, buff=0.18)


def _sel_dot(pt):
    """A selected point on the curve: dark halo (guarantees contrast) + ring."""
    halo = Dot(pt, radius=0.17).set_fill(BG, 1).set_stroke(width=0)
    ring = Circle(radius=0.155, stroke_color=INK, stroke_width=2.5,
                  fill_opacity=0).move_to(pt)
    core = Dot(pt, radius=0.075).set_fill(GOLD, 1).set_stroke(width=0)
    return VGroup(halo, ring, core)


def _size_card(name, width_n, params, val):
    l1 = txt(f"{name}  ·  width {width_n}", fs=21, color=INK, weight="BOLD")
    l2 = VGroup(
        txt(f"{params:,} params", fs=18, color=MUTED),
        txt("·", fs=18, color=MUTED),
        txt(f"{val * 100:.0f}% val", fs=18, color=GOLD, weight="BOLD"),
    ).arrange(RIGHT, buff=0.16)
    inner = VGroup(l1, l2).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    w = max(inner.width + 0.5, 2.7)
    box = RoundedRectangle(width=w, height=inner.height + 0.4, corner_radius=0.13,
                           stroke_color=MUTED, stroke_width=2.2,
                           fill_color=PANEL, fill_opacity=0.7)
    inner.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.22)
    g = VGroup(box, inner)
    g.box = box
    return g


def _loop_chip(n, text, color):
    badge = VGroup(
        Circle(radius=0.19, stroke_color=color, stroke_width=2.6,
               fill_color=color, fill_opacity=0.16),
        txt(str(n), fs=19, color=color, weight="BOLD"),
    )
    badge[1].move_to(badge[0])
    lab = txt(text, fs=19, color=INK)
    inner = VGroup(badge, lab).arrange(RIGHT, buff=0.16)
    box = RoundedRectangle(width=inner.width + 0.45, height=0.72, corner_radius=0.14,
                           stroke_color=color, stroke_width=2.2,
                           fill_color=color, fill_opacity=0.08)
    inner.move_to(box)
    g = VGroup(box, inner)
    g.box = box
    return g


# ========================================================================== #
def build_tune(scene):
    head = scene.section_header("TUNING", "Choosing the Size", GOLD)
    scene.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

    # ---------------------------------------------------------------- #
    # (A) parameters vs hyperparameters
    # ---------------------------------------------------------------- #
    n_params = int(DATA.params[1]) if DATA is not None else 1187   # medium net
    left = _info_panel(
        "PARAMETERS",
        ["Weights & biases", "set automatically by training",
         f"all {n_params:,} of them, via gradient descent"],
        GOOD)
    right = _info_panel(
        "HYPERPARAMETERS",
        ["Size · depth · learning rate", "chosen by us, before training",
         "the shape of the network itself"],
        GOLD)
    panels = VGroup(left, right).arrange(RIGHT, buff=0.6).move_to(UP * 0.75)

    scene.play(FadeIn(left, shift=RIGHT * 0.2), run_time=0.7)
    scene.play(FadeIn(right, shift=LEFT * 0.2), run_time=0.7)
    scene.say("Training tunes the weights for us. But it never picks the size.",
              hold=1.7)

    contrast = VGroup(
        txt("Training sets the weights.", fs=27, color=GOOD, weight="BOLD"),
        txt("We set the shape.", fs=27, color=GOLD, weight="BOLD"),
    ).arrange(RIGHT, buff=0.4).next_to(panels, DOWN, buff=0.55)
    scene.play(FadeIn(contrast[0], shift=UP * 0.1), run_time=0.6)
    scene.play(FadeIn(contrast[1], shift=UP * 0.1), run_time=0.6)
    scene.beat(1.0)

    focus = txt("One knob to explore: the number of hidden neurons (the width).",
                fs=24, color=INK).next_to(contrast, DOWN, buff=0.42)
    scene.play(Write(focus), run_time=1.0)
    scene.say("So we'll sweep one knob, the hidden width, and watch the score.",
              color=GOLD, hold=1.8)
    scene.beat(0.4)
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(panels, contrast, focus)), run_time=0.6)

    # ---------------------------------------------------------------- #
    # (B) the experiment loop
    # ---------------------------------------------------------------- #
    steps = [
        _loop_chip(1, "choose a size", CAR_C),
        _loop_chip(2, "train it", GOOD),
        _loop_chip(3, "measure val accuracy", GOLD),
        _loop_chip(4, "compare & adapt", WARN),
    ]
    row = VGroup(*steps).arrange(RIGHT, buff=0.62).move_to(UP * 0.45)
    _fit(row, 2 * config.frame_x_radius - 1.0)

    arrows = VGroup(*[arr(steps[i].get_right(), steps[i + 1].get_left(),
                          color=MUTED, sw=3.5, buff=0.1)
                      for i in range(3)])

    scene.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.12) for s in steps],
                           *[GrowArrow(a) for a in arrows],
                           lag_ratio=0.18, run_time=1.8))
    scene.say("Try a size, train it, check the score, adjust, then do it again.",
              hold=1.7)

    # the closing "repeat" arrow, bowing below the row
    loop = CurvedArrow(steps[3].get_bottom() + DOWN * 0.12,
                       steps[0].get_bottom() + DOWN * 0.12,
                       angle=-1.15, color=GOLD, stroke_width=4,
                       tip_length=0.24)
    rlab = txt("repeat", fs=21, color=GOLD, weight="BOLD")
    rlab.next_to(loop, DOWN, buff=0.12)
    scene.play(Create(loop), run_time=0.9)
    scene.play(FadeIn(rlab, shift=UP * 0.1), run_time=0.5)
    scene.beat(0.6)
    # step 3 is what the sweep records
    scene.play(Indicate(steps[2], color=GOLD, scale_factor=1.08), run_time=0.9)
    scene.say("The score we compare on is validation accuracy, on held-out data.",
              color=GOLD, hold=1.7)
    scene.beat(0.3)
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(row, arrows, loop, rlab)), run_time=0.6)

    # ---------------------------------------------------------------- #
    # (C) the sweep — the centrepiece
    # ---------------------------------------------------------------- #
    widths = [int(w) for w in DATA.sweep_w]
    xs = [float(np.log2(w)) for w in widths]           # log spacing: 0..7
    val = [float(v) for v in DATA.sweep_val]
    tr = [float(v) for v in DATA.sweep_tr]

    ax = Axes(x_range=[0, 7, 1], y_range=[0.3, 1.0, 0.1],
              x_length=7.6, y_length=4.2, tips=False,
              axis_config={"stroke_color": MUTED, "stroke_width": 2.2,
                           "include_ticks": False})
    ax.move_to([-1.5, 0.0, 0])

    # gridlines + ticks + labels (all hand-placed since include_ticks=False)
    grid = VGroup()
    ylabs = VGroup()
    for acc in (0.4, 0.6, 0.8, 1.0):
        gl = Line(ax.c2p(0, acc), ax.c2p(7, acc), stroke_color=FAINT, stroke_width=1.4)
        grid.add(gl)
        yl = txt(f"{acc * 100:.0f}%", fs=17, color=MUTED)
        yl.next_to(ax.c2p(0, acc), LEFT, buff=0.18)
        ylabs.add(yl)
    xlabs = VGroup()
    xticks = VGroup()
    for x, w in zip(xs, widths):
        tick = Line(ax.c2p(x, 0.3), ax.c2p(x, 0.3) + UP * 0.09,
                    stroke_color=MUTED, stroke_width=2)
        xticks.add(tick)
        xl = txt(str(w), fs=17, color=MUTED)
        xl.next_to(ax.c2p(x, 0.3), DOWN, buff=0.16)
        xlabs.add(xl)
    xtitle = txt("hidden neurons  (width)", fs=21, color=INK)
    xtitle.next_to(xlabs, DOWN, buff=0.2)
    xnote = txt("log scale: each tick doubles the width", fs=15, color=MUTED)
    xnote.next_to(xtitle, DOWN, buff=0.1)
    ytitle = txt("validation accuracy", fs=20, color=INK).rotate(PI / 2)
    ytitle.next_to(ylabs, LEFT, buff=0.22)

    # faint chance-level reference
    chance = DashedLine(ax.c2p(0, 0.33), ax.c2p(7, 0.33),
                        stroke_color=MUTED, stroke_width=2, dash_length=0.1)
    chance.set_stroke(opacity=0.5)
    chlab = txt("chance (33%)", fs=15, color=MUTED)
    chlab.next_to(ax.c2p(7, 0.33), UP, buff=0.06).align_to(ax.c2p(7, 0.33), RIGHT)

    axgrp = VGroup(ax, grid, xticks, xlabs, ylabs, xtitle, xnote, ytitle)
    scene.play(Create(ax), run_time=0.8)
    scene.play(LaggedStart(*[Create(g) for g in grid], lag_ratio=0.1),
               *[FadeIn(t) for t in ylabs], run_time=0.9)
    scene.play(LaggedStart(*[GrowFromCenter(t) for t in xticks], lag_ratio=0.05),
               *[FadeIn(t) for t in xlabs], run_time=0.9)
    scene.play(FadeIn(xtitle), FadeIn(xnote), FadeIn(ytitle), run_time=0.6)
    scene.play(Create(chance), FadeIn(chlab), run_time=0.6)
    scene.say("Same data, same training. We change only the width, and plot the score.",
              hold=1.6)

    # legend (upper-left inside the plot, where both curves are low)
    lg_val = _legend_row(VAL_C, "validation")
    lg_tr = _legend_row(TR_C, "train")
    legend = VGroup(lg_val, lg_tr).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    legend = plate(legend, pad_x=0.22, pad_y=0.16, op=0.6)
    legend.move_to([-3.95, 1.55, 0])

    # validation curve first (the hero)
    val_curve = _curve(ax, xs, val, VAL_C, sw=5)
    scene.play(Create(val_curve), run_time=2.1)
    scene.play(FadeIn(legend), run_time=0.4)
    scene.say("It climbs fast, then flattens out. A clear plateau.",
              color=VAL_C, hold=2.1)
    scene.beat(0.4)

    # train curve second (races to 100%)
    scene.clear_cap(0.3)
    tr_curve = _curve(ax, xs, tr, TR_C, sw=4.4)
    tr_curve.set_stroke(opacity=0.9)
    scene.play(Create(tr_curve), run_time=1.8)
    scene.say("Train accuracy, though, keeps climbing, all the way to 100%.",
              color=TR_C, hold=2.0)
    scene.beat(0.4)

    # ---------------------------------------------------------------- #
    # (D) interpretation — underfit / overfit
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    # underfit: point at the low-width end
    ufit = VGroup(
        txt("too small", fs=20, color=WARN, weight="BOLD"),
        txt("underfits: misses the patterns", fs=17, color=MUTED),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    ufit.move_to([-3.0, -1.05, 0])
    ua = arr(ufit.get_corner(UL) + UP * 0.03, ax.c2p(xs[0], val[0]),
             color=WARN, sw=3, buff=0.14)
    scene.play(FadeIn(ufit, shift=UP * 0.1), GrowArrow(ua), run_time=0.8)
    scene.say("At the small end the network underfits. Too simple to catch the patterns.",
              hold=2.1)

    # overfit: brace the train-val gap at the right end
    gap_line = Line(ax.c2p(7, val[-1]), ax.c2p(7, tr[-1]))
    brace = Brace(gap_line, direction=RIGHT, color=MUTED, buff=0.08)
    ofit = VGroup(
        txt("train 100%,", fs=19, color=TR_C, weight="BOLD"),
        txt("val plateaus", fs=19, color=VAL_C, weight="BOLD"),
        txt("= overfitting", fs=18, color=WARN),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    ofit.next_to(brace, RIGHT, buff=0.16)
    _fit(ofit, config.frame_x_radius - 0.35 - ofit.get_left()[0])
    scene.clear_cap(0.3)
    scene.play(GrowFromCenter(brace), FadeIn(ofit, shift=RIGHT * 0.1), run_time=0.9)
    scene.say("At the big end it memorises the training set, but validation barely improves.",
              hold=2.1)
    scene.beat(0.3)
    scene.say("Bigger helps, until it doesn't.", color=GOLD, fs=30, weight="BOLD",
              hold=2.2)
    scene.beat(0.4)

    # ---------------------------------------------------------------- #
    # (E) adapt & select — the three sizes for the finale
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(ufit, ua, brace, ofit)), run_time=0.5)

    names = [str(n) for n in DATA.arch_names]          # Tiny, Medium, Large
    cards = VGroup()
    dots = VGroup()
    tags = VGroup()
    for k, si in enumerate(SEL_IDX):
        pt = ax.c2p(xs[si], val[si])
        d = _sel_dot(pt)
        dots.add(d)
        tag = txt(names[k], fs=18, color=INK, weight="BOLD")
        tag.next_to(pt, DOWN, buff=0.28)
        tags.add(tag)
        card = _size_card(names[k], widths[si], int(DATA.params[k]), val[si])
        cards.add(card)
    cards.arrange(DOWN, buff=0.3).move_to([4.7, -0.05, 0])

    scene.say("So we read three sizes straight off the curve: small, medium, large.",
              hold=1.5)
    for k in range(3):
        scene.play(FadeIn(dots[k], scale=0.5),
                   FadeIn(tags[k], shift=UP * 0.08), run_time=0.5)
        scene.play(FadeIn(cards[k], shift=LEFT * 0.15), run_time=0.5)
        scene.beat(0.5)
    scene.clear_cap(0.3)
    scene.say("Tiny, Medium and Large, each sitting on the sweep at its real score.",
              color=GOLD, hold=2.2)
    scene.beat(0.4)

    # ---------------------------------------------------------------- #
    # (F) transition to the finale
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(axgrp, chance, chlab, val_curve, tr_curve,
                              legend, dots, tags, cards, head)), run_time=0.8)
    end = VGroup(
        txt("Three sizes chosen.", fs=40, color=INK, weight="BOLD"),
        txt("Time to see them classify, for real.", fs=32, color=GOLD, weight="BOLD"),
    ).arrange(DOWN, buff=0.4)
    scene.play(FadeIn(end[0], shift=UP * 0.15), run_time=0.8)
    scene.play(FadeIn(end[1], shift=UP * 0.15), run_time=0.8)
    scene.beat(1.6)
    scene.settle()
    scene.wipe()


class Tune(NNBase):
    def construct(self):
        build_tune(self)
