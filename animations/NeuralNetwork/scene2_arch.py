"""Scene 2 — The Architecture: the (untrained) network.

Flatten the 12x12 image into 144 inputs, build the feed-forward net
(144 → 8 → 3), explain what one neuron does, count the parameters, and run a
forward pass with *random* weights — it guesses "ship" for a car. That wrong
guess sets up Scene 3 (training). The net sits at a fixed left position the whole
scene; every explainer panel appears to its right.
"""
from nn_common import *

MED = 1                      # index of the "Medium" hero net in DATA arrays
HID = 8                      # its hidden width
IN = int(DATA.img) if DATA is not None else 28      # image side (28)
NIN = IN * IN                                        # network inputs (784)
NET_POS = LEFT * 1.85 + DOWN * 0.2


def _neuron_panel():
    title = txt("What each neuron does", fs=24, color=GOLD, weight="BOLD")
    steps = VGroup(
        VGroup(Dot(radius=0.05, color=CAR_C),
               txt("multiply every input by a weight", fs=19, color=INK)).arrange(RIGHT, buff=0.2),
        VGroup(Dot(radius=0.05, color=SHIP_C),
               txt("add them all up, plus a bias", fs=19, color=INK)).arrange(RIGHT, buff=0.2),
        VGroup(Dot(radius=0.05, color=WARN),
               txt("apply an activation (ReLU)", fs=19, color=INK)).arrange(RIGHT, buff=0.2),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
    f1 = txt("z  =  w · x  +  b", fs=25, color=INK, weight="BOLD")
    f2 = txt("a  =  ReLU(z)", fs=25, color=WARN, weight="BOLD")
    forms = VGroup(f1, f2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    return VGroup(title, steps, forms).arrange(DOWN, aligned_edge=LEFT, buff=0.34)


def _relu_mini():
    ax = Axes(x_range=[-1.5, 1.5, 1], y_range=[0, 1.5, 1], x_length=1.6, y_length=1.1,
              tips=False, axis_config={"stroke_color": MUTED, "stroke_width": 1.6,
                                       "include_ticks": False})
    graph = ax.plot(lambda x: max(0, x), x_range=[-1.5, 1.5], color=WARN, stroke_width=4)
    lab = txt("ReLU", fs=15, color=WARN).next_to(ax, UP, buff=0.06)
    return VGroup(ax, graph, lab)


def build_arch(scene):
    head = scene.section_header("THE NETWORK", "Building the Machine", CAR_C)
    scene.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

    # ---------------------------------------------------------------- #
    # (a) flatten the image into 144 inputs
    # ---------------------------------------------------------------- #
    img = DATA.demo_img if DATA is not None else np.zeros((IN, IN))
    grid = pixel_grid(img, cell=0.1).to_edge(LEFT, buff=1.15).shift(DOWN * 0.3)
    glab = txt(f"{IN} × {IN} image", fs=20, color=MUTED).next_to(grid, DOWN, buff=0.25)
    scene.play(FadeIn(grid), FadeIn(glab), run_time=0.7)

    vec = vec_column(img.ravel(), cw=0.2, color=INK, cap=16).next_to(grid, RIGHT, buff=1.6)
    ell0 = VGroup(*[Dot(radius=0.025, color=MUTED) for _ in range(3)]).arrange(DOWN, buff=0.06)
    ell0.next_to(vec, DOWN, buff=0.1)
    vlab = txt(f"{NIN} numbers", fs=20, color=INK).next_to(VGroup(vec, ell0), DOWN, buff=0.2)
    a = arr(grid.get_right(), vec.get_left(), color=MUTED)
    flat = txt("flatten", fs=18, color=MUTED).next_to(a, UP, buff=0.1)
    scene.play(GrowArrow(a), FadeIn(flat), TransformFromCopy(grid.cells[:16], vec), run_time=1.0)
    scene.play(FadeIn(ell0), FadeIn(vlab), run_time=0.4)
    scene.say(f"Line up all {NIN} pixels into a column. That's the network's input.", hold=1.4)
    scene.beat(0.3)

    # ---------------------------------------------------------------- #
    # (b) build the full network (fixed position for the rest of the scene)
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    net = build_network([NIN, HID, 3], shown=[6, HID, 3], width=5.6, height=3.6).move_to(NET_POS)
    net.style_edges(seed=3, settled=False)       # random init: faint, uniform
    inlab = txt(f"{NIN} inputs", fs=20, color=CAR_C).next_to(net.layers[0], UP, buff=0.35)
    hlab = txt(f"{HID} hidden neurons", fs=20, color=INK).next_to(net.layers[1], UP, buff=0.35)
    outlab = txt("3 outputs", fs=20, color=INK).next_to(net.layers[2], UP, buff=0.35)
    outs = VGroup(*[txt(n, fs=19, color=CLASS_COLORS[i])
                    for i, n in enumerate(("car", "plane", "ship"))])
    for t, d in zip(outs, net.layers[2]):
        t.next_to(d, RIGHT, buff=0.22)

    scene.play(ReplacementTransform(vec, net.layers[0]), FadeIn(net.ell[0]),
               FadeOut(VGroup(grid, glab, a, flat, vlab, ell0)), run_time=0.8)
    scene.play(FadeIn(inlab), run_time=0.3)
    scene.play(LaggedStart(*[GrowFromCenter(d) for d in net.layers[1]], lag_ratio=0.06),
               FadeIn(hlab), run_time=0.9)
    scene.play(Create(net.gaps[0]), run_time=1.0)
    scene.play(LaggedStart(*[GrowFromCenter(d) for d in net.layers[2]], lag_ratio=0.2),
               Create(net.gaps[1]), FadeIn(outlab), run_time=1.0)
    scene.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.1) for t in outs], lag_ratio=0.15, run_time=0.7))
    scene.say("Neurons in layers. Every connection a weight, every neuron a bias.", hold=1.6)
    scene.beat(0.3)

    # ---------------------------------------------------------------- #
    # (c) what one neuron does
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(outs), run_time=0.4)
    focus = net.layers[1][3]
    halo = Circle(radius=0.26, color=GOLD, stroke_width=3).move_to(focus)
    in_edges = VGroup(*[e for e in net.gaps[0]
                        if np.allclose(e.get_end(), focus.get_center(), atol=0.06)])
    scene.play(Create(halo), focus.animate.set_color(GOLD), run_time=0.5)
    scene.play(in_edges.animate.set_stroke(color=GOLD, width=2.6, opacity=0.95), run_time=0.6)

    panel = _neuron_panel().to_edge(RIGHT, buff=0.6).shift(UP * 0.55)
    relu = _relu_mini().next_to(panel, DOWN, buff=0.35).align_to(panel, LEFT)
    scene.play(FadeIn(panel[0], shift=UP * 0.1), run_time=0.5)
    for s in panel[1]:
        scene.play(FadeIn(s, shift=RIGHT * 0.12), run_time=0.4)
        scene.beat(0.35)
    scene.play(FadeIn(panel[2], shift=UP * 0.1), FadeIn(relu), run_time=0.7)
    scene.say("A weighted sum, a bias, a squash. That's the whole neuron.", color=GOLD, hold=1.6)
    scene.beat(0.3)

    # ---------------------------------------------------------------- #
    # (d) count the parameters
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(panel, relu, halo)), focus.animate.set_color(INK),
               in_edges.animate.set_stroke(color=MUTED, width=1.4, opacity=0.5), run_time=0.6)
    n_params = int(DATA.params[MED]) if DATA is not None else 6307
    n_w, n_b = NIN * HID + HID * 3, HID + 3
    pc = VGroup(
        txt(f"{n_w:,} weights", fs=25, color=CAR_C, weight="BOLD"),
        txt(f"+  {n_b} biases", fs=25, color=SHIP_C, weight="BOLD"),
        txt(f"=  {n_params:,} numbers", fs=30, color=GOLD, weight="BOLD"),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).to_edge(RIGHT, buff=1.0).shift(UP * 0.2)
    for p in pc:
        scene.play(FadeIn(p, shift=RIGHT * 0.12), run_time=0.5)
        scene.beat(0.4)
    scene.play(LaggedStart(*[Indicate(e, color=GOLD, scale_factor=1.0) for e in net.edges],
                           lag_ratio=0.006, run_time=1.6))
    scene.say(f"{n_params:,} knobs, and right now every one is a random number.", hold=1.6)
    scene.beat(0.3)

    # ---------------------------------------------------------------- #
    # (e) forward pass: signal flows → raw scores → softmax → a wrong guess
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(pc), run_time=0.5)
    thumb = pixel_grid(img, cell=0.055).next_to(net.layers[0], LEFT, buff=0.4)
    tlab = txt("a car", fs=18, color=CAR_C).next_to(thumb, DOWN, buff=0.18)
    scene.play(FadeIn(thumb), FadeIn(tlab), run_time=0.5)
    scene.say("Feed in a picture and let the signal flow forward…", hold=0.9)
    scene.flow(net, color=GOLD, rt=0.55)

    # the three output neurons emit raw scores (logits) whose softmax IS the real
    # untrained output — derive them from it so the numbers stay honest.
    probs = DATA.demo_before if DATA is not None else np.array([0.14, 0.50, 0.36])
    _lg = np.log(np.clip(np.asarray(probs, float), 1e-6, 1))
    _lg = _lg - _lg.min() + 0.3
    logits = [round(float(v), 1) for v in _lg]
    scores = VGroup(*[txt(f"{v:.1f}", fs=22, color=CLASS_COLORS[i], weight="BOLD")
                      for i, v in enumerate(logits)])
    for t, d in zip(scores, net.layers[2]):
        t.next_to(d, RIGHT, buff=0.25)
    scene.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.12) for s in scores],
                           lag_ratio=0.15, run_time=0.8))
    scene.say("Three raw scores come out, but they're not probabilities yet.", hold=1.2)

    # softmax -> probabilities that sum to 1
    soft = chip("softmax", GOLD, fs=20, w=2.0, h=0.58, weight="BOLD").to_edge(RIGHT, buff=1.4).shift(UP * 1.55)
    bars = prob_bars(probs, unit=2.3).next_to(soft, DOWN, buff=0.55).shift(RIGHT * 0.15)
    a_soft = arr(scores.get_right(), soft.get_left(), color=GOLD)
    scene.play(GrowArrow(a_soft), FadeIn(soft), run_time=0.6)
    scene.play(TransformFromCopy(scores, VGroup(*[r.bar for r in bars.rows])),
               LaggedStart(*[FadeIn(r.lab) for r in bars.rows],
                           *[FadeIn(r[2]) for r in bars.rows], lag_ratio=0.1),
               run_time=1.1)
    scene.say("Softmax → probabilities that sum to 1. Biggest score wins.", hold=1.4)
    scene.beat(0.3)

    win = int(np.argmax(probs))
    pick = SurroundingRectangle(bars.rows[win], color=CLASS_COLORS[win], buff=0.06, corner_radius=0.06)
    verdict = VGroup(cross_badge().scale(1.0),
                     txt(f"says “{class_name(win)}”, but it's a car", fs=21, color=BAD)).arrange(RIGHT, buff=0.2)
    verdict.next_to(bars, DOWN, buff=0.5)
    scene.play(Create(pick), run_time=0.5)
    scene.play(FadeIn(verdict[0], scale=0.6), FadeIn(verdict[1], shift=RIGHT * 0.1), run_time=0.7)
    scene.say("Random weights give a confident, wrong guess. So how does it get better?",
              color=GOLD, hold=1.9)
    scene.beat(0.4)
    scene.settle()
    scene.wipe()


class Arch(NNBase):
    def construct(self):
        build_arch(self)
