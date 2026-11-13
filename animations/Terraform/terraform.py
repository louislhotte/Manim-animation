"""Terraform: how a text file becomes real infrastructure.

A film made to be narrated: the picture carries the explanation, captions are few,
short and slow, and every beat lasts as long as its voice-over line takes to say
(``VOICEOVER.md`` is the timed script, generated from the render).

STORYBOARD (one line per scene: question | hero visual | what moves | takeaway)

    1 apply     What does Terraform do?
                | [3D] the file (five folded blocks) beside an empty cloud region
                | each block declares a ghost on the stage; ``terraform apply``
                  fills the ghosts with real resources, in dependency order
                | Infrastructure as code: the file is the source of truth.
    2 blocks    What is in the file?
                | the real main.tf in an editor that folds; one block opens
                | keyword, type, name and arguments are picked out (``count = 2``
                  declares ``web[0]`` and ``web[1]``); the block's picture builds
                  beside it; the script nobody writes any more fades; the provider
                  turns the five blocks into five API calls
                | You declare the result. Terraform works out the steps.
    3 graph     How does it know the order?
                | the file with its references drawn as arcs, then the same five
                  blocks as a dependency graph
                | a reference is picked apart; the blocks change places and the
                  arcs follow; every line becomes a node; apply walks the graph
                  wave by wave, in parallel; destroy walks it backwards
                | The graph decides the order, not the file.
    4 plan      How does it know what to do, and what it did?
                | one table, three columns: code, state, cloud
                | plan marks six rows ``+``; apply fills the cloud column, then
                  each id travels back into the state column; apply again: no changes
                | The state maps every block to a real object.
    5 change    How do I change the infrastructure?
                | [3D] the file beside the stage: ghost = declared, solid = real
                | 2 becomes 3 (one ``+``), a bigger instance type (three ``~``,
                  the servers grow), a new image (three ``-/+``, they are replaced)
                | Change the file. The plan shows only the difference.
    6 drift     What if someone changes the cloud by hand?
                | [3D] one server outgrows its ghost after a console click
                | plan scans the stage, finds the mismatch, apply shrinks it back
                | Every plan first reads the real resources.
    7 team      How do several people share this?
                | the state file inside a shared bucket, two terminals below
                | the state moves from a laptop to the bucket; with the lock file
                  on, Ada and Bob apply at once: one gets the lock, the other is
                  refused
                | The state is shared, and locked while someone applies.
    8 envs      How do I reuse it?
                | [3D] three islands: dev, staging, prod, from one module
                | the number of servers becomes the module's input; the editor tabs
                  through three calls (1, 2, 4 servers); each island rises from the
                  same code and hangs out its own state file
                | Same code, three environments.

Persistent motif: the five resources of ``demo/main.tf`` (a VPC, a subnet, a
security group, two servers, a bucket), one colour each, as blocks of code, graph
nodes, table rows and solids on the 3D stage; and the pair ghost / solid: what the
file declares against what really exists.

Data: nothing is typed in. ``sim.py`` parses ``demo/main.tf``, derives the graph
from its references and computes every plan, apply order, id and count shown; the
scenes assert the facts they state. It is a model, not a run: no Terraform binary
and no cloud account were used (ids are random, durations are typical orders of
magnitude), and the film says so on screen. Output lines follow the Terraform
CLI's wording.

Pacing: ``tell(caption, vo)`` starts a beat that lasts at least as long as the
voice-over line takes at ``WPS`` words per second; ``cue("phrase")`` waits until
the narrator reaches that phrase, so the picture changes on the right word.
``MX_TRACE_DIR=<dir>`` saves the timings ``tools/voiceover.py`` turns into the
script. Scenes render alone (``./render.sh blocks --quick --check``); the film is a
stitch of 2D and 3D scenes (``./render.sh full``). ``TF_QUICK=1`` collapses holds.
"""

from __future__ import annotations

import os
import re

import numpy as np
from kit import *
from manimx import *
from stage import *

import sim

# ---- the story, computed by sim.py (see its asserts) -------------------------- #
CONFIG = sim.CONFIG
ADDRESSES = sim.ADDRESSES  # the five blocks, in file order
KEYS = {  # block address -> the parts of the 3D stage it declares
    "aws_vpc.main": ["vpc"],
    "aws_subnet.public": ["subnet"],
    "aws_security_group.web": ["sg"],
    "aws_instance.web": ["web0", "web1"],
    "aws_s3_bucket.assets": ["bucket"],
}


KIND_C_OF = {  # the colour of each part of the stage
    "vpc": VPC_C, "subnet": SUBNET_C, "sg": SG_C, "bucket": BUCKET_C,
    "web0": SERVER_C, "web1": SERVER_C, "web2": SERVER_C, "web3": SERVER_C,
}  # fmt: skip


def stage_key(address):
    """``aws_instance.web[1]`` -> ``web1`` (the part of the stage it is)."""
    if address.startswith("aws_instance.web["):
        return "web" + address[len("aws_instance.web[") : -1]
    return KEYS[address][0]


def waves_of(events):
    """Apply events grouped by start time: what Terraform ran at the same moment."""
    out: dict[int, list] = {}
    for e in events:
        out.setdefault(e.t0, []).append(e)
    return [out[t] for t in sorted(out)]


FIRST_WAVES = waves_of(sim.FIRST.events)
assert [[stage_key(e.address) for e in w] for w in FIRST_WAVES] == [
    ["bucket", "vpc"],
    ["subnet", "sg"],
    ["web0", "web1"],
]

HUD_W = 6.62  # the width of the left column in the 3D scenes
HUD_X = -6.75 + HUD_W / 2
STAGE_ZONE = (-6.75 + HUD_W + 0.22, 6.84, -2.75, 3.25)  # the screen right of the column


def wrap_words(s, cols):
    """Break a long terminal line at spaces, the way a narrow terminal would."""
    out, cur = [], ""
    for w in s.split(" "):
        if cur and len(cur) + 1 + len(w) > cols:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    return [*out, cur]


def flow(a, b, bend=0.5):
    """A smooth left-to-right connector between two points (horizontal tangents)."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    dx = (b[0] - a[0]) * bend
    return CubicBezier(a, a + [dx, 0, 0], b - [dx, 0, 0], b)


def mono_chip(text, color, fs=17, h=0.5, w=None, fill=0.14, extra=None):
    """A tinted chip with monospaced text (an API call, a provider name)."""
    label = txt(text, fs=fs, color=INK, font=MONO)
    row = VGroup(label)
    if extra:
        row.add(txt(extra, fs=fs, color=color, weight="BOLD", font=MONO))
        row.arrange(RIGHT, buff=0.14)
    box = RoundedRectangle(
        width=w or row.width + 0.44,
        height=h,
        corner_radius=0.12,
        stroke_color=color,
        stroke_width=2.2,
        fill_color=color,
        fill_opacity=fill,
    )
    row.move_to(box)
    g = VGroup(box, row)
    g.box = box
    return g


def labelled_brace(target, label, sub, color=MUTED):
    """A brace under ``target`` with a word and a smaller gloss below it."""
    br = Brace(target, DOWN, buff=0.07, color=color, sharpness=1.2)
    br.set_stroke(width=0)
    word = txt(label, fs=20, color=INK, weight="BOLD")
    word.next_to(br, DOWN, buff=0.10)
    gloss = txt(sub, fs=16, color=MUTED)
    gloss.next_to(word, DOWN, buff=0.08)
    return VGroup(br, word, gloss)


class _Common(ExplainerMixin):
    """What the 2D and the 3D scenes share. Pacing is the house's narrated-beat
    pacing (``tell`` / ``cue`` / ``hold`` in manimx), at ``WPS`` words per second."""

    pace = Pace.from_env("TF", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "Terraform"
    SUBTITLE = "How a text file becomes real infrastructure"
    TAGLINE = "infrastructure as code: plan, apply, state"
    RECAP = "Describe what you want. Review the plan. Let the cloud match the file."
    TRACE_ENV = "TF_TRACE"
    # the narrator's pace, in words per second: 2.3 = 138 words a minute, unhurried.
    # TF_WPS=2.0 re-paces the whole film for a slower voice.
    WPS = float(os.environ.get("TF_WPS", 2.3))
    VO_PAD = 1.1  # a breath between two lines (the house default is 0.8 s)

    # ---- captions: fewer, bigger, slower (the film is narrated) --------------- #
    def say(self, text, color=INK, fs=27, y=CAPTION_Y, weight="MEDIUM"):
        m = txt(text, fs=fs, color=color, weight=weight)
        clamp_width(m, CAPTION_W)
        m.move_to([0, y, 0])
        return m

    def settle(self, ambient=None):
        """End of a scene: what is left of the narration, and at least a breath on
        the finished picture."""
        self.hold(extra=0.5, floor=0.3 if self.pace.quick else 1.3, ambient=ambient)

    def over_card(self, vo):
        """A line to say over a title card (it has no caption of its own)."""
        self.narrate(vo, need=len(vo.split()) / self.WPS + self.VO_PAD)

    def header(self, label, color=GOLD):
        h = self.pin(self.section_header(label, color))
        self.play(FadeIn(h, shift=DOWN * 0.2), run_time=0.5)
        return h

    def note(self, s):
        """The small source line at the bottom edge (what is real, what is a model)."""
        c = self.pin(self.cite(s))
        c.set_z_index(20)
        return c

    def intro_emblem(self):
        """The five resources, as flat icons, at the end of the title rule."""
        g = VGroup(*[res_icon(k, s=0.30) for k in KIND_C]).arrange(RIGHT, buff=0.12)
        pad = Rectangle(
            width=g.width + 0.4, height=0.1, stroke_opacity=0, fill_opacity=0
        )  # the card centres this box on the rule's end: the icons sit right of it
        return VGroup(g, pad.next_to(g, LEFT, buff=0))


class _Base(_Common, Scene):
    """A flat scene."""

    def editor(self, n=12, left=-6.75, top=2.30, fs=18):
        """The folding editor with the film's main.tf; returns (panel, folds)."""
        p = TextPanel(cols=39, n=n, title="main.tf", fs=fs)
        for b in CONFIG:
            p.block(b.lines)
        p.move_to([left + p.w0 / 2, top - p.h0 / 2, 0])
        p.refresh()
        return p, dict(zip(ADDRESSES, p.folds, strict=True))

    # ====================================================================== #
    # 2 · Say what, not how
    # ====================================================================== #
    def scene_blocks(self):
        self.header("2 · Say what, not how", LILAC)
        p, folds = self.editor()
        inst = folds["aws_instance.web"]
        x0, x1 = p.bg.get_right()[0] + 0.45, 6.75  # the zone right of the editor
        xm = (x0 + x1) / 2

        # -- one block: keyword, type, name, arguments ---------------------------- #
        self.play(
            FadeIn(p, shift=RIGHT * 0.2),
            self.tell(
                "One block declares a resource: a type, a name, its arguments.",
                "Open one block. The keyword resource means: this should exist. Then "
                "its type, an AWS server, and a name you choose. Inside, its "
                "arguments. Count equals two: this one block declares two servers, "
                "web zero and web one. Then their image, their size, their subnet "
                "and their firewall.",
            ),
            run_time=0.8,
        )
        self.cue("Open one block")
        self.play(
            Tween(inst, open=1.0, run_time=0.9), Tween(p, scroll=2.0, run_time=0.9)
        )
        big = Row(CONFIG[3].lines[0], 22)
        big.mob.move_to([xm, 1.95, 0])
        self.cue("The keyword resource")
        self.play(FadeIn(big.mob, shift=RIGHT * 0.4, scale=0.9), run_time=0.6)
        parts = [
            ("The keyword resource", "resource", "keyword", "this should exist"),
            ("its type", '"aws_instance"', "type", "an AWS server"),
            ("a name you choose", '"web"', "name", "yours to choose"),
        ]
        braces = VGroup(*[labelled_brace(big.span(t), w, g) for _, t, w, g in parts])
        base = min(b[1].get_center()[1] for b in braces)  # the words share a line
        for b in braces:
            b[1:].shift(UP * (base - b[1].get_center()[1]))
        for (phrase, *_), b in zip(parts, braces, strict=True):
            self.cue(phrase)
            self.play(
                GrowFromCenter(b[0]), FadeIn(b[1:], shift=DOWN * 0.1), run_time=0.5
            )

        # the block's picture, built argument by argument
        body = inst.body
        servers = VGroup(*[res_icon("aws_instance", s=0.9) for _ in range(2)])
        servers.arrange(RIGHT, buff=1.4).move_to([xm, -0.92, 0])
        names = VGroup(
            *[txt(f"web[{i}]", fs=18, color=INK, font=MONO).next_to(sv, UP, buff=0.10)
              for i, sv in enumerate(servers)]
        )  # fmt: skip
        amis = VGroup(
            *[mono_chip("ami-0f3a91c2", MUTED, fs=16, h=0.38).next_to(sv, DOWN, buff=0.12)
              for sv in servers]
        )  # fmt: skip
        types = VGroup(
            *[mono_chip("t3.micro", SERVER_C, fs=16, h=0.38).next_to(a, DOWN, buff=0.08)
              for a in amis]
        )  # fmt: skip
        inner = VGroup(names, servers, amis, types)
        sg_box = SurroundingRectangle(inner, color=SG_C, buff=0.18, corner_radius=0.16)
        sg_box.set_stroke(SG_C, width=2.6)
        sub_box = SurroundingRectangle(
            sg_box, color=SUBNET_C, buff=0.30, corner_radius=0.2
        )
        sub_box.set_stroke(SUBNET_C, width=2.6).set_fill(SUBNET_C, opacity=0.07)
        sub_tag = plate(txt("aws_subnet.public", fs=16, color=REF_C, font=MONO), op=1.0)
        sub_tag.move_to(sub_box.get_corner(UL) + RIGHT * (sub_tag.width / 2 + 0.25))
        sg_tag = plate(
            txt("aws_security_group.web", fs=16, color=REF_C, font=MONO), op=1.0
        )
        sg_tag.move_to(sg_box.get_corner(DR) + LEFT * (sg_tag.width / 2 + 0.2))
        picture = VGroup(sub_box, sg_box, inner, sub_tag, sg_tag)
        picture.move_to([xm, -1.17, 0])
        steps = [  # (the narrator's word, the lines it is about, what they draw)
            ("Count equals two", (body[0], body[0]),
             [FadeIn(sv, shift=UP * 0.15) for sv in servers]),
            ("web zero", None, [FadeIn(names[0], shift=DOWN * 0.1)]),
            ("web one", None, [FadeIn(names[1], shift=DOWN * 0.1)]),
            ("their image", (body[1], body[1]),
             [FadeIn(a, shift=UP * 0.1) for a in amis]),
            ("their size", (body[2], body[2]),
             [FadeIn(t, shift=UP * 0.1) for t in types]),
            ("their subnet", (body[3], body[3]), [Create(sub_box), FadeIn(sub_tag)]),
            ("their firewall", (body[5], body[7]), [Create(sg_box), FadeIn(sg_tag)]),
        ]  # fmt: skip
        self.cue("Inside, its arguments")
        whole = p.bar_over(body[0], body[-1], op=0.10)
        self.play(Tween(whole, alpha=1.0, run_time=0.4))
        bar = whole
        for phrase, rows, anims in steps:
            self.cue(
                phrase,
                ambient=(lambda t: [Throb(servers, t, amp=0.05, period=1.3)])
                if phrase == "web zero"
                else None,
            )
            if rows is None:
                self.play(*anims, run_time=0.4)
                continue
            new = p.bar_over(*rows, op=0.17)
            self.play(
                Tween(new, alpha=1.0, run_time=0.25),
                Tween(bar, alpha=0.0, run_time=0.25),
                *anims,
                run_time=0.55,
            )
            bar = new
        self.hold()

        # -- no steps: the provider turns blocks into API calls --------------------- #
        self.play(
            self.tell(
                "You declare the result. Terraform works out the steps.",
                "Notice what is missing: steps. You never write create this, wait "
                "for that, then launch. You declare the result, and Terraform works "
                "out the API calls.",
            ),
            FadeOut(VGroup(picture, braces, big.mob), shift=RIGHT * 0.3, run_time=0.5),
            Tween(bar, alpha=0.0, run_time=0.3),
        )
        self.play(
            Tween(inst, open=0.0, run_time=0.8),
            Tween(p, scroll=0.0, n=5.0, run_time=0.8),
        )
        # what you would write by hand: a script of steps (real AWS CLI verbs)
        script = TextPanel(
            cols=39, n=6, title="deploy.sh  (by hand)", fs=16, kind="terminal",
            pitch=0.295, bar_h=0.36, w=p.w0,
        )  # fmt: skip
        steps_ = script.lines(
            [
                "VPC=$(aws ec2 create-vpc ...)",
                "aws ec2 wait vpc-available ...",
                "aws ec2 create-subnet --vpc-id $VPC ...",
                "aws ec2 create-security-group ...",
                "aws ec2 run-instances --count 2 ...",
                "aws s3api create-bucket ...",
            ],
            vis=1.0,
            colors=shell_colors,
        )
        for r in steps_:
            r.alpha = 0.0
        script.move_to(
            [p.bg.get_center()[0], p.bg.get_bottom()[1] - 0.18 - script.h0 / 2, 0]
        )
        script.refresh()
        self.cue("steps")
        self.play(
            FadeIn(script, shift=UP * 0.15, run_time=0.5),
            LaggedStart(
                *[Tween(r, alpha=1.0, run_time=0.3) for r in steps_], lag_ratio=0.5
            ),
        )
        for phrase, r in (
            ("create this", steps_[0]),
            ("wait for that", steps_[1]),
            ("then launch", steps_[4]),
        ):
            assert phrase.split()[0] in r.text or "run-instances" in r.text
            self.cue(phrase)
            at = script.bar_over(r, color=INK, op=0.13)
            self.play(
                Succession(
                    Tween(at, alpha=1.0, run_time=0.25),
                    Wait(0.3),
                    Tween(at, alpha=0.0, run_time=0.3),
                )
            )
        heads = [folds[a].head for a in ADDRESSES]
        sweep = [p.bar_over(h, op=0.15) for h in heads]
        self.cue("You declare the result")
        self.play(
            *[Tween(r, alpha=0.42, run_time=0.6) for r in steps_],
            script.ttl.animate(run_time=0.6).set_opacity(0.6),
            LaggedStart(
                *[
                    Succession(
                        Tween(b, alpha=1.0, run_time=0.22),
                        Tween(b, alpha=0.0, run_time=0.4),
                    )
                    for b in sweep
                ],
                lag_ratio=0.4,
            ),
            run_time=1.5,
        )
        prov_label = Row('provider "aws"', 18).mob
        prov_sub = txt("a plugin", fs=16, color=MUTED)
        prov_in = VGroup(prov_label, prov_sub).arrange(DOWN, buff=0.10)
        prov_box = RoundedRectangle(
            width=prov_in.width + 0.5, height=prov_in.height + 0.44, corner_radius=0.16,
            stroke_color=LILAC, stroke_width=2.6, fill_color=PANEL, fill_opacity=1,
        )  # fmt: skip
        prov = VGroup(prov_box, prov_in).move_to(
            [x0 + prov_box.width / 2 + 0.35, 0.55, 0]
        )
        calls = VGroup()
        for b in CONFIG:
            n = len(b.instances())
            calls.add(
                mono_chip(sim.API_CALL[b.type], KIND_C[b.type], fs=17, h=0.5, w=3.05,
                          extra=f"×{n}" if n > 1 else None)
            )  # fmt: skip
        calls.arrange(DOWN, buff=0.22).move_to([x1 - 3.05 / 2, 0.35, 0])
        api = txt("AWS API", fs=18, color=MUTED, weight="BOLD")
        api.next_to(calls, UP, buff=0.22)
        xr = p.bg.get_right()[0]
        ins = [flow([xr, h.y, 0], prov_box.get_left() + UP * (0.22 - 0.11 * i))
               for i, h in enumerate(heads)]  # fmt: skip
        outs = [flow(prov_box.get_right() + UP * (0.22 - 0.11 * i), c.box.get_left())
                for i, c in enumerate(calls)]  # fmt: skip
        for path in (*ins, *outs):
            path.set_stroke(FAINT, width=2.2)
        self.cue("Terraform works out")
        self.play(FadeIn(prov, shift=LEFT * 0.2), FadeIn(api), run_time=0.5)
        self.play(
            LaggedStart(
                *[
                    AnimationGroup(
                        Succession(
                            Create(i_, run_time=0.35), Create(o_, run_time=0.35)
                        ),
                        Succession(
                            Wait(0.1),
                            Travel(glow_dot(KIND_C[b.type], r=0.06), i_, run_time=0.4),
                            Travel(glow_dot(KIND_C[b.type], r=0.06), o_, run_time=0.4),
                        ),
                        Succession(
                            Wait(0.75), FadeIn(c, shift=RIGHT * 0.15, run_time=0.3)
                        ),
                    )
                    for b, i_, o_, c in zip(CONFIG, ins, outs, calls, strict=True)
                ],
                lag_ratio=0.3,
            ),
        )

        def traffic(rt):  # calls keep flowing while the caption is read
            n = max(1, int(rt / 1.3))
            return [
                Succession(
                    *[
                        AnimationGroup(
                            *[
                                Succession(
                                    Wait(0.12 * k),
                                    Travel(
                                        glow_dot(KIND_C[b.type], r=0.055),
                                        i_,
                                        run_time=0.5,
                                    ),
                                    Travel(
                                        glow_dot(KIND_C[b.type], r=0.055),
                                        o_,
                                        run_time=0.5,
                                    ),
                                )
                                for k, (b, i_, o_) in enumerate(
                                    zip(CONFIG, ins, outs, strict=True)
                                )
                            ]
                        )
                        for _ in range(n)
                    ],
                    run_time=rt,
                )
            ]

        self.hold(ambient=traffic)

        # -- a provider speaks one API; there are thousands ---------------------------- #
        others = VGroup(
            *[mono_chip(n, MUTED, fs=17, h=0.46, w=prov_box.width)
              for n in ("azurerm", "google", "kubernetes")]
        )  # fmt: skip
        others.arrange(DOWN, buff=0.16).next_to(prov, DOWN, buff=0.34)
        more = txt("and thousands more", fs=18, color=MUTED)
        more.next_to(others, DOWN, buff=0.22)
        self.play(
            self.tell(
                "A provider is a plugin that speaks one platform's API.",
                "Those calls come from a provider, a plugin that speaks one API. "
                "There are providers for AWS, Azure, Google Cloud, Kubernetes, and "
                "thousands more.",
            )
        )
        self.cue("a provider")
        self.play(ripple(prov, color=LILAC, buff=0.10), run_time=0.8)
        self.cue("There are providers", ambient=traffic)
        for phrase, mob in (
            ("Azure", others[0]),
            ("Google Cloud", others[1]),
            ("Kubernetes", others[2]),
            ("thousands more", more),
        ):
            self.cue(phrase)
            self.play(FadeIn(mob, shift=UP * 0.12), run_time=0.4)
        self.add(self.note("Providers are listed on registry.terraform.io."))
        self.settle(ambient=traffic)
        self.wipe()

    # ====================================================================== #
    # 3 · References become a graph
    # ====================================================================== #
    def scene_graph(self):
        self.header("3 · References become a graph", SKY)
        p, folds = self.editor(n=5, left=-6.05, top=1.65)
        vpc, sub, sg, inst, bkt = (folds[a] for a in ADDRESSES)
        x0, x1 = p.bg.get_right()[0] + 0.5, 6.75
        xm = (x0 + x1) / 2

        # -- one block uses a value of another ------------------------------------- #
        self.play(
            FadeIn(p, shift=RIGHT * 0.2),
            self.tell(
                "A block can use a value from another block.",
                "Blocks can point at each other. The subnet needs the network's ID, "
                "which does not exist yet, so it references it. Terraform now knows "
                "the subnet depends on the network.",
            ),
            run_time=0.8,
        )
        self.cue("point at each other")
        self.play(
            Tween(vpc, open=1.0, run_time=0.9),
            Tween(sub, open=1.0, run_time=0.9),
            Tween(p, n=10.0, run_time=0.9),
        )
        ref_row = sub.body[0]
        assert ref_row.text.endswith("aws_vpc.main.id")
        bar = p.bar_over(ref_row, op=0.17)
        big = Row("aws_vpc.main.id", 30)
        big.mob.move_to([xm, 0.75, 0])
        self.cue("The subnet needs")
        b1 = labelled_brace(big.span("aws_vpc.main"), "a block", "the network")
        b2 = labelled_brace(big.span("id"), "its attribute", "set by the cloud")
        base = min(b[1].get_center()[1] for b in (b1, b2))  # the words share a line
        for b in (b1, b2):
            b[1:].shift(UP * (base - b[1].get_center()[1]))
        value = Row("= (known after apply)", 22, colors=term_colors)
        value.mob.next_to(VGroup(b1, b2), DOWN, buff=0.45)
        self.play(
            Tween(bar, alpha=1.0, run_time=0.3),
            FadeIn(big.mob, shift=RIGHT * 0.3, scale=0.9, run_time=0.6),
        )
        self.play(
            GrowFromCenter(b1[0]), FadeIn(b1[1:], shift=DOWN * 0.1),
            GrowFromCenter(b2[0]), FadeIn(b2[1:], shift=DOWN * 0.1),
            run_time=0.6,
        )  # fmt: skip
        self.cue("which does not exist yet")
        self.play(FadeIn(value.mob, shift=UP * 0.12), run_time=0.5)
        self.cue("so it references it")
        links = {
            ("aws_subnet.public", "aws_vpc.main"): p.link(
                ref_row, vpc.head, VPC_C, lane=0
            ),
        }
        self.play(
            Tween(links["aws_subnet.public", "aws_vpc.main"], grow=1.0, run_time=0.9)
        )
        self.cue("Terraform now knows")
        p.anchor()  # the folded file moves to the middle of the frame: it is the hero
        self.play(
            Tween(vpc, open=0.0, run_time=0.9),
            Tween(sub, open=0.0, run_time=0.9),
            Tween(p, n=5.0, px=0.3, py=1.2, run_time=0.9),
            Tween(bar, alpha=0.0, run_time=0.3),
            FadeOut(
                VGroup(big.mob, b1, b2, value.mob), shift=RIGHT * 0.3, run_time=0.5
            ),
        )
        # the other references of the file, straight from the parsed blocks
        lane = {("aws_security_group.web", "aws_vpc.main"): 1,
                ("aws_instance.web", "aws_security_group.web"): 0,
                ("aws_instance.web", "aws_subnet.public"): 2}  # fmt: skip
        for b in CONFIG:
            for dep in sim.GRAPH[b.address]:
                if (b.address, dep) not in links:
                    links[b.address, dep] = p.link(
                        folds[b.address].head, folds[dep].head,
                        KIND_C[sim.rtype(dep)], lane=lane[b.address, dep],
                    )  # fmt: skip
        assert len(links) == sum(len(v) for v in sim.GRAPH.values()) == 4
        rest = [
            v for k, v in links.items() if k != ("aws_subnet.public", "aws_vpc.main")
        ]
        self.play(
            LaggedStart(
                *[Tween(ln, grow=1.0, run_time=0.8) for ln in rest], lag_ratio=0.45
            )
        )
        self.hold(
            ambient=lambda t: [  # the arcs breathe, one after the other
                LaggedStart(
                    *[
                        Breathe(
                            ln, t * 0.7, attr="alpha", lo=0.35, hi=1.0, period=t * 0.7
                        )
                        for ln in links.values()
                    ],
                    lag_ratio=0.25,
                    run_time=t,
                )
            ]
        )

        # -- the file's order does not matter: the graph does ------------------------ #
        self.play(
            self.tell(
                "References become a dependency graph. It sets the order.",
                "The order of the blocks in the file does not matter. From the "
                "references, Terraform builds a dependency graph, and the graph decides.",
            )
        )
        self.cue("The order of the blocks")
        self.play(p.reorder([inst, sub, bkt, sg, vpc], run_time=1.3))

        def still_linked(rt):  # the arcs followed their blocks: they light in turn
            return [
                LaggedStart(
                    *[
                        Breathe(
                            ln, rt * 0.6, attr="alpha", lo=0.3, hi=1.0, period=rt * 0.6
                        )
                        for ln in links.values()
                    ],
                    lag_ratio=0.3,
                    run_time=rt,
                )
            ]

        # the same five blocks as nodes, ranked by what they need
        W, H = 4.65, 0.9
        spot = {
            "aws_vpc.main": (-2.0, 1.6),
            "aws_s3_bucket.assets": (4.4, 1.6),
            "aws_subnet.public": (-4.4, 0.0),
            "aws_security_group.web": (0.45, 0.0),
            "aws_instance.web": (-2.0, -1.6),
        }
        for a, (_, y) in spot.items():  # a row of the picture per rank of the graph
            assert abs(y - (1.6 - 1.6 * sim.RANKS[a])) < 1e-9
        cards = {}
        for b in CONFIG:
            c = ResCard(b.address, b.type, w=W, h=H, fs=17, n=len(b.instances()))
            c.move_to([*spot[b.address], 0])
            cards[b.address] = c
        edges = {}
        for a, dep in links:
            e = Line(
                cards[dep].point(DOWN),
                cards[a].point(UP),
                stroke_color=MUTED,
                stroke_width=3,
            )
            e.set_z_index(-1)
            edges[a, dep] = e
        self.cue("From the references", ambient=still_linked)
        block_of = {id(f): a for a, f in folds.items()}
        leaving = [cards[block_of[id(f)]] for f in p.folds]  # in the file's order now
        for f, c in zip(p.folds, leaving, strict=True):
            c.save_state()  # every card grows out of its line of the file
            c.scale(0.3).move_to(p.row_point(f.head, col=14)).set_opacity(0.0)
        self.play(
            FadeOut(p, run_time=0.4),
            LaggedStart(*[Restore(c, run_time=0.9) for c in leaving], lag_ratio=0.14),
        )
        for c in cards.values():
            c.refresh()
        self.play(
            LaggedStart(*[Create(e) for e in edges.values()], lag_ratio=0.2),
            run_time=1.0,
        )
        self.cue("the graph decides")
        for r in range(max(sim.RANKS.values()) + 1):
            row = [cards[a] for a in ADDRESSES if sim.RANKS[a] == r]
            self.play(*[Tween(c, lit=1.0, run_time=0.3) for c in row])
        self.hold()

        # -- apply walks the graph, in parallel where it can ------------------------- #
        strip = TextPanel(cols=20, n=1, title="", fs=18, kind="terminal", bar_h=0.0)
        strip.move_to([4.8, 0.0, 0])
        cmd = strip.command("terraform apply")
        strip.refresh()
        par = mono_chip("-parallelism=10", MUTED, fs=18, h=0.5)
        par_note = txt("up to 10 at once, by default", fs=19, color=MUTED)
        VGroup(par, par_note).arrange(DOWN, buff=0.16).move_to([4.75, -1.6, 0])
        assert sim.PARALLELISM == 10
        self.play(
            self.tell(
                "Apply walks the graph, building in parallel where it can.",
                "That is what apply did at the start: it walked the graph. Whatever "
                "has no pending dependency is created at once, in parallel: the "
                "network and the bucket, then the subnet and the firewall, then both "
                "servers.",
            ),
            FadeIn(strip, shift=LEFT * 0.2),
        )
        self.cue("it walked the graph")
        self.play(strip.type(cmd, cps=13))
        self.cue("Whatever has no pending dependency")
        roots = [cards[a] for a in ADDRESSES if not sim.GRAPH[a]]
        assert [c.address for c in roots] == ["aws_vpc.main", "aws_s3_bucket.assets"]
        self.play(*[ripple(c, color=GOLD, buff=0.08, run_time=1.0) for c in roots])
        self.cue(
            "in parallel",
            ambient=lambda t: [Throb(c, t, amp=0.045, period=1.1) for c in roots],
        )
        self.play(
            FadeIn(par, shift=UP * 0.1), FadeIn(par_note, shift=UP * 0.1), run_time=0.5
        )
        secs = sim.SECONDS["create"]
        film = lambda t: min(2.2, 0.45 * t)  # noqa: E731  seconds of film per wave
        for phrase, wave in zip(
            ("the network and the bucket", "then the subnet", "then both servers"),
            sim.WAVES,
            strict=True,
        ):
            self.cue(phrase)
            run = [
                Succession(
                    Tween(
                        cards[a],
                        run_time=film(secs[sim.rtype(a)]),
                        rate_func=linear,
                        prog=1.0,
                    ),
                    Tween(cards[a], run_time=0.25, done=1.0),
                )
                for a in wave
            ]
            self.play(*run)
            out = [e for (a, dep), e in edges.items() if dep in wave]
            if out:  # what was waiting on them may start
                self.play(
                    *[
                        e.animate(run_time=0.4).set_stroke(GOOD, opacity=0.9)
                        for e in out
                    ],
                    *[Travel(glow_dot(GOOD, r=0.06), e, run_time=0.45) for e in out],
                )

        def downstream(rt):  # what was built keeps feeding what depends on it
            n = max(1, round(rt / 1.4))
            order = sorted(cards, key=lambda a: sim.RANKS[a])
            return [
                Succession(
                    *[
                        LaggedStart(
                            *[Travel(glow_dot(GOOD, r=0.07), e, run_time=0.7)
                              for e in edges.values()],
                            lag_ratio=0.25,
                        )
                        for _ in range(n)
                    ],
                    run_time=rt,
                ),
                LaggedStart(
                    *[Throb(cards[a], rt * 0.5, amp=0.035, period=rt * 0.5) for a in order],
                    lag_ratio=0.3,
                    run_time=rt,
                ),
            ]  # fmt: skip

        self.hold(ambient=downstream)

        # -- destroy walks it backwards ------------------------------------------------ #
        self.play(
            self.tell(
                "Destroy walks the same graph in reverse.",
                "And terraform destroy walks the same graph in reverse, so nothing "
                "is removed while something still depends on it.",
            ),
            FadeOut(VGroup(par, par_note), run_time=0.4),
        )
        self.cue("terraform destroy")
        self.play(Retype(strip, cmd, "$ terraform destroy", run_time=0.7))
        for phrase, wave in zip(
            ("in reverse", "so nothing is removed", "still depends on it"),
            reversed(sim.WAVES),
            strict=True,
        ):
            # the bucket depends on nothing and nothing depends on it: it goes first
            now = [a for a in wave if a != "aws_s3_bucket.assets"]
            if wave is sim.WAVES[-1]:
                now.append("aws_s3_bucket.assets")
            gone = [e for (a, dep), e in edges.items() if a in now]
            self.cue(phrase)
            self.play(
                *[Tween(cards[a], run_time=1.0, gone=1.0) for a in now],
                *[e.animate(run_time=0.7).set_stroke(FAINT, opacity=0.5) for e in gone],
            )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 4 · Plan, apply, state
    # ====================================================================== #
    def scene_plan(self):
        self.header("4 · Plan, apply, state", GOOD)
        first = sim.FIRST
        addrs = [a for b in CONFIG for a in b.instances()]  # six rows, in file order
        assert len(addrs) == 6 and set(addrs) == set(first.state)

        # the command line, and three windows: what you want, what Terraform
        # remembers, what exists
        strip = TextPanel(cols=77, n=2, title="", fs=16, kind="terminal", bar_h=0.0)
        strip.move_to([0, 2.02, 0])
        init = strip.command("terraform init")
        strip.refresh()
        top, pitch, bar_h = 1.28, 0.585, 0.40
        h = bar_h + 6 * pitch + 0.30
        geo = (("main.tf", "desired", -6.75, 4.6), ("terraform.tfstate", "recorded", -1.6, 4.2),
               ("AWS  eu-west-3", "real", 3.15, 3.6))  # fmt: skip
        wins = []
        for title, role, x, w in geo:
            win = window(w, h, title, role=role, bar_h=bar_h, lights=False)
            win.move_to([x + w / 2, top - h / 2, 0])
            wins.append(win)
        w_code, w_state, w_cloud = wins
        ys = [top - bar_h - 0.15 - (i + 0.5) * pitch for i in range(6)]
        code_cells, state_cells, cloud_cells, badges, oks, slots = (
            [],
            [],
            [],
            [],
            [],
            [],
        )
        for a, y in zip(addrs, ys, strict=True):
            kind = sim.rtype(a)
            ic = res_icon(kind, s=0.34).move_to([w_code.bg.get_left()[0] + 0.42, y, 0])
            lab = txt(a, fs=17, color=INK, font=MONO)
            lab.next_to(ic, RIGHT, buff=0.2).set_y(y)
            code_cells.append(VGroup(ic, lab))
            oid = first.state[a]["id"]
            sid = txt(sim.short(oid), fs=16, color=INK, font=MONO)
            sid.move_to([w_state.bg.get_left()[0] + 0.3 + sid.width / 2, y, 0])
            state_cells.append(sid)
            dash = Line(
                [w_state.bg.get_left()[0] + 0.3, y, 0],
                [w_state.bg.get_left()[0] + 1.3, y, 0],
            )
            dash.set_stroke(FAINT, width=2.5)
            slots.append(dash)
            ci = res_icon(kind, s=0.40).move_to([w_cloud.bg.get_left()[0] + 0.45, y, 0])
            cid = txt(sim.short(oid), fs=16, color=MUTED, font=MONO)
            cid.next_to(ci, RIGHT, buff=0.2).set_y(y)
            cloud_cells.append(VGroup(ci, cid))
            gap_x = (w_code.bg.get_right()[0] + w_state.bg.get_left()[0]) / 2
            badges.append(plan_badge("+", s=0.34).move_to([gap_x, y, 0]))
            oks.append(make_tick(GOOD, sw=4.5, scale=0.5).move_to([gap_x, y, 0]))
        link_x = (w_state.bg.get_right()[0] + w_cloud.bg.get_left()[0]) / 2
        links = [
            Line(
                [link_x - 0.22, y, 0],
                [link_x + 0.22, y, 0],
                stroke_color=GOOD,
                stroke_width=3,
            )
            for y in ys
        ]

        def band(i, color=GOLD, op=0.10):  # a highlight across the three windows
            r = RoundedRectangle(
                width=w_cloud.bg.get_right()[0] - w_code.bg.get_left()[0] - 0.16,
                height=pitch * 0.9, corner_radius=0.08, stroke_width=0,
                fill_color=color, fill_opacity=op,
            )  # fmt: skip
            return r.move_to(
                [(w_cloud.bg.get_right()[0] + w_code.bg.get_left()[0]) / 2, ys[i], 0]
            )

        # -- init, then plan: a preview ----------------------------------------- #
        self.play(
            FadeIn(strip, shift=DOWN * 0.15),
            FadeIn(w_code, shift=UP * 0.15),
            FadeIn(VGroup(*code_cells), run_time=0.9),
            self.tell(
                "terraform plan previews every change before it happens.",
                "Now the same run again, one step at a time. First, terraform init "
                "downloads the provider. Then, before touching anything, terraform "
                "plan compares what you declared with what exists: six resources to "
                "add. It is a preview, like a diff.",
            ),
            run_time=0.9,
        )
        # what you want, then what Terraform remembers, then what really exists
        self.cue("again")
        self.play(
            FadeIn(w_state, shift=UP * 0.15), FadeIn(VGroup(*slots)), run_time=0.7
        )
        self.cue("at a time")
        self.play(FadeIn(w_cloud, shift=UP * 0.15), run_time=0.7)
        self.cue("First, terraform init")
        self.play(strip.type(init, cps=13))
        ok = strip.lines(["Terraform has been successfully initialized!"], vis=0.0,
                         colors=lambda t: [ADD_C] * len(t))  # fmt: skip
        self.play(strip.show(ok))
        self.cue("terraform plan compares")
        cmd = strip.command("terraform plan", vis=0.0)
        self.play(strip.show([cmd]))
        self.play(strip.type(cmd, cps=13))
        self.cue("what you declared")
        scan = band(0)
        self.play(FadeIn(scan), run_time=0.25)
        for i in range(6):
            self.play(
                scan.animate.move_to(band(i)),
                self.then(FadeIn(badges[i], scale=1.6, run_time=0.25), 0.1),
                run_time=0.36,
            )
        self.play(FadeOut(scan), run_time=0.25)
        assert first.plan.count("create") == 6
        self.cue("six resources to add")
        summary = strip.lines([first.plan.summary], vis=0.0)
        self.play(strip.show(summary))
        self.hold(ambient=lambda t: [Throb(b, t, amp=0.16, period=1.3) for b in badges])

        # -- apply: make the calls, record the ids --------------------------------- #
        self.play(
            self.tell(
                "terraform apply makes the calls and records what it created.",
                "terraform apply then makes those calls. And for each resource, it "
                "records the ID of the real object in a file called the state.",
            )
        )
        cmd = strip.command("terraform apply", vis=0.0)
        self.play(strip.show([cmd]))
        self.play(strip.type(cmd, cps=13))
        self.cue("makes those calls")
        row_of = {a: i for i, a in enumerate(addrs)}
        log = None  # the last line of the log: it changes as each wave completes
        for wave in FIRST_WAVES:
            idx = [row_of[e.address] for e in wave]
            calls = []
            for i in idx:
                path = Line(code_cells[i].get_right() + RIGHT * 0.15,
                            cloud_cells[i][0].get_left() + LEFT * 0.1)  # fmt: skip
                calls.append(
                    Travel(
                        glow_dot(KIND_C[sim.rtype(addrs[i])], r=0.07),
                        path,
                        run_time=0.6,
                    )
                )
            self.play(
                *calls,
                *[
                    self.then(FadeIn(cloud_cells[i], scale=1.25, run_time=0.35), 0.5)
                    for i in idx
                ],
                *[
                    self.then(FadeOut(badges[i], scale=0.6, run_time=0.3), 0.5)
                    for i in idx
                ],
            )
            last = max(wave, key=lambda e: (e.t1, e.address))  # the wave's last line
            if log is None:
                log = strip.line(last.done_line, vis=0.0)
                self.play(strip.show([log]))
            else:
                self.play(Retype(strip, log, last.done_line, run_time=0.6))
        assert log.text == sim.FIRST.events[-1].done_line
        self.cue("it records the ID")
        moves = []
        for i in range(6):
            # the id leaves the cloud column (from the left of its icon) for the state
            ghost = state_cells[i].copy()
            ghost.scale(0.4).move_to(cloud_cells[i][0].get_left() + LEFT * 0.2)
            ghost.set_opacity(0.0)
            moves.append(
                AnimationGroup(
                    Succession(
                        ghost.animate(run_time=0.6)
                        .scale(1 / 0.4)
                        .move_to(state_cells[i])
                        .set_opacity(1.0),
                        FadeOut(ghost, run_time=0.01),
                    ),
                    FadeOut(slots[i], run_time=0.3),
                    self.then(FadeIn(state_cells[i], run_time=0.2), 0.55),
                    self.then(Create(links[i], run_time=0.3), 0.6),
                )
            )
        self.play(LaggedStart(*moves, lag_ratio=0.18))
        model = self.note(
            "A model of Terraform, not a recorded run: example ids, abridged log."
        )
        self.play(
            strip.show(strip.lines([first.summary], vis=0.0)),
            FadeIn(model, run_time=0.5),
        )

        def pointing(rt):  # every recorded id points at its real object
            n = max(1, round(rt / 1.5))
            paths = [
                Line(state_cells[i].get_right() + RIGHT * 0.12,
                     cloud_cells[i][0].get_left() + LEFT * 0.06)
                for i in range(6)
            ]  # fmt: skip
            return [
                Succession(
                    *[
                        LaggedStart(
                            *[
                                Travel(glow_dot(GOOD, r=0.055), q, run_time=0.6)
                                for q in paths
                            ],
                            lag_ratio=0.2,
                        )
                        for _ in range(n)
                    ],
                    run_time=rt,
                )
            ]

        self.hold(ambient=pointing)

        # -- the state: this block is that object -------------------------------------- #
        k = row_of["aws_instance.web[0]"]
        focus = band(k, op=0.13)
        ring_state = SurroundingRectangle(
            w_state.bg, color=GOLD, buff=0.05, corner_radius=0.16
        )
        ring_state.set_stroke(GOLD, width=3.5)
        self.play(
            self.tell(
                "The state maps each block to a real object.",
                "The state is Terraform's memory. It is how it knows that this block "
                "in your code is that server in the cloud.",
            ),
            Create(ring_state, run_time=0.9),
            w_state.role.animate(run_time=0.6).set_color(GOLD),
        )
        self.cue("It is how it knows")
        self.play(
            LaggedStart(
                *[Indicate(c, color=GOLD, scale_factor=1.08) for c in state_cells],
                lag_ratio=0.3,
            ),
            run_time=2.2,
        )
        self.cue("this block in your code")
        self.play(
            FadeIn(focus),
            Indicate(code_cells[k], color=GOLD, scale_factor=1.06),
            run_time=0.8,
        )
        self.cue("that server in the cloud")
        self.play(
            Indicate(state_cells[k], color=GOLD, scale_factor=1.06),
            Indicate(cloud_cells[k], color=GOLD, scale_factor=1.08),
            run_time=0.9,
        )
        self.hold(
            ambient=lambda t: [Throb(VGroup(state_cells[k], links[k]), t, amp=0.05)]
        )

        # -- apply again: nothing to do -------------------------------------------------- #
        assert not sim.AGAIN.actions
        self.play(
            self.tell(
                "Run it again and nothing changes: the same file gives the same result.",
                "Apply again, and there is nothing to do. Code, state and cloud "
                "agree. You can apply the same file a hundred times and get the "
                "same result.",
            ),
            FadeOut(focus, run_time=0.4),
            FadeOut(ring_state, run_time=0.4),
            w_state.role.animate(run_time=0.4).set_color(MUTED),
        )
        cmd = strip.command("terraform apply", vis=0.0)
        self.play(strip.show([cmd]))
        self.play(strip.type(cmd, cps=13))
        scan = band(0, color=GOOD)
        self.play(FadeIn(scan), run_time=0.2)
        for i in range(6):
            self.play(
                scan.animate.move_to(band(i, color=GOOD)),
                self.then(FadeIn(oks[i], scale=1.5, run_time=0.2), 0.08),
                run_time=0.28,
            )
        self.play(FadeOut(scan), run_time=0.2)
        self.play(strip.show(strip.lines([sim.AGAIN.summary], vis=0.0)))
        done = strip.line(sim.AGAIN_SUMMARY, vis=0.0)
        self.play(strip.show([done]))
        self.cue("Code, state and cloud agree")
        self.play(
            LaggedStart(
                *[ripple(w.bg, color=GOOD, buff=0.05, run_time=0.9) for w in wins],
                lag_ratio=0.35,
            )
        )
        self.cue("a hundred times")
        runs = ValueTracker(1)
        count = live_number(
            runs, fmt="apply ×{:,.0f}", fs=18, color=GOLD, font=MONO,
            anchor=lambda m: m.move_to(
                [strip.bg.get_right()[0] - 0.3, done.y, 0], aligned_edge=RIGHT
            ),
        )  # fmt: skip
        self.add(count)
        self.play(
            runs.animate.set_value(100),
            run_time=2.8,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 7 · Working as a team
    # ====================================================================== #
    def scene_team(self):
        self.header("7 · Working as a team", MINT)
        backend = (sim.DEMO / "backend.tf").read_text().rstrip("\n").split("\n")
        where = {
            k: v for k, v in re.findall(r'(\w+)\s*=\s*"([^"]+)"', "\n".join(backend))
        }
        lock_path = f"{where['bucket']}/{where['key']}"
        assert (
            lock_path == "acme-tfstate/web.tfstate"
            and "use_lockfile = true" in "\n".join(backend)
        )

        # the shared bucket and the state file
        store = res_icon("aws_s3_bucket", s=2.0)
        store_name = txt(f"s3://{where['bucket']}", fs=18, color=BUCKET_C, font=MONO)
        store_name.next_to(store, UP, buff=0.16)
        bucket = VGroup(store, store_name).move_to([3.7, 1.15, 0])
        state = doc_icon("terraform.tfstate", w=2.8, fs=16, h=0.7)  # the local name
        keyed = doc_icon(where["key"], w=1.95, fs=16, h=0.62)  # the same, under its key
        ada = laptop("ada").move_to([1.5, -1.7, 0])
        bob = laptop("bob").move_to([3.7, -1.7, 0])
        ci = laptop("CI pipeline", w=1.5).move_to([5.9, -1.7, 0])
        ci[2].become(txt("▶", fs=20, color=MUTED).move_to(ci.screen))
        state.next_to(ada.screen, UP, buff=0.22)
        team = VGroup(ada, bob, ci)

        def lost(m):  # this machine cannot see the state
            q = txt("?", fs=30, color=BAD, weight="BOLD").next_to(
                m.screen, UP, buff=0.2
            )
            return q

        q_bob, q_ci = lost(bob), lost(ci)
        people = VGroup(team, state, q_bob, q_ci)
        people.save_state()  # where they end up, beside the backend's configuration
        people.scale(1.5).move_to([0, -0.45, 0])  # first, they have the frame

        # -- the state cannot stay on one laptop ---------------------------------------- #
        self.play(
            FadeIn(ada, shift=UP * 0.15),
            FadeIn(state, shift=UP * 0.15),
            self.tell(
                "A team keeps the state in a shared backend.",
                "In a team, the state cannot live on one laptop. It goes in a shared "
                "backend, like an S3 bucket, where everyone and your CI pipeline read "
                "the same state.",
            ),
            run_time=0.8,
        )
        self.cue("cannot live on one laptop")
        self.play(
            LaggedStart(
                AnimationGroup(FadeIn(bob, shift=UP * 0.15), FadeIn(q_bob, scale=1.5)),
                AnimationGroup(FadeIn(ci, shift=UP * 0.15), FadeIn(q_ci, scale=1.5)),
                lag_ratio=0.4,
            ),
            run_time=1.1,
        )
        code = TextPanel(cols=34, n=len(backend), title="backend.tf", fs=17)
        for ln in backend:
            code.line(ln)
        code.move_to([-6.75 + code.w0 / 2, 2.2 - code.h0 / 2, 0])
        code.refresh()
        rows = {r.text.split("=")[0].strip(): r for r in code.rows if "=" in r.text}
        self.cue("It goes in a shared backend")
        self.play(  # the team makes room for the backend's configuration
            Restore(people, run_time=0.9),
            self.then(FadeIn(code, shift=RIGHT * 0.2, run_time=0.6), 0.4),
            self.then(FadeIn(bucket, shift=DOWN * 0.15, run_time=0.6), 0.5),
        )
        bar = code.bar_over(rows["bucket"], rows["key"], op=0.17)
        keyed.move_to(store.get_center() + DOWN * 0.22)
        self.play(
            Tween(bar, alpha=1.0, run_time=0.3),
            state.animate(run_time=1.0, path_arc=-0.6).move_to(keyed),
        )
        local_name = state[1]
        self.play(  # in the bucket, the file is stored under the key of backend.tf
            Transform(state[0], keyed[0]),
            FadeOut(local_name, run_time=0.2),
            self.then(FadeIn(keyed[1], run_time=0.25), 0.2),
            run_time=0.45,
        )
        state.remove(local_name)  # (a faded part left in its group would come back)
        state.add(keyed[1])
        self.cue("everyone and your CI pipeline")
        wires = VGroup(
            *[Line(m.screen.get_top() + UP * 0.08, store.get_bottom() + DOWN * 0.12 + RIGHT * dx,
                   stroke_color=FAINT, stroke_width=2.5)
              for m, dx in ((ada, -0.35), (bob, 0.0), (ci, 0.35))]
        )  # fmt: skip
        wires.set_z_index(-1)
        oks = VGroup(
            *[make_tick(GOOD, sw=5, scale=0.6).move_to(q) for q in (q_bob, q_ci)]
        )
        self.play(
            LaggedStart(*[Create(w) for w in wires], lag_ratio=0.2),
            FadeOut(VGroup(q_bob, q_ci), scale=0.6, run_time=0.3),
            self.then(FadeIn(oks, scale=1.5, run_time=0.3), 0.3),
            run_time=0.9,
        )

        def sync(rt):  # every client reads and writes the same state
            n = max(1, int(rt / 1.2))
            return [
                Succession(
                    *[
                        AnimationGroup(
                            *[
                                Succession(
                                    Wait(0.15 * k),
                                    Travel(glow_dot(BUCKET_C, r=0.06), w, run_time=0.5),
                                    Travel(glow_dot(BUCKET_C, r=0.06), w.copy().reverse_points(),
                                           run_time=0.5),
                                )
                                for k, w in enumerate(wires)
                            ]
                        )
                        for _ in range(n)
                    ],
                    run_time=rt,
                )
            ]  # fmt: skip

        self.hold(ambient=sync)

        # -- and it is locked while someone applies -------------------------------------- #
        t_ada = TextPanel(cols=39, n=6, title="ada@laptop", fs=16, kind="terminal")
        t_bob = TextPanel(cols=39, n=6, title="bob@laptop", fs=16, kind="terminal")
        t_ada.move_to([-3.45, -0.15 - t_ada.h0 / 2, 0])
        t_bob.move_to([3.45, -0.15 - t_bob.h0 / 2, 0])
        c_ada, c_bob = (
            t_ada.command("terraform apply"),
            t_bob.command("terraform apply"),
        )
        t_ada.refresh()
        t_bob.refresh()
        vault = VGroup(bucket, state)
        lock_row = code.bar_over(rows["use_lockfile"], op=0.2)
        self.play(
            self.tell(
                "The state is locked while someone applies.",
                "Turn on the lock file, and the state is locked while someone "
                "applies. If two people run apply at the same time, the second one "
                "is refused, instead of corrupting the state.",
            ),
            Tween(bar, alpha=0.0, run_time=0.3),
            Tween(lock_row, alpha=1.0, run_time=0.4),
        )
        self.cue(
            "the state is locked",
            ambient=lambda t: [
                Breathe(lock_row, t, attr="alpha", lo=0.45, hi=1.0, period=1.1)
            ],
        )
        self.play(
            Tween(lock_row, alpha=0.0, run_time=0.3),
            FadeOut(VGroup(code, ada, bob, ci, wires, oks), run_time=0.5),
            vault.animate(run_time=0.9).move_to([0, 1.45, 0]),
        )
        self.play(
            FadeIn(t_ada, shift=UP * 0.15), FadeIn(t_bob, shift=UP * 0.15), run_time=0.5
        )
        to_ada = Line(t_ada.bg.get_top() + UP * 0.06 + RIGHT * 1.6, store.get_left() + LEFT * 0.12,
                      stroke_color=FAINT, stroke_width=2.5)  # fmt: skip
        to_bob = Line(t_bob.bg.get_top() + UP * 0.06 + LEFT * 1.6, store.get_right() + RIGHT * 0.12,
                      stroke_color=FAINT, stroke_width=2.5)  # fmt: skip
        self.play(Create(to_ada), Create(to_bob), run_time=0.5)
        self.cue("If two people run apply")
        self.play(t_ada.type(c_ada, cps=14), self.then(t_bob.type(c_bob, cps=14), 0.25))
        lock = padlock(GOLD, s=1.1).next_to(store, RIGHT, buff=0.3)
        held = txt("locked by ada", fs=20, color=GOLD, weight="BOLD")
        held.next_to(lock, RIGHT, buff=0.22)
        acquiring = t_ada.lines(
            wrap_words("Acquiring state lock. This may take a few moments...", 38),
            vis=0.0,
        )
        refused = t_bob.lines(
            [
                "│ Error: Error acquiring the state lock",
                "│ Lock Info:",
                f"│   Path:      {lock_path}",
                "│   Operation: OperationTypeApply",
                "│   Who:       ada@laptop",
            ],
            vis=0.0,
        )
        self.play(
            Travel(glow_dot(GOLD, r=0.075), to_ada, run_time=0.6),
            self.then(Travel(glow_dot(GOLD, r=0.075), to_bob, run_time=0.6), 0.3),
            self.then(FadeIn(lock, scale=1.6, run_time=0.3), 0.55),
            self.then(FadeIn(held, shift=LEFT * 0.15, run_time=0.3), 0.6),
            self.then(t_ada.show(acquiring, lag=0.2), 0.6),
        )
        self.cue("the second one is refused")
        bounce = to_bob.copy().reverse_points()
        self.play(
            Travel(glow_dot(BAD, r=0.075), bounce, run_time=0.6),
            Indicate(lock, color=GOLD, scale_factor=1.15, run_time=0.6),
            self.then(t_bob.show(refused, lag=0.22), 0.5),
        )
        self.cue("instead of corrupting")
        done = t_ada.lines(wrap_words(sim.SCALE.summary, 36), vis=0.0)
        opened = padlock(GOOD, s=1.1, shut=False).move_to(lock)
        free = txt("released", fs=20, color=GOOD, weight="BOLD").move_to(
            held, aligned_edge=LEFT
        )
        self.play(
            t_ada.show(done, lag=0.2),
            Travel(
                glow_dot(GOOD, r=0.075), to_ada.copy().reverse_points(), run_time=0.6
            ),
            self.then(FadeOut(lock, run_time=0.25), 0.5),
            self.then(FadeIn(opened, run_time=0.3), 0.75),
            self.then(FadeOut(held, run_time=0.25), 0.5),
            self.then(FadeIn(free, run_time=0.3), 0.75),
        )
        self.add(
            self.note(
                "Abridged lock error of the S3 backend with use_lockfile (Terraform 1.10 and later)."
            )
        )
        self.settle()
        self.wipe()


class _Base3D(_Common, Explainer3DScene):
    """A scene on the 3D stage, with a fixed HUD column on the left."""

    def __init__(self, **kw):
        super().__init__(camera_class=StageCamera, **kw)

    def frame(
        self,
        stages,
        zone=STAGE_ZONE,
        theta=-52,
        phi=63,
        amp=8,
        period=17,
        extra=(),
        grow=1.45,
    ):
        """Aim the camera at ``stages`` and let it sway slowly around them. Zoom and
        screen position are computed so that everything stays inside ``zone``
        ``(x0, x1, y0, y1)`` of the screen at every angle of the sway. ``grow`` is
        how much larger a server may become in the scene (1.0: they keep their size)."""
        cam = self.camera
        self.set_camera_orientation(phi=phi * DEGREES, theta=theta * DEGREES, zoom=1.0)
        cam.screen_shift = np.zeros(3)
        pts = np.vstack(
            [
                *[d.hull(grow) for d in stages],
                *[np.array([q], dtype=float) for q in extra],
            ]
        )
        lo, hi = np.full(2, np.inf), np.full(2, -np.inf)
        for th in np.linspace(theta - amp, theta + amp, 9):
            cam.set_theta(th * DEGREES)
            cam.reset_rotation_matrix()
            q = cam.project_points(pts.copy())[:, :2]
            lo, hi = np.minimum(lo, q.min(axis=0)), np.maximum(hi, q.max(axis=0))
        x0, x1, y0, y1 = zone
        zoom = float(min((x1 - x0) / (hi[0] - lo[0]), (y1 - y0) / (hi[1] - lo[1])))
        mid = (lo + hi) / 2 * zoom
        cam.set_theta(theta * DEGREES)
        cam.set_zoom(zoom)
        cam.reset_rotation_matrix()
        cam.screen_shift = np.array(
            [(x0 + x1) / 2 - mid[0], (y0 + y1) / 2 - mid[1], 0.0]
        )
        tr = self.camera.theta_tracker
        tr.clear_updaters()
        tr.sway = (theta, amp, period, 0.0)

        def swing(m, dt):
            th, a, per, t = m.sway
            t += dt
            m.sway = (th, a, per, t)
            m.set_value((th + a * np.sin(TAU * t / per)) * DEGREES)

        if amp:
            tr.add_updater(swing)
            self.add(tr)

    def hud_root(self, *mobs):
        """Groups that live on the screen, not in the scene (panels with updaters)."""
        for m in mobs:
            m.set_z_index(10)
            self.camera.hud_roots.append(m)
        return mobs[0] if len(mobs) == 1 else mobs

    def billboard(self, mob, point):
        """A label that floats at ``point()`` (a world position) facing the camera."""
        mob.anchor_fn = point
        mob.move_to(point())
        mob.add_updater(lambda m: m.move_to(m.anchor_fn()))
        self.camera.add_fixed_orientation_mobjects(mob)
        mob.set_z_index(5)
        return mob

    def wipe(self, rt=None):
        tr = self.camera.theta_tracker
        tr.clear_updaters()
        self.remove(tr)
        super().wipe(rt)

    def call(self, term, d, key, n=3, color=None):
        """An API call: packets leave the terminal for a resource on the stage."""
        a = term.bg.get_right() + LEFT * 0.3
        b = self.camera.project_point(d.here(key, lift=-0.25))
        b[2] = 0.0
        path = flow(a, b, bend=0.35)
        c = color or KIND_C_OF[key]
        dots = [self.pin(glow_dot(c, r=0.065).set_z_index(12)) for _ in range(n)]
        return LaggedStart(
            *[Travel(m, path, run_time=0.55) for m in dots],
            lag_ratio=0.22,
            run_time=0.8,
        )

    def badge(self, d, key, symbol, lift=0.5):
        """The plan's verdict floating over a resource of the stage."""
        return self.billboard(
            plan_badge(symbol, s=0.40), lambda: d.here(key, lift=lift)
        )

    # ---- the left column --------------------------------------------------------- #
    def file_panel(self, n=5, blocks=None, title="main.tf", top=2.45, fs=16):
        """The folding editor with the film's main.tf, at the top of the column."""
        p = TextPanel(cols=39, n=n, title=title, fs=fs, w=HUD_W)
        for b in blocks or CONFIG:
            p.block(b.lines)
        p.move_to([HUD_X, top - p.h0 / 2, 0])
        p.refresh()
        return self.hud_root(p)

    def term_panel(self, n, top, title="terminal", fs=16):
        p = TextPanel(cols=45, n=n, title=title, fs=fs, kind="terminal", w=HUD_W)
        p.move_to([HUD_X, top - p.h0 / 2, 0])
        p.refresh()
        return self.hud_root(p)

    # ====================================================================== #
    # 1 · One file, one cloud
    # ====================================================================== #
    def scene_apply(self):
        d = Diorama(slots=3)
        self.frame([d])
        self.header("1 · One file, one cloud", GOLD)
        d.slab.alpha = 0.0
        d.refresh()
        self.add(d)
        file = self.file_panel(n=5, fs=17)
        folds = dict(zip(ADDRESSES, file.folds, strict=True))
        bars = {a: file.bar_over(f.head, op=0.15) for a, f in folds.items()}
        ticks = {
            a: file.mark(f.head, make_tick(GOOD, sw=4.5, scale=0.46), dx=-0.10)
            for a, f in folds.items()
        }

        # -- the file declares five things -------------------------------------- #
        self.play(
            FadeIn(file, shift=RIGHT * 0.2),
            Tween(d.slab, alpha=1.0, run_time=0.9),
            self.tell(
                "Five blocks of text describe a small piece of cloud infrastructure.",
                "This is a Terraform file. Five short blocks, each describing a "
                "piece of cloud infrastructure: a network, a subnet, a firewall, "
                "two servers, and a storage bucket.",
            ),
            run_time=0.9,
        )
        self.cue("Five short blocks")
        self.play(
            LaggedStart(
                *[
                    Succession(
                        Tween(b, alpha=1.0, run_time=0.25),
                        Tween(b, alpha=0.0, run_time=0.4),
                    )
                    for b in bars.values()
                ],
                lag_ratio=0.45,
            ),
            run_time=3.0,
        )
        last = None
        for phrase, addr in (
            ("a network", "aws_vpc.main"),
            ("a subnet", "aws_subnet.public"),
            ("a firewall", "aws_security_group.web"),
            ("two servers", "aws_instance.web"),
            ("a storage bucket", "aws_s3_bucket.assets"),
        ):
            self.cue(phrase)
            anims = [Tween(bars[addr], alpha=1.0, run_time=0.3)]
            if last is not None:
                anims.append(Tween(bars[last], alpha=0.0, run_time=0.3))
            self.play(*anims, *[d.declare(k, run_time=0.7) for k in KEYS[addr]])
            last = addr
        self.hold()

        # -- one command builds them, in dependency order ---------------------- #
        term = self.term_panel(n=4, top=file.bg.get_bottom()[1] - 0.22, fs=17)
        cmd = term.command("terraform apply")
        term.refresh()
        self.play(
            Tween(bars[last], alpha=0.0, run_time=0.3),
            self.tell(
                "One command builds all of it, in the right order.",
                "None of it exists yet. Run one command, terraform apply, say yes, "
                "and Terraform calls the cloud's API to build it all, in the right "
                "order.",
            ),
        )
        self.cue("Run one command")
        self.play(FadeIn(term, shift=UP * 0.15), run_time=0.5)
        self.cue("terraform apply")
        self.play(term.type(cmd, cps=13))
        self.cue("say yes")  # apply always asks before it changes anything
        ask = term.line("  Enter a value: yes", vis=0.0)
        ask.typed = float(len("  Enter a value: "))
        self.play(term.show([ask]))
        self.play(term.type(ask, cps=8))
        self.cue("calls the cloud")
        for wave in FIRST_WAVES:
            keys = [stage_key(e.address) for e in wave]
            done = {sim.base(e.address) for e in wave}
            self.play(
                *[self.call(term, d, k) for k in keys],
                *[self.then(d.build(k, run_time=1.0), 0.45) for k in keys],
                *[
                    Succession(Wait(1.25), Tween(ticks[a], alpha=1.0, run_time=0.3))
                    for a in ADDRESSES
                    if a in done
                ],
            )
            self.wait(0.1 if self.pace.quick else 0.25)
        assert sim.FIRST.summary == (
            "Apply complete! Resources: 6 added, 0 changed, 0 destroyed."
        )
        rows = term.lines(wrap_words(sim.FIRST.summary, 36), vis=0.0)
        self.play(term.show(rows, lag=0.2))
        self.hold()

        # -- the file is now the source of truth --------------------------------- #
        ring = SurroundingRectangle(file.bg, color=GOLD, buff=0.06, corner_radius=0.18)
        ring.set_stroke(GOLD, width=4)
        self.pin(ring)
        self.play(
            self.tell(
                "Infrastructure as code: the file is the source of truth.",
                "From now on, the file is the source of truth. To change the cloud, "
                "you change the file. That is infrastructure as code.",
            ),
            Create(ring, run_time=0.9),
        )
        self.cue("To change the cloud")
        for addr in ADDRESSES:  # this line is that object
            self.play(
                Succession(
                    Tween(bars[addr], alpha=1.0, run_time=0.22),
                    Tween(bars[addr], alpha=0.0, run_time=0.38),
                ),
                *[d.pulse(k, GOLD, run_time=0.6) for k in KEYS[addr]],
            )
        self.add(self.note("A model of Terraform's behaviour, not a recorded run."))
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 5 · Change the file, not the cloud
    # ====================================================================== #
    def scene_change(self):
        d = Diorama(slots=3)
        d.set_built("vpc", "subnet", "sg", "web0", "web1", "bucket")
        self.frame([d])
        self.header("5 · Change the file, not the cloud", AMBER)
        file = self.file_panel(n=5)
        inst = file.folds[ADDRESSES.index("aws_instance.web")]
        inst.open, file.scroll = 1.0, 3.0  # the instance block, open, fills the window
        file.refresh()
        term = self.term_panel(n=6, top=file.bg.get_bottom()[1] - 0.22)
        webs = ("web0", "web1", "web2")

        def row_of(arg):
            return next(r for r in inst.body if r.text.strip().startswith(arg + " "))

        def line_of(blocks, arg):  # the source line of an argument after an edit
            b = next(b for b in blocks if b.address == "aws_instance.web")
            return next(ln for ln in b.lines if ln.strip().startswith(arg + " "))

        def run(cmd_text):  # a fresh command line in a cleared terminal
            if term.rows:
                self.play(*term.fade_rows(), run_time=0.3)
                term.drop()
            cmd = term.command(cmd_text)
            self.play(term.type(cmd, cps=14))
            return cmd

        # -- two servers become three: one thing to add ---------------------------- #
        self.play(
            FadeIn(d, run_time=0.8),
            FadeIn(file, shift=RIGHT * 0.2),
            FadeIn(term, shift=RIGHT * 0.2),
            self.tell(
                "Change the file: the plan shows only the difference.",
                "To change the infrastructure, you change the file. Two servers "
                "become three. The plan shows exactly one resource to add, and "
                "leaves the other six alone. Apply, and it is built.",
            ),
            run_time=0.8,
        )
        bar = file.bar_over(row_of("count"), op=0.18)
        self.cue("Two servers become three")
        self.play(Tween(bar, alpha=1.0, run_time=0.3))
        self.play(
            Retype(file, row_of("count"), line_of(sim.SCALED, "count")),
            d.declare("web2", run_time=0.8),
        )
        self.cue("The plan shows")
        run("terraform plan")
        act = sim.SCALE.plan.of("aws_instance.web[2]")
        assert act.kind == "create" and sim.SCALE.plan.count("create") == 1
        plus = self.badge(d, "web2", act.symbol)
        self.play(
            term.show(
                term.lines(
                    [act.headline, act.resource_line, "    …", sim.SCALE.plan.summary],
                    vis=0.0,
                ),
                lag=0.3,
            ),
            self.then(FadeIn(plus, scale=1.6, run_time=0.3), 0.3),
        )
        self.cue("leaves the other six alone")
        self.play(
            LaggedStart(
                *[d.pulse(k, INK, k=0.32, run_time=0.55)
                  for k in ("vpc", "subnet", "sg", "web0", "web1", "bucket")],
                lag_ratio=0.3,
            )
        )  # fmt: skip
        self.cue("Apply, and it is built")
        run("terraform apply")
        self.play(
            self.call(term, d, "web2"),
            self.then(d.build("web2"), 0.45),
            self.then(FadeOut(plus, scale=0.6, run_time=0.3), 0.5),
            Tween(bar, alpha=0.0, run_time=0.4),
        )
        self.play(
            term.show(term.lines(wrap_words(sim.SCALE.summary, 36), vis=0.0), lag=0.2)
        )
        self.hold()

        # -- a bigger instance type: updated in place --------------------------------- #
        big = 1.18  # how much larger a t3.small is drawn than a t3.micro
        self.play(
            self.tell(
                "Some changes update a resource in place.",
                "Some changes can be made in place. A bigger instance type is an "
                "update: same servers, new size, after a restart.",
            )
        )
        bar = file.bar_over(row_of("instance_type"), op=0.18)
        self.cue("A bigger instance type")
        self.play(Tween(bar, alpha=1.0, run_time=0.3))
        self.play(
            Retype(
                file, row_of("instance_type"), line_of(sim.RESIZED, "instance_type")
            ),
            *[Tween(d[k].ghost, run_time=0.8, size=big, alpha=1.0) for k in webs],
        )
        run("terraform plan")
        act = sim.RESIZE.plan.actions[0]
        assert {a.kind for a in sim.RESIZE.plan.actions} == {"update"}
        marks = [self.badge(d, k, act.symbol) for k in webs]
        self.play(
            term.show(
                term.lines(
                    [act.headline, act.resource_line, "    " + act.change_lines()[0], "    …",
                     sim.RESIZE.plan.summary],
                    vis=0.0,
                ),
                lag=0.3,
            ),
            *[self.then(FadeIn(m, scale=1.6, run_time=0.3), 0.3 + 0.15 * i)
              for i, m in enumerate(marks)],
        )  # fmt: skip
        self.cue("same servers, new size")
        run("terraform apply")
        self.play(
            *[self.call(term, d, k, n=2) for k in webs],
            *[
                self.then(
                    AnimationGroup(
                        Tween(
                            d[k].solid,
                            run_time=0.9,
                            rate_func=rate_functions.ease_out_back,
                            size=big,
                        ),
                        Tween(d[k].shade, run_time=0.9, size=big),
                        Tween(d[k].ghost, run_time=0.9, alpha=0.0),
                        d.pulse(k, CHANGE_C, run_time=1.0),
                    ),
                    0.45,
                )
                for k in webs
            ],
            *[self.then(FadeOut(m, scale=0.6, run_time=0.3), 0.6) for m in marks],
            Tween(bar, alpha=0.0, run_time=0.4),
        )
        self.play(
            term.show(term.lines(wrap_words(sim.RESIZE.summary, 36), vis=0.0), lag=0.2)
        )
        self.hold()

        # -- a new image: destroy, then create ------------------------------------------ #
        self.play(
            self.tell(
                "Others force a replacement: destroy, then create.",
                "Others cannot. A new machine image forces a replacement: Terraform "
                "destroys each server and creates a new one. The plan tells you "
                "which, before you say yes.",
            )
        )
        bar = file.bar_over(row_of("ami"), op=0.18)
        self.cue("A new machine image")
        self.play(Tween(bar, alpha=1.0, run_time=0.3))
        self.play(Retype(file, row_of("ami"), line_of(sim.REIMAGED, "ami")))
        run("terraform apply")
        act = sim.REIMAGE.plan.actions[0]
        assert {a.kind for a in sim.REIMAGE.plan.actions} == {"replace"}
        change, why = act.change_lines()[0].split(" # ")
        marks = [self.badge(d, k, act.symbol) for k in webs]
        self.play(
            term.show(
                term.lines(
                    [act.headline, act.resource_line, "    " + change, "      # " + why,
                     sim.REIMAGE.plan.summary],
                    vis=0.0,
                ),
                lag=0.3,
            ),
            *[self.then(FadeIn(m, scale=1.6, run_time=0.3), 0.3 + 0.15 * i)
              for i, m in enumerate(marks)],
        )  # fmt: skip
        self.cue("before you say yes")
        ask = term.line("  Enter a value: yes", vis=0.0)
        ask.typed = float(len("  Enter a value: "))
        self.play(term.show([ask]))
        self.play(term.type(ask, cps=7))
        self.play(*[d.destroy(k, run_time=0.9, ghost=0.9) for k in webs])
        self.play(
            *[d.build(k, run_time=1.0) for k in webs],
            *[FadeOut(m, scale=0.6, run_time=0.3) for m in marks],
            Tween(bar, alpha=0.0, run_time=0.4),
        )
        self.play(
            term.show(term.lines(wrap_words(sim.REIMAGE.summary, 36), vis=0.0), lag=0.2)
        )
        self.add(
            self.note(
                "A model of Terraform's behaviour, not a recorded run. … marks omitted output."
            )
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 6 · Drift
    # ====================================================================== #
    def scene_drift(self):
        big, huge = 1.18, 1.38  # a t3.small, and the t3.large someone picked by hand
        d = Diorama(slots=3)
        d.set_built("vpc", "subnet", "sg", "web0", "web1", "web2", "bucket")
        for k in ("web0", "web1", "web2"):
            for part in d[k].parts:
                part.size = big
        d.refresh()
        self.frame([d])
        self.header("6 · Drift", BAD)
        key = stage_key(sim.DRIFT_ADDR)
        was, now = sim.DRIFT_PLAN.of(sim.DRIFT_ADDR).changes["instance_type"]
        assert (key, was, now) == ("web1", "t3.large", "t3.small")

        # the cloud console: a window where someone changes things by hand
        w, h = HUD_W, 2.36
        con = window(w, h, "cloud console", role="by hand")
        con.move_to([HUD_X, 2.45 - h / 2, 0])
        left = con.bg.get_left()[0]

        def field(label, value, y, wide=2.9, caret=False):
            lab = txt(label, fs=17, color=MUTED).move_to(
                [left + 0.36, y, 0], aligned_edge=LEFT
            )
            box = RoundedRectangle(width=wide, height=0.46, corner_radius=0.08, stroke_color=FAINT,
                                   stroke_width=2, fill_color=PANEL, fill_opacity=1)  # fmt: skip
            box.move_to([left + 2.55 + wide / 2, y, 0])
            val = txt(value, fs=17, color=INK, font=MONO)
            val.move_to([box.get_left()[0] + 0.18 + val.width / 2, y, 0])
            g = VGroup(lab, box, val)
            if caret:
                tri = Triangle(fill_color=MUTED, fill_opacity=1, stroke_width=0).rotate(
                    PI
                )
                tri.set_width(0.16).move_to([box.get_right()[0] - 0.24, y, 0])
                g.add(tri)
            g.box, g.val = box, val
            return g

        y0 = con.bar.get_bottom()[1]
        f_id = field("Instance", sim.short(sim.DRIFT_ID), y0 - 0.48)
        f_type = field("Instance type", now, y0 - 1.08, caret=True)
        save = mono_chip("Save", SKY, fs=17, h=0.44, w=1.2, fill=0.22)
        save.move_to([con.bg.get_right()[0] - 0.9, y0 - 1.66, 0])
        mouse = pointer(0.8).move_to([left + 1.2, y0 - 1.75, 0], aligned_edge=UL)
        console = VGroup(con, f_id, f_type, save, mouse)
        self.hud_root(console)
        mouse.set_z_index(14)
        term = self.term_panel(n=6, top=con.bg.get_bottom()[1] - 0.22)

        def click(at):
            ring, anim = click_ring(at)
            self.pin(ring.set_z_index(14))
            return anim

        # -- someone changes a server by hand ---------------------------------------- #
        self.play(
            FadeIn(d, run_time=0.8),
            FadeIn(console, shift=RIGHT * 0.2),
            self.tell(
                "Someone changes the cloud by hand: that is drift.",
                "Now someone changes a server by hand, in the cloud console. The "
                "real infrastructure no longer matches the file. This is called drift.",
            ),
            run_time=0.8,
        )
        self.cue("changes a server by hand")
        tip = f_type.box.get_right() + LEFT * 0.3 + DOWN * 0.05
        self.play(mouse.animate.move_to(tip, aligned_edge=UL), run_time=0.7)
        new_val = txt(was, fs=17, color=BAD, font=MONO)
        new_val.move_to(
            [
                f_type.box.get_left()[0] + 0.18 + new_val.width / 2,
                f_type.val.get_center()[1],
                0,
            ]
        )
        self.pin(new_val.set_z_index(11))
        hot = f_type.box.copy().set_fill(opacity=0).set_stroke(BAD, width=2.5)
        self.pin(hot.set_z_index(11))
        self.play(
            click(tip),
            FadeOut(f_type.val, run_time=0.25),
            self.then(FadeIn(new_val, run_time=0.3), 0.25),
            FadeIn(hot, run_time=0.4),
        )
        tip = save.get_center() + RIGHT * 0.1 + DOWN * 0.02
        self.play(mouse.animate.move_to(tip, aligned_edge=UL), run_time=0.6)
        solid, ghost, shade = d[key].solid, d[key].ghost, d[key].shade
        solid.tint_c = BAD
        self.play(
            click(tip),
            self.then(
                AnimationGroup(
                    Tween(
                        solid,
                        run_time=0.9,
                        rate_func=rate_functions.ease_out_back,
                        size=huge,
                    ),
                    Tween(shade, run_time=0.9, size=huge),
                    Succession(
                        Tween(solid, run_time=0.3, tint=0.7),
                        Tween(solid, run_time=0.9, tint=0.22),
                    ),
                ),
                0.3,
            ),
        )
        self.cue("no longer matches the file")
        for f in ghost.submobjects:  # the declared size, drawn boldly on the server
            f.sw, f.fill_op = 3.2, 0.16
        ghost._sig = None
        self.play(Tween(ghost, run_time=0.6, alpha=1.0), FadeOut(mouse, run_time=0.4))
        tag = mono_chip("drift", BAD, fs=18, h=0.46, fill=0.9)
        tag[1].set_color(BG)
        self.billboard(tag, lambda: d.here(key, lift=0.55))
        self.cue("This is called drift")
        self.play(FadeIn(tag, scale=1.5), run_time=0.4)
        self.hold(
            ambient=lambda t: [
                Breathe(ghost, t, attr="alpha", lo=0.35, hi=1.0, period=1.1)
            ]
        )

        # -- every plan first reads the real resources ----------------------------------- #
        self.play(
            self.tell(
                "Every plan first reads the real resources.",
                "The next plan notices. Every plan starts by reading the real "
                "resources, and comparing them with the state and the code.",
            ),
            Tween(ghost, run_time=0.4, alpha=1.0),
            FadeIn(term, shift=UP * 0.15, run_time=0.6),
        )
        cmd = term.command("terraform plan")
        self.play(term.type(cmd, cps=14))
        self.cue("reading the real resources")
        reading = term.lines(
            wrap_words(
                f"{sim.DRIFT_ADDR}: Refreshing state... [id={sim.DRIFT_ID}]", 44
            ),
            vis=0.0,
        )

        def seen(k):
            return d.pulse(
                k,
                BAD if k == key else BLUEPRINT,
                k=0.75 if k == key else 0.5,
                run_time=0.7,
            )

        self.play(d.scan(run_time=2.2, on_pass=seen), term.show(reading, lag=0.2))
        self.cue("comparing them")
        self.play(*term.fade_rows(reading), run_time=0.3)
        term.drop(reading)
        act = sim.DRIFT_PLAN.of(sim.DRIFT_ADDR)
        mark = self.badge(d, key, act.symbol, lift=1.05)
        self.play(
            term.show(
                term.lines(
                    [act.headline, act.resource_line, "    " + act.change_lines()[0], "    …",
                     sim.DRIFT_PLAN.summary],
                    vis=0.0,
                ),
                lag=0.3,
            ),
            self.then(FadeIn(mark, scale=1.6, run_time=0.3), 0.6),
        )  # fmt: skip
        self.hold()

        # -- apply puts it back ------------------------------------------------------------ #
        self.play(
            self.tell(
                "Apply puts the cloud back in line with the file.",
                "It proposes to put the server back the way the file says. Apply, "
                "and the drift is gone.",
            )
        )
        self.cue("Apply, and the drift is gone")
        self.play(*term.fade_rows(), run_time=0.3)
        term.drop()
        cmd = term.command("terraform apply")
        self.play(term.type(cmd, cps=14))
        cool = f_type.box.copy().set_fill(opacity=0).set_stroke(GOOD, width=2.5)
        self.pin(cool.set_z_index(11))
        back = txt(now, fs=17, color=GOOD, font=MONO)
        back.move_to(
            [
                f_type.box.get_left()[0] + 0.18 + back.width / 2,
                new_val.get_center()[1],
                0,
            ]
        )
        self.pin(back.set_z_index(11))
        solid.tint_c = CHANGE_C
        self.play(
            self.call(term, d, key),
            self.then(
                AnimationGroup(
                    Tween(
                        solid,
                        run_time=0.9,
                        rate_func=rate_functions.ease_out_back,
                        size=big,
                    ),
                    Tween(shade, run_time=0.9, size=big),
                    Succession(
                        Tween(solid, run_time=0.3, tint=0.7),
                        Tween(solid, run_time=0.8, tint=0.0),
                    ),
                    Tween(ghost, run_time=0.9, alpha=0.0),
                    FadeOut(mark, scale=0.6, run_time=0.3),
                    FadeOut(tag, scale=0.6, run_time=0.3),
                    FadeOut(new_val, run_time=0.25),
                    FadeOut(hot, run_time=0.25),
                    self.then(FadeIn(back, run_time=0.3), 0.3),
                    self.then(FadeIn(cool, run_time=0.3), 0.3),
                ),
                0.45,
            ),
        )
        self.play(
            term.show(term.lines(wrap_words(sim.DRIFT.summary, 36), vis=0.0), lag=0.2)
        )
        self.add(
            self.note(
                "A model of Terraform's behaviour, not a recorded run. … marks omitted output."
            )
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 8 · One module, many environments
    # ====================================================================== #
    def scene_envs(self):
        envs = list(sim.ENVS)
        assert envs == ["dev", "staging", "prod"]
        probe = Diorama(slots=4, cols=2, label=None)
        pitch = probe.size_w + 1.0
        stages = {  # no lettering on these small floors: each island gets a sign
            e: Diorama(slots=4, cols=2, origin=((i - 1) * pitch, 0, 0), label=None,
                       names=False)
            for i, e in enumerate(envs)
        }  # fmt: skip

        # two windows above the islands: the module, and the call of one environment
        top, gap, w_mod, w_call = 2.6, 0.6, 6.1, 5.2
        left = -(w_mod + gap + w_call) / 2
        look = {"fs": 16, "pitch": 0.295, "bar_h": 0.36}
        mod = TextPanel(cols=39, n=6, title="main.tf", w=w_mod, **look)
        for b in CONFIG:
            mod.block(b.lines)
        inst = mod.folds[ADDRESSES.index("aws_instance.web")]
        var = mod.block(sim.MODULE_INPUT, index=0, vis=0.0)  # the module's one input
        mod.move_to([left + w_mod / 2, top - mod.h0 / 2, 0])
        mod.refresh()
        self.hud_root(mod)
        count_row = inst.body[0]
        module_blocks = sim.parse(sim.MODULE_SOURCE)
        new_count = module_blocks[ADDRESSES.index("aws_instance.web")].lines[1]
        assert new_count.split("=")[1].strip() == "var.servers"

        # every island gets its own state file, hung under its front edge. A billboard
        # is drawn at its own size whatever the zoom, so the zone leaves it half its
        # height. Only prod has servers in the back row, the tallest point of the set,
        # and prod stands right of the module's window: the zone may reach above its
        # bottom edge.
        doc_w = max(len(v["state_key"]) for v in sim.ENVS.values()) * char_adv(16) + 0.5
        tag_h = 0.46
        drop = np.array([0.0, -probe.size_d / 2, -0.77])
        tag_at = {e: st.centre + drop for e, st in stages.items()}
        self.frame(
            list(stages.values()),
            zone=(-6.8, 6.8, -2.92 + tag_h / 2, mod.bg.get_bottom()[1] + 0.1),
            theta=-90, phi=58, amp=5, period=19, extra=list(tag_at.values()), grow=1.0,
        )  # fmt: skip
        self.header("8 · One module, many environments", LILAC)

        self.play(
            *[FadeIn(st, run_time=0.9) for st in stages.values()],
            FadeIn(mod, shift=DOWN * 0.15),
            self.tell(
                "Wrap the blocks in a module, with inputs.",
                "Finally, wrap those five blocks in a module, with the number of "
                "servers as an input.",
            ),
            run_time=0.9,
        )
        self.cue("in a module")
        new_title = txt("modules/web/main.tf", fs=16, color=GOLD, font=MONO)
        new_title.move_to(mod.ttl, aligned_edge=LEFT)
        self.pin(new_title.set_z_index(11))
        ring = SurroundingRectangle(mod.bg, color=GOLD, buff=0.05, corner_radius=0.17)
        ring.set_stroke(GOLD, width=3.5)
        self.pin(ring.set_z_index(11))
        self.play(
            # (not FadeOut: removing a child from the scene replaces the panel by
            # its other children there, and the panel's own updater stops running)
            mod.ttl.animate(run_time=0.25).set_opacity(0.0),
            self.then(FadeIn(new_title, run_time=0.3), 0.25),
            Create(ring, run_time=0.8),
        )
        self.cue("the number of servers")
        self.play(Tween(inst, open=1.0, run_time=0.7))
        bar = mod.bar_over(count_row, op=0.18)
        self.play(
            Tween(bar, alpha=1.0, run_time=0.3), Retype(mod, count_row, new_count)
        )
        self.cue("as an input")
        var_bar = mod.bar_over(var.head, op=0.18)
        uses = mod.link(count_row, var.head, REF_C, lane=0)  # count reads the input
        self.play(mod.show([var.head], scroll=False), Tween(var_bar, alpha=1.0))
        self.play(Tween(uses, grow=1.0, run_time=0.6))
        self.hold(
            ambient=lambda t: [
                Breathe(uses, t, attr="alpha", lo=0.4, hi=1.0, period=1.2)
            ]
        )

        # one call per environment: the editor tabs through them
        call = TextPanel(cols=30, n=4, title="main.tf", w=w_call, **look)
        first = sim.ENVS[envs[0]]["call"]
        call_fold = call.block(first, open=1.0)
        call.move_to([mod.bg.get_right()[0] + gap + w_call / 2, top - call.h0 / 2, 0])
        call.refresh()
        self.hud_root(call)
        n_row = call_fold.body[1]
        assert n_row.text.split("=")[0].strip() == "servers"
        n_bar = call.bar_over(n_row, op=0.18)
        tabs = VGroup(*[txt(e, fs=16, color=MUTED, font=MONO) for e in envs]).arrange(
            RIGHT, buff=0.34
        )
        tabs.move_to(
            [
                call.bg.get_right()[0] - tabs.width / 2 - 0.28,
                call.bar.get_center()[1],
                0,
            ]
        )
        tab_on = Line(tabs[0].get_corner(DL), tabs[0].get_corner(DR)).shift(DOWN * 0.07)
        tab_on.set_stroke(GOLD, width=3)
        chrome = VGroup(tabs, tab_on)
        self.hud_root(chrome)
        chrome.set_z_index(12)
        # the value of the call feeds the module's input
        wire = flow(
            [call.bg.get_left()[0], n_row.y, 0],
            [mod.bg.get_right()[0] + 0.05, var.head.y, 0],
            bend=0.5,
        )
        wire.set_stroke(GOLD, width=2.6)
        self.pin(wire.set_z_index(9))

        def raise_env(e):
            st, n = stages[e], sim.ENVS[e]["servers"]
            keys = [["vpc", "bucket"], ["subnet", "sg"], [f"web{i}" for i in range(n)]]
            waves = [
                AnimationGroup(*[st.build(k, run_time=0.35) for k in w]) for w in keys
            ]  # (a build glows a little longer than it rises: the waves overlap)
            return Succession(
                AnimationGroup(
                    *[st.declare(k, run_time=0.25) for w in keys for k in w]
                ),
                LaggedStart(*waves, lag_ratio=0.66),
            )

        def tag_for(e):
            doc = doc_icon(sim.ENVS[e]["state_key"], w=doc_w, fs=16, h=tag_h)
            return self.billboard(doc, lambda: tag_at[e])

        self.play(
            self.tell(
                "The same code builds three environments, each with its own state.",
                "Now the same code builds dev, with one server. Then staging, with "
                "two servers. And production, with four. Three environments, three "
                "state files, one definition, and nothing done by hand.",
            ),
            Tween(uses, alpha=1.0, run_time=0.3),
            FadeIn(call, shift=LEFT * 0.2),
            FadeIn(chrome),
            Create(wire),
            Tween(n_bar, alpha=1.0, run_time=0.5),
            tabs[0].animate.set_color(INK),
        )
        tags = {}
        for i, (e, phrase) in enumerate(
            zip(envs, ("dev", "staging", "production"), strict=True)
        ):
            self.cue(phrase)
            switch = []
            if i:  # the next tab: the same call, another number
                under = Line(tabs[i].get_corner(DL), tabs[i].get_corner(DR))
                switch = [
                    Retype(call, n_row, sim.ENVS[e]["call"][2], run_time=0.45),
                    tab_on.animate(run_time=0.4)
                    .move_to(under.shift(DOWN * 0.07))
                    .set_width(tabs[i].width),
                    tabs[i - 1].animate(run_time=0.4).set_color(MUTED),
                    tabs[i].animate(run_time=0.4).set_color(INK),
                ]
            lead = 0.3 if i else 0.0
            tags[e] = tag_for(e)
            dot = self.pin(glow_dot(GOLD, r=0.07).set_z_index(12))
            self.play(
                *switch,
                self.then(Travel(dot, wire, run_time=0.45), lead),
                self.then(
                    Breathe(bar, 0.5, attr="alpha", lo=1.0, hi=0.35, period=0.5),
                    lead + 0.4,
                ),
                self.then(raise_env(e), lead + 0.3),
                self.then(FadeIn(tags[e], shift=UP * 0.1, run_time=0.35), lead + 1.3),
            )
        assert [sim.ENVS[e]["state_key"] for e in envs] == [
            "dev.tfstate",
            "staging.tfstate",
            "prod.tfstate",
        ]
        self.cue("three state files")
        self.play(
            LaggedStart(
                *[
                    tags[e].animate(run_time=0.7, rate_func=there_and_back).scale(1.16)
                    for e in envs
                ],
                lag_ratio=0.3,
            )
        )
        self.cue("one definition")
        self.play(
            ring.animate(run_time=0.9, rate_func=there_and_back).set_stroke(width=7.5)
        )
        self.hold()

        # -- the takeaway ---------------------------------------------------------------------- #
        self.play(
            self.tell(
                "Describe what you want. Review the plan. Let the cloud match the file.",
                "That is Terraform: describe the infrastructure you want, review "
                "the plan, and let it make the cloud match.",
                color=GOLD,
            )
        )
        for e in envs:
            st, n = stages[e], sim.ENVS[e]["servers"]
            self.play(
                LaggedStart(
                    *[st.pulse(k, GOLD, run_time=0.6)
                      for k in ("vpc", "subnet", "sg", *[f"web{i}" for i in range(n)], "bucket")],
                    lag_ratio=0.12,
                ),
                run_time=1.1,
            )  # fmt: skip
        self.settle()
        self.wipe()


# ---- renderable scenes ------------------------------------------------------ #
class Intro(_Base):
    def construct(self):
        self.over_card(
            "Terraform: how a text file becomes real infrastructure. We will follow "
            "one small example, from an empty cloud region to three full environments."
        )
        self.play_intro()


class Apply(_Base3D):
    def construct(self):
        self.scene_apply()


class Blocks(_Base):
    def construct(self):
        self.scene_blocks()


class Graph(_Base):
    def construct(self):
        self.scene_graph()


class Plan(_Base):
    def construct(self):
        self.scene_plan()


class Team(_Base):
    def construct(self):
        self.scene_team()


class Change(_Base3D):
    def construct(self):
        self.scene_change()


class Drift(_Base3D):
    def construct(self):
        self.scene_drift()


class Envs(_Base3D):
    def construct(self):
        self.scene_envs()


class Outro(_Base):
    def construct(self):
        self.over_card("Thank you for watching.")
        self.play_outro()
