"""Scene 1 — The Task: the supervised-learning paradigm + labeled data.

Opens the film (house intro card), then: you can't *write* the rules for "car",
so instead we learn from **labeled examples**. Introduces the three classes, the
mapping f(image) → label, and the punchline that to a computer an image is just a
grid of numbers — setting up the architecture scene.
"""
from nn_common import *

IN = int(DATA.img) if DATA is not None else 28      # image side (28)
NIN = IN * IN                                        # network inputs (784)


def build_task(scene):
    scene.play_intro()

    # ---------------------------------------------------------------- #
    # (a) the problem: you can't write the rules
    # ---------------------------------------------------------------- #
    q = txt("How do you teach a computer to recognize a car?", fs=40, color=INK, weight="BOLD")
    q.move_to(UP * 0.7)
    car = car_glyph(s=1.15).next_to(q, DOWN, buff=0.7)
    scene.play(Write(q), run_time=1.3)
    scene.play(FadeIn(car, shift=UP * 0.2), run_time=0.8)
    scene.beat(1.0)

    # the naive "write rules" attempt, struck out
    rules = VGroup(
        txt("if it has wheels…", fs=26, color=MUTED),
        txt("if it's metal and shiny…", fs=26, color=MUTED),
        txt("if it's on a road…", fs=26, color=MUTED),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
    rules.next_to(car, DOWN, buff=0.6)
    scene.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rules],
                           lag_ratio=0.3, run_time=1.5))
    scene.beat(1.2)
    strike = VGroup(*[Line(r.get_left(), r.get_right(), color=BAD, stroke_width=4) for r in rules])
    scene.play(LaggedStart(*[Create(s) for s in strike], lag_ratio=0.2, run_time=0.9))
    scene.beat(0.9)
    # clear the crossed-out rules, then land the punchline in that cleared space
    scene.play(FadeOut(rules), FadeOut(strike), run_time=0.5)
    punch = txt("Real images are endless exceptions. The rules never end.",
                fs=28, color=BAD, weight="BOLD").next_to(car, DOWN, buff=0.75)
    scene.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
    scene.beat(1.6)
    scene.play(FadeOut(VGroup(q, car, punch)), run_time=0.7)

    # the pivot
    pivot = txt("So we don't write the rules.", fs=40, color=INK, weight="BOLD").move_to(UP * 0.4)
    pivot2 = txt("We show it examples, and let it learn them.", fs=34, color=GOLD, weight="BOLD")
    pivot2.next_to(pivot, DOWN, buff=0.4)
    scene.play(FadeIn(pivot, shift=UP * 0.15), run_time=0.8)
    scene.play(FadeIn(pivot2, shift=UP * 0.15), run_time=0.8)
    scene.beat(1.6)
    scene.play(FadeOut(VGroup(pivot, pivot2)), run_time=0.6)

    # ---------------------------------------------------------------- #
    # (b) the labeled dataset
    # ---------------------------------------------------------------- #
    head = scene.section_header("THE TASK", "Learning from Examples", GOLD)
    scene.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

    pattern = ["car", "plane", "ship", "plane",
               "ship", "car", "plane", "car",
               "ship", "plane", "car", "ship"]
    cards = VGroup(*[labeled_example(n, s=0.5, card_w=1.5, card_h=1.5) for n in pattern])
    cards.arrange_in_grid(rows=3, cols=4, buff=0.32)
    cards.scale_to_fit_height(4.5).move_to(DOWN * 0.35)
    scene.play(LaggedStart(*[FadeIn(c, scale=0.85) for c in cards],
                           lag_ratio=0.06, run_time=1.8))
    scene.say("Thousands of images, every one already labeled by a human.", hold=1.6)

    # the label IS the answer we're given
    scene.play(LaggedStart(*[Indicate(c.tag, color=c.tag.box.get_stroke_color(), scale_factor=1.12)
                             for c in cards], lag_ratio=0.05, run_time=1.6))
    scene.say("The coloured tag is the answer: the label tells us what it is.",
              color=GOLD, hold=1.6)
    scene.beat(0.4)

    # ---------------------------------------------------------------- #
    # (c) three classes, with counts
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(cards), run_time=0.6)
    n_each = int(DATA.n_train) // 3 if DATA is not None else 500
    cols = VGroup()
    for name in ("car", "plane", "ship"):
        col_c = CLASS_COLORS[("car", "plane", "ship").index(name)]
        big = class_glyph(name, s=1.05)
        nm = txt(name, fs=30, color=col_c, weight="BOLD")
        cnt = txt(f"{n_each} examples", fs=20, color=MUTED)
        card = VGroup(big, nm, cnt).arrange(DOWN, buff=0.28)
        box = RoundedRectangle(width=3.4, height=3.2, corner_radius=0.14,
                               stroke_color=col_c, stroke_width=2.4,
                               fill_color=col_c, fill_opacity=0.06).move_to(card)
        cols.add(VGroup(box, card))
    cols.arrange(RIGHT, buff=0.55).move_to(DOWN * 0.35)
    scene.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cols],
                           lag_ratio=0.2, run_time=1.5))
    scene.say(f"Three classes, {DATA.n_train if DATA is not None else 1500:,} labelled images in all.", hold=1.6)
    scene.beat(0.3)

    # ---------------------------------------------------------------- #
    # (c2) name the paradigm: supervised learning
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(cols), run_time=0.5)
    ptitle = txt("This is supervised learning", fs=40, color=GOLD, weight="BOLD").move_to(UP * 1.75)
    pts = VGroup(
        VGroup(make_tick(GOOD, scale=0.95),
               txt("we have examples, and their answers (the labels)", fs=27)).arrange(RIGHT, buff=0.3),
        VGroup(make_tick(GOOD, scale=0.95),
               txt("the network learns the mapping   image  →  label", fs=27)).arrange(RIGHT, buff=0.3),
        VGroup(make_tick(GOOD, scale=0.95),
               txt("the real goal: be right on images it has never seen", fs=27)).arrange(RIGHT, buff=0.3),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).next_to(ptitle, DOWN, buff=0.75)
    scene.play(Write(ptitle), run_time=1.0)
    for p in pts:
        scene.play(FadeIn(p, shift=RIGHT * 0.2), run_time=0.6)
        scene.beat(0.9)
    scene.beat(0.6)

    # ---------------------------------------------------------------- #
    # (d) the mapping f(image) -> label
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(ptitle, pts)), FadeOut(head), run_time=0.6)

    ex = class_glyph("ship", s=0.95)
    excard = RoundedRectangle(width=2.4, height=2.4, corner_radius=0.14, stroke_color=MUTED,
                              stroke_width=2, fill_color=PANEL, fill_opacity=0.6).move_to(ex)
    left = VGroup(excard, ex).to_edge(LEFT, buff=1.3)
    inlab = txt("an image", fs=22, color=MUTED).next_to(left, DOWN, buff=0.25)

    fbox = chip("neural network", GOLD, w=2.7, h=1.4, fs=24, weight="BOLD")
    fbox.move_to(ORIGIN + DOWN * 0.05)
    flab = txt("a function  f", fs=22, color=GOLD).next_to(fbox, DOWN, buff=0.25)

    outs = VGroup(*[chip(n, CLASS_COLORS[i], w=2.0, h=0.62, fs=22)
                    for i, n in enumerate(("car", "plane", "ship"))]).arrange(DOWN, buff=0.3)
    outs.to_edge(RIGHT, buff=1.5)
    outlab = txt("one label", fs=22, color=MUTED).next_to(outs, DOWN, buff=0.25)

    a1 = arr(left.get_right(), fbox.get_left(), color=MUTED)
    a2 = arr(fbox.get_right(), outs.get_left(), color=GOLD)

    scene.play(FadeIn(left, shift=RIGHT * 0.2), FadeIn(inlab), run_time=0.7)
    scene.play(GrowArrow(a1), FadeIn(fbox), FadeIn(flab), run_time=0.7)
    scene.play(GrowArrow(a2), LaggedStart(*[FadeIn(o, shift=RIGHT * 0.15) for o in outs],
                                          lag_ratio=0.15, run_time=1.0), FadeIn(outlab))
    scene.beat(0.6)
    pick = SurroundingRectangle(outs[2], color=SHIP_C, buff=0.08, corner_radius=0.1)
    scene.play(Create(pick), run_time=0.6)
    scene.say("The whole job: turn an image into the one right label.", color=GOLD, hold=1.6)
    scene.beat(0.3)

    # ---------------------------------------------------------------- #
    # (e) but the network sees numbers, not pictures
    # ---------------------------------------------------------------- #
    scene.clear_cap(0.3)
    scene.play(FadeOut(VGroup(fbox, flab, outs, outlab, a1, a2, pick, inlab)), run_time=0.6)
    scene.play(left.animate.move_to(LEFT * 3.6 + UP * 0.2), run_time=0.7)

    px = pixel_grid(DATA.gal_ship[0] if DATA is not None else np.zeros((IN, IN)),
                    cell=0.135).move_to(RIGHT * 0.5 + UP * 0.2)
    a = arr(left.get_right(), px.get_left(), color=MUTED)
    plab = txt(f"{IN} × {IN}  =  {NIN} numbers", fs=24, color=INK).next_to(px, DOWN, buff=0.3)
    scene.play(GrowArrow(a), FadeIn(px), run_time=0.8)
    scene.play(FadeIn(plab, shift=UP * 0.1), run_time=0.6)
    scene.say("But the network never sees a ship. It sees pixels. Just numbers.",
              color=INK, hold=1.8)
    scene.beat(0.4)
    setup = txt(f"So how does it turn {NIN} numbers into the right label?",
                fs=30, color=GOLD, weight="BOLD").to_edge(DOWN, buff=0.5)
    scene.clear_cap(0.2)
    scene.play(Write(setup), run_time=1.2)
    scene.beat(0.5)
    scene.settle()
    scene.wipe()


class Task(NNBase):
    def construct(self):
        build_task(self)
