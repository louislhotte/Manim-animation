"""TCP, HTTP, HTTPS: what really happens when one machine calls another.

A film made to be narrated, and built to move: the voice carries the explanation,
the screen carries data (packets, bytes, numbers, real error messages) and almost no
sentences. The camera never moves; depth comes from a stack of flat sheets.

STORYBOARD (question | hero visual | what moves | on-screen words)

    1 One request      what happened in a third of a second?   a map, Paris to Singapore;
                       then the five lines of the client and the stack they stand on
                       | a pulse crosses six times; sheets fan out | km, ms, code
    2 Packets          what does a network carry?   routers between two copies of a
                       picture | 158 packets take different roads, one queue overflows,
                       the phone's copy fills in disorder, with holes | addresses, counts
    3 A connection     how do two programs find each other?   the wire and its trace
                       in time | SYN, SYN-ACK, ACK draw one round trip (the handshake); a
                       reset bounces back; SYNs die at a wall, 1 2 3 4 5 7 11 ... 75 s;
                       refused or timed out, replayed side by side | flags, seconds
    4 A reliable       how do lossy packets become a stream?   the two pictures and the
      stream           wire between them | trains of 10, 20, 40, 80 packets (slow start);
                       ACKs come back; a packet falls off the wire, a hole, a veil over
                       what waits, one resend, the window cut | byte count, window
    5 HTTP             what do the programs say?   the request and the response, real
                       bytes | text flows down the pipe, the route lights, the status
                       turns 200 / 404 / 401 / 500; three lanes of round trips race:
                       a connection per request, keep-alive, HTTP/2
    6 In the clear     who else can read it?   a tap on the wire and its screen | the
                       token is read and reused, 24.4 becomes 2.44
    7 HTTPS            how to talk privately with the right server?   two secrets, two
                       public values, one key; a chain of certificates, and a signature
                       made with the key that never leaves the server; noise on the
                       tap's screen | keys meet and match, the chain is checked link by
                       link, a copied certificate has no key, one flipped bit is rejected
    8 Between servers  what does this look like in production?   a relay of
                       connections | pulses hop from balancer to app to solver; a port
                       refuses (502), a wait runs out (504); the ledger of round trips
    9 The stack        how to hold all of it?   the five lines above the stack | each
                       line lights what it stands on (the lookup: a directory, not a
                       layer); every layer replays at once; each line fails with its
                       real error, and shows where to look

Motif: the five lines of ``demo/client.py`` (look up, connect, secure, send, read) and
the stack of four sheets (IP green, TCP blue, TLS purple, HTTP orange; a small copy
sits top right in every scene, with the layer at hand lit). Gold marks the thing to
look at, red what is lost or hostile.

Real data, baked by ``generate_assets.py`` into ``assets/story.json`` (see README):
bytes, handshakes, certificates and error messages are recorded between two programs
on this machine's loopback interface (``lab.py``, ``demo/``); the kernel's first
window, its refusal and its 75 s of SYN retries are measured; packet-level pictures
come from a model of TCP (``tcpsim.py``), since a capture needs administrator rights;
delays are the physical minimum for light in fibre between Paris and Singapore. The
server's name and addresses are documentation values; nothing left this machine.

Scenes render alone (``./render.sh stream --quick --check``) or stitched
(``./render.sh``). Pacing: ``NET_WPS`` (narrator's words per second), ``NET_QUICK``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from manimx import *

from kit import *  # noqa: F403


class _Common(NarratedMixin):
    pace = Pace.from_env("NET", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "TCP, HTTP, HTTPS"
    SUBTITLE = "What really happens when one machine calls another"
    TAGLINE = "one request, followed down to the wire"
    RECAP = "Packets. A reliable stream. A sealed stream. A conversation."
    TRACE_ENV = "NET_TRACE"
    WPS = float(os.environ.get("NET_WPS", 2.3))  # the narrator: 138 words a minute
    VO_PAD = 1.1

    def intro_emblem(self):
        """The four layers, at the end of the title rule."""
        g = mini_stack(None, s=1.5)
        # the card centres this group on the rule's end: invisible pads keep the
        # sheets inside the frame and above the rule
        right = Rectangle(
            width=0.5, height=0.1, stroke_opacity=0, fill_opacity=0
        ).next_to(g, RIGHT, buff=0)
        below = Rectangle(
            width=0.1, height=0.62, stroke_opacity=0, fill_opacity=0
        ).next_to(g, DOWN, buff=0)
        return VGroup(g, right, below)

    # ---- narration helpers ------------------------------------------------------ #
    def glide(self, clock, to, phrase=None, floor=0.5, cap=None, also=()):
        """Run the clock to ``to`` so that it gets there on ``phrase``."""
        self.play(clock.run(to, self.span(phrase, floor=floor, cap=cap)), *also)

    def chapter(self, label, lit, color=None):
        """Section header (top left) and the stack compass (top right)."""
        color = color or (
            dict(LAYERS)[lit] if isinstance(lit, str) and lit in dict(LAYERS) else GOLD
        )
        head = self.section_header(label, color)
        compass = mini_stack(lit).move_to([6.42, 3.44, 0])
        VGroup(head, compass).set_z_index(12)
        self.play(
            FadeIn(head, shift=DOWN * 0.2),
            FadeIn(compass, shift=DOWN * 0.2),
            run_time=0.5,
        )
        return head, compass


class _Flat(_Common, Scene):
    """A flat scene whose painters draw straight onto the frame."""

    def __init__(self, **kw):
        kw.setdefault("camera_class", PainterCamera)
        super().__init__(**kw)

    def fill_app(self, app, rt=1.0):
        """The answer becomes Lea's screen."""
        return AnimationGroup(
            FadeOut(app.skeleton, run_time=rt * 0.35),
            FadeOut(app.money_bar, run_time=rt * 0.35),
            LaggedStart(
                *[FadeIn(t, shift=RIGHT * 0.1) for t in app.real],
                lag_ratio=0.14,
                run_time=rt,
            ),
            Succession(
                Wait(rt * 0.55), FadeIn(app.money, scale=1.2, run_time=rt * 0.45)
            ),
        )

    PIC_Y, PIC_X, PIC_W = -1.05, 4.08, 5.0
    WIRE_Y = 2.42

    def devices(self, y=None):
        """The phone (left) and the server (right) of the top band."""
        y = self.WIRE_Y if y is None else y
        return phone_icon(0.86).move_to([-6.42, y, 0]), server_icon(0.86).move_to(
            [6.38, y, 0]
        )

    # ---- the five lines and the stack they stand on (scenes 1 and 9) -------------- #
    def code_and_stack(self):
        lines = client_lines()
        panel, rows = code_panel(
            [(0, ln) for ln in lines],
            CLIENT_COLORS,
            title="client.py",
            fs=19,
            target_w=8.4,
            line_buff=0.2,
        )
        panel.move_to([0, 1.12, 0])
        dots = VGroup(*[
            Dot(radius=0.062, color=LINE_COLOR[i]).next_to(r, LEFT, buff=0.15) for i, r in enumerate(rows)
        ])  # fmt: skip
        for d, r in zip(dots, rows, strict=True):
            d.set_y(r.get_center()[1])
        sheets = Sheets((0.5, -1.8), w=5.6, skew=(1.5, 0.42), gap=0.56)
        return panel, rows, dots, sheets

    # ====================================================================== #
    # 1 · One request
    # ====================================================================== #
    def scene_request(self):
        km, trips3 = GEO["km"], LEDGER["fresh_https"]
        assert (
            10_700 < km < 10_760
            and 52 < ONE_WAY < 53
            and trips3["round_trips"] == 3
            and 314 < trips3["ms"] < 317
        )
        atlas = Atlas()
        self.chapter("1 · One request", None)
        note = self.note(
            "Delays: the physical minimum for light in optical fibre along the great circle (a model, not a measurement)."
        )

        # ---- 1.1 a tap, an answer ------------------------------------------------------------ #
        app = phone_app((0.0, -0.45))
        whole = VGroup(app, app.skeleton, app.real, app.money, app.money_bar)
        whole.scale(1.18).move_to([0, -0.42, 0])
        waiting = VGroup(app.skeleton, app.money_bar)
        self.voice(
            "Léa, a courier in Paris, taps her screen. A third of a second later, at "
            "best, her next deliveries are there. They came from a server in Singapore."
        )
        self.play(
            FadeIn(app, shift=UP * 0.2), FadeIn(waiting), FadeIn(note), run_time=0.8
        )
        self.cue("taps her screen", ambient=lambda rt: [Shimmer(waiting, rt)])
        touch = Circle(radius=0.16, stroke_color=INK, stroke_width=5).move_to(
            app.slot.get_center() + DOWN * 0.1
        )
        watch = Clock(0.0)
        stop = always_redraw(
            lambda: line_txt(
                f"{min(watch.t, trips3['ms']):.0f} ms", fs=30, font=MONO
            ).move_to([2.6, -0.3, 0])
        )
        self.play(FadeIn(touch, scale=0.4, run_time=0.15), run_time=0.15)
        self.add(stop)
        self.play_unstretched(
            touch.animate.scale(3.2).set_stroke(opacity=0.0), watch.run(trips3["ms"], trips3["ms"] / 1000),
            run_time=trips3["ms"] / 1000,
        )  # fmt: skip
        self.remove(touch)
        best = label("at best", fs=18).move_to([2.6, -0.76, 0])
        self.play(self.fill_app(app, 0.5), FadeIn(best, shift=UP * 0.1, run_time=0.4))
        self.cue("They came from", ambient=lambda rt: [Throb(app.money, rt, amp=0.08)])

        # ---- 1.2 the trip ------------------------------------------------------------------------ #
        paris, singa = city_dot(atlas.paris, HERO_C), city_dot(atlas.singapore, INK)
        n_p = label("Paris", fs=20, color=INK).next_to(paris, UP, buff=0.14)
        srv = server_icon(0.62).next_to(singa, RIGHT, buff=0.22)
        n_s = label("Singapore", fs=20, color=INK).next_to(
            VGroup(singa, srv), UP, buff=0.16
        )
        mini = phone_icon(0.66).move_to(atlas.paris + LEFT * 0.44)
        self.play(
            whole.animate.scale(0.14).move_to(mini).set_opacity(0.0),
            FadeIn(mini, scale=4.0),
            FadeOut(stop, run_time=0.4),
            FadeOut(best, run_time=0.4),
            FadeIn(atlas.land, run_time=1.2),
            run_time=1.2,
        )
        whole = mini
        self.play(
            FadeIn(paris),
            FadeIn(n_p),
            FadeIn(singa),
            FadeIn(n_s),
            FadeIn(srv, shift=LEFT * 0.2),
            run_time=0.7,
        )

        def here(rt):
            """Rings spreading from the server: this is where the answer came from."""
            rings = [
                Circle(radius=0.12, stroke_color=INK, stroke_width=3).move_to(
                    atlas.singapore
                )
                for _ in range(3)
            ]
            return [
                LaggedStart(
                    *[Succession(FadeIn(r, run_time=0.01), r.animate(run_time=rt * 0.5).scale(5).set_stroke(opacity=0.0)) for r in rings],
                    lag_ratio=0.5, run_time=rt,
                )
            ]  # fmt: skip

        self.hold(ambient=here)
        self.voice(
            "Ten thousand seven hundred kilometres away. Even light, in glass fibre, "
            "needs more than fifty milliseconds for that trip. And before the answer "
            "arrived, the trip was made six times: three round trips."
        )
        road = atlas.arc()
        mid = road.point_from_proportion(0.5)
        dist = line_txt(f"{km:,.0f} km", fs=26, weight="BOLD").move_to(
            mid + UP * 0.42 + RIGHT * 0.5
        )
        self.play(Create(road), run_time=1.5)
        self.play(FadeIn(dist, shift=UP * 0.1), run_time=0.4)
        self.cue("Even light")
        watch.set(0.0)

        def reads(t):  # 52.5 one way, 105 there and back: the two must add up on screen
            return f"{t:.1f} ms" if t < 100 else f"{t:.0f} ms"

        ms = always_redraw(
            lambda: line_txt(reads(watch.t), fs=24, font=MONO, color=HERO_C).move_to(
                mid + DOWN * 0.5 + LEFT * 0.4
            )
        )
        self.add(ms)
        rt = self.span("And before the answer", floor=2.4)
        self.play(
            ShowPassingFlash(
                atlas.arc(color=HERO_C, width=7), time_width=0.3, run_time=rt
            ),
            watch.run(ONE_WAY, rt),
        )
        rt = self.span("the trip was made", floor=1.2)
        self.play(
            ShowPassingFlash(
                atlas.back(color=HERO_C, width=7), time_width=0.3, run_time=rt
            ),
            watch.run(RTT, rt),
        )
        # in real time: six crossings in a third of a second
        there = [atlas.arc(color=INK, width=7), atlas.back(color=INK, width=7)]
        for k in range(6):
            self.play_unstretched(
                ShowPassingFlash(there[k % 2].copy(), time_width=0.6),
                run_time=ONE_WAY / 1000,
            )
        self.wait(0.4)
        # and again, slowly: three round trips
        blocks = trips([TCP_C, TLS_C, HTTP_C], unit=1.3, h=0.5, gap=0.08).move_to(
            [-3.55, -2.3, 0]
        )
        total = label(
            f"3 round trips: at least {trips3['ms']:.0f} ms", fs=20, color=INK
        ).next_to(blocks, DOWN, buff=0.16)
        base = SurroundingRectangle(
            VGroup(blocks, total), buff=0.26, corner_radius=0.14
        )
        base.set_stroke(FAINT, width=2).set_fill(BG, opacity=0.9)
        self.play(FadeIn(base), FadeOut(ms), FadeOut(note), run_time=0.4)
        for k, c in enumerate((TCP_C, TLS_C, HTTP_C)):
            go, come = atlas.arc(color=c, width=7), atlas.back(color=c, width=7)
            self.play(
                Succession(
                    ShowPassingFlash(go, time_width=0.35, run_time=0.7),
                    ShowPassingFlash(come, time_width=0.35, run_time=0.7),
                ),
                GrowFromEdge(blocks[k], LEFT, run_time=1.4, rate_func=linear),
            )
        self.play(FadeIn(total, shift=UP * 0.1), run_time=0.5)
        self.hold(ambient=lambda rt: [Throb(blocks, rt, amp=0.05)])

        # ---- 1.3 five steps ---------------------------------------------------------------------------- #
        panel, rows, dots, sheets = self.code_and_stack()
        self.voice(
            "Why three? Because her app does not send one message. It runs five small "
            "steps: find the server's address, open a connection, secure it, send a "
            "request, read the reply."
        )
        self.cue(
            "It runs five", ambient=lambda rt: [Throb(blocks, rt, amp=0.08, period=0.9)]
        )
        on_map = [
            atlas.land,
            paris,
            singa,
            n_p,
            n_s,
            srv,
            road,
            dist,
            whole,
            base,
            blocks,
            total,
        ]
        frame = VGroup(*[m for m in panel if m is not panel.code])
        code = VGroup(panel, dots)
        up = panel.get_center()[1]
        code.shift(DOWN * (up + 0.25))  # alone on screen at first: in the middle of it
        self.play(*[FadeOut(m) for m in on_map], run_time=0.5)
        self.play(FadeIn(frame, shift=UP * 0.15), run_time=0.4)
        for i, phrase in enumerate(
            (
                "find the server",
                "open a connection",
                "secure it",
                "send a request",
                "read the reply",
            )
        ):
            self.cue(phrase)
            self.play(
                FadeIn(rows[i], shift=RIGHT * 0.2),
                FadeIn(dots[i], scale=0.4),
                run_time=0.5,
            )
        self.hold(
            ambient=lambda rt: [
                LaggedStart(
                    *[Indicate(d, color=INK, scale_factor=1.9) for d in dots],
                    lag_ratio=0.3,
                    run_time=rt,
                )
            ]
        )

        # ---- 1.4 a stack -------------------------------------------------------------------------------- #
        self.voice(
            "Each step speaks a protocol, and each protocol relies on the one below. So "
            "start at the bottom: what does a network really carry?"
        )
        layers = [VGroup(sheets.sheet[n], sheets.name[n]) for n in sheets.names]
        for k, g in enumerate(layers):
            g[0].shift(DOWN * sheets.gap * k)  # all four start folded onto the lowest
        self.play(
            code.animate.shift(UP * (up + 0.25)),
            *[FadeIn(g[0]) for g in layers],
            run_time=0.7,
        )
        self.play(
            *[g[0].animate.shift(UP * sheets.gap * k) for k, g in enumerate(layers)],
            run_time=1.2,
        )
        self.play(
            LaggedStart(
                *[FadeIn(g[1], shift=RIGHT * 0.15) for g in layers], lag_ratio=0.2
            ),
            run_time=0.7,
        )
        self.cue("and each protocol relies")
        self.play(
            LaggedStart(
                *[
                    g[0].animate(rate_func=there_and_back).set_fill(opacity=0.55)
                    for g in reversed(layers)
                ],
                lag_ratio=0.35,
            ),
            run_time=1.8,
        )
        self.cue("start at the bottom")
        clock = Clock(0.0)
        flow = SheetFlow(clock, sheets)
        flow.only = ("IP",)
        self.add(flow)
        self.play(
            *[
                g[0].animate.set_fill(opacity=0.04).set_stroke(opacity=0.3)
                for g in layers[1:]
            ],
            *[g[1].animate.set_opacity(0.3) for g in layers[1:]],
            *[m.animate.set_opacity(0.3) for m in (*rows, *dots)],
            layers[0][0].animate.set_fill(opacity=0.4),
            clock.run(RTT * 3, self.span(None, floor=3.2)),
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 2 · Packets
    # ====================================================================== #
    def scene_packets(self):
        roads = Roads()
        f = roads.facts
        assert f["sent"] == 158 and len(f["lost"]) == 9 and f["arrived"] == 149
        assert HTTP["map"]["bytes"]["body"] // 1000 == 230
        clock = Clock(-1.0)
        ROW = {"a": 2.74, "b": 2.05, "c": 1.36}
        COL = {4: 3.6, 3: 1.2, 2: -1.2, 1: -3.6}
        nodes = {f"{r}{c}": (COL[c], ROW[r]) for r in ROW for c in COL}
        nodes.update(S=(5.9, 2.05), P=(-6.0, 2.05))
        phone, srv = self.devices(2.05)
        mesh = Mesh(clock, roads, nodes)
        mesh.edges = 0.0
        routers = VGroup(
            *[router_icon().move_to([*nodes[k], 0]) for k in nodes if k not in "SP"]
        ).set_z_index(4)
        got = Picture(
            (-self.PIC_X, self.PIC_Y), self.PIC_W, drive=roads_drive(clock, roads)
        )
        src = Picture((self.PIC_X, self.PIC_Y), self.PIC_W)
        links = VGroup(
            Line([-6.42, 1.56, 0], [-6.42, got.top() + 0.06, 0]),
            Line([6.38, 1.56, 0], [6.38, src.top() + 0.06, 0]),
        ).set_stroke(FAINT, width=2)
        self.chapter("2 · Packets", "IP")
        note = self.note(
            "A model of best-effort delivery, exaggerated to be visible. Map data © OpenStreetMap contributors."
        )

        # ---- 2.1 a name becomes an address ---------------------------------------------- #
        ip_s = tag(SERVER_IP, IP_C, fs=16)
        ip_s.move_to([6.2 - ip_s.width / 2, 1.2, 0])
        ip_p = tag(PHONE_IP, IP_C, fs=16)
        ip_p.move_to([-6.24 + ip_p.width / 2, 1.2, 0])
        LY = -0.75
        big_name = line_txt(HOST, fs=29, font=MONO).move_to([-3.55, LY, 0])
        book = VGroup(
            RoundedRectangle(width=1.05, height=1.25, corner_radius=0.12)
            .set_stroke(DNS_C, width=3)
            .set_fill(PANEL, 1),
            *[
                Line(LEFT * 0.3, RIGHT * 0.3)
                .set_stroke(DNS_C, width=3)
                .shift(UP * (0.3 - 0.2 * k))
                for k in range(4)
            ],
        ).move_to([0.2, LY, 0])
        pages = VGroup(*book[1:])
        dns = label("DNS", fs=20, color=DNS_C, weight="BOLD").next_to(
            book, DOWN, buff=0.16
        )
        big_ip = line_txt(
            SERVER_IP, fs=29, font=MONO, color=IP_C, weight="BOLD"
        ).move_to([3.5, LY, 0])
        ask_a = arr(
            big_name.body.get_right(),
            book.get_left(),
            color=MUTED,
            sw=3.5,
            buff=0.14,
            tip=0.17,
        )
        ans_a = arr(
            book.get_right(),
            big_ip.body.get_left(),
            color=IP_C,
            sw=3.5,
            buff=0.14,
            tip=0.17,
        )

        self.voice(
            "First, the address. A directory service, DNS, turns the server's name "
            "into a number: an IP address. Every machine on the Internet has one."
        )
        self.play(
            FadeIn(phone),
            FadeIn(srv),
            FadeIn(big_name, shift=UP * 0.15),
            FadeIn(note),
            run_time=0.7,
        )
        self.cue("A directory", ambient=lambda rt: [Throb(big_name, rt, amp=0.04)])
        self.play(FadeIn(book, scale=0.7), FadeIn(dns), GrowArrow(ask_a), run_time=0.6)
        rt = self.span("into a number", floor=0.9)
        self.play(
            LaggedStart(
                *[
                    ln.animate(rate_func=there_and_back).set_stroke(INK, width=5)
                    for ln in pages
                ],
                lag_ratio=0.3,
            ),
            run_time=rt,
        )
        self.play(GrowArrow(ans_a), FadeIn(big_ip, shift=RIGHT * 0.3), run_time=0.6)
        self.cue("Every machine", ambient=lambda rt: [Throb(big_ip, rt, amp=0.06)])
        lookup = VGroup(big_name, book, dns, ask_a, ans_a)
        self.play(
            TransformFromCopy(big_ip, ip_s), FadeIn(ip_p, shift=UP * 0.1), run_time=1.0
        )
        self.hold(
            ambient=lambda rt: [Throb(ip_p, rt, amp=0.1), Throb(ip_s, rt, amp=0.1)]
        )
        self.play(FadeOut(lookup), FadeOut(big_ip), run_time=0.4)

        # ---- 2.2 cut into packets ---------------------------------------------------------- #
        self.voice(
            "Now the server sends Léa the map of her course: two hundred and thirty "
            "kilobytes. No network carries that in one piece. It is cut into packets "
            "of at most fifteen hundred bytes, each stamped with its destination."
        )
        size_b = HTTP["map"]["bytes"]["body"]
        meter = Clock(0.0)
        size_n = always_redraw(
            lambda: line_txt(f"{meter.t:,.0f}", fs=27, font=MONO).move_to([0, 0.36, 0])
        )
        size_l = label("bytes", fs=16).move_to([0, 0.0, 0])
        self.add(size_n)
        rt = self.span("No network carries", floor=2.4)
        self.play(
            FadeIn(src), FadeIn(got), FadeIn(links), FadeIn(size_l),
            Tween(src, reveal=1.0, run_time=rt, rate_func=linear), meter.run(size_b, rt, rate_func=smooth),
        )  # fmt: skip
        # the whole picture, in one piece, does not fit the wire
        ghost = (
            Rectangle(width=src.w, height=src.h)
            .move_to(src.at)
            .set_stroke(INK, width=3)
            .set_fill(INK, opacity=0.08)
        )
        ghost.set_z_index(6)
        rt = self.span("It is cut", floor=2.6)
        self.play(ghost.animate.scale(0.2).move_to([5.3, 2.05, 0]), run_time=rt * 0.36)
        self.play(
            ghost.animate.set_stroke(LOST_C).set_fill(LOST_C, opacity=0.3),
            run_time=rt * 0.08,
        )
        self.play(
            Wiggle(ghost, scale_value=1.3, rotation_angle=0.03 * TAU, n_wiggles=8),
            run_time=rt * 0.4,
        )
        self.play(FadeOut(ghost, shift=DOWN * 0.4), run_time=rt * 0.16)
        many_n = line_txt(str(f["sent"]), fs=27, font=MONO).move_to([0, 0.36, 0])
        many_l = label("packets", fs=16).move_to([0, 0.0, 0])
        size_n.clear_updaters()
        self.play(
            Tween(src, slices=1.0, run_time=1.2),
            FadeOut(size_n, shift=UP * 0.1, run_time=0.35), FadeOut(size_l, run_time=0.35),
            self.then(FadeIn(many_n, shift=UP * 0.1, run_time=0.45), 0.4),
            self.then(FadeIn(many_l, run_time=0.45), 0.4),
        )  # fmt: skip
        self.cue(
            "each stamped",
            ambient=lambda rt: [
                Breathe(src, rt, attr="slices", lo=0.3, hi=1.0, period=1.0)
            ],
        )
        src.slices = 1.0
        card = packet_card(0).move_to([0, -1.25, 0])
        cap_c = label("1,500 bytes at most", fs=16).next_to(card, DOWN, buff=0.16)
        self.play(
            FadeIn(card, shift=LEFT * 0.5, scale=0.6), FadeIn(cap_c), run_time=0.7
        )
        self.hold(ambient=lambda rt: [Throb(card.head, rt, amp=0.06, period=0.9)])

        # ---- 2.3 hop by hop ------------------------------------------------------------------ #
        self.voice(
            "Routers pass each packet along, hop by hop, looking only at that address. "
            "Packets may take different roads, and overtake each other. And a router "
            "that is overwhelmed simply drops what it cannot hold."
        )
        self.add(mesh)
        self.play(
            Tween(mesh, edges=1.0, run_time=0.9),
            LaggedStart(
                *[FadeIn(r, scale=0.4) for r in routers], lag_ratio=0.06, run_time=0.9
            ),
            FadeOut(card, shift=RIGHT * 1.5 + UP * 1.2, scale=0.3, run_time=0.8),
            FadeOut(cap_c, run_time=0.4),
            Tween(src, slices=0.0, run_time=0.8),
        )
        arrived = always_redraw(
            lambda: line_txt(str(roads.arrived(clock.t)), fs=27, font=MONO).move_to(
                many_n
            )
        )
        of = label(f"of {f['sent']} arrived", fs=16).move_to(many_l)
        self.remove(many_n)
        self.add(arrived)
        self.play(
            clock.run(26, self.span("Packets may take")),
            FadeOut(many_l, run_time=0.3),
            self.then(FadeIn(of, run_time=0.4), 0.3),
        )
        self.glide(clock, 58, "And a router")
        halo = (
            Circle(radius=0.3, stroke_color=HERO_C, stroke_width=4)
            .move_to([*nodes[roads.slow], 0])
            .set_z_index(5)
        )
        rt = self.span(None)
        self.play(
            clock.run(112, rt),
            Succession(
                FadeIn(halo, scale=1.5, run_time=0.4),
                Wait(max(0.2, rt - 1.2)),
                FadeOut(halo, run_time=0.5),
            ),
        )

        # ---- 2.4 best effort ------------------------------------------------------------------- #
        vo = (
            "This is all the Internet Protocol promises: its best effort. In this run, "
            "nine packets of the picture never arrived, and nobody was told."
        )
        self.play(FadeOut(note), run_time=0.3)
        self.play(
            self.tell("The network promises nothing: only its best effort.", vo),
            clock.run(165, self.span("nine packets", floor=1.5)),
        )
        got.marks = tuple(roads.lost)
        nine = line_txt(str(len(roads.lost)), fs=27, font=MONO, color=LOST_C).move_to(
            [0, -1.0, 0]
        )
        nine_l = label("never arrived", fs=16, color=LOST_C).move_to([0, -1.42, 0])
        self.play(FadeIn(nine, scale=1.3), FadeIn(nine_l), run_time=0.5)
        self.settle(
            ambient=lambda rt: [
                Breathe(got, rt, attr="flag", lo=0.25, hi=1.0, period=1.0)
            ]
        )
        self.wipe()

    # ====================================================================== #
    # 3 · A connection
    # ====================================================================== #
    def scene_connect(self):
        quiet, refused = KERNEL["silence"], KERNEL["refused"]
        syn_s, gave_up = quiet["syn_s"], quiet["kernel"]["gave_up_s"]
        assert (
            syn_s[:8] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 11.0]
            and round(gave_up) == 75
        )
        assert refused["text"] == "[Errno 61] Connection refused" and refused["ms"] < 5
        assert quiet["kernel"]["text"] == "[Errno 60] Operation timed out"
        Y, XP, XS = self.WIRE_Y, -5.95, 5.86
        TOP = 1.55
        phone, srv = self.devices()
        wire = Line([XP, Y, 0], [XS, Y, 0]).set_stroke(FAINT, width=2.2)
        self.chapter("3 · A connection", "TCP")
        note = self.note(
            "Packets: a model of TCP. Errors and timers: this Mac's kernel (Linux: Errno 111 and 110, about 2 minutes)."
        )

        # ---- 3.1 a port ---------------------------------------------------------------- #
        machine = port_panel(
            (0.9, -0.9),
            [(22, "ssh", "sshd"), (80, "http", None), (443, "https", "dispatch api"), (5432, "postgres", None)],
            w=5.6,
        )  # fmt: skip
        zoom = Line(
            srv.get_bottom() + DOWN * 0.08, machine.box.get_corner(UR) + LEFT * 0.3
        ).set_stroke(FAINT, width=2)
        door = port_tag(443, True).move_to([6.38, 1.62, 0])
        self.voice(
            "TCP repairs all this, and it starts with a connection. On the server, a "
            "program listens on a numbered door, a port: four four three, by "
            "convention, for HTTPS."
        )
        self.play(FadeIn(phone), FadeIn(srv), Create(wire), FadeIn(note), run_time=0.9)
        self.cue(
            "On the server",
            ambient=lambda rt: [
                stream(Line([XS, Y, 0], [XP, Y, 0]), IP_C, n=9, run_time=rt, lag=0.1)
            ],
        )
        self.play(
            Create(zoom), FadeIn(machine.box), FadeIn(machine[1]),
            LaggedStart(*[FadeIn(machine.line[p], shift=RIGHT * 0.2) for p in machine.line], lag_ratio=0.25),
            run_time=1.2,
        )  # fmt: skip
        live = VGroup(machine.program[22], machine.program[443])
        self.cue(
            "four four three", ambient=lambda rt: throbs(live, rt, amp=0.08, period=0.9)
        )
        others = VGroup(*[machine.line[p] for p in machine.line if p != 443])
        self.play(
            others.animate.set_opacity(0.3),
            machine.door[443].animate.scale(1.25),
            run_time=0.7,
        )
        self.hold(
            ambient=lambda rt: [Throb(machine.program[443], rt, amp=0.08, period=0.9)]
        )

        # ---- 3.2 three packets, one round trip --------------------------------------------- #
        clock = Clock(-1.0)
        shake = TCP["handshake"]
        ends = {">": (XP, XS), "<": (XS, XP)}
        ev = [
            dict(
                t0=h["t0"],
                t1=h["t1"],
                xa=ends[h["way"]][0],
                xb=ends[h["way"]][1],
                color=TCP_C,
            )
            for h in shake
        ]
        K = 0.0242
        ladder = Ladder(clock, ev, XP, XS, TOP, K, y_min=-3.05)
        flags = [
            ride(
                tag(h["flags"], TCP_C, fs=16).set_z_index(6),
                clock,
                h["t0"],
                h["t1"],
                *ends[h["way"]],
                Y,
            )
            for h in shake
        ]
        self.voice(
            "The phone sends a packet flagged SYN: let's synchronise. The server "
            "answers SYN, ACK. The phone acknowledges. This is the handshake: three "
            "packets, one round trip, and each side knows the other is there. No data "
            "has moved yet."
        )
        self.play(
            FadeIn(ladder), FadeOut(machine), FadeOut(zoom),
            FadeIn(door, shift=RIGHT * 2.0 + UP * 1.4),
            run_time=0.8,
        )  # fmt: skip
        self.add(*flags)
        self.glide(clock, shake[0]["t1"], "The server answers")
        # one way 52.5 ms, there and back 105 ms: the two labels must add up
        t_syn = label(f"{shake[0]['t1']:.1f} ms", fs=16).move_to(
            [6.4, ladder.y(shake[0]["t1"]), 0]
        )
        t_syn.shift(LEFT * max(0.0, t_syn.get_right()[0] - 6.74))
        t_0 = label("0 ms", fs=16).move_to([-6.45, ladder.y(0) - 0.02, 0])
        self.add(t_0, t_syn)
        self.glide(clock, shake[1]["t1"], "The phone acknowledges")
        t_ack = label(f"{shake[1]['t1']:.0f} ms", fs=16).move_to(
            [-6.45, ladder.y(shake[1]["t1"]), 0]
        )
        self.add(t_ack)
        self.glide(clock, shake[2]["t1"], "This is the handshake")
        trip = (
            VGroup(
                line_txt("the handshake: 1 round trip", fs=25, weight="BOLD"),
                label(f"at least {RTT:.0f} ms from Paris to Singapore", fs=17),
            )
            .arrange(DOWN, buff=0.08)
            .move_to([-2.9, ladder.y(shake[0]["t1"]) + 0.02, 0])
        )
        self.play(FadeIn(trip, shift=RIGHT * 0.2), run_time=0.6)
        # the connection exists: from now on, a pipe between the two programs
        tube = RoundedRectangle(width=XS - XP, height=0.42, corner_radius=0.21).move_to(
            [(XP + XS) / 2, Y, 0]
        )
        tube.set_stroke(TCP_C, width=2.8).set_fill(TCP_C, opacity=0.08)
        legs = [
            Line(
                [ends[h["way"]][0], ladder.y(h["t0"]), 0],
                [ends[h["way"]][1], ladder.y(h["t1"]), 0],
            )
            for h in shake
        ]

        def thrice(rt):
            return [
                LaggedStart(
                    *[ShowPassingFlash(m.copy().set_stroke(INK, width=6).set_z_index(3), time_width=0.5) for m in legs],
                    lag_ratio=0.6, run_time=rt,
                )
            ]  # fmt: skip

        self.cue("and each side knows", ambient=thrice)
        self.play(Create(tube), run_time=1.0)
        self.hold(
            ambient=lambda rt: [
                Throb(trip[0], rt, amp=0.06),
                tube.animate(rate_func=there_and_back, run_time=rt).set_fill(
                    opacity=0.3
                ),
            ]
        )

        # ---- 3.3 refused ----------------------------------------------------------------------- #
        clock2 = Clock(-1.0)
        d = ONE_WAY
        ev2 = [
            dict(t0=0, t1=d, xa=XP, xb=XS, color=TCP_C),
            dict(t0=d, t1=2 * d, xa=XS, xb=XP, color=LOST_C),
        ]
        ladder2 = Ladder(clock2, ev2, XP, XS, TOP, K, y_min=-3.05)
        syn2 = ride(tag("SYN", TCP_C, fs=16).set_z_index(6), clock2, 0, d, XP, XS, Y)
        rst = ride(
            tag("RST", LOST_C, fs=16).set_z_index(6), clock2, d, 2 * d, XS, XP, Y
        )
        closed = port_tag(8080).move_to(door)
        self.voice(
            "If no program listens on that port, the machine itself answers at once "
            "with a reset: connection refused. The failure is instant."
        )
        self.play(
            FadeOut(ladder), FadeOut(trip), FadeOut(t_0), FadeOut(t_syn), FadeOut(t_ack), FadeOut(tube),
            FadeOut(door, shift=UP * 0.1), run_time=0.5,
        )  # fmt: skip
        for m in flags:
            m.clear_updaters()
            self.remove(m)
        self.play(FadeIn(ladder2), FadeIn(closed, shift=UP * 0.1), run_time=0.5)
        self.add(syn2, rst)
        self.glide(clock2, d, "answers at once", floor=1.2)
        self.glide(clock2, 2 * d, "connection refused", floor=1.2)
        no = error_chip(refused["text"], fs=19).move_to([-2.4, ladder2.y(d) - 0.05, 0])
        self.play(FadeIn(no, shift=RIGHT * 0.2), run_time=0.5)
        self.hold(ambient=lambda rt: [Throb(no, rt, amp=0.04)])

        # ---- 3.4 silence -------------------------------------------------------------------------- #
        clock3 = Clock(-0.5)
        XW = 0.0
        line = Timeline(clock3, syn_s, -5.6, 5.6, -1.25, gave_up)
        wall = wall_icon().move_to([XW, Y, 0]).set_z_index(6)
        self.voice(
            "But if a firewall silently drops the packet, nothing comes back. The "
            "phone asks again after one second, and again, then waits longer and "
            "longer, and gives up: here, after seventy-five seconds."
        )
        gone = [syn2, rst]
        fast = label("one round trip", fs=17)
        self.play(
            FadeOut(ladder2), FadeOut(closed, shift=UP * 0.1),
            no.animate.move_to([-3.3, 1.02, 0]),
            run_time=0.6,
        )  # fmt: skip
        for m in gone:
            m.clear_updaters()
            self.remove(m)
        fast.next_to(no, RIGHT, buff=0.3)
        door.move_to([6.38, 1.62, 0])
        self.play(
            FadeIn(wall, scale=0.6),
            FadeIn(line),
            FadeIn(door),
            FadeIn(fast),
            run_time=0.6,
        )

        def knocks(a, b, rt):
            """The SYNs that leave between clock times a and b, timed inside a play of rt."""
            out = []
            for s_k in syn_s:
                if a <= s_k < b:
                    k = tag("SYN", TCP_C, fs=16).set_z_index(5)
                    out.append(
                        Succession(
                            Wait((s_k - a) / (b - a) * rt + 1e-3),
                            Travel(
                                k,
                                Line([XP + 0.4, Y, 0], [XW - 0.5, Y, 0]),
                                run_time=0.45,
                                rate_func=linear,
                            ),
                        )
                    )
            return out

        def tick(sec):
            return label(f"{sec:.0f} s", fs=16).move_to([line.x(sec), line.y - 0.36, 0])

        def stretch(a, b, phrase, floor=1.0, marks=(), trim=0.0):
            rt = self.span(phrase, floor=floor)
            if trim:
                rt = max(0.5, rt - trim)
            anims = [clock3.run(b, rt), *knocks(a, b, rt)]
            for sec in marks:
                anims.append(
                    Succession(
                        Wait((sec - a) / (b - a) * rt + 0.15),
                        FadeIn(tick(sec), run_time=0.25),
                    )
                )
            self.play(*anims)

        now = always_redraw(
            lambda: line_txt(
                f"{min(max(clock3.t, 0), gave_up):.0f} s", fs=22, font=MONO
            ).move_to([min(max(line.x(clock3.t), -5.25), 5.2), line.y + 1.06, 0])
        )
        stretch(-0.5, 0.7, "The phone asks again", floor=1.4)
        self.add(now)
        stretch(0.7, 5.6, "then waits longer", marks=(1, 5))
        stretch(5.6, 40.0, "and gives up", marks=(11, 19, 35))
        stretch(
            40.0, gave_up, None, floor=2.0, marks=(67,), trim=1.0
        )  # it gives up as the number is said
        out = error_chip(quiet["kernel"]["text"], fs=19).move_to([3.1, -2.55, 0])
        slow = label(f"{gave_up:.0f} seconds", fs=17).next_to(out, LEFT, buff=0.3)
        self.play(FadeIn(out, shift=UP * 0.15), FadeIn(slow), run_time=0.5)
        self.hold(ambient=lambda rt: [Throb(out, rt, amp=0.04)])

        # ---- 3.5 fast or slow: where to look -------------------------------------------------------- #
        self.voice(
            "A refusal is fast, a timeout is slow, and that alone tells you where to "
            "look. Refused: something answered no. Usually the machine itself: nothing "
            "listens on that port. "
            "Timed out: a firewall, most often; or an address where no machine answers."
        )
        self.play(
            VGroup(no, fast).animate(rate_func=there_and_back).scale(1.1), run_time=0.9
        )
        self.cue("a timeout is slow")
        self.play(
            VGroup(out, slow).animate(rate_func=there_and_back).scale(1.1), run_time=0.9
        )
        self.cue("Refused", ambient=lambda rt: [Throb(wall, rt, amp=0.16, period=1.0)])
        # refused: the packet gets there, and the machine itself says no
        shut = port_tag(8080).move_to(door)
        there = Line([XP + 0.4, Y, 0], [XS - 0.5, Y, 0])
        self.play(
            FadeOut(wall, run_time=0.5), FadeOut(door, run_time=0.25), self.then(FadeIn(shut, run_time=0.3), 0.25),
            srv.animate(rate_func=there_and_back, run_time=0.6).scale(1.18),
        )  # fmt: skip
        rt = max(1.1, (self.span("Timed out", floor=2.2) - 0.9) / 2)
        self.play(
            Travel(
                tag("SYN", TCP_C, fs=16).set_z_index(6),
                there,
                run_time=rt,
                rate_func=linear,
            )
        )
        self.play(
            Travel(
                tag("RST", LOST_C, fs=16).set_z_index(6),
                Line(there.get_end(), there.get_start()),
                run_time=rt,
                rate_func=linear,
            )
        )
        self.play(
            VGroup(no, fast).animate(rate_func=there_and_back).scale(1.1), run_time=0.7
        )
        self.cue("Timed out")
        # timed out: the packet never gets an answer
        self.play(
            FadeIn(wall, scale=0.6, run_time=0.5), FadeOut(shut, run_time=0.25), self.then(FadeIn(door, run_time=0.3), 0.25),
        )  # fmt: skip
        self.play(
            Travel(
                tag("SYN", TCP_C, fs=16).set_z_index(5),
                Line([XP + 0.4, Y, 0], [XW - 0.5, Y, 0]),
                run_time=0.8,
                rate_func=linear,
            )
        )
        self.play(wall.animate(rate_func=there_and_back).scale(1.25), run_time=0.6)
        self.cue("or an address")
        self.play(
            FadeOut(wall), FadeOut(door), srv.animate.set_opacity(0.14), run_time=0.6
        )
        self.play(
            Travel(
                tag("SYN", TCP_C, fs=16).set_z_index(5),
                there,
                run_time=1.5,
                rate_func=linear,
            )
        )
        self.settle(ambient=lambda rt: [Throb(out, rt, amp=0.05, period=1.0)])
        self.wipe()

    # ====================================================================== #
    # 4 · A reliable stream
    # ====================================================================== #
    def scene_stream(self):
        tr = Transfer()
        f = tr.facts
        assert (
            f["flights"][:4] == [10, 20, 40, 80]
            and f["lost"] == [92]
            and f["segments"] == 158
        )
        clock = Clock(-4.0)
        Y = self.WIRE_Y
        phone, srv = self.devices()
        wire = Wire(clock, tr, -5.95, 5.86, Y)
        got = Picture(
            (-self.PIC_X, self.PIC_Y), self.PIC_W, drive=receiver_drive(clock, tr)
        )
        got.cursor = True
        src = Picture(
            (self.PIC_X, self.PIC_Y), self.PIC_W, drive=sender_drive(clock, tr)
        )
        src.reveal = 1.0
        src.flight = (0, 0)
        links = VGroup(
            Line([-6.42, Y - 0.5, 0], [-6.42, got.top() + 0.06, 0]),
            Line([6.38, Y - 0.5, 0], [6.38, src.top() + 0.06, 0]),
        ).set_stroke(FAINT, width=2)

        self.chapter("4 · A reliable stream", "TCP")
        note = self.note(
            "A model of TCP. This Mac's own kernel also starts at 10 packets. Map © OpenStreetMap contributors."
        )
        self.add(note)

        # ---- centre column: what the phone has in order, how much the server dares --- #
        def count():
            return f"{min(tr.acked_bytes(clock.t), f['bytes']):,}"

        lab_a = label("received, in order", fs=17).move_to([0, 0.62, 0])
        val_a = always_redraw(
            lambda: line_txt(count(), fs=27, font=MONO).move_to([0, 0.2, 0])
        )
        unit_a = label("bytes", fs=16).move_to([0, -0.14, 0])
        chart = WindowChart(clock, tr, (0, -1.72), w=2.36, h=1.46)
        lab_w = label("congestion window", fs=17).move_to([0, -2.78, 0])

        def win():
            return f"{tr.sender(clock.t)[2]:.0f} packets"

        val_w = always_redraw(
            lambda: line_txt(win(), fs=19, font=MONO, color=TCP_C).move_to(
                [0, -0.72, 0]
            )
        )

        # ---- 4.1 numbered bytes, acknowledgments ---------------------------------- #
        self.voice(
            "Once connected, TCP numbers every byte. Each packet says where its bytes "
            "belong, so the phone can put them back in order. And for each packet it "
            "receives, it answers with an acknowledgment: I have everything up to here."
        )
        self.play(
            FadeIn(phone), FadeIn(srv), FadeIn(wire), FadeIn(links),
            FadeIn(src), FadeIn(got), run_time=0.9,
        )  # fmt: skip
        first = tr.data[: f["flights"][0]]
        up_y, down_y = Y + 0.17 + 0.37, Y - 0.17 - 0.37

        def numbered(r):
            t = tag(
                ("byte " if r["seq"] == 0 else "") + f"{r['seq']:,}",
                TCP_C,
                fs=14,
                pad=(0.2, 0.14),
            )
            lead = Line(
                t.get_top(), t.get_top() + UP * (Y + 0.04 - down_y - t.height / 2)
            ).set_stroke(TCP_C, width=2)
            return VGroup(t, lead).set_z_index(6)

        riders = []
        for r in (first[0], first[-1]):
            m = numbered(r)
            off = m.get_center()[1] - m[0].get_center()[1]
            riders.append(ride(m, clock, r["t0"], r["t1"], 5.86, -5.95, down_y + off))
        last_ack = tr.acks[len(first) - 1]
        riders.append(
            ride(tag(f"ack {last_ack['ack']:,}", TCP_C, fs=14, fill=0.0, tcolor=INK, pad=(0.2, 0.14)).set_z_index(6),
                 clock, last_ack["t0"], last_ack["t1"], -5.95, 5.86, down_y)
        )  # fmt: skip
        riders[-1].box.set_stroke(TCP_C, width=2)
        del up_y
        self.add(*riders)
        self.glide(clock, 30, "so the phone")
        self.glide(clock, 58, "And for each")
        self.add(val_a)
        self.play(
            clock.run(100, self.span(None, floor=3.0)), FadeIn(lab_a), FadeIn(unit_a)
        )

        # ---- 4.2 slow start ----------------------------------------------------------- #
        self.voice(
            "The server starts carefully: ten packets. Each acknowledgment that comes "
            "back lets it send two more. Twenty packets in the second round trip: this "
            "is slow start. Forty in the third: its congestion window doubles every "
            "time. And in the fourth, eighty."
        )
        self.add(val_w)
        self.play(
            clock.run(104.6, self.span("Each acknowledgment")),
            FadeIn(chart),
            FadeIn(lab_w),
        )
        # in slow motion: each acknowledgment that lands lets two packets leave
        self.glide(clock, 111.0, "two more")
        # then the number on screen is the number being said: 20, 40, 80
        w20, w40, w80 = (
            next(w["t"] for w in tr.window if w["shown"] >= k) for k in (20, 40, 80)
        )
        assert w20 < 119.5 and w40 < 224 and w80 < 338.5, (w20, w40, w80)
        self.glide(clock, 119.5, "Twenty packets")
        self.glide(clock, 224, "Forty in the third")
        self.glide(clock, 338.5, "eighty")
        drop = tr.lost[0]["t0"] + Wire.DROP * ONE_WAY  # where the next line begins
        self.glide(clock, drop - 2.5, None)

        # ---- 4.3 a loss ------------------------------------------------------------------ #
        hole, resend = tr.holes[0], tr.resent[0]
        assert drop < hole[1] < resend["t0"] < hole[2], (drop, hole, resend)
        self.voice(
            "Then a packet is lost. The phone keeps what follows, but cannot hand it to "
            "the app: there is a hole. Its acknowledgments repeat the same number. "
            "Three repeats, and the server sends that packet again, and cuts its "
            "window: to TCP, a loss means congestion."
        )
        self.glide(
            clock, drop + 6, "The phone keeps"
        )  # it falls off the wire as the line begins
        self.glide(
            clock, hole[1] + 14, "there is a hole"
        )  # what follows arrives, and waits (the picture flags the hole)
        self.glide(clock, 414, "Its acknowledgments")
        self.glide(clock, resend["t0"] - 3.6, "Three repeats")
        self.glide(
            clock, resend["t0"] - 0.3, "and the server sends"
        )  # the three repeats land
        self.glide(clock, 452, "and cuts its window")
        cut = SurroundingRectangle(
            VGroup(val_w, lab_w), buff=0.14, corner_radius=0.12
        ).set_stroke(HERO_C, width=3)
        cut.stretch_to_fit_width(chart.w + 0.3)
        rt = self.span(None, floor=2.0)
        self.play(
            clock.run(470, rt),
            Succession(
                FadeIn(cut, run_time=0.3),
                Wait(max(0.2, rt - 1.0)),
                FadeOut(cut, run_time=0.5),
            ),
        )

        # ---- 4.4 the promise ----------------------------------------------------------------- #
        vo = (
            "One more round trip, and the hole is filled: the picture is complete, "
            "every byte, in order. That is TCP's promise: bytes go in at one end, and "
            "the same bytes come out at the other."
        )
        self.play(FadeOut(note), run_time=0.3)
        self.play(
            self.tell(
                "TCP: bytes go in at one end and come out at the other, in order.", vo
            ),
            run_time=0.6,
        )
        self.glide(clock, hole[2] + 1.5, "the hole is filled")
        self.glide(clock, 548, "That is TCP")
        self.play(
            ripple(Rectangle(width=got.w, height=got.h).move_to(got.at), color=OK_C),
            run_time=0.9,
        )
        # the same bytes, in the same order, at both ends
        left = max(2.0, self.time_left(0.4))
        n = max(1, round(left / 4.2))
        for _ in range(n):
            src.scan = got.scan = 0.0
            rt = left / n
            self.play(
                Tween(src, scan=1.0, run_time=rt * 0.9, rate_func=linear),
                Succession(
                    Wait(rt * 0.1),
                    Tween(got, scan=1.0, run_time=rt * 0.9, rate_func=linear),
                ),
            )
        src.scan = got.scan = None
        self.settle()
        self.wipe()


def head_rows(text):
    """The lines of an HTTP head, with one empty line where the head ends."""
    lines = text.split("\r\n")
    return lines[: lines.index("")] + [""]


def wrap_json(body, width=44):
    """A long JSON line cut after a comma (for display only)."""
    out = []
    while len(body) > width:
        k = body.rindex(",", 0, width) + 1
        out.append(body[:k])
        body = body[k:]
    return out + [body]


class _Talk(_Flat):
    """The scenes where two programs talk down a pipe (HTTP, the tap, HTTPS)."""

    X0, X1 = -5.95, 5.86
    APP_AT, SRV_AT = (-5.66, -0.74), (5.56, 0.5)
    ROUTES = ("/courses/{id}", "/courses/{id}/map", "/courses/{id}/eta", "/health")

    def stage(self, clock, routes=True):
        """Pipe, phone and server: the frame of every conversation."""
        pipe = Pipe(clock, self.X0, self.X1, self.WIRE_Y)
        app = phone_app(self.APP_AT)
        srv = server_icon(1.7).move_to([*self.SRV_AT, 0])
        links = VGroup(
            Line(
                [self.APP_AT[0], self.WIRE_Y - 0.21, 0],
                [self.APP_AT[0], app.body.get_top()[1], 0],
            ),
            Line(
                [self.SRV_AT[0], self.WIRE_Y - 0.21, 0],
                [self.SRV_AT[0], srv.get_top()[1], 0],
            ),
        ).set_stroke(TCP_C, width=2.6, opacity=0.55)
        chips = VGroup()
        if routes:
            for k, r in enumerate(self.ROUTES):
                c = tag(r, FAINT, fs=15, fill=0.0, tcolor=MUTED, weight="MEDIUM")
                c.box.set_stroke(FAINT, width=2)
                c.move_to([self.SRV_AT[0], -0.82 - 0.46 * k, 0])
                chips.add(c)
        return pipe, app, srv, links, chips

    def cards(self, edge=FAINT):
        req = Card(head_rows(HTTP["request"]), (-0.3, 1.74), title="request", edge=edge)
        res = Card(
            head_rows(HTTP["head"]) + wrap_json(HTTP["body"]), (-0.3, -0.42), title="response", body_rows=2,
            edge=edge,
        )  # fmt: skip
        return req, res

    def passing(self, pipe, t0, n, x=0.0, way=">"):
        """Clock times between which a train of ``n`` cells sent at ``t0`` passes ``x``."""
        dist = (x - pipe.x0) if way == ">" else (pipe.x1 - x)
        return t0 + dist / pipe.speed(), t0 + (dist + n * pipe.PITCH) / pipe.speed()

    # ====================================================================== #
    # 5 · HTTP
    # ====================================================================== #
    def scene_http(self):
        cases = {c["case"]: c for c in STORY["status"]}
        assert [
            cases[k]["status"][:3] for k in ("ok", "unknown", "anonymous", "bug")
        ] == ["200", "404", "401", "500"]
        assert (
            STORY["keep_alive"]["connections_when_reused"] == 1
            and STORY["keep_alive"]["connections_when_fresh"] == 3
        )
        clock = Clock(-5.0)
        pipe, app, srv, links, chips = self.stage(clock)
        req, res = self.cards()
        req.dim()
        res.dim()
        n_req = HTTP["bytes"]["request"] // 4
        n_res = (HTTP["bytes"]["head"] + HTTP["bytes"]["body"]) // 4
        self.chapter("5 · HTTP", "HTTP")
        note = self.note(
            "Recorded between two programs on this machine, in the clear. Map © OpenStreetMap contributors."
        )

        # ---- 5.1 a request ------------------------------------------------------------- #
        self.voice(
            "On that stream, the two programs can finally talk. Their language is "
            "HTTP: in its classic form, plain text. A request: a method, GET; a path, "
            "which says what is wanted; then headers, one per line, and an empty line "
            "to say: I am done."
        )
        self.play(
            FadeIn(pipe), FadeIn(links), FadeIn(app), FadeIn(app.skeleton), FadeIn(app.money_bar),
            FadeIn(srv), FadeIn(chips), FadeIn(note), run_time=0.9,
        )  # fmt: skip
        idle = VGroup(app.skeleton, app.money_bar)
        self.cue(
            "Their language",
            ambient=lambda rt: [Shimmer(idle, rt), Breathe(pipe, rt, lo=0.0, hi=0.9)],
        )
        self.play(*[FadeIn(m, shift=UP * 0.1) for m in req.mobs()], run_time=0.6)
        self.cue(
            "A request",
            ambient=lambda rt: [Shimmer(idle, rt), Breathe(pipe, rt, lo=0.0, hi=0.9)],
        )
        landed = pipe.send(0.0, ">", n_req, HTTP_C)
        self.play(
            Tween(
                req,
                sent=req.total(),
                run_time=self.span("a method", floor=1.0),
                rate_func=linear,
            ),
            clock.run(14, self.span("a method", floor=1.0)),
        )
        m_get = req.mark(0, "GET")
        self.play(FadeIn(m_get), clock.run(24, self.span("a path", floor=0.8)))
        m_path = req.mark(0, "/courses/lea")
        self.play(
            FadeOut(m_get),
            FadeIn(m_path),
            clock.run(40, self.span("then headers", floor=0.8)),
        )
        m_head = VGroup(*[req.mark(i, color=HTTP_C) for i in (1, 2, 3)])
        self.play(
            FadeOut(m_path),
            LaggedStart(*[FadeIn(m) for m in m_head], lag_ratio=0.3),
            clock.run(56, self.span("an empty line", floor=0.8)),
        )
        blank = req.blank.copy().set_stroke(HERO_C, width=5, opacity=1)
        self.play(
            FadeOut(m_head),
            FadeIn(blank),
            clock.run(landed, self.span(None, floor=1.0)),
        )

        # ---- 5.2 a response ---------------------------------------------------------------- #
        self.voice(
            "The server reads the path, finds the function in charge, and answers in "
            "the same style: a status line, headers, an empty line, and the body. "
            "Here, Léa's course, as JSON."
        )
        flyer = req.find(0, "/courses/lea").copy().set_color(HERO_C)
        self.add(flyer)
        route = chips[0]
        lit = tag(self.ROUTES[0], HTTP_C, fs=15).move_to(route)
        self.play(
            FadeOut(blank),
            flyer.animate.scale(0.83).move_to(route).set_opacity(0.0),
            Succession(Wait(0.55), FadeIn(lit, run_time=0.35)),
            run_time=0.9,
        )
        self.remove(flyer)
        self.cue(
            "and answers", ambient=lambda rt: [Throb(lit, rt, amp=0.1, period=0.8)]
        )
        t_res = landed + 6
        back = pipe.send(t_res, "<", n_res, HTTP_C)
        clock.set(t_res - 1)
        self.play(*[FadeIn(m) for m in res.mobs()], run_time=0.5)
        self.play(
            Tween(
                res,
                sent=res.total(),
                run_time=self.span("a status line", floor=1.0),
                rate_func=linear,
            ),
            clock.run(t_res + 16, self.span("a status line", floor=1.0)),
        )
        m_status = res.mark(0, "200 OK", color=OK_C)
        self.play(
            FadeIn(m_status), clock.run(t_res + 30, self.span("headers", floor=0.6))
        )
        m_h2 = VGroup(*[res.mark(i, color=HTTP_C) for i in (1, 2)])
        self.play(
            FadeOut(m_status),
            FadeIn(m_h2),
            clock.run(t_res + 42, self.span("an empty line", floor=0.6)),
        )
        blank2 = res.blank.copy().set_stroke(HERO_C, width=5, opacity=1)
        self.play(
            FadeOut(m_h2),
            FadeIn(blank2),
            clock.run(t_res + 52, self.span("and the body", floor=0.6)),
        )
        m_body = SurroundingRectangle(
            VGroup(res.rows[4].body, res.rows[5].body), buff=0.08, corner_radius=0.07
        )
        m_body.set_stroke(HERO_C, width=2.5).set_fill(HERO_C, opacity=0.10)
        self.play(
            FadeOut(blank2),
            FadeIn(m_body),
            clock.run(back, self.span("Here", floor=0.6)),
        )
        self.play(self.fill_app(app, 1.3), FadeOut(lit, run_time=0.5))
        self.hold(ambient=lambda rt: [Throb(app.money, rt, amp=0.06)])

        # ---- 5.3 status codes ---------------------------------------------------------------- #
        self.voice(
            "The status code says how it went. Two hundred: fine. Four hundred and "
            "four: the caller asked for something that does not exist. Four hundred "
            "and one: the caller did not say who is asking. Five hundred: the server "
            "itself failed. So read the first digit: four, the caller's mistake; five, "
            "the server's."
        )
        legend = (
            VGroup(
                verdict("2xx", OK_C),
                verdict("4xx", HERO_C, "phone"),
                verdict("5xx", LOST_C, "server"),
            )
            .arrange(RIGHT, buff=0.9)
            .move_to([-0.3, -3.36, 0])
        )
        m_status = res.mark(0, "200 OK", color=OK_C)
        self.play(FadeOut(m_body), FadeIn(m_status), FadeOut(note), run_time=0.5)
        res.sent = req.sent = None

        def dip(m, rt, lo=0.2):
            """``m`` dims while the answer is on its way, and comes back with it. One
            animation: two ``.animate`` builders on one mobject would share a target."""

            def at(mob, alpha):
                t = alpha * rt
                v = (
                    1 - t / 0.25
                    if t < 0.25
                    else (t - rt * 0.62) / (rt * 0.3)
                    if t > rt * 0.62
                    else 0.0
                )
                mob.set_opacity(lo + (1 - lo) * min(1.0, max(0.0, v)))

            return UpdateFromAlphaFunc(m, at, run_time=rt, rate_func=linear)

        def retry(case, color, phrase, floor=1.0):
            """Send a variant of the request; the real answer is back when ``phrase`` is said."""
            c = cases[case]
            anims = []
            if req.rows[0].string != c["request_line"]:
                old, new = req.swap(0, c["request_line"])
                anims += [
                    FadeOut(old, run_time=0.25),
                    self.then(FadeIn(new, run_time=0.3), 0.25),
                ]
            want = c["has_token"]
            anims.append(
                req.rows[2].animate(run_time=0.4).set_opacity(1.0 if want else 0.16)
            )
            old_s, new_s = res.swap(0, "HTTP/1.1 " + c["status"])
            old_l, new_l = res.swap(2, f"Content-Length: {len(c['body'])}")
            body = wrap_json(c["body"]) + [""]
            old_b, new_b = res.swap(4, body[0])
            old_c, new_c = res.swap(5, body[1] or " ")
            box = res.mark(0, c["status"], color=color)
            t0 = clock.t + 2
            up = pipe.send(t0, ">", n_req, HTTP_C)
            down = pipe.send(up + 4, "<", max(8, (71 + len(c["body"])) // 4), HTTP_C)
            rt = self.span(phrase, floor=floor)
            self.play(
                *anims,
                dip(res.rows[1], rt),
                FadeOut(self.status_box, run_time=0.25),
                *[FadeOut(m, run_time=0.25) for m in (old_s, old_l, old_b, old_c)],
                clock.run(down, rt),
                Succession(
                    Wait(rt * 0.62),
                    AnimationGroup(
                        *[FadeIn(m) for m in (new_s, new_l, new_b, new_c, box)],
                        run_time=rt * 0.3,
                    ),
                ),
            )
            self.status_box = box

        def stays(rt):
            return [Throb(self.status_box, rt, amp=0.1, period=0.9)]

        self.status_box = m_status
        self.cue("Two hundred", ambient=stays)
        self.play(FadeIn(legend[0], shift=UP * 0.1), run_time=0.5)
        # each request leaves when its number starts being said: the answer lands with the
        # number, and stays on screen until the next number
        self.cue("Four hundred and four", ambient=stays)
        retry("unknown", HERO_C, "the caller asked", floor=1.6)
        self.play(FadeIn(legend[1], shift=UP * 0.1), run_time=0.4)
        self.cue("Four hundred and one", ambient=stays)
        retry("anonymous", HERO_C, "the caller did not say", floor=1.6)
        self.cue("Five hundred", ambient=stays)
        retry("bug", LOST_C, "itself failed", floor=1.6)
        self.play(
            FadeIn(legend[2], shift=UP * 0.1),
            srv.leds.animate.set_color(LOST_C),
            run_time=0.4,
        )
        self.cue("So read the first digit", ambient=stays)
        digit = res.mark(0, "5", color=LOST_C)
        self.play(
            FadeOut(self.status_box, run_time=0.25),
            self.then(FadeIn(digit, scale=1.3, run_time=0.35), 0.25),
        )
        self.status_box = digit
        for v, phrase in (
            (legend[1], "four, the caller"),
            (legend[2], "five, the server"),
        ):
            self.cue(phrase)
            self.play(v.animate(rate_func=there_and_back).scale(1.25), run_time=0.8)
        self.hold(ambient=lambda rt: [Throb(legend, rt, amp=0.05)])

        # ---- 5.4 no memory -------------------------------------------------------------------- #
        self.voice(
            "HTTP is stateless: nothing in the protocol ties a request to the one "
            "before. So every request must carry everything, including who is asking. "
            "That is what this token is for."
        )
        self.play(srv.leds.animate.set_color(OK_C), FadeOut(legend), run_time=0.4)
        into = Line(
            [self.SRV_AT[0], self.WIRE_Y - 0.21, 0],
            [self.SRV_AT[0], srv.get_center()[1] + 0.25, 0],
        )
        self.cue(
            "So every request",
            ambient=lambda rt: [stream(into, HTTP_C, n=5, run_time=rt, lag=0.2)],
        )
        retry("ok", OK_C, "including who", floor=1.6)
        m_tok = req.mark(2, color=HERO_C)
        self.play(FadeIn(m_tok), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(m_tok, rt, amp=0.07, period=0.9)])

        # ---- 5.5 keep the connection ------------------------------------------------------------ #
        self.voice(
            "Opening a connection for every request costs two round trips each time. "
            "Keep the connection, and the next request costs one: that is keep-alive. "
            "HTTP 2 goes further: several requests travel at once on the same "
            "connection."
        )
        gone = [m for c in (req, res) for m in c.mobs()] + [m_tok, self.status_box]
        self.play(*[FadeOut(m) for m in gone], run_time=0.5)
        T, H = TCP_C, HTTP_C
        three = [H, HERO_C, "#F4A261"]
        rows = [
            ("a new connection for every request", [T, H, T, H, T, H], None),
            ("keep-alive: one connection, one request at a time", [T, H, H, H], None),
            ("HTTP/2: the three at once, on the same connection", [T, H], {1: 3}),
        ]
        lanes = []
        for k, (name, colors, stacked) in enumerate(rows):
            y = 0.95 - 1.3 * k
            lab = label(name, fs=18, color=INK).move_to([0, y + 0.42, 0])
            lab.shift(RIGHT * (-3.75 - lab.get_left()[0]))
            blocks = trips(colors, unit=0.6, stacked=stacked)
            blocks.shift(
                [-3.75 - blocks.get_left()[0], y - 0.12 - blocks.get_center()[1], 0]
            )
            cols, i = [], 0
            for j in range(len(colors)):  # a column: what one round trip carries
                n = (stacked or {}).get(j, 1)
                cols.append(VGroup(*blocks[i : i + n]))
                i += n
            total = label(f"{len(colors)} round trips", fs=18, color=MUTED)
            total.move_to([0, y - 0.12, 0]).shift(RIGHT * (0.55 - total.get_left()[0]))
            lanes.append((lab, cols, total, colors))
        key = VGroup(
            VGroup(
                VGroup(
                    trips([T], unit=0.3, h=0.2), label("opening the connection", fs=16)
                ).arrange(RIGHT, buff=0.14),
                VGroup(
                    trips([H], unit=0.3, h=0.2), label("request and response", fs=16)
                ).arrange(RIGHT, buff=0.14),
            ).arrange(RIGHT, buff=0.6),
            label(
                f"one block: one round trip, at least {RTT:.0f} ms between Paris and Singapore",
                fs=16,
            ),
        ).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        key.shift([-3.75 - key.get_left()[0], -2.95 - key.get_center()[1], 0])
        TRIP = (
            2 * ONE_WAY + 12
        )  # clock units for one round trip down the pipe and back, trains included
        BEAT = 0.75  # seconds per round trip, the same in every lane: fewer trips, sooner done

        def lane(k, *also):
            """Lane ``k``: each block grows while its round trip crosses the pipe."""
            lab, cols, total, colors = lanes[k]
            t0 = clock.t + 2
            for j, c in enumerate(colors):
                kw = dict(colors=three) if len(cols[j]) > 1 else {}
                pipe.send(t0 + j * TRIP, ">", 9 if kw else 4, c, **kw)
                pipe.send(t0 + j * TRIP + ONE_WAY + 5, "<", 12 if kw else 6, c, **kw)
            grow = [
                AnimationGroup(
                    *[GrowFromEdge(b, LEFT) for b in col],
                    run_time=BEAT,
                    rate_func=linear,
                )
                for col in cols
            ]
            self.play(
                FadeIn(lab, shift=RIGHT * 0.15, run_time=0.4),
                Succession(*grow),
                clock.run(t0 + len(colors) * TRIP, BEAT * len(colors)),
                *also,
            )
            self.play(FadeIn(total, shift=LEFT * 0.1), run_time=0.3)

        # a connection of its own for every request: the tube closes, another opens
        reopen = []
        for _ in range(3):
            reopen += [
                Tween(pipe, alpha=1.0, run_time=0.2),
                Wait(2 * BEAT - 0.4),
                Tween(pipe, alpha=0.22, run_time=0.2),
            ]
        lane(0, FadeIn(key, run_time=0.5), Succession(*reopen))
        self.cue("Keep the connection")
        lane(
            1,
            Tween(pipe, alpha=1.0, run_time=0.25),
            Tween(pipe, glow=1.0, run_time=0.8),
        )
        self.cue(
            "HTTP 2 goes further",
            ambient=lambda rt: [Breathe(pipe, rt, lo=0.35, hi=1.0)],
        )
        pipe.glow = 1.0
        lane(2)
        img = app_map(app)
        self.play(FadeIn(img), run_time=0.6)
        # the same three requests, side by side: six round trips, four, two
        race = []
        for _lab, cols, total, colors in lanes:
            n = len(colors)
            y = min(c.get_bottom()[1] for c in cols) - 0.09
            under = Line([cols[0].get_left()[0], y, 0], [cols[-1].get_right()[0], y, 0])
            race.append(
                Create(
                    under.set_stroke(INK, width=4), run_time=BEAT * n, rate_func=linear
                )
            )
            race.append(
                Succession(
                    Wait(BEAT * n),
                    total.animate(rate_func=there_and_back, run_time=0.5).scale(1.15),
                )
            )
        self.play(*race)
        self.settle(ambient=lambda rt: [Throb(lanes[2][1][1], rt, amp=0.04)])
        self.wipe()

    # ====================================================================== #
    # 6 · In the clear
    # ====================================================================== #
    def scene_tap(self):
        tap = STORY["tap"]
        assert (
            tap["stolen_token"]
            and tap["replay"]["status"] == "200 OK"
            and tap["replay"]["courier"] == "lea"
        )
        assert tap["altered"] == {"sent": 24.4, "received": 2.44, "status": "200 OK"}
        clock = Clock(-5.0)
        pipe, app, srv, links, _ = self.stage(clock, routes=False)
        req, res = self.cards()  # the exchange of scene 5, about to be watched
        req.dim()
        res.dim()
        n_req = HTTP["bytes"]["request"] // 4
        n_res = (HTTP["bytes"]["head"] + HTTP["bytes"]["body"]) // 4
        XT = 0.0
        hops = VGroup(
            *[
                router_icon(0.14).move_to([x, self.WIRE_Y, 0])
                for x in (-4.1, -2.3, 2.3, 4.1)
            ]
        ).set_z_index(5)
        eye = eye_icon().move_to([XT, self.WIRE_Y + 0.6, 0]).set_z_index(6)
        knot = (
            Dot(radius=0.075, color=LOST_C).move_to([XT, self.WIRE_Y, 0]).set_z_index(6)
        )
        stem = Line(
            [XT, self.WIRE_Y - 0.21, 0], [XT, req.box.get_top()[1], 0]
        ).set_stroke(LOST_C, width=2.6)
        self.chapter("6 · In the clear", "HTTP", color=LOST_C)
        note = self.note(
            "Recorded on this machine: a relay between the two programs read, reused and rewrote the exchange."
        )

        # ---- 6.1 anyone on the path can read ------------------------------------------------ #
        self.voice(
            "There is a problem. Those packets cross networks that belong to "
            "strangers: a café's Wi-Fi, then several operators. Anyone on the path "
            "can read every byte: the path, the answer, and the token, which is all "
            "it takes to pass for Léa."
        )
        self.play(
            FadeIn(pipe), FadeIn(links), FadeIn(app), FadeIn(app.skeleton), FadeIn(app.money_bar),
            FadeIn(srv), FadeIn(note), *[FadeIn(m) for m in (*req.mobs(), *res.mobs())], run_time=0.8,
        )  # fmt: skip
        idle = VGroup(app.skeleton, app.money_bar)
        self.cue("Those packets cross", ambient=lambda rt: [Shimmer(idle, rt)])
        landed = pipe.send(0.0, ">", n_req, HTTP_C)
        a1, b1 = self.passing(pipe, 0.0, n_req, XT)
        self.play(
            LaggedStart(
                *[FadeIn(h, scale=0.4) for h in hops], lag_ratio=0.2, run_time=1.2
            ),
            clock.run(a1 - 6, self.span("Anyone on the path", floor=1.2)),
        )
        self.play(
            FadeIn(eye, shift=DOWN * 0.15), FadeIn(knot), Create(stem),
            req.box.animate.set_stroke(LOST_C), res.box.animate.set_stroke(LOST_C),
            clock.run(a1, 0.7),
        )  # fmt: skip
        self.play(
            clock.run(b1, self.span("read every byte", floor=1.4)),
            Tween(
                req,
                sent=req.total(),
                run_time=self.span("read every byte", floor=1.4),
                rate_func=linear,
            ),
        )
        t_res = landed + 4
        back = pipe.send(t_res, "<", n_res, HTTP_C)
        a2, b2 = self.passing(pipe, t_res, n_res, XT, "<")
        self.glide(clock, a2, "the path, the answer", floor=0.8)
        rt = self.span("and the token", floor=1.4)
        self.play(
            clock.run(b2, rt),
            Tween(res, sent=res.total(), run_time=rt, rate_func=linear),
        )
        m_tok = req.mark(2, "Bearer lea-4f1c9a", color=LOST_C)
        self.play(
            FadeIn(m_tok, scale=1.1), clock.run(back, 0.9), self.fill_app(app, 1.0)
        )
        self.cue("which is all it takes")
        # the tap asks for itself, with the token it read
        t0 = clock.t + 2
        there = pipe.send(t0, ">", n_req, LOST_C, a=XT)
        home = pipe.send(there + 4, "<", n_res, LOST_C, b=XT)
        # the proof that the token is enough: the server's answer to the tap. It stays on screen.
        thief = VGroup(
            phone_icon(0.56, LOST_C), tag(tap["replay"]["status"], LOST_C, fs=18)
        ).arrange(RIGHT, buff=0.14)
        thief.move_to([XT + 1.7, self.WIRE_Y + 0.6, 0]).set_z_index(6)
        flyer = req.find(2, "Bearer lea-4f1c9a").copy().set_color(LOST_C)
        self.add(flyer)
        rt = self.span(None, floor=3.0)
        self.play(
            flyer.animate(run_time=0.8)
            .move_to([XT, self.WIRE_Y, 0])
            .scale(0.5)
            .set_opacity(0),
            clock.run(home, rt),
            Succession(
                Wait(rt * 0.72), FadeIn(thief, shift=LEFT * 0.15, run_time=rt * 0.14)
            ),
        )
        self.remove(flyer)

        # ---- 6.2 ... and change it ---------------------------------------------------------------- #
        self.voice(
            "They can also change bytes on the way. Twenty-four euros forty becomes "
            "two forty-four, and the phone has no way to know."
        )
        req.sent = res.sent = None
        pipe.tap = XT
        t0 = clock.t + 2
        up = pipe.send(t0, ">", n_req, HTTP_C)
        hit = n_res - 3
        down = pipe.send(up + 4, "<", n_res, HTTP_C, bad=range(hit - 1, hit + 1))
        a3, _ = self.passing(pipe, up + 4, n_res, XT, "<")
        self.play(
            FadeOut(m_tok), clock.run(a3, self.span("Twenty-four euros", floor=2.0))
        )
        last = res.rows[5].string
        old, new = res.swap(5, last.replace("24.4", "2.44"))
        m_bad = res.mark(5, "2.44", color=LOST_C)
        self.play(
            FadeOut(old, run_time=0.25), self.then(FadeIn(new, run_time=0.3), 0.25),
            self.then(FadeIn(m_bad, scale=1.2, run_time=0.3), 0.5),
            clock.run(down, self.span("and the phone", floor=2.2)),
        )  # fmt: skip
        wrong = line_txt(
            f"€{tap['altered']['received']:.2f}", fs=26, color=LOST_C, weight="BOLD"
        ).move_to(app.money)
        self.play(
            FadeOut(app.money, run_time=0.25),
            self.then(FadeIn(wrong, scale=1.25, run_time=0.4), 0.25),
        )
        self.settle(
            ambient=lambda rt: [
                Throb(wrong, rt, amp=0.14, period=0.9),
                Throb(eye, rt, amp=0.2, period=0.9),
            ]
        )
        self.wipe()

    # ====================================================================== #
    # 7 · HTTPS
    # ====================================================================== #
    def scene_sealed(self):
        tls, fail, kx = TLS, STORY["tls_failures"], STORY["key_agreement"]
        chain, trusted = (
            STORY["certificates"]["chain"],
            STORY["certificates"]["trusted_on_this_machine"],
        )
        assert (
            tls["version"] == "TLSv1.3" and tls["client_hello"]["server_name"] == HOST
        )
        assert [f["way"] for f in tls["flights"][:3]] == [">", "<", ">"], (
            "one round trip, then the request"
        )
        assert trusted == 195 and [c["subject"].split(",")[0] for c in chain] == [
            f"CN={HOST}", "CN=Demo Issuing CA", "CN=Demo Root CA"]  # fmt: skip
        assert fail["impostor"]["reason"] == "self-signed certificate"
        assert fail["one_bit_flipped"]["text"].startswith("[SSL] record layer failure")
        assert (
            tls["request"]["record_bytes"] == 139
            and LEDGER["fresh_https"]["round_trips"] == 3
        )
        clock = Clock(-5.0)
        pipe, app, srv, links, _ = self.stage(clock, routes=False)
        Y, XT = self.WIRE_Y, 0.0
        eye = eye_icon().move_to([XT, Y + 0.6, 0]).set_z_index(6)
        knot = Dot(radius=0.075, color=LOST_C).move_to([XT, Y, 0]).set_z_index(6)
        self.chapter("7 · HTTPS", "TLS")
        note = self.note(
            "Recorded on this machine: a real TLS 1.3 handshake. A demo authority stands in for a public one."
        )

        # ---- 7.1 one more layer; two secrets ------------------------------------------------- #
        self.voice(
            "HTTPS closes both holes by slipping one more protocol, TLS, between TCP "
            "and HTTP. It begins with a handshake of its own. Each side invents a "
            "secret number, and sends the other a public value computed from it."
        )
        st = Sheets((0.4, -0.35), w=4.6)
        top = VGroup(st.sheet["HTTP"], st.name["HTTP"]).shift(DOWN * st.gap)
        low = st.group(["IP", "TCP"])
        mid = VGroup(st.sheet["TLS"], st.name["TLS"])
        self.play(
            FadeIn(low, shift=UP * 0.2),
            FadeIn(top, shift=UP * 0.2),
            FadeIn(note),
            run_time=0.8,
        )
        self.cue("slipping one more", ambient=lambda rt: [Throb(top, rt, amp=0.03)])
        self.play(top.animate.shift(UP * st.gap), run_time=0.8)
        self.play(FadeIn(mid, shift=LEFT * 2.2), run_time=0.9)
        hand = Clock(
            2 * ONE_WAY
        )  # the request's third and fourth crossings: the TLS handshake
        shake = SheetFlow(hand, st)
        self.add(shake)
        self.cue("It begins with", ambient=lambda rt: [hand.run(4 * ONE_WAY, rt)])
        self.play(
            FadeOut(low), FadeOut(top), FadeOut(mid), FadeOut(shake),
            FadeIn(pipe), FadeIn(links), FadeIn(app), FadeIn(app.skeleton), FadeIn(app.money_bar), FadeIn(srv),
            FadeIn(eye), FadeIn(knot), run_time=0.9,
        )  # fmt: skip
        XP, XS, CELL = -2.55, 2.6, 0.165
        sec = {x: secret_box(CELL) for x in (XP, XS)}
        for x, m in sec.items():
            m.shift([x - m.row.get_center()[0], 0.9 - m.row.get_center()[1], 0])
        pub = {
            XP: key_row(kx["public_client"], cell=CELL),
            XS: key_row(kx["public_server"], cell=CELL),
        }
        for x, m in pub.items():
            m.move_to([x, 0.9, 0])
        # "a handshake of its own": the two hellos cross on the TCP stream (sizes to scale)
        hello = pipe.send(
            clock.t + 2, ">", max(4, tls["flights"][0]["bytes"] // 24), TLS_C
        )
        answer = pipe.send(
            hello + 3, "<", max(4, tls["flights"][1]["bytes"] // 24), TLS_C
        )
        self.cue("Each side invents", ambient=lambda rt: [clock.run(answer, rt)])
        clock.set(answer)
        self.play(*[FadeIn(m, scale=0.8) for m in sec.values()], run_time=0.7)
        self.cue("and sends the other")
        self.play(
            *[m.animate.move_to([x, 1.62, 0]) for x, m in pub.items()], run_time=0.8
        )
        for m in pub.values():
            m.set_z_index(7)
        seen = []
        for x, other, slot in ((XP, XS, 1.66), (XS, XP, 1.3)):
            m = pub[x]
            copy = m.copy().scale(0.7).move_to([XT, Y, 0]).set_z_index(6)
            seen.append(copy)
            self.play(m.animate.scale(0.7).move_to([x, Y, 0]), run_time=0.5)
            self.play(
                m.animate(run_time=1.5).move_to([other, Y, 0]),
                Succession(
                    Wait(0.72),
                    FadeIn(copy, run_time=0.05),
                    copy.animate(run_time=0.6).move_to([XT, slot, 0]).scale(0.82),
                ),
            )
            self.play(m.animate.scale(1 / 0.7).move_to([other, 1.62, 0]), run_time=0.5)
        self.hold(
            ambient=lambda rt: [*throbs(seen, rt, amp=0.08), Throb(eye, rt, amp=0.2)]
        )

        # ---- 7.2 the same key on both sides ------------------------------------------------------- #
        self.voice(
            "Mixing its own secret with the other's public value, each side arrives at "
            "the same key. The eavesdropper saw both public values, and cannot compute it."
        )
        shared = {
            x: key_row(kx["shared"], cell=CELL, edge=HERO_C).move_to([x, 0.0, 0])
            for x in (XP, XS)
        }
        self.play(
            *[
                AnimationGroup(
                    pub[other].animate.move_to([x, 0.9, 0]).set_opacity(0.0),
                    sec[x].animate.set_opacity(0.35),
                    FadeIn(shared[x], shift=DOWN * 0.6),
                )
                for x, other in ((XP, XS), (XS, XP))
            ],
            run_time=1.4,
        )
        both = VGroup(shared[XP], shared[XS])
        self.cue(
            "arrives at the same key",
            ambient=lambda rt: throbs(both, rt, amp=0.05, period=0.9),
        )
        self.play(
            shared[XP].animate.move_to([-1.75, -1.25, 0]),
            shared[XS].animate.move_to([1.75, -1.25, 0]),
            run_time=0.9,
        )
        same = make_tick(OK_C, sw=7, scale=1.3).move_to([0, -1.25, 0])
        self.play(
            FadeIn(same, scale=0.5),
            ripple(shared[XP], shared[XS], color=OK_C),
            run_time=0.8,
        )
        self.cue("The eavesdropper saw")
        cross = make_cross(LOST_C, sw=6, scale=1.0).next_to(
            VGroup(*seen), RIGHT, buff=0.3
        )
        self.play(
            *[m.animate(rate_func=there_and_back).shift(RIGHT * 0.12) for m in seen],
            run_time=0.5,
        )
        self.play(FadeIn(cross, scale=0.5), run_time=0.4)
        self.hold(
            ambient=lambda rt: throbs(
                [shared[XP], shared[XS], same], rt, amp=0.06, period=0.9
            )
        )

        # ---- 7.3 a key shared with whom? ------------------------------------------------------------ #
        self.voice(
            "But a key shared with whom? The server must prove its name. It presents a "
            "certificate, signed by an authority, itself signed by a root that the "
            "phone already trusts: one of the couple of hundred that every system "
            "ships with. The chain holds, and the name matches."
        )
        gone = [*sec.values(), *pub.values(), *shared.values(), *seen, same, cross]
        self.play(
            *[FadeOut(m) for m in gone],
            Tween(pipe, glow=0.6, run_time=0.6),
            run_time=0.6,
        )
        pipe.hue = TLS_C
        who = line_txt("?", fs=46, color=HERO_C, weight="BOLD").move_to([3.9, 0.5, 0])
        self.play(FadeIn(who, scale=0.4), run_time=0.4)
        self.cue(
            "It presents a certificate",
            ambient=lambda rt: [Throb(who, rt, amp=0.25, period=0.9)],
        )
        CY = 1.0
        leaf = cert_card(HOST, w=3.05).move_to([2.93, CY, 0])
        mid_c = cert_card("Demo Issuing CA", w=2.45).move_to([-0.35, CY, 0])
        root = cert_card("Demo Root CA", w=2.15, color=HERO_C).move_to([-3.18, CY, 0])
        tray = trust_tray(trusted).move_to([-3.18, -1.22, 0])
        # (the count is that of the bundle this Python's OpenSSL reads, not of macOS's own store)
        tray_l = label(
            f"{trusted} authorities in this laptop's OpenSSL bundle", fs=16
        ).next_to(tray, DOWN, buff=0.16)
        tray_l.shift(RIGHT * (tray.get_left()[0] - tray_l.get_left()[0]))
        a1 = arr(
            leaf.get_left(), mid_c.get_right(), color=MUTED, sw=3.5, buff=0.07, tip=0.16
        )
        a2 = arr(
            mid_c.get_left(), root.get_right(), color=MUTED, sw=3.5, buff=0.07, tip=0.16
        )
        home = Line(root.get_bottom(), tray.mine.get_center()).set_stroke(
            HERO_C, width=2.6
        )
        ticks = [
            make_tick(OK_C, sw=4.5, scale=0.5).next_to(a, UP, buff=0.12)
            for a in (a1, a2)
        ]
        self.play(
            FadeOut(who, run_time=0.3), FadeIn(leaf, shift=LEFT * 1.2), run_time=0.8
        )
        self.cue("signed by an authority")
        self.play(GrowArrow(a1), FadeIn(mid_c, shift=LEFT * 0.4), run_time=0.8)
        self.cue("itself signed by a root")
        self.play(GrowArrow(a2), FadeIn(root, shift=LEFT * 0.4), run_time=0.8)
        self.cue(
            "one of the couple",
            ambient=lambda rt: [Throb(root, rt, amp=0.06, period=0.9)],
        )
        self.play(FadeIn(tray, shift=UP * 0.2), FadeIn(tray_l), run_time=0.6)
        # look the root up among the authorities this machine was shipped with
        cols = 15
        lines = [
            VGroup(*tray.dots[i : i + cols]) for i in range(0, len(tray.dots), cols)
        ]
        rt = max(1.0, self.span("The chain holds", floor=1.8) - 0.9)
        self.play(
            LaggedStart(
                *[
                    ln.animate(rate_func=there_and_back).set_opacity(1.0).set_color(INK)
                    for ln in lines
                ],
                lag_ratio=0.22,
            ),
            run_time=rt,
        )
        self.play(
            Create(home),
            tray.mine.animate.set_color(HERO_C).set_opacity(1).scale(2.2),
            run_time=0.8,
        )
        self.play(
            LaggedStart(
                *[FadeIn(t, scale=0.5) for t in reversed(ticks)], lag_ratio=0.5
            ),
            run_time=0.9,
        )
        asked = tag(HOST, STEEL, fs=15, fill=0.0, tcolor=INK, weight="MEDIUM")
        asked.box.set_stroke(STEEL, width=2)
        asked.move_to([2.93, 0.02, 0])
        t_name = make_tick(OK_C, sw=4.5, scale=0.6).next_to(asked, LEFT, buff=0.16)
        self.cue("and the name matches")
        self.play(
            FadeIn(asked, shift=UP * 0.15), FadeIn(t_name, scale=0.5), run_time=0.6
        )
        self.hold(ambient=lambda rt: throbs([*ticks, t_name], rt, amp=0.25, period=0.9))

        # ---- 7.4 a certificate is public: the proof is a signature ------------------------------------ #
        self.voice(
            "One thing is still missing: a certificate is public, anyone can copy it. "
            "So the server signs the handshake with the matching private key, which "
            "never leaves it."
        )
        self.cue(
            "a certificate is public",
            ambient=lambda rt: [Throb(leaf, rt, amp=0.04, period=0.9)],
        )
        stolen = leaf.copy().set_z_index(6)
        stolen.box.set_stroke(LOST_C)
        stolen.seal.set_color(LOST_C)
        self.add(stolen)
        self.play(
            stolen.animate.scale(0.62).move_to([XT + 1.62, Y + 0.7, 0]), run_time=0.9
        )
        self.cue(
            "So the server signs",
            ambient=lambda rt: [
                Throb(stolen, rt, amp=0.06, period=0.9),
                Throb(eye, rt, amp=0.2, period=0.9),
            ],
        )
        key = key_icon(0.72).move_to([self.SRV_AT[0], -0.82, 0])
        key_l = label("private key", fs=16).next_to(key, DOWN, buff=0.14)
        self.play(FadeIn(key, scale=0.5), FadeIn(key_l), run_time=0.5)
        sig = signature().move_to([self.X1 - 0.75, Y, 0]).set_z_index(7)
        self.play(FadeIn(sig, scale=0.5), run_time=0.4)
        self.play(
            sig.animate.move_to([self.X0 + 1.05, Y, 0]),
            run_time=self.span("which never leaves", floor=1.4, cap=2.4),
        )
        t_sig = (
            make_tick(OK_C, sw=4.5, scale=0.6)
            .next_to(sig, RIGHT, buff=0.16)
            .set_z_index(7)
        )
        self.play(FadeIn(t_sig, scale=0.5), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(key, rt, amp=0.18, period=0.9)])

        # ---- 7.5 an impostor -------------------------------------------------------------------------------- #
        self.voice(
            "An impostor can copy the certificate, but not that key. Its only option "
            "is a certificate of its own making, which no authority vouches for. The "
            "handshake stops right there, with an error you will meet one day: "
            "certificate verify failed."
        )
        nokey = VGroup(key_icon(0.5, LOST_C), make_cross(LOST_C, sw=5, scale=0.7))
        nokey[1].move_to(nokey[0])
        nokey.next_to(stolen, RIGHT, buff=0.22).set_z_index(6)
        self.play(
            FadeOut(sig),
            FadeOut(t_sig),
            stolen.animate(rate_func=there_and_back).scale(1.15),
            run_time=0.7,
        )
        self.cue("but not that key")
        self.play(
            FadeIn(nokey, scale=0.5),
            key.animate(rate_func=there_and_back).scale(1.3),
            run_time=0.7,
        )
        self.cue("Its only option")
        fake = cert_card(HOST, w=2.42, color=LOST_C).move_to([2.35, -1.15, 0])
        dim = VGroup(leaf, mid_c, root, a1, a2, home, asked, t_name, *ticks)
        self.play(
            dim.animate.set_opacity(0.22),
            FadeIn(fake, shift=DOWN * 1.6 + RIGHT * 1.0),
            run_time=0.9,
        )
        probe = DashedLine(
            fake.get_left(), [tray.box.get_right()[0] + 0.12, -1.15, 0], dash_length=0.1
        )
        probe.set_stroke(LOST_C, width=3)
        no = make_cross(LOST_C, sw=6, scale=0.8).move_to(probe.get_end() + RIGHT * 0.22)
        self.cue(
            "which no authority",
            ambient=lambda rt: [Throb(fake, rt, amp=0.06, period=0.8)],
        )
        self.play(Create(probe), run_time=0.8)
        self.play(FadeIn(no, scale=0.5), run_time=0.3)
        self.cue(
            "you will meet",
            ambient=lambda rt: [
                Throb(fake, rt, amp=0.06, period=0.8),
                Throb(no, rt, amp=0.2, period=0.8),
            ],
        )
        why = error_chip(
            ["certificate verify failed:", fail["impostor"]["reason"]], fs=17
        )
        why.move_to([max(1.65, tray_l.get_right()[0] + 0.4 + why.width / 2), -2.45, 0])
        self.play(FadeIn(why, shift=UP * 0.15), run_time=0.5)
        self.hold(ambient=lambda rt: [Throb(why, rt, amp=0.035)])

        # ---- 7.6 sealed records ------------------------------------------------------------------------------- #
        self.voice(
            "From then on, every byte is sealed. On the wire, the same request is "
            "noise. Flip a single bit, and the receiver rejects the whole record. "
            "What still shows: the two addresses, the size of the messages, and the "
            "server's name, in a field called SNI."
        )
        screen = tls["client_hello"]["screen"]
        k = screen.index(HOST)
        hello = screen[k - 5 : k + len(HOST) + 5]
        noise = chunks(tls["request"]["screen"], 44)
        wire = Card(
            [hello, ""] + noise,
            (-0.3, 1.52),
            title="seen on the wire",
            edge=LOST_C,
            body_rows=len(noise),
        )
        wire.title.next_to(
            wire.box, UP, buff=0.1, aligned_edge=RIGHT
        )  # the first row needs its whole width
        wire.rows[0].set_opacity(0.5)
        for r in wire.rows[2:]:
            r.set_opacity(0.0)
        stem = Line([XT, Y - 0.21, 0], [XT, wire.box.get_top()[1], 0]).set_stroke(
            LOST_C, width=2.6
        )
        self.play(
            *[
                FadeOut(m)
                for m in (
                    dim,
                    fake,
                    probe,
                    no,
                    why,
                    tray,
                    tray_l,
                    stolen,
                    nokey,
                    key,
                    key_l,
                )
            ],
            run_time=0.6,
        )
        n_req, n_res = (
            tls["request"]["record_bytes"] // 4,
            tls["reply"]["record_bytes"] // 4,
        )
        landed = pipe.send(clock.t + 3, ">", n_req, TLS_C, sealed=True)
        a1_, b1_ = self.passing(pipe, clock.t + 3, n_req, XT)
        self.play(
            *[FadeIn(m) for m in wire.mobs()],
            Create(stem),
            clock.run(a1_, self.span("On the wire", floor=1.0)),
        )
        rt = self.span("Flip a single bit", floor=1.6)
        self.play(
            clock.run(b1_ + 4, rt),
            LaggedStart(
                *[r.animate.set_opacity(0.9) for r in wire.rows[2:]],
                lag_ratio=0.35,
                run_time=rt * 0.8,
            ),
        )
        pipe.tap = XT
        back = pipe.send(landed + 4, "<", n_res, TLS_C, sealed=True, bad=[n_res // 2])
        rt = self.span("What still shows", floor=2.6)
        bang = error_chip(
            fail["one_bit_flipped"]["text"].split(" (")[0], fs=18
        ).move_to([-0.3, -2.25, 0])
        spark = Circle(radius=0.3, stroke_color=LOST_C, stroke_width=5).move_to(
            [self.APP_AT[0], Y - 0.21, 0]
        )
        self.play(
            clock.run(back, rt * 0.7),
            Succession(
                Wait(rt * 0.66),
                FadeIn(spark, scale=0.3, run_time=0.2),
                FadeOut(spark, scale=1.8, run_time=0.4),
            ),
        )
        self.play(FadeIn(bang, shift=UP * 0.15), run_time=min(0.5, rt * 0.3))
        self.cue("What still shows")
        shows = VGroup(
            tag(
                f"{PHONE_IP} to {SERVER_IP}:443",
                STEEL,
                fs=15,
                fill=0.0,
                tcolor=INK,
                weight="MEDIUM",
            ),
            tag(
                f"{tls['request']['record_bytes']} bytes",
                STEEL,
                fs=15,
                fill=0.0,
                tcolor=INK,
                weight="MEDIUM",
            ),
        )
        for t in shows:
            t.box.set_stroke(STEEL, width=2)
        shows.arrange(RIGHT, buff=0.3).move_to([-0.3, wire.bottom - 0.42, 0])
        self.play(FadeIn(shows[0], shift=UP * 0.1), run_time=0.5)
        self.cue(
            "the size of the messages",
            ambient=lambda rt: [Throb(shows[0], rt, amp=0.06, period=0.9)],
        )
        self.play(FadeIn(shows[1], shift=UP * 0.1), run_time=0.5)
        self.cue("and the server's name")
        m_name = wire.mark(0, HOST, color=LOST_C)
        sni = tag("SNI", LOST_C, fs=15).next_to(m_name, RIGHT, buff=0.85)
        self.play(
            wire.rows[0].animate.set_opacity(1.0),
            FadeIn(m_name, scale=1.1),
            run_time=0.6,
        )
        self.cue("in a field called")
        self.play(FadeIn(sni, shift=LEFT * 0.15), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(m_name, rt, amp=0.05, period=0.9)])

        # ---- 7.7 the price ------------------------------------------------------------------------------------------ #
        vo = (
            "The price, with TLS one point three: one more round trip when the "
            "connection opens. In exchange: nobody can read, nobody can alter, and you "
            "know who is answering."
        )
        gone = [*wire.mobs(), stem, m_name, sni, shows, bang, note]
        blocks = trips([TCP_C, TLS_C, HTTP_C], unit=1.5, h=0.6, gap=0.08)
        blocks.move_to([-0.3, 0.3, 0])
        names = VGroup(*[
            line_txt(n, fs=21, color=BG, weight="BOLD").move_to(b) for n, b in zip(("TCP", "TLS", "HTTP"), blocks, strict=True)
        ])  # fmt: skip
        total = (
            VGroup(
                line_txt("3 round trips", fs=27, weight="BOLD"),
                label(
                    f"at least {LEDGER['fresh_https']['ms']:.0f} ms before the answer begins",
                    fs=18,
                ),
            )
            .arrange(DOWN, buff=0.1)
            .move_to([-0.3, -0.75, 0])
        )
        pipe.tap = None
        self.play(
            *[FadeOut(m) for m in gone], run_time=0.4
        )  # the caption arrives on a clean frame
        self.play(
            self.tell("HTTPS: the same conversation, in a sealed pipe.", vo),
            run_time=0.6,
        )
        self.play(
            LaggedStart(
                *[GrowFromEdge(b, LEFT) for b in blocks], lag_ratio=0.5, run_time=1.5
            ),
            LaggedStart(*[FadeIn(n) for n in names], lag_ratio=0.5, run_time=1.5),
        )
        # the middle block is the price: it lights when the narrator names it, and
        # keeps breathing until the sentence is over
        self.cue("one more round trip")
        self.play(
            FadeIn(total, shift=UP * 0.1),
            Indicate(blocks[1], color=TLS_C, scale_factor=1.12),
            run_time=0.8,
        )
        self.cue(
            "In exchange",
            ambient=lambda rt: throbs([blocks[1], names[1]], rt, amp=0.07, period=0.9),
        )
        t0 = clock.t + 2
        up = pipe.send(t0, ">", n_req, TLS_C, sealed=True)
        done = pipe.send(up + 4, "<", n_res, TLS_C, sealed=True)
        self.play(
            clock.run(done, self.span(None, floor=2.6)),
            Succession(Wait(1.6), self.fill_app(app, 1.0)),
        )
        self.settle(ambient=lambda rt: [Throb(app.money, rt, amp=0.06)])
        self.wipe()


class _Chain(_Talk):
    """Scenes 8 and 9: the request in production, and the whole stack."""

    # ====================================================================== #
    # 8 · Between servers
    # ====================================================================== #
    def scene_servers(self):
        gw = GATEWAY
        assert (
            gw["upstream_down"]["status"] == "502 Bad Gateway"
            and gw["upstream_down"]["s"] < 0.05
        )
        slow = gw["upstream_slow"]
        assert (
            slow["status"] == "504 Gateway Timeout"
            and slow["upstream_needs_s"] == 3.4
            and slow["proxy_waits_s"] == 3.0
        )
        assert abs(slow["s"] - 3.0) < 0.1
        clock = Clock(0.0)  # seconds
        Y0 = 0.55
        phone = node(phone_icon(1.45), "phone", (-6.02, Y0), fs=20)
        lb = node(balancer_icon(1.4), "load balancer", (-2.55, Y0), fs=20)
        api = node(server_icon(1.45), "application", (0.95, Y0), fs=20)
        solver = node(server_icon(1.45), "solver", (4.8, Y0), fs=20)
        db = node(database_icon(1.2), "database", (0.95, -2.12), fs=20)
        for n in (phone, lb, api, solver):
            n.label.next_to(n.icon, UP, buff=0.18)
            n.label.set_y(
                phone.label.get_y()
            )  # one baseline: the icons differ in height
        hops = {
            "edge": Hop(clock, (-5.52, Y0), (-3.3, Y0), color=TLS_C, r=0.2),
            "app": Hop(clock, (-1.8, Y0), (0.18, Y0), r=0.2),
            "solve": Hop(clock, (1.72, Y0), (4.03, Y0), r=0.2),
            "data": Hop(clock, (0.95, Y0 - 0.82), (0.95, -1.44), r=0.2),
        }
        ports = VGroup(
            port_tag(":443", True, fs=16).move_to([-3.72, Y0 + 0.56, 0]),
            port_tag(":8080", True, fs=16).move_to([-0.3, Y0 + 0.56, 0]),
            port_tag(":9000", True, fs=16).move_to([3.55, Y0 + 0.56, 0]),
            port_tag(":5432", True, fs=16).move_to([1.72, -1.22, 0]),
        ).set_z_index(5)
        self.chapter("8 · Between servers", None)
        note = self.note(
            "502 and 504 recorded on this machine with a small proxy (demo/proxy.py). Delays to Singapore: a model."
        )

        # ---- 8.1 a relay ------------------------------------------------------------------------- #
        self.voice(
            "In production, a load balancer receives the request, and that is usually "
            "where the sealed pipe ends. Behind it, the balancer opens its own "
            "connection to an application server, which opens others: to a solver, "
            "to a database."
        )
        self.play(
            FadeIn(phone), FadeIn(note), FadeIn(lb, shift=LEFT * 0.3), FadeIn(hops["edge"]), FadeIn(ports[0]),
            run_time=0.8,
        )  # fmt: skip
        rt = self.span("Behind it", floor=1.6)
        k = 0
        while (
            0.3 + 1.5 * k < rt - 0.8
        ):  # the request keeps arriving while the narrator sets the scene
            hops["edge"].send(clock.t + 0.3 + 1.5 * k, ">", 8, TLS_C, sealed=True)
            k += 1
        self.play(clock.run(clock.t + rt, rt))
        self.play(
            FadeIn(api, shift=LEFT * 0.3),
            FadeIn(hops["app"]),
            FadeIn(ports[1]),
            run_time=0.7,
        )
        t = hops["app"].send(clock.t + 0.1, ">", 8, HTTP_C)
        self.play(clock.run(t, self.span("which opens others", floor=1.4)))
        self.play(
            FadeIn(solver, shift=LEFT * 0.3), FadeIn(hops["solve"]), FadeIn(ports[2]),
            FadeIn(db, shift=UP * 0.3), FadeIn(hops["data"]), FadeIn(ports[3]), run_time=0.8,
        )  # fmt: skip
        t1 = hops["solve"].send(clock.t + 0.1, ">", 8, HTTP_C)
        t2 = hops["data"].send(clock.t + 0.4, ">", 6, MINT)
        t3 = hops["solve"].send(t1 + 0.3, "<", 8, HTTP_C)
        t4 = hops["data"].send(t2 + 0.2, "<", 10, MINT)
        t5 = hops["app"].send(max(t3, t4) + 0.1, "<", 10, HTTP_C)
        t6 = hops["edge"].send(t5 + 0.1, "<", 10, TLS_C, sealed=True)
        self.play(clock.run(t6, self.span(None, floor=5.0)))

        # ---- 8.2 connections, all the way down ------------------------------------------------------- #
        self.voice(
            "Each link is a separate TCP connection, kept open and reused whenever "
            "possible. Not all of them speak HTTP: a database has its own language. "
            "But underneath, it is the same reliable stream of bytes."
        )
        order = ("edge", "app", "solve", "data")
        self.play(
            LaggedStart(
                *[Tween(hops[k], glow=1.0, run_time=0.5) for k in order], lag_ratio=0.5
            ),
            run_time=2.0,
        )

        def traffic(t_end):
            """Requests keep flowing on the open connections until ``t_end``."""
            t = clock.t + 0.1
            while t < t_end - 1.2:
                for k, col, sealed in (
                    ("edge", TLS_C, True),
                    ("app", HTTP_C, False),
                    ("solve", HTTP_C, False),
                    ("data", MINT, False),
                ):
                    hops[k].send(t, ">", 5, col, sealed)
                    hops[k].send(t + 1.05, "<", 6, col, sealed)
                t += 2.3

        rt = self.span("a database has its own", floor=3.0)
        traffic(clock.t + rt)
        self.play(clock.run(clock.t + rt, rt))
        rt = self.span("But underneath", floor=2.0)
        traffic(clock.t + rt + 4)
        self.play(
            clock.run(clock.t + rt, rt),
            Indicate(ports[3], color=MINT, scale_factor=1.25, run_time=1.0),
        )
        rt = self.span(None, floor=2.5)
        self.play(
            clock.run(clock.t + rt, rt),
            LaggedStart(
                *[Tween(hops[k], glow=0.2, run_time=0.6) for k in order], lag_ratio=0.3
            ),
        )

        # ---- 8.3 where it broke -------------------------------------------------------------------------- #
        self.voice(
            "So when something breaks, the chain tells you where. The application is "
            "down: its port refuses, and the balancer answers five zero two, or five "
            "zero three with some products. The solver takes three point four seconds, "
            "but the balancer only waits three: five zero four."
        )
        rt = self.span("The application is down", floor=1.5)
        traffic(clock.t + rt + 1.2)
        self.play(clock.run(clock.t + rt, rt))
        for h in hops.values():
            h.flows.clear()
        # the LEDs are animated on their own: an animation of the whole icon, in the same
        # play, would override their colour with the icon's
        shell = VGroup(*[m for m in api.icon if m not in api.icon.leds])
        # and they are lifted above the body: a part that is animated on its own is
        # drawn after its siblings from then on, and the body would cover them
        api.icon.leds.set_z_index(1)
        self.play(
            api.icon.leds.animate.set_color(LOST_C), shell.animate.set_opacity(0.45),
            Tween(hops["app"], broken=1.0, run_time=0.5), run_time=0.5,
        )  # fmt: skip
        self.cue("its port refuses")
        go = Line([-1.6, Y0, 0], [-0.05, Y0, 0])
        self.play(Travel(tag("SYN", TCP_C, fs=14).set_z_index(6), go, run_time=0.6))
        self.play(
            Travel(
                tag("RST", LOST_C, fs=14).set_z_index(6),
                Line(go.get_end(), go.get_start()),
                run_time=0.6,
            )
        )
        e502 = tag("502", LOST_C, fs=20).set_z_index(6)
        home = Line([-3.45, Y0, 0], [-5.3, Y0, 0])
        self.cue("and the balancer answers")
        self.play(Travel(e502, home, run_time=0.8, keep=True))
        self.play(e502.animate.move_to([-6.02, Y0 - 1.3, 0]), run_time=0.45)
        b502 = label(gw["upstream_down"]["status"][4:], fs=16, color=LOST_C).next_to(
            e502, DOWN, buff=0.12
        )
        b502.align_to(phone.icon, LEFT)
        self.play(FadeIn(b502), run_time=0.3)
        self.cue(
            "The solver takes",
            ambient=lambda rt: [Throb(e502, rt, amp=0.12, period=0.9)],
        )
        first = VGroup(
            e502, b502
        )  # it stays, dimmed: the second failure will stack under it
        self.play(
            api.icon.leds.animate.set_color(OK_C), shell.animate.set_opacity(1.0),
            Tween(hops["app"], broken=0.0, run_time=0.5),
            first.animate.set_opacity(0.45), run_time=0.5,
        )  # fmt: skip
        wait = Clock(0.0)
        need_box, need_fill = timer_bar(
            wait, slow["upstream_needs_s"], (4.8, Y0 - 1.12), w=2.0, color=STEEL
        )
        pat_box, pat_fill = timer_bar(
            wait, slow["proxy_waits_s"], (-2.55, Y0 - 1.12), w=2.0, color=HERO_C
        )
        need_l = label(f"needs {slow['upstream_needs_s']:.1f} s", fs=17).next_to(
            need_box, DOWN, buff=0.14
        )
        pat_l = label(f"waits {slow['proxy_waits_s']:.1f} s", fs=17).next_to(
            pat_box, DOWN, buff=0.14
        )
        self.play(
            FadeIn(need_box),
            FadeIn(pat_box),
            FadeIn(need_l),
            FadeIn(pat_l),
            run_time=0.4,
        )
        self.add(need_fill, pat_fill)
        hops["app"].send(clock.t, ">", 8, HTTP_C)
        hops["solve"].send(clock.t + 0.9, ">", 8, HTTP_C)
        # three real seconds
        self.play_unstretched(wait.run(3.0, 3.0), clock.run(clock.t + 3.0, 3.0))
        e504 = tag("504", LOST_C, fs=20).set_z_index(6)
        self.play(
            pat_box.animate.set_stroke(LOST_C),
            Travel(e504, home, run_time=0.9, keep=True),
        )
        self.play(e504.animate.move_to([-6.02, Y0 - 2.2, 0]), run_time=0.5)
        b504 = label(slow["status"][4:], fs=16, color=LOST_C).next_to(
            e504, DOWN, buff=0.12
        )
        b504.align_to(phone.icon, LEFT)
        self.play(FadeIn(b504), run_time=0.3)
        self.hold(ambient=lambda rt: [Throb(e504, rt, amp=0.12, period=0.9)])

        # ---- 8.4 what a hop costs ---------------------------------------------------------------------------- #
        atlas = Atlas()
        vo = (
            "And every hop costs time. A round trip to Singapore: a hundred and five "
            "milliseconds, at best. A new secure connection needs three of them before "
            "the answer comes; an open one, just one. So keep connections open, and "
            "put servers close to their users."
        )
        chain = [phone, lb, api, solver, db, ports, *hops.values(), need_box, pat_box, need_l, pat_l,
                 need_fill, pat_fill, first, e504, b504]  # fmt: skip
        for m in (need_fill, pat_fill):
            m.clear_updaters()
        paris, singa = city_dot(atlas.paris, HERO_C), city_dot(atlas.singapore, INK)
        n_p = label("Paris", fs=20, color=INK).next_to(paris, UP, buff=0.14)
        # up and to the right of its dot: clear of the caption's line and of the arc
        n_s = label("Singapore", fs=20, color=INK).next_to(singa, UR, buff=0.06)
        road = atlas.arc()
        self.play(
            *[FadeOut(m) for m in chain], FadeOut(note), run_time=0.5
        )  # the caption arrives on a clean frame
        self.play(
            self.tell("Latency is round trips, times distance.", vo),
            FadeIn(atlas.land),
            run_time=1.0,
        )
        self.play(
            FadeIn(paris),
            FadeIn(n_p),
            FadeIn(singa),
            FadeIn(n_s),
            Create(road),
            run_time=0.9,
        )
        ends = VGroup(paris, singa)
        X, U = -6.3, 1.25
        rows = []
        for k, (name, colors, text) in enumerate((
            ("a new secure connection", [TCP_C, TLS_C, HTTP_C], f"{3 * RTT:.0f} ms"),
            ("a connection kept open", [HTTP_C], f"{RTT:.0f} ms"),
        )):  # fmt: skip
            y = -0.3 - 1.05 * k
            lab = label(name, fs=18, color=INK).move_to([0, y + 0.42, 0])
            lab.shift(RIGHT * (X - lab.get_left()[0]))
            bl = trips(colors, unit=U, h=0.4, gap=0.07)
            bl.shift([X - bl.get_left()[0], y - 0.05 - bl.get_center()[1], 0])
            tot = line_txt(text, fs=22, font=MONO).next_to(bl, RIGHT, buff=0.22)
            rows.append((lab, bl, tot))
        plate_ = SurroundingRectangle(
            VGroup(*[m for r in rows for m in r], Rectangle(width=6.3, height=2.9).move_to([X + 3.0, -1.3, 0])),
            buff=0.2, corner_radius=0.14,
        ).set_stroke(FAINT, width=2).set_fill(BG, opacity=0.92)  # fmt: skip
        self.cue(
            "A round trip to Singapore",
            ambient=lambda rt: [*throbs(ends, rt, amp=0.3, period=0.9),
                                ShowPassingFlash(atlas.arc(color=INK, width=4), time_width=0.5, run_time=rt)],
        )  # fmt: skip
        go, come = atlas.arc(color=HERO_C, width=7), atlas.back(color=HERO_C, width=7)
        self.play(
            Succession(
                ShowPassingFlash(go, time_width=0.35, run_time=0.9),
                ShowPassingFlash(come, time_width=0.35, run_time=0.9),
            )
        )
        self.cue(
            "A new secure connection",
            ambient=lambda rt: [Succession(
                ShowPassingFlash(atlas.arc(color=HERO_C, width=7), time_width=0.35, run_time=rt / 2),
                ShowPassingFlash(atlas.back(color=HERO_C, width=7), time_width=0.35, run_time=rt / 2),
            )],
        )  # fmt: skip
        self.play(FadeIn(plate_), FadeIn(rows[0][0]), run_time=0.4)
        self.play(
            LaggedStart(*[GrowFromEdge(b, LEFT) for b in rows[0][1]], lag_ratio=0.5),
            run_time=1.5,
        )
        self.play(FadeIn(rows[0][2]), run_time=0.3)
        self.cue(
            "an open one",
            ambient=lambda rt: [Throb(rows[0][1], rt, amp=0.05, period=0.9)],
        )
        self.play(FadeIn(rows[1][0]), GrowFromEdge(rows[1][1][0], LEFT), run_time=0.8)
        self.play(FadeIn(rows[1][2]), run_time=0.3)
        self.cue(
            "and put servers close",
            ambient=lambda rt: [Succession(
                ShowPassingFlash(atlas.arc(color=HTTP_C, width=7), time_width=0.35, run_time=rt / 2),
                ShowPassingFlash(atlas.back(color=HTTP_C, width=7), time_width=0.35, run_time=rt / 2),
            )],
        )  # fmt: skip
        # the server moves to Paris: the round trip shrinks with the distance
        y = -0.3 - 1.05 * 2
        lab3 = label("the same, with the server in Paris", fs=18, color=INK).move_to(
            [0, y + 0.42, 0]
        )
        lab3.shift(RIGHT * (X - lab3.get_left()[0]))
        sliver = trips([HTTP_C], unit=0.05, h=0.4).move_to([X + 0.025, y - 0.05, 0])
        tot3 = line_txt("under 1 ms", fs=22, font=MONO).next_to(
            sliver, RIGHT, buff=0.22
        )
        near = atlas.paris + RIGHT * 0.34 + DOWN * 0.1
        self.play(
            Uncreate(road, run_time=1.6),
            singa.animate(run_time=1.6).move_to(near),
            FadeOut(n_s, run_time=0.4),
            FadeIn(lab3, run_time=0.5),
        )
        self.play(GrowFromEdge(sliver, LEFT), FadeIn(tot3), run_time=0.5)
        self.settle(ambient=lambda rt: [Throb(VGroup(sliver, tot3), rt, amp=0.05)])
        self.wipe()

    # ====================================================================== #
    # 9 · The stack
    # ====================================================================== #
    def scene_stack(self):
        fail, kern, gw = STORY["tls_failures"], KERNEL, GATEWAY
        # (the line or lines, where to look, the message). The name lookup is a service
        # of its own, not a layer of the stack. A timeout means packets are not getting
        # through: that is the network's business, below TCP.
        errors = [
            ((0,), None, kern["no_such_name"]["text"]),
            ((1,), "TCP", kern["refused"]["text"]),
            ((1,), "IP", kern["silence"]["kernel"]["text"]),
            ((2,), "TLS", "certificate verify failed: " + fail["expired"]["reason"]),
            ((3, 4), "HTTP", "HTTP/1.1 " + gw["upstream_slow"]["status"]),
        ]
        assert errors[0][2] == "[Errno 8] nodename nor servname provided, or not known"
        assert errors[3][2].endswith("certificate has expired") and errors[4][
            2
        ].endswith("504 Gateway Timeout")
        panel, rows, dots, sheets = self.code_and_stack()
        clock = Clock(-1.0)
        flow = SheetFlow(clock, sheets)
        layers = {n: VGroup(sheets.sheet[n], sheets.name[n]) for n in sheets.names}
        wires = {n: sheets.wire(n) for n in sheets.names}
        dns = tag("DNS", DNS_C, fs=15)
        dns.move_to(
            [panel.get_right()[0] - 0.8, rows[0].get_center()[1], 0]
        ).set_z_index(3)
        ask = Line(
            rows[0].get_right() + RIGHT * 0.2, dns.get_left() + LEFT * 0.1
        ).set_stroke(DNS_C, width=2.2, opacity=0.75)
        self.chapter("9 · The stack", None)
        note = self.note(
            "Errors as this Mac words them. Linux: Errno -2 Name or service not known, 111 refused, 110 timed out."
        )

        # ---- 9.1 what each line stands on ---------------------------------------------------------- #
        self.voice(
            "Back to the five lines. The first asks a directory for an address. The "
            "second opens a connection: TCP, a reliable stream of bytes, on top of IP, "
            "packets with no guarantee. The third seals it: TLS, a private stream with "
            "a proven identity. The last two speak HTTP: a request, and a response."
        )
        self.play(
            FadeIn(panel),
            FadeIn(dots),
            *[FadeIn(g) for g in layers.values()],
            FadeIn(note),
            run_time=0.9,
        )
        self.add(flow)
        flow.only, flow.loop = (
            (),
            True,
        )  # between two cues, the request keeps going round
        marks = {}

        def line_on(*lines):
            """The code lines light up, in the colour of what they speak."""
            bar = self.hl_lines(
                panel, rows, list(lines), color=LINE_COLOR[lines[0]], opacity=0.22
            )
            marks[lines[0]] = bar
            return FadeIn(bar)

        def sheet_on(name):
            """A sheet lights up, and its first crossing of the request starts with it."""
            flow.only = (*flow.only, name)
            clock.set(flow.plan[name][0][0])
            return [
                Create(wires[name]),
                layers[name][0].animate.set_fill(opacity=0.34),
                clock.run(clock.t + ONE_WAY, 1.3),
            ]

        self.cue(
            "The first asks",
            ambient=lambda rt: [
                LaggedStart(
                    *[Indicate(d, color=INK, scale_factor=2.0) for d in dots],
                    lag_ratio=0.3,
                    run_time=rt,
                )
            ],
        )
        self.play(line_on(0), FadeIn(dns, shift=LEFT * 0.2), Create(ask), run_time=0.8)
        self.cue(
            "The second opens",
            ambient=lambda rt: [Throb(dns, rt, amp=0.12, period=0.9)],
        )
        self.play(line_on(1), run_time=0.5)
        self.cue("TCP, a reliable")
        self.play(*sheet_on("TCP"), run_time=1.3)
        self.cue("on top of IP")
        self.play(*sheet_on("IP"), run_time=1.3)
        self.cue(
            "The third seals", ambient=lambda rt: [clock.run(clock.t + 40 * rt, rt)]
        )
        self.play(line_on(2), *sheet_on("TLS"), run_time=1.3)
        self.cue(
            "The last two speak", ambient=lambda rt: [clock.run(clock.t + 40 * rt, rt)]
        )
        self.play(line_on(3, 4), *sheet_on("HTTP"), run_time=1.3)
        # the whole request, every layer at once
        clock.set(0.0)
        self.play(clock.run(3 * RTT, self.span(None, floor=4.0)))

        # ---- 9.2 five ways to fail ------------------------------------------------------------------- #
        self.voice(
            "And each line fails in its own way. The first: the name is unknown. The "
            "second: a refusal, if nothing listens; a timeout, if nothing answers. The "
            "third: a certificate that does not check out. The last two: a status "
            "code. Find the line that failed, and you know where to look."
        )
        flow.only = ()
        self.play(
            *[m.animate.set_fill(opacity=0.08) for m in marks.values()],
            FadeOut(note),
            run_time=0.5,
        )
        self.cue(
            "The first",
            ambient=lambda rt: [
                LaggedStart(
                    *[Indicate(d, color=LOST_C, scale_factor=2.0) for d in dots],
                    lag_ratio=0.3,
                    run_time=rt,
                )
            ],
        )

        def culprit(lines, name):
            """What turns red: the line or lines, and where to look (a sheet, or the directory)."""
            hot = self.hl_lines(panel, rows, list(lines), color=LOST_C, opacity=0.3)
            if name is None:
                return VGroup(
                    hot, tag("DNS", LOST_C, fs=15).move_to(dns).set_z_index(4)
                )
            return VGroup(
                hot,
                sheets.sheet[name]
                .copy()
                .set_fill(opacity=0)
                .set_stroke(LOST_C, width=5),
            )

        def replay(name, rt):
            """The failure in the language of its sheet: what goes out, what comes back (or does not)."""
            if name is None:  # the directory knows no such name
                n = max(1, round(rt / 1.1))
                hit = ask.copy().set_stroke(LOST_C, width=5, opacity=1).set_z_index(4)
                return [
                    Succession(
                        *[
                            ShowPassingFlash(
                                hit.copy(), time_width=0.6, run_time=rt / n
                            )
                            for _ in range(n)
                        ]
                    )
                ]
            (a, b), col = sheets.ends(name), dict(LAYERS)[name]

            def dot(c):
                return glow_dot(c, r=0.1).set_z_index(5)

            if name == "IP":  # nothing comes back: it asks again, and again
                way = Line(a, a + (b - a) * 0.62)
                tries = [
                    Travel(dot(col), way, run_time=rt * 0.5, rate_func=linear)
                    for _ in range(max(2, round(rt / 0.7)))
                ]
                return [LaggedStart(*tries, lag_ratio=0.5, run_time=rt)]
            return [  # something comes back, and it is a no
                Succession(
                    Travel(dot(col), Line(a, b), run_time=rt * 0.48, rate_func=linear),
                    Travel(
                        dot(LOST_C), Line(b, a), run_time=rt * 0.48, rate_func=linear
                    ),
                )
            ]

        shown = []
        phrases = ("The first", "The second", "a timeout", "The third", "The last two")
        for k, ((lines, name, text), phrase) in enumerate(
            zip(errors, phrases, strict=True)
        ):
            self.cue(
                phrase,
                ambient=(lambda rt, last=errors[k - 1][1]: replay(last, rt))
                if k
                else None,
            )
            chip = error_chip(text, fs=18).move_to([0.0, -3.3, 0])
            red = culprit(lines, name)
            self.play(
                *[FadeOut(m, run_time=0.25) for m in shown],
                FadeIn(red), self.then(FadeIn(chip, shift=UP * 0.12, run_time=0.35), 0.25),
            )  # fmt: skip
            shown = [chip, red]
        self.cue("Find the line", ambient=lambda rt: replay(errors[-1][1], rt))
        # once more, quickly: a line, and where to look. Nothing stale stays up meanwhile.
        self.play(*[FadeOut(m) for m in shown], run_time=0.3)
        pairs = [
            culprit(lines, name)
            for lines, name in (
                ((0,), None),
                ((1,), "TCP"),
                ((2,), "TLS"),
                ((3, 4), "HTTP"),
            )
        ]
        pairs[1].add(culprit((1,), "IP")[1])
        left = max(2.4, self.time_left(0.2))
        self.play(
            LaggedStart(
                *[Succession(FadeIn(pr, run_time=left * 0.12), FadeOut(pr, run_time=left * 0.12)) for pr in pairs],
                lag_ratio=0.75, run_time=left,
            ),
        )  # fmt: skip

        # ---- 9.3 the takeaway ---------------------------------------------------------------------------- #
        vo = "One request, four layers: each one simple, because of the one below it."
        self.play(
            self.tell(
                "One request, four layers: each one simple, because of the one below.",
                vo,
            ),
            *[m.animate.set_fill(opacity=0.22) for m in marks.values()],
            run_time=0.7,
        )
        flow.only = None
        clock.set(0.0)
        self.play(clock.run(3 * RTT, self.span(None, floor=5.0)))
        self.settle()
        self.wipe()


class Servers(_Chain):
    def construct(self):
        self.scene_servers()


class Stack(_Chain):
    def construct(self):
        self.scene_stack()


class Intro(_Flat):
    def construct(self):
        self.over_card(
            "TCP, HTTP, HTTPS: what really happens when one machine calls another. "
            "We will follow a single request, from a phone in Paris to a server in Singapore."
        )
        self.play_intro()


class Outro(_Flat):
    def construct(self):
        self.play_outro()


class Request(_Talk):
    def construct(self):
        self.scene_request()


class Http(_Talk):
    def construct(self):
        self.scene_http()


class Sealed(_Talk):
    def construct(self):
        self.scene_sealed()


class Tap(_Talk):
    def construct(self):
        self.scene_tap()


class Packets(_Flat):
    def construct(self):
        self.scene_packets()


class Connect(_Flat):
    def construct(self):
        self.scene_connect()


class Stream(_Flat):
    def construct(self):
        self.scene_stream()
