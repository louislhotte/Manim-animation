"""Scene 3 — Training: how the network learns from its mistakes.

Continues straight from Scene 2 (the untrained net called a car "ship"). We make
the error concrete and then fix it:

    forward pass  ->  a one-number loss  ->  backpropagation (a gradient for every
    weight)  ->  one downhill step that flips the SAME image from "ship" to "car"

then we scale up: a live training dashboard where the loss curve falls and
accuracy climbs over 90 epochs — the emotional core of the film. Every number is
real (``DATA.demo_*`` for the single-step demo, ``DATA.med_*`` for the curves,
baked by ``generate_assets.py``).

House rules honoured here:
  * the net is built ONCE at a fixed left position and never moved (moving a
    piece-by-piece-revealed net triggers manim "mobject in two animations");
    panels / bars / loss sit to its right, and the montage fades the net for a
    centred dashboard.
  * no ``always_redraw`` is Created/FadeIn'd — the two counters (epoch, loss) are
    plain ``Text`` shown first, then given a ValueTracker updater, then cleared;
    the curves are polylines animated with ``Create``.
  * numbers are set in the shadowed ``Text`` (Helvetica), never ``DecimalNumber``
    (that renders in LaTeX Computer Modern and clashes with the body font).
"""
from nn_common import *

IN = int(DATA.img) if DATA is not None else 28      # image side (28)
NIN = IN * IN                                        # network inputs (784)
NPARAMS = int(DATA.params[1]) if DATA is not None else 6307   # the medium net
NET_POS = LEFT * 1.85 + DOWN * 0.2

# right-hand panel geometry (net stays left, everything explanatory goes right)
PANEL_X = 3.75
BAR_UNIT = 2.0
BAR_H = 0.30
BAR_GAP = 0.52
BARS_Y = 1.25
LOSS_Y = -0.55
VERDICT_Y = -1.82


# --------------------------------------------------------------------------- #
# local helpers
# --------------------------------------------------------------------------- #
def _settled_edge_styles(net, seed=1):
    """Per-edge target strokes for a *trained* net — mirrors, exactly, the
    ``Network.style_edges(settled=True)`` logic so we can animate toward it."""
    g = np.random.default_rng(seed)
    styles = []
    for _ in net.edges:
        w = g.normal(0, 1)
        styles.append((WPOS if w >= 0 else WNEG,
                       0.6 + 2.6 * min(abs(w), 2.2) / 2.2, 0.85))
    return styles


def _polyline(ax, xs, ys, color, sw=4.5):
    pts = [ax.c2p(float(x), float(y)) for x, y in zip(xs, ys)]
    return VMobject().set_points_as_corners(pts).set_stroke(color=color, width=sw)


def _mini_axes(y_top, y_step, center):
    ax = Axes(x_range=[0, 90, 30], y_range=[0, y_top, y_step],
              x_length=4.7, y_length=2.5, tips=False,
              axis_config={"stroke_color": MUTED, "stroke_width": 1.8,
                           "include_ticks": True, "include_numbers": False})
    ax.move_to(center)
    return ax


def _fade_rest(scene, keep, rt=0.7):
    """Fade every top-level mobject except those in ``keep`` (e.g. header + caption)."""
    ms = [m for m in scene.mobjects if m not in keep and m is not None]
    if ms:
        scene.play(*[FadeOut(m) for m in ms], run_time=rt)


# --------------------------------------------------------------------------- #
def build_train(scene):
    head = scene.section_header("TRAINING", "Learning from Mistakes", WARN)
    scene.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

    # ---------------------------------------------------------------- #
    # the network — built once, fixed here for beats A–D
    # ---------------------------------------------------------------- #
    net = build_network([NIN, 8, 3], shown=[6, 8, 3], width=5.6, height=3.6).move_to(NET_POS)
    net.style_edges(seed=3, settled=False)          # untrained: faint, uniform
    scene.play(LaggedStart(FadeIn(net.layers[0], shift=RIGHT * 0.15), FadeIn(net.ell[0]),
                           FadeIn(net.layers[1]), FadeIn(net.layers[2]),
                           lag_ratio=0.22, run_time=1.3))
    scene.play(Create(net.edges), run_time=1.1)

    # ================================================================ #
    # BEAT A — forward pass -> a confident, WRONG guess (recap of S2)
    # ================================================================ #
    img = DATA.demo_img
    thumb = pixel_grid(img, cell=0.055).next_to(net.layers[0], LEFT, buff=0.4)
    tlab = txt("a car", fs=18, color=CAR_C).next_to(thumb, DOWN, buff=0.18)
    scene.play(FadeIn(thumb), FadeIn(tlab), run_time=0.5)
    scene.say("Same untrained network, same car. Watch it guess.", hold=1.3)

    bars = prob_bars(DATA.demo_before, unit=BAR_UNIT, bar_h=BAR_H, gap=BAR_GAP)
    bars.move_to([PANEL_X, BARS_Y, 0])
    scene.flow(net, color=GOLD, rt=0.55)
    scene.play(LaggedStart(*[GrowFromEdge(r.bar, LEFT) for r in bars.rows],
                           *[FadeIn(r.lab) for r in bars.rows],
                           *[FadeIn(r[2]) for r in bars.rows],
                           lag_ratio=0.1, run_time=1.2))
    win = int(np.argmax(DATA.demo_before))          # the (wrong) predicted class
    wrong = class_name(win)
    ship_box = SurroundingRectangle(bars.rows[win], color=BAD, buff=0.06, corner_radius=0.06)
    verdict = VGroup(cross_badge().scale(0.95),
                     txt(f"predicts: {wrong}", fs=20, color=BAD)).arrange(RIGHT, buff=0.18)
    verdict.move_to([PANEL_X, VERDICT_Y, 0])
    scene.play(Create(ship_box), run_time=0.45)
    scene.play(FadeIn(verdict[0], scale=0.6), FadeIn(verdict[1], shift=RIGHT * 0.1), run_time=0.6)
    scene.say(f"Random weights, so it says “{wrong}.” Confident, and wrong.", color=BAD, hold=2.0)
    scene.beat(0.3)

    # ================================================================ #
    # BEAT B — the loss: how wrong was it? measure it.
    # ================================================================ #
    scene.clear_cap(0.3)
    row_ys = [bars.rows[i].bar.get_center()[1] for i in range(3)]
    tcol_x = bars.get_left()[0] - 0.52
    tcells = VGroup()
    for i, y in enumerate(row_ys):
        v = 1 if i == int(DATA.demo_true) else 0
        c = CLASS_COLORS[i] if v else MUTED
        cell = chip(str(v), c, fs=18, w=0.5, h=BAR_H + 0.14, tcolor=c,
                    weight="BOLD", fill=0.20 if v else 0.05)
        cell.move_to([tcol_x, y, 0])
        tcells.add(cell)
    thead = txt("target", fs=15, color=MUTED).move_to([tcol_x, row_ys[0] + 0.46, 0])
    target_grp = VGroup(thead, tcells)
    scene.play(FadeIn(thead), LaggedStart(*[FadeIn(c, scale=0.7) for c in tcells],
                                          lag_ratio=0.15, run_time=0.8))
    scene.say("The true answer is a 1 for car, 0 for the rest. That's the target.", hold=1.9)

    # cross-entropy loss box (WARN); value counts down in beat D
    loss_title = txt("cross-entropy loss", fs=16, color=MUTED)
    loss_big = txt(f"{float(DATA.demo_loss_before):.2f}", fs=33, color=WARN, weight="BOLD")
    loss_sub = txt("= -log P(car)", fs=16, color=MUTED)
    loss_col = VGroup(loss_title, loss_big, loss_sub).arrange(DOWN, buff=0.09)
    loss_bx = RoundedRectangle(width=loss_col.width + 0.55, height=loss_col.height + 0.34,
                               corner_radius=0.12, stroke_color=WARN, stroke_width=2.2,
                               fill_color=WARN, fill_opacity=0.08).move_to(loss_col)
    loss_grp = VGroup(loss_bx, loss_col).move_to([PANEL_X, LOSS_Y, 0])
    loss_anchor = loss_big.get_center()
    loss_vt = ValueTracker(float(DATA.demo_loss_before))

    def loss_upd(m):
        m.become(txt(f"{loss_vt.get_value():.2f}", fs=33, color=WARN, weight="BOLD")
                 .move_to(loss_anchor))

    scene.play(FadeIn(loss_grp, shift=UP * 0.12), run_time=0.7)
    scene.say("Cross-entropy folds that gap into one number: the loss.", hold=1.9)
    scene.play(Indicate(loss_big, color=WARN, scale_factor=1.25), run_time=0.7)
    scene.beat(0.9)
    scene.say(f"Big loss means very wrong. Right now it's {float(DATA.demo_loss_before):.2f}.",
              color=WARN, hold=2.0)
    scene.beat(0.3)

    # ================================================================ #
    # BEAT C — backpropagation: send the error backward
    # ================================================================ #
    scene.clear_cap(0.3)
    scene.say("Now send that error backward through the network.", hold=1.3)
    scene.flow(net, color=WARN, reverse=True, rt=0.6)
    scene.say("Backprop asks every weight: how much did you add to this error?",
              color=WARN, hold=2.2)
    scene.say(f"The answer is a gradient: a direction for all {NPARAMS:,} numbers.", hold=2.1)
    scene.beat(0.3)

    # ================================================================ #
    # BEAT D — the update: one step downhill; same image now reads "car"
    # ================================================================ #
    scene.clear_cap(0.3)
    scene.say("Nudge each weight one tiny step downhill, against its gradient.", hold=1.8)
    styles = _settled_edge_styles(net, seed=1)
    scene.play(LaggedStart(*[e.animate.set_stroke(color=c, width=w, opacity=o)
                             for e, (c, w, o) in zip(net.edges, styles)],
                           lag_ratio=0.012, run_time=1.7))
    scene.play(Indicate(net.edges, color=GOLD, scale_factor=1.0), run_time=0.7)
    scene.clear_cap(0.25)
    scene.say("Same picture, forward again…", hold=0.8)
    scene.flow(net, color=GOLD, rt=0.55)

    # morph the probability bars before -> after (bar rects only; crossfade values)
    bar_anims, val_fades, after_vals = [], [], []
    for i, p in enumerate(DATA.demo_after):
        old = bars.rows[i].bar
        left_pt = old.get_left()
        new_bw = max(0.04, BAR_UNIT * float(p))
        new_rect = Rectangle(width=new_bw, height=BAR_H, stroke_width=0,
                             fill_color=CLASS_COLORS[i], fill_opacity=0.9)
        new_rect.move_to(left_pt, aligned_edge=LEFT)
        bar_anims.append(Transform(old, new_rect))
        new_val = txt(f"{float(p):.2f}", fs=16, color=MUTED).next_to(new_rect, RIGHT, buff=0.14)
        after_vals.append(new_val)
        val_fades.append(FadeOut(bars.rows[i][2]))
        val_fades.append(FadeIn(new_val))
    loss_big.add_updater(loss_upd)
    scene.play(*bar_anims, *val_fades, FadeOut(ship_box),
               loss_vt.animate.set_value(float(DATA.demo_loss_after)), run_time=1.3)
    loss_big.clear_updaters()

    # verdict flips wrong -> right
    verdict2 = VGroup(check_badge().scale(0.95),
                      txt("predicts: car", fs=20, color=GOOD)).arrange(RIGHT, buff=0.18)
    verdict2.move_to([PANEL_X, VERDICT_Y, 0])
    car_box = SurroundingRectangle(bars.rows[0], color=GOOD, buff=0.06, corner_radius=0.06)
    scene.play(FadeOut(verdict, shift=DOWN * 0.12), FadeIn(verdict2, shift=UP * 0.12),
               Create(car_box), run_time=0.7)
    scene.say(f"…and now it says car. The loss fell from {float(DATA.demo_loss_before):.2f} "
              f"to {float(DATA.demo_loss_after):.2f}.", color=GOOD, hold=2.4)
    scene.beat(0.4)

    # ================================================================ #
    # BEAT E — scale up: the training dashboard (the iconic curves)
    # ================================================================ #
    _fade_rest(scene, keep=[head, scene._cap], rt=0.7)
    scene.say("One image, one step. Now repeat, thousands of images, over and over.",
              hold=2.0)

    # epoch counter (font-consistent Text driven by a ValueTracker)
    epoch_vt = ValueTracker(0)
    epoch_num = txt("0", fs=30, color=GOLD, weight="BOLD")
    counter = VGroup(txt("epoch", fs=22, color=MUTED), epoch_num).arrange(RIGHT, buff=0.26)
    counter.move_to([0, 2.05, 0])
    enum_left = epoch_num.get_left()

    def epoch_upd(m):
        n = txt(str(int(round(epoch_vt.get_value()))), fs=30, color=GOLD, weight="BOLD")
        n.move_to(enum_left, aligned_edge=LEFT)
        m.become(n)

    # two charts: loss (left) | accuracy (right)
    ax_loss = _mini_axes(1.15, 0.5, [-3.05, -0.35, 0])
    ax_acc = _mini_axes(1.0, 0.5, [3.05, -0.35, 0])
    loss_ttl = txt("training loss", fs=19, color=WARN, weight="BOLD").next_to(ax_loss, UP, buff=0.24)
    acc_ttl = VGroup(txt("accuracy:", fs=19, color=INK),
                     txt("train", fs=19, color=GOOD, weight="BOLD"),
                     txt("/", fs=19, color=MUTED),
                     txt("val", fs=19, color=CAR_C, weight="BOLD")).arrange(RIGHT, buff=0.14)
    acc_ttl.next_to(ax_acc, UP, buff=0.24)
    # axis labels (no LaTeX numbers — plain Text)
    xlab_l = txt("epochs 0 → 90", fs=15, color=MUTED).next_to(ax_loss, DOWN, buff=0.2)
    xlab_r = txt("epochs 0 → 90", fs=15, color=MUTED).next_to(ax_acc, DOWN, buff=0.2)
    yl_l0 = txt("0", fs=13, color=MUTED).next_to(ax_loss.c2p(0, 0), LEFT, buff=0.12)
    yl_l1 = txt("1.1", fs=13, color=MUTED).next_to(ax_loss.c2p(0, 1.1), LEFT, buff=0.12)
    yl_a0 = txt("0", fs=13, color=MUTED).next_to(ax_acc.c2p(0, 0), LEFT, buff=0.12)
    yl_a1 = txt("100%", fs=13, color=MUTED).next_to(ax_acc.c2p(0, 1.0), LEFT, buff=0.12)

    dash_static = VGroup(counter, ax_loss, ax_acc, loss_ttl, acc_ttl,
                         xlab_l, xlab_r, yl_l0, yl_l1, yl_a0, yl_a1)
    scene.play(FadeIn(dash_static, shift=UP * 0.15), run_time=0.9)

    # real curves
    ep = DATA.cur_epoch
    loss_curve = _polyline(ax_loss, ep, DATA.med_train_loss, WARN)
    acc_tr = _polyline(ax_acc, ep, DATA.med_train_acc, GOOD)
    acc_va = _polyline(ax_acc, ep, DATA.med_val_acc, CAR_C)

    epoch_num.add_updater(epoch_upd)
    scene.play(Create(loss_curve), Create(acc_tr), Create(acc_va),
               epoch_vt.animate.set_value(90), run_time=5.0, rate_func=linear)
    epoch_num.clear_updaters()

    # mark the endpoints
    end_dots = VGroup(
        Dot(loss_curve.get_end(), radius=0.06, color=WARN),
        Dot(acc_tr.get_end(), radius=0.06, color=GOOD),
        Dot(acc_va.get_end(), radius=0.06, color=CAR_C),
    )
    scene.play(FadeIn(end_dots, scale=0.5), run_time=0.5)
    scene.beat(1.2)
    scene.say("Loss slides down; accuracy climbs. That's the network learning.",
              color=GOLD, hold=2.4)
    scene.beat(0.4)

    # ================================================================ #
    # BEAT F — payoff + transition to Scene 4
    # ================================================================ #
    _fade_rest(scene, keep=[head, scene._cap], rt=0.7)
    scene.clear_cap(0.3)

    tr_pct = round(float(DATA.med_train_acc[-1]) * 100)
    va_pct = round(float(DATA.med_val_acc[-1]) * 100)
    stat = VGroup(
        VGroup(txt("train", fs=22, color=GOOD),
               txt(f"{tr_pct}%", fs=32, color=GOOD, weight="BOLD")).arrange(RIGHT, buff=0.22),
        VGroup(txt("validation", fs=22, color=CAR_C),
               txt(f"{va_pct}%", fs=32, color=CAR_C, weight="BOLD")).arrange(RIGHT, buff=0.22),
    ).arrange(RIGHT, buff=1.2).move_to(UP * 1.45)
    scene.play(LaggedStart(*[FadeIn(s, shift=UP * 0.12) for s in stat],
                           lag_ratio=0.25, run_time=1.0))
    scene.beat(0.7)

    punch = txt("That's how it learns: guess, measure the error, correct. A million times over.",
                fs=29, color=GOLD, weight="BOLD")
    maxw = 2 * config.frame_x_radius - 1.1
    if punch.width > maxw:
        punch.scale(maxw / punch.width)
    punch.move_to(DOWN * 0.05)
    scene.play(Write(punch), run_time=1.6)
    scene.beat(1.4)

    # one Text (perfect baseline alignment) with "right" coloured via t2c
    setup = Text("But is this the right network?", font_size=26, color=INK,
                 t2c={"right": GOLD}).move_to(DOWN * 1.55)
    scene.play(FadeIn(setup, shift=UP * 0.12), run_time=0.8)
    scene.beat(1.0)
    scene.settle()
    scene.wipe()


class Train(NNBase):
    def construct(self):
        build_train(self)
