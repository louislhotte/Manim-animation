"""Scene 5 — The Verdict: three trained networks go head-to-head, then we zoom
out from nine examples to all 2,400 test images.

Beat A introduces the three contenders (Tiny 299 · Medium 1,187 · Large 9,475).
Beat B runs each on the same 3x3 showcase — the red misses thin out as the net
grows (3/9 → 6/9 → 9/9). Beat C is the signature dezoom: the baked correctness
PNGs over all 2,400 test images (green = right, red = wrong), with the real
accuracies counting up. Beat D lands the headline (Large: 87.5%, up from 33% by
chance). Beat E keeps it honest with the large net's confusion matrix. Beat F is
the closing takeaway, then the house outro card (this is the last scene).

Every number is real (baked by generate_assets.py into assets/nn_learn.npz);
the correctness grids are pre-rendered PNGs in assets/.
"""
from nn_common import *

# --- the three contenders (indices 0=Tiny, 1=Medium, 2=Large) -------------- #
NAMES = [str(x) for x in DATA.arch_names]                 # Tiny / Medium / Large
WIDTHS = [int(DATA.arch_sizes[i][1]) for i in range(3)]   # 2 / 8 / 64
PARAMS = [int(p) for p in DATA.params]                    # 299 / 1187 / 9475
ACCS = [float(a) for a in DATA.test_acc]                  # 0.655 / 0.783 / 0.875
ACCENTS = [MUTED, CAR_C, GOLD]                            # small -> big colour ramp

TRUE = [int(x) for x in DATA.show_true]                   # [0,0,0,1,1,1,2,2,2]
PREDS = [[int(x) for x in DATA.show_pred_tiny],
         [int(x) for x in DATA.show_pred_med],
         [int(x) for x in DATA.show_pred_large]]
GRID_FILES = ["grid_tiny.png", "grid_medium.png", "grid_large.png"]
N_TEST = int(DATA.n_test)
NIN = int(DATA.img) ** 2                                  # network inputs (784)
CONF = np.asarray(DATA.confusion_large)                   # 3x3, rows=true, cols=pred


# ========================================================================== #
# local helpers
# ========================================================================== #
def _contender_card(i):
    """A card: a small network diagram (growing with i) + name / width / params."""
    accent = ACCENTS[i]
    shown = [[4, 2, 3], [4, 6, 3], [5, 7, 3]][i]
    scl = [0.75, 0.90, 1.05][i]
    net = build_network([NIN, WIDTHS[i], 3], shown=shown, width=2.3, height=1.2,
                        node_r=0.085, edge_op=0.5).scale(scl)
    name = txt(NAMES[i], fs=27, color=accent, weight="BOLD")
    wlab = txt(f"width {WIDTHS[i]}", fs=18, color=MUTED)
    plab = txt(f"{PARAMS[i]:,} params", fs=22, color=accent, weight="BOLD")
    inner = VGroup(net, name, wlab, plab).arrange(DOWN, buff=0.22)
    box = RoundedRectangle(width=3.4, height=4.1, corner_radius=0.14,
                           stroke_color=accent, stroke_width=2.4,
                           fill_color=accent, fill_opacity=0.05).move_to(inner)
    card = VGroup(box, inner)
    card.accent = accent
    card.param_lbl = plab
    card.name_lbl = name
    return card


def _fmt_pct(v):
    return f"{v:.1f}%"


def _counter(vt, fmt, fs, color, weight="BOLD"):
    """A Helvetica number driven by a ValueTracker. DecimalNumber renders via
    LaTeX/Computer-Modern, which clashes with the body font — this keeps every
    number in the same sans-serif. Attach with _live(), detach with
    clear_updaters() before any FadeOut."""
    m = txt(fmt(vt.get_value()), fs=fs, color=color, weight=weight)
    m._spec = (vt, fmt, fs, color, weight)
    return m


def _live(m):
    vt, fmt, fs, color, weight = m._spec
    m.add_updater(lambda mob: mob.become(
        txt(fmt(vt.get_value()), fs=fs, color=color, weight=weight).move_to(mob)))
    return m


def _badge(ok, r=0.24):
    """A clear, opaque verdict badge: a solid coloured disc with a bold light
    tick / cross — reads instantly on top of a busy image corner."""
    col = GOOD if ok else BAD
    disc = Circle(radius=r, fill_color=col, fill_opacity=1.0, stroke_color=BG, stroke_width=4)
    sym = (make_tick(color=INK, sw=6, scale=1.1 * r / 0.22) if ok
           else make_cross(color=INK, sw=6, scale=0.95 * r / 0.22))
    g = VGroup(disc, sym.move_to(disc))
    g.set_z_index(20)
    return g


def _confusion(mat, cx, cy):
    """The large net's 3x3 confusion matrix (rows=true, cols=predicted)."""
    cw, ch, sx, sy = 1.3, 0.85, 1.4, 0.95
    grp = VGroup()
    cells = [[None] * 3 for _ in range(3)]
    cellgroups = [[None] * 3 for _ in range(3)]
    for r in range(3):
        for c in range(3):
            x, y = cx + (c - 1) * sx, cy - (r - 1) * sy
            diag = (r == c)
            rect = RoundedRectangle(
                width=cw, height=ch, corner_radius=0.06,
                stroke_color=(GOOD if diag else FAINT), stroke_width=(2.6 if diag else 1.6),
                fill_color=(GOOD if diag else PANEL), fill_opacity=(0.16 if diag else 0.5))
            rect.move_to([x, y, 0])
            n = int(mat[r][c])
            t = txt(str(n), fs=(24 if diag else 20),
                    color=(GOOD if diag else MUTED), weight=("BOLD" if diag else "NORMAL"))
            t.move_to(rect)
            cells[r][c] = rect
            cellgroups[r][c] = VGroup(rect, t)
            grp.add(rect, t)
    # axis labels
    top = cy + 1 * sy + ch / 2
    axis = VGroup()
    for c in range(3):
        h = txt(class_name(c), fs=18, color=CLASS_COLORS[c], weight="BOLD")
        h.move_to([cx + (c - 1) * sx, top + 0.3, 0])
        axis.add(h)
    axis.add(txt("predicted", fs=16, color=MUTED).move_to([cx, top + 0.72, 0]))
    left_edge = cx - sx - cw / 2                     # left edge of the matrix
    rlabels = VGroup()
    for r in range(3):
        h = txt(class_name(r), fs=18, color=CLASS_COLORS[r], weight="BOLD")
        h.next_to(np.array([left_edge, cy - (r - 1) * sy, 0]), LEFT, buff=0.32)
        axis.add(h)
        rlabels.add(h)
    tlab = txt("true", fs=16, color=MUTED).rotate(PI / 2).next_to(rlabels, LEFT, buff=0.3)
    axis.add(tlab)
    grp.add(axis)
    grp.cells = cells
    grp.cellgroups = cellgroups
    grp.axis = axis
    return grp


# ========================================================================== #
def build_verdict(scene):
    head = scene.section_header("THE VERDICT", "Three Networks, 2,400 Images", GOLD)
    scene.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

    # ---------------------------------------------------------------- #
    # Beat A — the three contenders
    # ---------------------------------------------------------------- #
    cards = VGroup(*[_contender_card(i) for i in range(3)])
    cards.arrange(RIGHT, buff=0.5).move_to(DOWN * 0.45)
    scene.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards],
                           lag_ratio=0.2, run_time=1.6))
    scene.say("Three networks, all trained on the same task, but very different sizes.",
              hold=1.6)
    scene.play(LaggedStart(*[Indicate(c.param_lbl, color=c.accent, scale_factor=1.18)
                             for c in cards], lag_ratio=0.25, run_time=1.4))
    scene.say(f"From {PARAMS[0]:,} knobs up to {PARAMS[2]:,}. Does bigger really mean smarter?",
              color=GOLD, hold=1.8)
    scene.beat(0.4)

    # ---------------------------------------------------------------- #
    # Beat B — the showcase on 9 images
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(cards), run_time=0.6)

    imgs = [pixel_grid(DATA.show_imgs[k], cell=0.045) for k in range(9)]
    grid = VGroup(*imgs).arrange_in_grid(rows=3, cols=3, buff=0.4)
    grid.move_to([-1.7, -0.3, 0])
    # class row labels on the left (top row cars, then planes, then ships)
    rowlabs = VGroup()
    for r in range(3):
        rc = CLASS_COLORS[r]
        lab = chip(class_name(r), rc, fs=18, h=0.44, w=1.0)
        lab.next_to(imgs[r * 3], LEFT, buff=0.32)
        rowlabs.add(lab)
    scene.play(LaggedStart(*[FadeIn(im, scale=0.9) for im in imgs],
                           lag_ratio=0.05, run_time=1.3),
               LaggedStart(*[FadeIn(l, shift=RIGHT * 0.12) for l in rowlabs],
                           lag_ratio=0.15, run_time=1.0))
    scene.say("First, just nine pictures: three cars, three planes, three ships.", hold=1.5)

    # right-hand scoreboard
    panel_x = 3.7
    name_lbl = txt(NAMES[0], fs=30, color=ACCENTS[0], weight="BOLD").move_to([panel_x, 1.4, 0])
    svt = ValueTracker(0)
    score = _counter(svt, lambda v: f"{int(round(v))}  /  9", 50, INK, "BOLD").move_to([panel_x, -0.15, 0])
    correct_lbl = txt("correct", fs=20, color=MUTED).move_to([panel_x, -1.35, 0])

    def place_badge(k, ok):
        return _badge(ok).move_to(imgs[k].get_corner(UR))

    def frame_anim(k, ok):
        return imgs[k].box.animate.set_stroke(color=(GOOD if ok else BAD), width=5)

    # Tiny — badges appear and each image's frame turns green (right) or red (wrong)
    scene.play(FadeIn(name_lbl), FadeIn(score), FadeIn(correct_lbl), run_time=0.6)
    _live(score)
    oks = [PREDS[0][k] == TRUE[k] for k in range(9)]
    badges = [place_badge(k, oks[k]) for k in range(9)]
    scene.play(LaggedStart(*[GrowFromCenter(b) for b in badges], lag_ratio=0.07),
               *[frame_anim(k, oks[k]) for k in range(9)], run_time=1.5)
    scene.play(svt.animate.set_value(sum(oks)), run_time=0.9)
    scene.say("Tiny gets three of nine, barely better than a coin toss.", hold=1.7)
    scene.beat(0.3)

    # Medium, then Large: flip the changed badges + frames, count the score up
    prev = PREDS[0]
    for i in (1, 2):
        cur = PREDS[i]
        new_name = txt(NAMES[i], fs=30, color=ACCENTS[i], weight="BOLD").move_to([panel_x, 1.4, 0])
        scene.play(FadeOut(name_lbl, shift=UP * 0.1), FadeIn(new_name, shift=UP * 0.1), run_time=0.5)
        name_lbl = new_name
        badge_flips, frame_flips = [], []
        for k in range(9):
            if (prev[k] == TRUE[k]) != (cur[k] == TRUE[k]):
                nb = place_badge(k, cur[k] == TRUE[k])
                badge_flips.append(ReplacementTransform(badges[k], nb))
                badges[k] = nb
                frame_flips.append(frame_anim(k, cur[k] == TRUE[k]))
        scene.play(LaggedStart(*badge_flips, lag_ratio=0.2), *frame_flips,
                   svt.animate.set_value(sum(cur[k] == TRUE[k] for k in range(9))), run_time=1.2)
        if i == 1:
            scene.say("Medium: six of nine. The red is thinning out.", color=CAR_C, hold=1.7)
        else:
            scene.say("Large: a perfect nine. But nine images is easy…", color=GOLD, hold=1.9)
        scene.beat(0.3)
        prev = cur

    # ---------------------------------------------------------------- #
    # Beat C — the dezoom to 2,400
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    score.clear_updaters()
    scene.play(FadeOut(grid), FadeOut(rowlabs), FadeOut(VGroup(*badges)),
               FadeOut(name_lbl), FadeOut(score), FadeOut(correct_lbl), run_time=0.7)

    t1 = txt("Nine images is easy.", fs=38, color=INK, weight="BOLD")
    t2 = txt("How about all 2,400?", fs=38, color=GOLD, weight="BOLD")
    ask = VGroup(t1, t2).arrange(DOWN, buff=0.34).move_to(ORIGIN)
    scene.play(FadeIn(t1, shift=UP * 0.1), run_time=0.7)
    scene.play(FadeIn(t2, shift=UP * 0.1), run_time=0.7)
    scene.beat(1.4)
    scene.play(FadeOut(ask), run_time=0.6)

    xcen = [-4.25, 0.0, 4.25]
    grids, glabels, gaccs = [], [], []
    for i in range(3):
        g = ImageMobject(str(ROOT / "assets" / GRID_FILES[i]))
        g.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
        g.set_height(2.5).move_to([xcen[i], -0.1, 0])
        lab = txt(f"{NAMES[i]} · width {WIDTHS[i]}", fs=20, color=ACCENTS[i], weight="BOLD")
        lab.next_to(g, UP, buff=0.22)
        avt = ValueTracker(0.0)
        acc = _counter(avt, _fmt_pct, 32, ACCENTS[i], "BOLD").next_to(g, DOWN, buff=0.3)
        acc._avt = avt
        grids.append(g); glabels.append(lab); gaccs.append(acc)

    c_lines = [
        "Each tile is one real test image, green if right, red if wrong.",
        "Medium: more green. Nearly five out of six.",
        "Large: almost the whole wall turns green.",
    ]
    for i in range(3):
        scene.play(FadeIn(grids[i]), FadeIn(glabels[i], shift=UP * 0.1),
                   FadeIn(gaccs[i]), run_time=0.7)
        _live(gaccs[i])
        scene.play(gaccs[i]._avt.animate.set_value(ACCS[i] * 100), run_time=1.4)
        scene.say(c_lines[i], color=(INK if i == 0 else ACCENTS[i]), hold=1.7)
        scene.beat(0.2)
    scene.say("The bigger the network, the more of the grid turns green.",
              color=GOLD, hold=1.8)
    scene.beat(0.3)

    # ---------------------------------------------------------------- #
    # Beat D — the real global value
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    for a in gaccs:
        a.clear_updaters()
    faded = [grids[0], glabels[0], gaccs[0], grids[1], glabels[1], gaccs[1],
             glabels[2], gaccs[2]]
    scene.play(*[FadeOut(m) for m in faded],
               grids[2].animate.scale(3.3 / 2.5).move_to([-3.5, 0.15, 0]),
               run_time=1.0)

    dname = txt("Large network", fs=30, color=GOLD, weight="BOLD").move_to([3.35, 1.75, 0])
    bvt = ValueTracker(33.0)
    big = _counter(bvt, _fmt_pct, 64, GOLD, "BOLD").move_to([3.35, 0.25, 0])
    sub = txt("correct on 2,400 unseen images", fs=22, color=INK).move_to([3.35, -1.05, 0])
    chance = txt("random guessing:  33%", fs=20, color=MUTED).move_to([3.35, -1.9, 0])

    scene.play(FadeIn(dname, shift=DOWN * 0.1), run_time=0.5)
    scene.play(FadeIn(big), FadeIn(chance), run_time=0.6)
    _live(big)
    scene.say("A coin-flip guess would get one class in three: just 33%.", hold=1.6)
    scene.play(bvt.animate.set_value(ACCS[2] * 100), run_time=2.2,
               rate_func=rate_functions.ease_out_cubic)
    big.clear_updaters()
    scene.play(FadeIn(sub, shift=UP * 0.1), Indicate(big, color=GOLD, scale_factor=1.12),
               run_time=0.8)
    scene.say(f"The best network: {ACCS[2] * 100:.1f}%, on images it had never seen before.",
              color=GOLD, hold=2.0)
    scene.beat(0.4)

    # ---------------------------------------------------------------- #
    # Beat E — what it still gets wrong (confusion matrix)
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(dname), FadeOut(big), FadeOut(sub), FadeOut(chance),
               FadeOut(grids[2]), run_time=0.7)

    etitle = txt("Even the best isn't perfect", fs=26, color=INK, weight="BOLD")
    etitle.move_to([-1.9, 2.35, 0])
    conf = _confusion(CONF, cx=-1.9, cy=-0.65)
    scene.play(FadeIn(etitle, shift=DOWN * 0.1), run_time=0.5)
    scene.play(FadeIn(conf.axis, shift=UP * 0.1), run_time=0.6)
    scene.play(LaggedStart(*[FadeIn(conf.cellgroups[r][c])
                             for r in range(3) for c in range(3)],
                           lag_ratio=0.06, run_time=1.4))
    scene.say("Rows are the truth, columns are its guess. The green diagonal is correct.",
              hold=2.0)
    scene.play(LaggedStart(*[Indicate(conf.cells[i][i], color=GOOD, scale_factor=1.08)
                             for i in range(3)], lag_ratio=0.2, run_time=1.2))

    # its worst mix-up = the largest off-diagonal count (true `wr`, predicted `wc`)
    _off = CONF.copy()
    np.fill_diagonal(_off, 0)
    wr, wc = (int(v) for v in np.unravel_index(_off.argmax(), _off.shape))
    n_slip = int(CONF[wr][wc])
    slipbox = SurroundingRectangle(conf.cellgroups[wr][wc], color=BAD, buff=0.03, corner_radius=0.06)
    ctitle = txt("Its most common slip", fs=22, color=WARN, weight="BOLD")
    glyph_row = VGroup(class_glyph(wr, s=0.5), arr([0, 0, 0], [0.55, 0, 0], color=MUTED),
                       class_glyph(wc, s=0.5)).arrange(RIGHT, buff=0.28)
    cnt = txt(f"{n_slip} times", fs=26, color=BAD, weight="BOLD")
    cnote = txt(f"a {class_name(wr)} mistaken for a {class_name(wc)}", fs=19, color=MUTED)
    callout = VGroup(ctitle, glyph_row, cnt, cnote).arrange(DOWN, buff=0.3).move_to([3.55, 0.0, 0])
    scene.play(Create(slipbox), FadeIn(callout, shift=RIGHT * 0.15), run_time=0.9)
    scene.say(f"Its worst mix-up: {n_slip} {class_name(wr)}s called {class_name(wc)}s. "
              f"Close, but not flawless.", color=WARN, hold=2.0)
    scene.beat(0.4)

    # ---------------------------------------------------------------- #
    # Beat F — closing takeaway + outro
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(etitle, conf, slipbox, callout)), FadeOut(head), run_time=0.8)

    l1 = txt(f"From random noise to {ACCS[2] * 100:.1f}%.", fs=42, color=GOLD, weight="BOLD")
    l2 = txt("The same recipe: examples, errors,", fs=30, color=INK, weight="BOLD")
    l3 = txt("and a million tiny corrections.", fs=30, color=INK, weight="BOLD")
    take = VGroup(l1, VGroup(l2, l3).arrange(DOWN, buff=0.18)).arrange(DOWN, buff=0.5)
    take.move_to(ORIGIN)
    maxw = 2 * config.frame_x_radius - 1.0
    if take.width > maxw:
        take.scale(maxw / take.width)
    scene.play(Write(l1), run_time=1.4)
    scene.beat(0.4)
    scene.play(FadeIn(l2, shift=UP * 0.1), FadeIn(l3, shift=UP * 0.1), run_time=1.0)
    scene.beat(1.4)
    scene.settle()

    scene.wipe()
    scene.play_outro(recap="Examples in, errors out, weights nudged: that's how a machine learns.")


class Verdict(NNBase):
    def construct(self):
        build_verdict(self)
