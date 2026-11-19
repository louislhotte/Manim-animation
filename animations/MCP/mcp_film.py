"""MCP, the Model Context Protocol: how an AI application plugs into tools and data.

A film made to be narrated: the voice carries the explanation, the screen carries the
real artifacts (the model's context, JSON-RPC messages, a function, a table) and two
captions. Flat scenes, no camera. One stage, three actors, in the order a request
crosses them:

    model (its context)  |  host (the app, its user, a client)  ==wire==  server

STORYBOARD (question | hero visual | what moves)

    1 A model alone   what can a model do by itself?   its context, a list of blocks;
                      far right, a table of 906 orders | a question arrives, a band of
                      light reads it, an answer is typed: "I can't see your orders";
                      a probe towards the table stops short; the name fills the gap
    2 One protocol    who talks to whom, and in what?   the host is drawn into the
                      gap, the server around the table, a cable between a client and
                      a socket | a request and its response, as JSON, with the same
                      id; a function's name, docstring and type hint fly into a tool
                      definition, which crosses the wire into the context
    3 One call        what happens when the model uses a tool?   the whole stage |
                      the model types a call, the host asks the user, an envelope
                      crosses, 412 dots light up and 29 turn gold, the result comes
                      back as a block, the model types the answer
    4 Three doors     what else can a server offer?   three offers on the server,
                      three people who can open them | a slash command (the user), a
                      paper clip (the application), a call (the model): three blocks
                      land in the same context
    5 Anywhere        where does a server run?   the wire itself | a child process
                      and two pipes; then far away, an HTTP POST with a token; then,
                      since nothing is remembered between two requests, three copies
                      behind a balancer, and one of them dies without loss
    6 Trust           what are you plugging in?   three hosts, four servers, one
                      plug: 7 pieces instead of 12 | then a stranger's tool whose
                      description gives the model an order; it lands in the context
                      in red; the user says no
    7 Recap           the stage again, each actor lit on its sentence

Motif: the model's context (every scene ends with text arriving in it) and the
question "How many orders shipped late in week 46?". Colour is identity: purple the
model, blue the host and its client, orange a server and whatever text comes from
one, green the user. Gold marks the thing to look at, red what is hostile.

What is real: nothing was captured. The messages are written from the MCP
specification, revision 2026-07-28 (the stateless revision), in ``wire.py``, which
checks them against that revision when it is imported; the note at the bottom of
the screen says so. The table is synthetic (seeded); the function that reads it is
real Python, runs at import, and its source and its result are what the film shows;
the tool definition is derived from that function's signature.

Scenes render alone (``./render.sh call --quick --check``) or stitched
(``./render.sh``). Every scene opens on the picture the previous one ended on
(``enter`` / ``handoff``), so the cuts between clips do not show. Pacing: ``MCP_WPS``
(the narrator's words per second), ``MCP_QUICK``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from manimx import *

from kit import *  # noqa: F403
import wire as W

# ---- what the actors say (every number comes from wire.py) ------------------------- #
LATE, TOTAL = W.ANSWER["late"], W.ANSWER["total"]
assert (LATE, TOTAL, W.WEEK) == (29, 412, 46), "the narration says 29 of 412, week 46"
Q_BUBBLE = ["How many orders", "shipped late", f"in week {W.WEEK}?"]
Q_BLOCK = [("How many orders shipped", "prose"), (f"late in week {W.WEEK}?", "prose")]
NO_ACCESS = [("I can't see your orders.", "prose")]
SIGNATURE = "{}({})".format(
    W.TOOL["name"],
    ", ".join(f"{k}: {v['type']}" for k, v in W.TOOL["inputSchema"]["properties"].items()),
)
TOOLS_ROWS = [(SIGNATURE, "mono")]
ARGS = json.dumps(W.exchange(2)[0]["params"]["arguments"])
CALL_ROWS = [(f"{W.TOOL['name']} {ARGS}", "mono")]
RESULT_ROWS = [(W.ANSWER_TEXT, "mono")]
ANSWER_ROWS = [(f"{LATE} of {TOTAL} orders shipped late.", "prose")]
ANSWER_BUBBLE = [f"{LATE} of {TOTAL} orders", "shipped late."]
SPEC_NOTE = (
    "Messages written from the MCP specification, revision 2026-07-28. "
    "Not captured from a running system."
)
DATA_NOTE = f"The table is synthetic: {len(W.db)} orders generated with a fixed seed."


class _Common(NarratedMixin):
    pace = Pace.from_env("MCP", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "MCP"
    SUBTITLE = "The Model Context Protocol"
    TAGLINE = "how an AI application plugs into tools and data"
    RECAP = "The model writes. The host carries. The server does the work."
    TRACE_ENV = "MCP_TRACE"
    WPS = float(os.environ.get("MCP_WPS", 2.6))  # the narrator: 156 words a minute
    VO_PAD = 0.7

    def setup(self):
        super().setup()
        self.head = self.foot = None

    def intro_emblem(self):
        """A plug about to enter a socket, at the end of the title rule."""
        sock = socket_glyph().scale(1.5)
        plug = plug_glyph().scale(1.5).next_to(sock, LEFT, buff=0.16)
        cable = Line(plug.get_left() + LEFT * 0.5, plug.get_left()).set_stroke(STEEL, width=6)
        g = VGroup(cable, sock, plug)
        pad = Rectangle(width=0.9, height=0.1).set_stroke(opacity=0).set_fill(opacity=0)
        low = Rectangle(width=0.1, height=0.36).set_stroke(opacity=0).set_fill(opacity=0)
        return VGroup(g, pad.next_to(g, RIGHT, buff=0), low.next_to(g, DOWN, buff=0))

    # ---- chapters, and the hand-off from one scene to the next ---------------------- #
    def chapter(self, label, color=GOLD, note=None):
        """The animations that bring in the section header and the source note."""
        self.head = self.section_header(label, color).set_z_index(Z_HEAD)
        anims = [FadeIn(self.head, shift=DOWN * 0.2)]
        self.foot = None
        if note:
            self.foot = self.note(note)
            anims.append(FadeIn(self.foot))
        return anims

    def aside(self, text):
        """One of the film's rare captions: it stays until the scene closes or the
        next line starts."""
        cap = self.say(text).set_z_index(20)
        self._cap = cap
        return FadeIn(cap, shift=UP * 0.1)

    def enter(self, state):
        """Open on the picture the previous scene ended on."""
        s = state()
        self.add(*s.mobs)
        return s

    def _picture(self):
        self.renderer.static_image = None
        self.renderer.update_frame(self)
        return self.renderer.get_frame().astype(np.int16)

    def close(self, state=None):
        """End of a scene: header, note and caption leave. With ``state``, the stage is
        then swapped for a fresh build of itself, the one the next scene opens on,
        and the two pictures are compared: a cut between two clips must not show."""
        out = [m for m in (self.head, self.foot, self._cap) if m is not None and m in self.mobjects]
        if out:
            self.play(*[FadeOut(m) for m in out], run_time=0.4)
        self._cap = None
        if state is None:
            return
        before = self._picture()
        for m in list(self.mobjects):
            m.clear_updaters()
        self.clear()
        self.add(*state().mobs)
        after = self._picture()
        delta = np.abs(after - before)[..., :3].max(axis=-1)
        bad = int((delta > 30).sum())
        print(
            f"\n== hand-off {type(self).__name__} -> {state.__name__}: "
            f"{bad} px differ (max {int(delta.max())})"
        )
        if bad and os.environ.get("MCP_HANDOFF_DEBUG"):  # look at what moved
            from PIL import Image

            out = Path(config.media_dir) / "handoff"
            out.mkdir(parents=True, exist_ok=True)
            ys, xs = np.nonzero(delta > 30)
            print(f"   differences in x {xs.min()}..{xs.max()}, y {ys.min()}..{ys.max()} (pixels)")
            for tag, pic in (("before", before), ("after", after)):
                Image.fromarray(pic.astype(np.uint8)).save(out / f"{type(self).__name__}_{tag}.png")
            mask = np.zeros(delta.shape + (3,), np.uint8)
            mask[delta > 30] = 255
            Image.fromarray(mask).save(out / f"{type(self).__name__}_diff.png")
        self.wait(2 / config.frame_rate)

    # ---- the pictures scenes hand to each other --------------------------------------- #
    def st_alone(self):
        """End of scene 1: a model, a question it cannot answer, a table out of reach,
        and the name of the protocol in the gap."""
        model, grid = ModelPanel(), OrdersGrid()
        ask = model.block("user", Q_BLOCK, "user")
        reply = model.block("assistant", NO_ACCESS, "model")
        words, caps = name_words()
        return SimpleNamespace(
            model=model, grid=grid, ask=ask, reply=reply, words=words, caps=caps,
            mobs=[*model.furniture(), ask, reply, *grid.furniture(), *words, *caps],
        )  # fmt: skip

    def st_protocol(self):
        """End of scene 2: the three actors, connected; the tool's definition is in
        the context."""
        model, host, server, link = ModelPanel(), HostFrame(), ServerFrame(), Link()
        tools = model.block("tools", TOOLS_ROWS, "server")
        return SimpleNamespace(
            model=model, host=host, server=server, link=link, grid=server.grid, tools=tools,
            mobs=[*model.furniture(), tools, *host.furniture(), *server.furniture(), *link.mobs()],
        )  # fmt: skip

    def st_call(self):
        """End of scene 3: the whole exchange is on screen."""
        s = self.st_protocol()
        s.ask = s.model.block("user", Q_BLOCK, "user")
        s.call = s.model.block("tool call", CALL_ROWS, "model")
        s.res = s.model.block("tool result", RESULT_ROWS, "server")
        s.ans = s.model.block("assistant", ANSWER_ROWS, "model")
        s.q, s.reply = s.host.say(Q_BUBBLE), s.host.answer(ANSWER_BUBBLE)
        s.lit, s.late = s.grid.lit(), s.grid.late()
        s.n_rows = s.grid.count(f"{TOTAL} orders", INK, 0)
        s.n_late = s.grid.count(f"{LATE} late", LOOK_C, 1)
        s.mobs += [s.ask, s.call, s.res, s.ans, s.q, s.reply, s.lit, s.late, s.n_rows, s.n_late]
        return s


class _Flat(_Common, Scene):
    # ====================================================================== #
    # 1 · A model alone
    # ====================================================================== #
    def scene_alone(self):
        model, grid = ModelPanel(), OrdersGrid()

        # ---- 1.1 it reads, it writes ----------------------------------------------- #
        self.voice(
            "A language model does one thing. It reads the text in its context, and "
            "writes more text."
        )
        self.play(
            *self.chapter("1 · A model alone", MODEL_C),
            Create(model.frame.box),
            FadeIn(model.frame.tag),
            FadeIn(model.chip, scale=0.6),
            FadeIn(model.ctx),
            Create(model.rule),
            run_time=1.0,
        )
        self.cue("It reads the text", ambient=lambda rt: [Throb(model.chip, rt, amp=0.14)])
        ask = model.block("user", Q_BLOCK, "user")
        self.play(FadeIn(ask, shift=RIGHT * 0.25), run_time=0.5)
        self.play(model.reading(self.span("and writes", floor=0.8, cap=1.6)))
        reply = model.block("assistant", NO_ACCESS, "model")
        typing = reply.typed(1.3)
        self.play(FadeIn(reply, shift=RIGHT * 0.2), run_time=0.3)
        self.play(typing, Throb(model.chip, 1.3, amp=0.14, period=0.65))
        self.hold(ambient=lambda rt: [Throb(model.chip, rt, amp=0.08)])

        # ---- 1.2 the answer is elsewhere --------------------------------------------- #
        self.voice(
            "Ask it how many orders shipped late in week forty-six, and it cannot know. "
            "The answer sits in a database it cannot reach."
        )
        self.play(glow(ask.box, USER_C), run_time=1.0)
        self.cue("it cannot know", ambient=lambda rt: [Throb(ask, rt, amp=0.02)])
        self.play(glow(reply.box, MODEL_C), run_time=1.0)
        self.cue("The answer sits")
        foot = self.note(DATA_NOTE)
        self.foot = foot
        self.play(
            FadeIn(grid.title, shift=LEFT * 0.2),
            LaggedStart(*[FadeIn(h) for h in grid.heads.values()], lag_ratio=0.3),
            DotsReveal(grid.base, rate_func=smooth),
            FadeIn(foot),
            run_time=self.span("it cannot reach", floor=1.2, cap=2.2),
        )
        a = np.array([MODEL_X[1] + 0.14, -0.5, 0.0])
        b = np.array([SERVER_X[0] + 0.1, -0.5, 0.0])
        reach = DashedLine(a, a + (b - a) * 0.6, dash_length=0.13).set_stroke(MODEL_C, width=3)
        stop = make_cross(BAD, sw=5, scale=0.85).move_to(reach.get_end() + RIGHT * 0.32)
        self.play(Create(reach, rate_func=smooth), run_time=0.9)
        self.play(FadeIn(stop, scale=1.7), run_time=0.3)
        self.hold(ambient=lambda rt: [Throb(stop, rt, amp=0.22)])

        # ---- 1.3 the name --------------------------------------------------------------- #
        self.voice(
            "The Model Context Protocol, MCP, is a standard way to bring that outside "
            "world into the model's context."
        )
        words, caps = name_words()
        self.play(FadeOut(reach), FadeOut(stop), run_time=0.3)
        self.play(
            LaggedStart(*[FadeIn(w, shift=UP * 0.2) for w in words], lag_ratio=0.3),
            run_time=1.2,
        )
        self.cue("MCP")
        self.play(
            LaggedStart(*[FadeIn(c, scale=1.6) for c in caps], lag_ratio=0.35),
            run_time=0.9,
        )
        self.cue("bring that outside")
        y = -1.72
        way = arr(
            [grid.x0 - 0.2, y, 0], [MODEL_X[1] + 0.12, y, 0], color=LOOK_C, sw=5, buff=0.0
        )
        self.play(GrowArrow(way), run_time=self.span("into the model's", floor=0.8, cap=1.4))
        self.play(glow(model.frame.box, LOOK_C), run_time=1.0)
        self.settle(ambient=lambda rt: [Throb(VGroup(*caps), rt, amp=0.05)])
        self.play(FadeOut(way), run_time=0.3)
        self.close(self.st_alone)

    # ====================================================================== #
    # 2 · One protocol
    # ====================================================================== #
    def scene_protocol(self):
        s = self.enter(self.st_alone)
        model, grid = s.model, s.grid
        host, link, server = HostFrame(), Link(), ServerFrame(grid=grid)

        # ---- 2.1 three roles ------------------------------------------------------------ #
        self.voice(
            "It names three roles. The application you talk to is the host. Each "
            "outside system is wrapped by a small program, a server. And inside the "
            "host, one client per server speaks the protocol."
        )
        self.play(
            *self.chapter("2 · One protocol", HOST_C, SPEC_NOTE),
            *[FadeOut(m, shift=UP * 0.2) for m in (*s.words, *s.caps)],
            FadeOut(s.ask),
            FadeOut(s.reply),
            run_time=0.7,
        )
        model.drop(s.ask, s.reply)
        self.cue("is the host")
        self.play(Create(host.frame.box), FadeIn(host.frame.tag), run_time=0.9)
        self.play(
            LaggedStart(
                FadeIn(host.avatar, scale=0.6),
                FadeIn(host.who),
                FadeIn(host.bar),
                FadeIn(host.clip),
                lag_ratio=0.2,
            ),
            run_time=0.7,
        )
        self.cue("is wrapped", ambient=lambda rt: [Throb(host.avatar, rt, amp=0.1)])
        self.play(Create(server.frame.box), FadeIn(server.frame.tag), run_time=0.9)
        self.play(FadeIn(server.tool, shift=DOWN * 0.2), run_time=0.5)
        self.cue("one client per server", ambient=lambda rt: [Throb(server.tool, rt, amp=0.04)])
        home = link.plug.get_center().copy()
        link.plug.move_to(link.port.get_center() + RIGHT * 0.22)
        self.play(
            FadeIn(link.port, scale=0.5),
            FadeIn(link.name, shift=RIGHT * 0.1),
            FadeIn(link.socket, scale=0.5),
            run_time=0.5,
        )
        self.play(Create(link.cable), link.plug.animate.move_to(home), run_time=0.8)
        self.play(glow(link.socket[0], LOOK_C, width=5), run_time=0.7)
        self.hold(ambient=lambda rt: [Throb(link.port, rt, amp=0.12)])

        # ---- 2.2 a request, a response, one id ------------------------------------------- #
        self.voice(
            "They exchange plain JSON messages. A request names a method and carries "
            "an id. The response comes back with the same id."
        )
        req, res = W.exchange(1)
        shade = veil()
        top = 0.62
        rq = MsgCard(
            W.jlines(req, fold=("params._meta",)), at=(-5.93, top), fs=19,
            title="request", edge=HOST_C,
        )  # fmt: skip
        rs = MsgCard(
            W.jlines(res, fold=("result.tools",), keep={"result": ["tools"]}),
            at=(rq.x0 + rq.w + 0.5, top), fs=19, title="response", edge=SERVER_C,
        )  # fmt: skip
        letter = link.letter().move_to(link.port.get_center())
        self.play(FadeIn(shade), FadeIn(letter, scale=0.5), run_time=0.5)
        self.play(
            letter.animate.move_to(link.middle()), rq.fade_in(shift=DOWN * 0.2), run_time=0.7
        )
        self.cue("names a method")
        m_method = rq.mark('"method": "tools/list"')
        self.play(FadeIn(m_method), run_time=0.3)
        self.cue("carries")
        m_id = rq.mark('"id": 1')
        self.play(FadeIn(m_id), run_time=0.3)
        self.cue("The response comes back", ambient=lambda rt: [Throb(m_id, rt, amp=0.08)])
        back = link.letter(back=True).move_to(link.plug.body.get_center())
        self.play(letter.animate.move_to(link.plug.body.get_center()), run_time=0.35)
        self.play(FadeOut(letter), FadeIn(back), run_time=0.2)
        self.play(
            back.animate.move_to(link.middle()), rs.fade_in(shift=DOWN * 0.2), run_time=0.7
        )
        self.cue("the same id")
        m_same = rs.mark('"id": 1')
        tie = DashedLine(m_id.get_right(), m_same.get_left(), dash_length=0.1)
        tie.set_stroke(LOOK_C, width=2.5).set_z_index(Z_CARD + 1)
        self.play(FadeIn(m_same), Create(tie), run_time=0.5)
        self.hold(ambient=lambda rt: throbs([m_id, m_same], rt, amp=0.08))

        # ---- 2.3 what can you do? ----------------------------------------------------------- #
        self.voice(
            "This first request asks: what can you do? The server answers with its "
            "tools. Each one is a name, a description, and a schema for its arguments, "
            "often built straight from a function's signature."
        )
        self.play(FadeOut(tie), FadeOut(m_id), FadeOut(m_same), run_time=0.3)
        self.cue("what can you do", ambient=lambda rt: [Throb(m_method, rt, amp=0.06)])
        m_tools = rs.mark('"tools": [ … ]')
        self.play(FadeOut(m_method), FadeIn(m_tools), run_time=0.4)
        self.cue("its tools", ambient=lambda rt: [Throb(m_tools, rt, amp=0.06)])
        define = MsgCard(
            W.jlines(W.TOOL, inline=36), at=(-6.23, 1.25), fs=17,
            title="one entry of tools, as it is sent", edge=SERVER_C,
        )  # fmt: skip
        code = MsgCard(
            W.source_lines(W.late_orders), at=(define.x0 + define.w + 0.4, 1.25), fs=18,
            title="on the server: a function", edge=FAINT, title_color=MUTED, kind="python",
        )  # fmt: skip
        d = define.lines
        assert d[1].string.startswith('  "name"') and d[7].string.startswith('      "week"')
        assert len(d) == 12 and "Count late orders" in d[3].string
        self.play(rq.fade_out(), rs.fade_out(), FadeOut(m_tools), run_time=0.4)
        self.play(
            code.fade_in(),
            *[FadeIn(m) for m in (define.box, define.title, d[0], d[11])],
            run_time=0.6,
        )
        self.cue("a name")
        src = code.lines[0]
        hot = mark(src, W.TOOL["name"]).set_z_index(Z_CARD + 1)
        self.play(FadeIn(hot), run_time=0.25)
        self.play(TransformFromCopy(src.span(W.TOOL["name"]), d[1]), run_time=0.6)
        self.cue("a description")
        doc = W.TOOL["description"]
        hot2 = mark(code.lines[1], doc).set_z_index(Z_CARD + 1)
        self.play(Transform(hot, hot2), run_time=0.3)
        self.play(
            TransformFromCopy(code.lines[1].span(doc), d[3]), FadeIn(d[2]), run_time=0.6
        )
        self.cue("and a schema")
        hot3 = mark(src, "week: int").set_z_index(Z_CARD + 1)
        self.play(Transform(hot, hot3), run_time=0.3)
        self.play(
            TransformFromCopy(src.span("week: int"), d[7]),
            *[FadeIn(d[i]) for i in (4, 5, 6, 8, 9, 10)],
            run_time=0.7,
        )
        self.cue("a function's signature")
        hot4 = mark(src).set_z_index(Z_CARD + 1)
        self.play(Transform(hot, hot4), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(hot, rt, amp=0.03)])

        # ---- 2.4 into the context ------------------------------------------------------------ #
        self.voice(
            "The host places those definitions in the model's context. That is the "
            "context in the name: the protocol exists to put the right text in front "
            "of the model."
        )
        tools = model.block("tools", TOOLS_ROWS, "server")
        self.play(
            *[FadeOut(m, target_position=back.get_center(), scale=0.12) for m in define.mobs()],
            *[
                FadeOut(m, target_position=server.tool.get_center(), scale=0.2)
                for m in (*code.mobs(), hot)
            ],
            FadeOut(shade),
            run_time=0.8,
        )
        self.play(back.animate.move_to(link.port.get_center()), run_time=0.5)
        self.play(FadeTransform(back, tools), run_time=0.7)
        self.cue("the context in the name", ambient=lambda rt: [Throb(tools, rt, amp=0.03)])
        ring = SurroundingRectangle(model.ctx, buff=0.09, corner_radius=0.08, color=LOOK_C)
        ring.set_stroke(LOOK_C, width=2.5).set_fill(LOOK_C, opacity=0.14)
        self.play(self.aside("The context of the Model Context Protocol."), FadeIn(ring), run_time=0.5)
        self.settle(ambient=lambda rt: [Throb(ring, rt, amp=0.08), Throb(model.chip, rt, amp=0.1)])
        self.play(FadeOut(ring), run_time=0.3)
        self.close(self.st_protocol)

    # ====================================================================== #
    # 3 · One call
    # ====================================================================== #
    def scene_call(self):
        s = self.enter(self.st_protocol)
        model, host, server, link, grid = s.model, s.host, s.server, s.link, s.grid
        gear = server.tool.icon.get_center()

        # ---- 3.1 the model writes a call ---------------------------------------------------- #
        self.voice(
            "Now the same question. The model reads it, sees a tool that fits, and "
            "writes a call: a name and arguments. Still only text."
        )
        q = host.say(Q_BUBBLE)
        self.play(
            *self.chapter("3 · One call", LOOK_C, SPEC_NOTE),
            FadeIn(q, shift=UP * 0.15),
            run_time=0.6,
        )
        ask = model.block("user", Q_BLOCK, "user")
        self.play(TransformFromCopy(q.box, ask.box), FadeIn(ask, shift=LEFT * 0.4), run_time=0.6)
        self.cue("The model reads", ambient=lambda rt: [Throb(model.chip, rt, amp=0.12)])
        self.play(model.reading(self.span("and writes", floor=0.9, cap=2.0)))
        call = model.block("tool call", CALL_ROWS, "model")
        typing = call.typed(1.3)
        self.play(FadeIn(call, shift=RIGHT * 0.2), run_time=0.3)
        self.play(typing, Throb(model.chip, 1.3, amp=0.14, period=0.65))
        self.cue("Still only text")
        self.play(glow(call.box, MODEL_C), run_time=1.0)
        self.hold(ambient=lambda rt: [Throb(call, rt, amp=0.02)])

        # ---- 3.2 the host asks the user -------------------------------------------------------- #
        self.voice(
            "The host catches it, and first asks you. The specification wants a human "
            "in the loop, able to say no."
        )
        card = host.consent(W.SERVER["name"], W.TOOL["name"], ARGS)
        ghost = call.rows[0].copy()
        self.play(
            ghost.animate.move_to(card.tool.get_center()).set_opacity(0.0),
            *[FadeIn(m) for m in card.mobs()],
            run_time=0.7,
        )
        self.remove(ghost)
        self.cue("asks you")
        self.play(Throb(host.avatar, 1.0, amp=0.25, period=0.5), glow(card.box, LOOK_C))
        self.cue("able to say no", ambient=lambda rt: [Throb(host.avatar, rt, amp=0.1)])
        self.play(Indicate(card.deny, color=HOSTILE_C, scale_factor=1.12), run_time=0.9)
        self.hold(ambient=lambda rt: [Throb(card.allow, rt, amp=0.05)])
        on = card.pressed("allow")
        self.play(
            tap_ring(card.allow.get_center()),
            Succession(Wait(0.12), FadeIn(on, run_time=0.2)),
        )

        # ---- 3.3 the call crosses, the server works ------------------------------------------ #
        self.voice(
            "Then the client sends the call. The server runs its function against the "
            "real table: four hundred and twelve orders that week, twenty-nine of them "
            "late."
        )
        letter = link.letter().move_to(link.port.get_center())
        m_lab, i_lab = link.method("tools/call"), link.ident(2)
        self.play(
            *[
                FadeOut(m, target_position=link.port.get_center(), scale=0.15)
                for m in (*card.mobs(), on)
            ],
            FadeIn(letter, scale=0.4),
            run_time=0.5,
        )
        self.play(
            letter.animate.move_to(link.plug.body.get_center()),
            FadeIn(m_lab, shift=UP * 0.1),
            FadeIn(i_lab, shift=DOWN * 0.1),
            run_time=0.8,
        )
        spin = spinner(gear)

        def turning(rt):
            return Rotate(spin, angle=-TAU * rt / 1.1, about_point=gear, rate_func=linear, run_time=rt)

        self.play(FadeOut(letter, target_position=gear, scale=0.4), FadeIn(spin), run_time=0.35)
        self.cue("four hundred", ambient=lambda rt: [turning(rt)])
        lit, n = grid.lit(), ValueTracker(0)
        n_rows = always_redraw(lambda: grid.count(f"{n.get_value():.0f} orders", INK, 0))
        reveal = DotsReveal(lit)
        self.add(n_rows)
        rt = self.span("twenty-nine", floor=1.5, cap=2.4)
        self.play(reveal, n.animate.set_value(TOTAL), turning(rt), run_time=rt, rate_func=linear)
        self.remove(n_rows)
        n_rows = grid.count(f"{TOTAL} orders", INK, 0)
        self.add(n_rows)
        late, k = grid.late(), ValueTracker(0)
        n_late = always_redraw(lambda: grid.count(f"{k.get_value():.0f} late", LOOK_C, 1))
        reveal = DotsReveal(late)
        self.add(n_late)
        self.play(reveal, k.animate.set_value(LATE), turning(1.6), run_time=1.6, rate_func=linear)
        self.remove(n_late)
        n_late = grid.count(f"{LATE} late", LOOK_C, 1)
        self.add(n_late)
        self.play(FadeOut(spin), run_time=0.3)
        self.hold(ambient=lambda rt: [Throb(n_late, rt, amp=0.1)])

        # ---- 3.4 the result comes back ----------------------------------------------------------- #
        self.voice(
            "The result travels back under the same id, and lands in the context as "
            "more text."
        )
        back = link.letter(back=True).move_to(link.plug.body.get_center())
        r_lab = link.method("result", SERVER_C)
        self.play(
            FadeIn(back, scale=0.4, run_time=0.4),
            FadeOut(m_lab, run_time=0.25),
            Succession(Wait(0.25), FadeIn(r_lab, run_time=0.3)),
        )
        self.play(
            back.animate.move_to(link.port.get_center()),
            run_time=self.span("the same id", floor=0.7, cap=1.2),
        )
        self.play(Indicate(i_lab, color=INK, scale_factor=1.3), run_time=0.7)
        self.cue("lands in the context")
        res = model.block("tool result", RESULT_ROWS, "server")
        self.play(FadeTransform(back, res), FadeOut(r_lab), FadeOut(i_lab), run_time=0.7)
        self.hold(ambient=lambda rt: [Throb(res, rt, amp=0.02)])

        # ---- 3.5 the answer --------------------------------------------------------------------- #
        self.voice(
            "The model reads again, and answers. It never touched the database. It "
            "wrote a request, the host carried it, and the server did the work."
        )
        self.play(model.reading(1.1), Throb(model.chip, 1.1, amp=0.12, period=0.55))
        ans = model.block("assistant", ANSWER_ROWS, "model")
        typing = ans.typed(1.2)
        self.play(FadeIn(ans, shift=RIGHT * 0.2), run_time=0.3)
        self.play(typing, Throb(model.chip, 1.2, amp=0.14, period=0.6))
        reply = host.answer(ANSWER_BUBBLE)
        self.play(FadeIn(reply, shift=RIGHT * 0.4), run_time=0.5)
        self.cue("It never touched")
        self.play(self.aside("The model never touches the database."), run_time=0.5)
        self.cue("It wrote a request")
        self.play(glow(model.frame.box, MODEL_C), run_time=1.0)
        self.cue("the host carried")
        self.play(glow(host.frame.box, HOST_C), run_time=1.0)
        self.cue("the server did")
        self.play(glow(server.frame.box, SERVER_C), run_time=1.0)
        self.settle(ambient=lambda rt: [Throb(n_late, rt, amp=0.08)])
        self.close(self.st_call)


# ---- renderable scenes ---------------------------------------------------------------- #
class Intro(_Flat):
    def construct(self):
        self.over_card(
            "MCP, the Model Context Protocol. How does an AI application reach the "
            "tools and data it needs? Follow one question, from a model to a database "
            "and back."
        )
        self.play_intro()


class Alone(_Flat):
    def construct(self):
        self.scene_alone()


class Protocol(_Flat):
    def construct(self):
        self.scene_protocol()


class Call(_Flat):
    def construct(self):
        self.scene_call()


class Outro(_Flat):
    def construct(self):
        self.play_outro()
