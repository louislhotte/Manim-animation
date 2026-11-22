"""MCP, the Model Context Protocol: how an AI application plugs into tools and data.

A film made to be narrated: the voice carries the explanation, the screen carries the
real artifacts (the model's context, JSON-RPC messages, a function, a table) and five
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
                      behind a balancer: one of them dies, the others carry on
    6 Trust           what are you plugging in?   three hosts, four servers, one
                      plug: 7 pieces instead of 12 | then two servers, one the user
                      trusts (it reads files) and a stranger whose tool description
                      gives the model an order: it lands in the context like any
                      other text, the model writes a call to the trusted server's
                      tool, the user says no and unplugs the stranger
    7 Recap           the stage again, each actor lit on its sentence

Motif: the model's context (scenes 1 to 4 and 6 all show text arriving in it) and the
question "How many orders shipped late in week 46?". Colour is identity: purple the
model, blue the host and its client, orange a server and whatever text comes from
one, green the user. Gold marks the thing to look at, red what is hostile.

What is real: nothing was captured, and nothing was run: no model, no client, no
server. The messages are written from the MCP specification, revision 2026-07-28
(the stateless revision), in ``wire.py``, which checks them against that revision
when it is imported; what the model "writes" is scripted; the notes at the bottom
of the screen say so. The table is synthetic (seeded); the function that reads it
is real Python, runs at import, and its source and its result are what the film
shows; the tool definition is derived from that function's signature.

Scenes render alone (``./render.sh call --quick --check``) or stitched
(``./render.sh``). Scenes 2 to 5 open on the picture the previous one ended on
(``enter`` / ``close``), so the cuts between those clips do not show. Pacing:
``MCP_WPS`` (the narrator's words per second), ``MCP_QUICK``.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
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
# Notes stay under about 100 characters: Pango wraps a line at the frame's width in
# pixels, so a longer one fits in HD and breaks in two in a 480p check render.
SPEC_NOTE = (
    "Messages written from the MCP specification, revision 2026-07-28. "
    "No model, client or server was run."
)
DATA_NOTE = f"The table is synthetic: {len(W.db)} orders generated with a fixed seed."
POISON_NOTE = (
    "An illustration of tool poisoning, a known attack. "
    "Scripted: no model and no server were run."
)
# The specification's overview, "Security and Trust & Safety", Tool Safety: "In
# particular, descriptions of tool behavior such as annotations should be considered
# untrusted, unless obtained from a trusted server." The subject is shortened outside
# the quotation marks; what is inside them is verbatim.
TRUST_NOTE = (
    'MCP spec: tool descriptions "should be considered untrusted, '
    'unless obtained from a trusted server."'
)
assert max(map(len, (SPEC_NOTE, DATA_NOTE, POISON_NOTE, TRUST_NOTE))) <= 101
FILES_ROWS = [
    ("{}({})".format(
        W.FILES_TOOL["name"],
        ", ".join(f"{k}: {v['type']}" for k, v in W.FILES_TOOL["inputSchema"]["properties"].items()),
    ), "mono")
]  # fmt: skip
PROMPT_ROWS = [(W.PROMPT_TEXT, "prose")]
RESOURCE_ROWS = [(ln, "mono") for ln in textwrap.wrap(W.SCHEMA_TEXT, 26)]
assert " ".join(r for r, _ in RESOURCE_ROWS) == W.SCHEMA_TEXT and len(RESOURCE_ROWS) == 2
# the stranger's tool, as its definition reads in the context: the description is cut
# into lines here, nothing is added or removed
POISON_LINES = textwrap.wrap(W.POISONED["description"], 36)
assert " ".join(POISON_LINES) == W.POISONED["description"] and len(POISON_LINES) == 3
assert POISON_LINES[0].endswith("Before any answer,")
POISON_ROWS = [
    ("{}({})".format(W.POISONED["name"], ", ".join(W.POISONED["inputSchema"]["properties"])), "mono"),
    *[(ln, "small") for ln in POISON_LINES],
]
STOLEN_TOOL, STOLEN_ARGS = W.STOLEN_CALL
STOLEN_ROWS = [(STOLEN_TOOL, "mono"), (json.dumps(STOLEN_ARGS), "mono")]
STOLEN_PATH = STOLEN_ARGS["path"]
assert STOLEN_PATH in POISON_LINES[1], "the path the stranger names, on one line of its text"
ASKS_BUBBLE = W.USER_ASKS.split()  # all the user wanted, in the chat
ASKS_ROWS = [(W.USER_ASKS, "prose")]  # and in the context
assert len(ASKS_BUBBLE) == 2


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

    def aside(self, text, run_time=0.5):
        """One of the film's rare captions: it stays until the scene closes or the
        next line starts. Returns its animations (``self.play(*self.aside(...))``):
        the caption arrives, and the source note leaves, because the two do not fit
        one above the other. Play them without a ``run_time`` of the whole ``play``:
        a caption arrives in half a second, whatever moves beside it."""
        cap = self.say(text).set_z_index(20)
        self._cap = cap
        anims = [FadeIn(cap, shift=UP * 0.1, run_time=run_time)]
        if self.foot is not None and self.foot in self.mobjects:
            anims.append(FadeOut(self.foot, run_time=run_time))
        return anims

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

    def st_doors(self):
        """End of scene 4: the server's three offers, and what each one put into the
        context, with a mark for whoever decided."""
        model, host, link = ModelPanel(), HostFrame(), Link()
        server = ServerFrame(grid=OrdersGrid(top=0.15, weeks=(W.WEEK,)))
        prompt_offer, resource_offer = door_offers()
        tools = model.block("tools", TOOLS_ROWS, "server")
        prompt = model.block("prompt", PROMPT_ROWS, "server")
        resource = model.block("resource", RESOURCE_ROWS, "server")
        call = model.block("tool call", CALL_ROWS, "model")
        res = model.block("tool result", RESULT_ROWS, "server")
        marks = [badge_on(prompt, "user"), badge_on(resource, "app"), badge_on(call, "model")]
        left = [
            *model.furniture(), tools, prompt, resource, call, res, *marks,
            *host.furniture(), *link.mobs(),
        ]  # fmt: skip
        right = [*server.furniture(), prompt_offer, resource_offer]
        return SimpleNamespace(
            model=model, host=host, link=link, server=server,
            left=left, right=right, mobs=left + right,
        )  # fmt: skip

    def exchange(self, link, method, n, flash=None, rt=0.45, arrive=()):
        """A request crosses the wire and its result comes back. Returns the letter
        that has just come back (it is at the client's port) and the two labels still
        on screen, the method and the id: a quick round trip keeps its method's name
        up all the way, long enough to be read. The caller turns the letter into what
        it carried and takes the labels away. ``flash``: the offer that answers;
        ``arrive``: what else happens when the request arrives."""
        out = link.letter().move_to(link.port.get_center())
        m_lab, i_lab = link.method(method), link.ident(n)
        self.play(
            FadeIn(out, scale=0.4),
            FadeIn(m_lab, shift=UP * 0.1),
            FadeIn(i_lab, shift=DOWN * 0.1),
            run_time=0.25,
        )
        self.play(out.animate.move_to(link.plug.body.get_center()), run_time=rt)
        back = link.letter(back=True).move_to(link.plug.body.get_center())
        self.play(
            FadeOut(out, run_time=0.2),
            FadeIn(back, run_time=0.2),
            *([glow(flash.box, LOOK_C, 5, rt=0.4)] if flash is not None else []),
            *arrive,
        )
        self.play(back.animate.move_to(link.port.get_center()), run_time=rt)
        return back, [m_lab, i_lab]


class _Flat(_Common, Scene):
    # ====================================================================== #
    # 1 · A model alone
    # ====================================================================== #
    def scene_alone(self):
        # a model alone: in the middle of the frame, until the world it cannot reach
        # appears and it takes its place on the left of the stage
        middle = -(MODEL_X[0] + MODEL_X[1]) / 2
        model, grid = ModelPanel().shifted(middle), OrdersGrid()

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
            *model.slide(-middle),
            FadeIn(grid.title, shift=LEFT * 0.2),
            FadeIn(grid.lock, shift=LEFT * 0.2),
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
            "It names three roles. The application you talk to, a chat window or a code "
            "editor, is the host. Each outside system is wrapped by a small program, a "
            "server. And inside the host, one client per server speaks the protocol."
        )
        self.play(
            *self.chapter("2 · One protocol", HOST_C, SPEC_NOTE),
            *[FadeOut(m, shift=UP * 0.2) for m in (*s.words, *s.caps)],
            FadeOut(s.ask),
            FadeOut(s.reply),
            run_time=0.7,
        )
        model.drop(s.ask, s.reply)
        # each actor is drawn while the sentence describes it, and gets its name on
        # the word that names it: host, server, client
        self.cue("The application")
        self.play(
            Create(host.frame.box),
            run_time=self.span("a chat window", floor=0.9, cap=2.2),
        )
        self.play(
            LaggedStart(
                FadeIn(host.avatar, scale=0.6),
                FadeIn(host.who),
                FadeIn(host.bar),
                FadeIn(host.clip),
                lag_ratio=0.5,
            ),
            run_time=self.span("is the host", floor=0.7, cap=2.6),
        )
        self.cue("is the host")  # the name first, then the glow: its plate hides the halo
        self.play(FadeIn(host.frame.tag), run_time=0.35)
        self.play(glow(host.frame.box, HOST_C, rt=0.8))
        self.cue("Each outside system")
        self.play(
            Create(server.frame.box),
            run_time=self.span("by a small program", floor=0.9, cap=2.2),
        )
        self.play(FadeIn(server.tool, shift=DOWN * 0.2), run_time=0.5)
        self.cue("a server", ambient=lambda rt: [Throb(server.tool, rt, amp=0.05)])
        self.play(FadeIn(server.frame.tag), run_time=0.35)
        self.play(glow(server.frame.box, SERVER_C, rt=0.8))
        self.cue("And inside the host")
        home = link.plug.get_center().copy()
        link.plug.move_to(link.parked())
        self.play(FadeIn(link.port, scale=0.5), run_time=0.4)
        self.cue("one client", ambient=lambda rt: [Throb(link.port, rt, amp=0.25)])
        self.play(FadeIn(link.name, shift=RIGHT * 0.1), glow(link.port, LOOK_C, 5), run_time=0.8)
        self.cue("per server")
        self.play(FadeIn(link.socket, scale=0.5), run_time=0.3)
        self.play(Create(link.cable), link.plug.animate.move_to(home), run_time=0.8)
        self.play(glow(link.socket[0], LOOK_C, width=5), run_time=0.7)
        self.hold(
            ambient=lambda rt: [
                Throb(link.port, rt, amp=0.2),
                ShowPassingFlash(
                    link.cable.copy().set_stroke(LOOK_C, width=7).set_z_index(Z_LINK + 1),
                    time_width=0.5,
                    run_time=rt,
                ),
            ]
        )

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
        # (a token is marked with the comma that follows it: the box then closes in free
        # space, not on the comma)
        m_method = rq.mark('"method": "tools/list",')
        self.play(FadeIn(m_method), run_time=0.3)
        self.cue("carries")
        m_id = rq.mark('"id": 1,')
        self.play(FadeIn(m_id), run_time=0.3)
        self.cue("The response comes back", ambient=lambda rt: [Throb(m_id, rt, amp=0.08)])
        back = link.letter(back=True).move_to(link.plug.body.get_center())
        self.play(letter.animate.move_to(link.plug.body.get_center()), run_time=0.35)
        self.play(FadeOut(letter), FadeIn(back), run_time=0.2)
        self.play(
            back.animate.move_to(link.middle()), rs.fade_in(shift=DOWN * 0.2), run_time=0.7
        )
        self.cue("the same id")
        m_same = rs.mark('"id": 1,')
        tie = DashedLine(m_id.get_right(), m_same.get_left(), dash_length=0.1)
        tie.set_stroke(LOOK_C, width=2.5).set_z_index(Z_CARD + 1)
        self.play(FadeIn(m_same), Create(tie), run_time=0.5)
        self.hold(ambient=lambda rt: throbs([m_id, m_same], rt, amp=0.08))

        # ---- 2.3 what can you do? ----------------------------------------------------------- #
        self.voice(
            "This first request asks: which tools do you have? The server answers with "
            "its list. Each tool is a name, a description, and a schema for its "
            "arguments, often built straight from a function's signature."
        )
        self.play(FadeOut(tie), FadeOut(m_id), FadeOut(m_same), run_time=0.3)
        self.cue("which tools do you have", ambient=lambda rt: [Throb(m_method, rt, amp=0.06)])
        self.play(Indicate(m_method, color=LOOK_C, scale_factor=1.1), run_time=0.9)  # the question
        self.cue("The server answers", ambient=lambda rt: [Throb(m_method, rt, amp=0.06)])
        m_tools = rs.mark('"tools": [ … ],')  # and the answer, on the words that say so
        self.play(FadeOut(m_method), FadeIn(m_tools), run_time=0.4)
        self.cue("its list", ambient=lambda rt: [Throb(m_tools, rt, amp=0.06)])
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
        self.cue("for its arguments")  # the type hint and what it became, side by side
        twin = mark(d[7], d[7].string.strip()).set_z_index(Z_CARD + 1)
        self.play(FadeIn(twin), run_time=0.3)
        self.cue("a function's signature", ambient=lambda rt: throbs([hot, twin], rt, amp=0.05))
        hot4 = mark(src).set_z_index(Z_CARD + 1)
        self.play(Transform(hot, hot4), FadeOut(twin), run_time=0.4)
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
        self.play(*self.aside("This is the context in Model Context Protocol."), FadeIn(ring, run_time=0.5))
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
        self.play(FadeIn(ask, shift=LEFT * 0.4), run_time=0.6)  # the host puts it in the context
        self.cue(
            "The model reads",
            ambient=lambda rt: [Throb(model.chip, rt, amp=0.2), Throb(ask, rt, amp=0.03)],
        )
        self.play(model.reading(self.span("sees a tool", floor=0.9, cap=2.0)))
        self.play(glow(s.tools.box, LOOK_C), Throb(model.chip, 1.0, amp=0.12, period=0.5))
        self.cue("and writes", ambient=lambda rt: [Throb(model.chip, rt, amp=0.2)])
        call = model.block("tool call", CALL_ROWS, "model")
        typing = call.typed(1.3)
        self.play(FadeIn(call, shift=RIGHT * 0.2), run_time=0.3)
        self.play(typing, Throb(model.chip, 1.3, amp=0.14, period=0.65))
        self.cue("a name")  # the two parts of a call, each on its word
        part = mark(call.rows[0], W.TOOL["name"])
        self.play(FadeIn(part), run_time=0.3)
        self.cue("and arguments")
        self.play(Transform(part, mark(call.rows[0], ARGS)), run_time=0.3)
        self.cue("Still only text")
        self.play(FadeOut(part, run_time=0.3), glow(call.box, MODEL_C))
        self.hold(ambient=lambda rt: [Throb(call, rt, amp=0.04), Throb(model.chip, rt, amp=0.2)])

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
        self.cue(
            "able to say no",
            ambient=lambda rt: [
                Throb(host.avatar, rt, amp=0.25),
                *throbs([card.deny, card.allow], rt, amp=0.035),
            ],
        )
        self.play(Indicate(card.deny, color=INK, scale_factor=1.12), run_time=0.9)
        self.hold(ambient=lambda rt: [Throb(card.allow, rt, amp=0.05)])
        on = card.pressed("allow")
        self.play(
            tap_ring(card.allow.get_center()),
            Succession(Wait(0.12), FadeIn(on, run_time=0.2)),
        )

        # ---- 3.3 the call crosses, the server works ------------------------------------------ #
        self.voice(
            "Then the client sends the call. The server runs its function against the "
            "table: four hundred and twelve orders that week, twenty-nine of them "
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
        self.cue("against the table", ambient=lambda rt: [turning(rt)])
        # the function reads the table: a band of light runs down its rows
        cx = (grid.x0 + grid.x1) / 2
        scan = Rectangle(width=grid.x1 - grid.x0 + 0.14, height=0.26)
        scan.set_stroke(width=0).set_fill(SERVER_C, opacity=0.3).set_z_index(Z_BAND)
        scan.move_to([cx, max(grid.head_y.values()) - 0.25, 0])
        rt = self.span("four hundred", floor=0.9, cap=1.6)
        self.play(
            Succession(
                FadeIn(scan, run_time=0.15),
                scan.animate(run_time=rt - 0.3, rate_func=linear).move_to([cx, grid.bottom + 0.13, 0]),
                FadeOut(scan, run_time=0.15),
            ),
            turning(rt),
        )
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
            "The model reads again, and answers. It never touched the database, and "
            "never saw its password. It wrote a request, the host carried it, and the "
            "server did the work."
        )
        self.play(model.reading(1.1), Throb(model.chip, 1.1, amp=0.12, period=0.55))
        ans = model.block("assistant", ANSWER_ROWS, "model")
        typing = ans.typed(1.2)
        self.play(FadeIn(ans, shift=RIGHT * 0.2), run_time=0.3)
        self.play(typing, Throb(model.chip, 1.2, amp=0.14, period=0.6))
        reply = host.answer(ANSWER_BUBBLE)
        self.play(FadeIn(reply, shift=RIGHT * 0.4), run_time=0.5)
        self.cue("It never touched")
        self.play(*self.aside("The model never touches the database."))
        self.cue("never saw")  # the credentials stay with the server
        self.play(Indicate(grid.lock, color=LOOK_C, scale_factor=1.5), run_time=0.9)
        self.cue("It wrote a request")
        self.play(glow(model.frame.box, MODEL_C), run_time=1.0)
        self.cue("the host carried")
        self.play(glow(host.frame.box, HOST_C), run_time=1.0)
        self.cue("the server did")
        self.play(glow(server.frame.box, SERVER_C), run_time=1.0)
        self.settle(ambient=lambda rt: [Throb(n_late, rt, amp=0.12), Throb(reply, rt, amp=0.04)])
        self.close(self.st_call)

    # ====================================================================== #
    # 4 · Three doors
    # ====================================================================== #
    def scene_doors(self):
        s = self.enter(self.st_call)
        model, host, server, link = s.model, s.host, s.server, s.link
        table = OrdersGrid(top=0.15, weeks=(W.WEEK,))
        prompt_offer, resource_offer = door_offers()
        for n, method in ((3, "prompts/list"), (4, "resources/list"), (5, "prompts/get"),
                          (6, "resources/read"), (7, "tools/call")):  # fmt: skip
            assert W.exchange(n)[0]["method"] == method

        # ---- 4.1 three things a server can offer ----------------------------------------------- #
        self.voice(
            "Tools are one of three things a server can offer. What separates them is "
            "who decides to use them."
        )
        gone = [s.ask, s.call, s.res, s.ans, s.q, s.reply, s.lit, s.late, s.n_rows, s.n_late]
        self.play(
            *self.chapter("4 · Three doors", USER_C, SPEC_NOTE),
            *[FadeOut(m) for m in (*gone, *s.grid.furniture())],
            run_time=0.6,
        )
        model.drop(s.ask, s.call, s.res, s.ans)
        self.play(*[FadeIn(m) for m in table.furniture()], run_time=0.5)
        for method, n, offered in (("prompts/list", 3, prompt_offer), ("resources/list", 4, resource_offer)):
            back, labs = self.exchange(
                link, method, n, arrive=[FadeIn(offered, shift=LEFT * 0.2, run_time=0.4)]
            )
            self.play(
                FadeOut(back, target_position=host.bar.get_center(), scale=0.3),
                *[FadeOut(m) for m in labs],
                run_time=0.3,
            )
        self.cue("who decides")
        self.play(
            LaggedStart(
                glow(host.avatar[0], USER_C, 6),
                glow(host.frame.box, HOST_C),
                glow(model.frame.box, MODEL_C),
                lag_ratio=0.45,
            ),
            run_time=1.6,
        )
        self.hold(ambient=lambda rt: throbs([prompt_offer, resource_offer], rt, amp=0.03))

        # ---- 4.2 a prompt: the user decides ------------------------------------------------------ #
        self.voice("A prompt is a ready-made message. The user picks it, like a slash command.")
        slash = Chars("/", fs=17, color=INK, font=MONO).at(host.field_x, host.field_y)
        menu, item = slash_menu(host)
        self.play(Throb(host.avatar, 0.5, amp=0.3, period=0.25), FadeIn(slash, scale=1.5), run_time=0.5)
        self.play(
            FadeIn(menu, shift=UP * 0.1),
            FadeIn(item, shift=UP * 0.1),
            glow(prompt_offer.box, LOOK_C, 5, rt=0.6),
            run_time=0.6,
        )
        self.cue("The user picks", ambient=lambda rt: [Throb(item, rt, amp=0.06)])
        # what the user sends is the prompt's name and its argument: the request that
        # leaves is prompts/get with exactly those
        sent = W.exchange(5)[0]["params"]
        assert (sent["name"], sent["arguments"]) == (W.PROMPT["name"], {"week": str(W.WEEK)})
        typed = Chars(f"/{sent['name']} {sent['arguments']['week']}", fs=17, color=INK, font=MONO)
        typed.at(host.field_x, host.field_y)
        week = typed.span(sent["arguments"]["week"])
        week.set_opacity(0)
        self.play(tap_ring(item.get_center()))
        self.play(
            FadeOut(menu),
            FadeOut(item),
            FadeOut(slash, run_time=0.15),
            Succession(Wait(0.15), FadeIn(typed, run_time=0.25)),
        )
        self.play(  # the user types the argument
            TypeOut(typed, SimpleNamespace(glyphs=list(week)), run_time=0.4),
            Throb(host.avatar, 0.4, amp=0.3, period=0.2),
        )
        back, labs = self.exchange(link, "prompts/get", 5, flash=prompt_offer)
        prompt = model.block("prompt", PROMPT_ROWS, "server")
        by_user = badge_on(prompt, "user")
        self.play(
            FadeTransform(back, prompt),
            FadeIn(by_user, scale=0.5),
            FadeOut(typed),
            *[FadeOut(m) for m in labs],
            run_time=0.6,
        )
        self.hold(ambient=lambda rt: [Throb(by_user, rt, amp=0.25)])

        # ---- 4.3 a resource: the application decides ----------------------------------------------- #
        self.voice(
            "A resource is data with an address: here, the table's schema. The "
            "application decides to attach it."
        )
        self.cue("data with an address")
        address = mark(resource_offer.label)
        self.play(FadeIn(address), run_time=0.3)
        self.cue("the table's schema", ambient=lambda rt: [Throb(address, rt, amp=0.04)])
        what = SurroundingRectangle(  # what the address points to
            VGroup(table.title, table.lock), buff=0.06, corner_radius=0.08, color=LOOK_C
        )
        what.set_stroke(LOOK_C, width=2.5).set_fill(LOOK_C, opacity=0.12)
        self.play(Succession(FadeIn(what, run_time=0.3), Wait(0.4), FadeOut(what, run_time=0.3)))
        self.cue("The application decides")
        ring = Circle(radius=0.25, stroke_color=HOST_C, stroke_width=3.5).move_to(host.clip)
        self.play(
            FadeIn(ring, scale=1.8), glow(host.frame.box, HOST_C, rt=0.7), FadeOut(address), run_time=0.7
        )
        back, labs = self.exchange(link, "resources/read", 6, flash=resource_offer)
        resource = model.block("resource", RESOURCE_ROWS, "server")
        by_app = badge_on(resource, "app")
        self.play(
            FadeTransform(back, resource),
            FadeIn(by_app, scale=0.5),
            FadeOut(ring),
            *[FadeOut(m) for m in labs],
            run_time=0.6,
        )
        self.hold(ambient=lambda rt: [Throb(by_app, rt, amp=0.25)])

        # ---- 4.4 a tool: the model decides ---------------------------------------------------------- #
        self.voice("And a tool, as we saw, runs when the model decides.")
        self.play(model.reading(0.7), Throb(model.chip, 0.7, amp=0.2, period=0.35))
        call = model.block("tool call", CALL_ROWS, "model")
        typing, by_model = call.typed(0.6), badge_on(call, "model")
        self.play(FadeIn(call, shift=RIGHT * 0.2), FadeIn(by_model, scale=0.5), run_time=0.3)
        self.play(typing)
        back, labs = self.exchange(link, "tools/call", 7, flash=server.tool, rt=0.35)
        res = model.block("tool result", RESULT_ROWS, "server")
        self.play(FadeTransform(back, res), *[FadeOut(m) for m in labs], run_time=0.5)
        self.hold(ambient=lambda rt: [Throb(by_model, rt, amp=0.25)])

        # ---- 4.5 one place ------------------------------------------------------------------------- #
        self.voice("Three doors, and all of them lead to the same place: the model's context.")
        self.play(
            *self.aside(
                "The user picks prompts, the application attaches resources, "
                "the model calls tools."
            ),
            LaggedStart(
                glow(prompt.box, USER_C), glow(resource.box, HOST_C), glow(call.box, MODEL_C),
                lag_ratio=0.5, run_time=2.0,
            ),  # fmt: skip
        )
        self.cue("the model's context", ambient=lambda rt: throbs([by_user, by_app, by_model], rt, amp=0.25))
        self.play(glow(model.frame.box, LOOK_C), Throb(model.chip, 1.0, amp=0.2, period=0.5))
        self.settle(ambient=lambda rt: throbs([by_user, by_app, by_model], rt, amp=0.25))
        self.close(self.st_doors)

    # ====================================================================== #
    # 5 · Anywhere
    # ====================================================================== #
    def scene_anywhere(self):
        s = self.enter(self.st_doors)
        y = 0.95
        ht = host_tile((-5.0, y))
        st = server_tile((0.75, y), label=W.TOOL["name"])
        far_x = 5.05  # where the server stands once it is remote
        near = st.get_center().copy()
        far = near + RIGHT * (far_x - 0.75)  # a move straight to the right: the cable stays level
        machine = Frame((-6.75, 2.6), STEEL, "your machine", top=y + 1.3, bot=y - 1.25, fs=18)
        p0, p1 = ht.port.get_right(), st.socket.get_left()
        lanes = VGroup(
            Line(p0 + UP * 0.1, p1 + UP * 0.1), Line(p1 + DOWN * 0.1, p0 + DOWN * 0.1)
        ).set_stroke(STEEL, width=3)
        mid = (p0 + p1) / 2
        names = [
            Chars(t, fs=17, color=c, font=MONO).at(mid[0] - 0.4, y + dy)
            for t, c, dy in (("stdin", HOST_C, 0.45), ("stdout", SERVER_C, -0.45))
        ]

        def one_line(message, key):
            """A message as it goes down the pipe: one line, its payload folded."""
            text = W.on_one_line(message)
            assert "\n" not in text
            return text[: text.index(f'"{key}":') + len(key) + 3] + "{…}}"

        req1, res1 = W.exchange(1)
        lines = []  # one request, one response: enough to see "a line each"
        for i, (message, key, color) in enumerate(
            ((req1, "params", HOST_C), (res1, "result", SERVER_C))
        ):
            ln = Chars(one_line(message, key) + "\\n", fs=18, font=MONO)
            paint_json(ln).tint("\\n", LOOK_C)
            ln.at(-3.7, -1.1 - 0.58 * i)
            lines.append(VGroup(Dot(radius=0.07, color=color).move_to([-4.0, -1.1 - 0.58 * i, 0]), ln))

        # ---- 5.1 on your machine: a child process, two pipes ------------------------------------- #
        self.voice(
            "Where does a server run? On your own machine, the host starts it as a "
            "child process, and they exchange lines of JSON over standard input and "
            "output."
        )
        self.play(
            *self.chapter("5 · Anywhere", STEEL, SPEC_NOTE),
            FadeTransform(VGroup(*s.left), ht),
            *[FadeOut(m, scale=0.7) for m in s.right],
            run_time=1.0,
        )
        self.cue("On your own machine", ambient=lambda rt: [Throb(ht, rt, amp=0.03)])
        self.play(Create(machine.box), FadeIn(machine.tag), run_time=0.8)
        self.cue("starts it as a child", ambient=lambda rt: [Throb(ht.port, rt, amp=0.3, period=0.7)])
        st.save_state()
        st.scale(0.15).move_to(ht.port.get_center())
        self.play(Restore(st), Create(lanes), run_time=0.9)
        self.play(*[FadeIn(n, shift=UP * 0.05) for n in names], run_time=0.3)

        def flowing(rt):
            return [
                stream(lanes[0], HOST_C, n=max(2, round(rt * 1.4)), run_time=rt, lag=0.18),
                stream(lanes[1], SERVER_C, n=max(2, round(rt * 1.4)), run_time=rt, lag=0.18),
            ]

        self.cue("lines of JSON", ambient=flowing)
        self.play(
            LaggedStart(*[FadeIn(ln, shift=UP * 0.15) for ln in lines], lag_ratio=0.5),
            *flowing(1.2),
            run_time=1.2,
        )
        self.hold(ambient=flowing)

        # ---- 5.2 or far away: HTTP, and a token ----------------------------------------------------- #
        self.voice(
            "Or far away. Then every request is an HTTP POST, and an access token can "
            "say who is asking."
        )
        q1 = p1 + (far - near)
        cable = Line(p0, q1).set_stroke(STEEL, width=5)
        alone = Frame((-6.75, -3.0), STEEL, "your machine", top=y + 1.3, bot=y - 1.25, fs=18)
        lock = lock_icon(0.4, STEEL).move_to((p0 + q1) / 2)
        https = Chars("HTTPS", fs=17, color=MUTED, font=MONO)
        https.at((p0 + q1)[0] / 2 - https.body.width / 2, y + 0.48)
        self.play(
            st.animate.move_to(far),
            Transform(machine.box, alone.box),
            ReplacementTransform(lanes, cable),
            *[FadeOut(m) for m in (*names, *lines)],
            run_time=1.1,
        )
        self.play(FadeIn(lock, scale=1.6), FadeIn(https), run_time=0.4)
        rows = [W.HTTP_HEAD[i] for i in (0, 2, 5, 6, 7)] + ["…"]
        post = MsgCard(
            rows, at=(-2.75, 0.15), fs=19, kind="http", title="one request, over the network", edge=HOST_C
        )
        self.play(post.fade_in(), run_time=0.5)
        self.cue("an HTTP POST")
        hot = post.mark("POST")
        self.play(FadeIn(hot), run_time=0.3)
        self.cue("an access token", ambient=lambda rt: [Throb(hot, rt, amp=0.08)])
        self.play(Transform(hot, mark(post.line("Authorization")).set_z_index(Z_CARD + 1)), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(hot, rt, amp=0.03), Throb(lock, rt, amp=0.2)])

        # ---- 5.3 nothing to remember: every request says it all ------------------------------------ #
        self.voice(
            "Since the July twenty twenty-six revision, there is no handshake and no "
            "session. Every request carries the protocol version and what the client "
            "supports."
        )
        folded = W.META_KEYS[1]
        body = MsgCard(
            W.jlines(W.meta(), fold=(folded,), inline=64), at=(-4.6, -0.8), fs=17,
            title="in every request: params._meta", edge=HOST_C,
        )  # fmt: skip
        gone = [struck("initialize", 18), struck("Mcp-Session-Id", 18)]
        gone[0].move_to([-0.6, 0.2, 0])
        gone[1].next_to(gone[0], RIGHT, buff=0.7)
        self.play(post.fade_out(), FadeOut(hot), run_time=0.4)
        self.play(body.fade_in(), run_time=0.5)
        rev = body.mark(f'"{W.PROTOCOL}",')  # the revision, as every request states it
        self.play(FadeIn(rev), run_time=0.3)
        self.cue("no handshake", ambient=lambda rt: [Throb(rev, rt, amp=0.06)])
        self.play(FadeIn(gone[0], shift=DOWN * 0.1), FadeOut(rev), run_time=0.4)
        self.cue("no session")
        self.play(FadeIn(gone[1], shift=DOWN * 0.1), run_time=0.4)
        self.cue("the protocol version", ambient=lambda rt: throbs(gone, rt, amp=0.05))
        hot = mark(body.line(W.META_KEYS[0])).set_z_index(Z_CARD + 1)
        self.play(FadeIn(hot), *[FadeOut(g) for g in gone], run_time=0.4)
        self.cue("what the client supports", ambient=lambda rt: [Throb(hot, rt, amp=0.02)])
        self.play(Transform(hot, mark(body.line(W.META_KEYS[2])).set_z_index(Z_CARD + 1)), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(hot, rt, amp=0.02)])

        # ---- 5.4 so any copy can answer -------------------------------------------------------------- #
        self.voice(
            "So a busy server can run as many copies as it needs behind a load balancer. "
            "Any copy can answer any request, and if one disappears, the others carry on."
        )
        ys = (2.1, 0.4, -1.3)  # a clear gap between a copy's name and the copy above
        copies = [server_tile((far_x, yy), label=W.TOOL["name"]) for yy in ys]
        lb = balancer((1.9, 0.4), s=0.7)
        trunk = Line(p0, lb.get_left()).set_stroke(STEEL, width=5)
        legs = [Line(lb.get_right(), c.socket.get_left()).set_stroke(STEEL, width=4) for c in copies]
        before, after = (0, 1, 2), (0, 2, 0, 2)  # who answers, before and after a copy dies
        tally = Chars("answered", fs=18, color=MUTED).at(-6.6, -0.95)
        ticks = [
            Dot(radius=0.1, color=USER_C).move_to([-5.15 + 0.34 * k, -0.95, 0])
            for k in range(len(before) + len(after))
        ]

        def trips(order, first):
            """Requests dealt to the copies in ``order``; each answer adds a dot."""
            runs = []
            for i, k in enumerate(order):
                way = polyline(p0, lb.get_center(), copies[k].socket.get_left())
                home = polyline(copies[k].socket.get_left(), lb.get_center(), p0)
                runs.append(
                    Succession(
                        Travel(envelope(HOST_C, 0.3, 0.2), way, run_time=0.7),
                        Travel(envelope(SERVER_C, 0.3, 0.2), home, run_time=0.7),
                        FadeIn(ticks[first + i], scale=2.5, run_time=0.15),
                    )
                )
            return LaggedStart(*runs, lag_ratio=0.3)

        # the first copy, with the balancer already in front of it: no loose cable
        self.play(
            body.fade_out(),
            *[FadeOut(m) for m in (hot, lock, https)],
            ReplacementTransform(st, copies[0]),
            ReplacementTransform(cable, trunk),
            FadeIn(lb, scale=0.5),
            Create(legs[0]),
            run_time=0.8,
        )
        self.cue("as many copies", ambient=lambda rt: [Throb(copies[0], rt, amp=0.03)])
        self.play(
            LaggedStart(
                *[
                    AnimationGroup(FadeIn(c, shift=UP * 0.3), Create(leg))
                    for c, leg in zip(copies[1:], legs[1:], strict=True)
                ],
                lag_ratio=0.5,
            ),
            run_time=1.1,
        )
        self.cue("a load balancer", ambient=lambda rt: throbs(copies, rt, amp=0.03))
        self.play(glow(lb[0], LOOK_C, 5, rt=0.9), Throb(lb, 0.9, amp=0.12, period=0.45))
        self.cue("Any copy", ambient=lambda rt: throbs(copies, rt, amp=0.03))
        self.play(FadeIn(tally, run_time=0.3), trips(before, 0))
        self.cue("if one disappears")
        dead = make_cross(BAD, sw=7, scale=1.3).move_to(copies[1])
        down = copies[1].copy().fade(0.8)  # fade(), not set_opacity(): frames have no fill
        down[1][0].set_fill(BG, opacity=1)  # the plate under its name stays whole
        self.play(
            Transform(copies[1], down),
            legs[1].animate.set_stroke(opacity=0.15),
            FadeIn(dead, scale=1.6),
            run_time=0.5,
        )
        self.cue("the others carry on")
        self.play(trips(after, len(before)))
        self.settle(ambient=lambda rt: throbs(ticks, rt, amp=0.3))
        self.wipe()

    # ====================================================================== #
    # 6 · Trust
    # ====================================================================== #
    def scene_trust(self):
        assert (W.BESPOKE, W.SHARED) == (12, 7), "the narration says seven, not twelve"
        servers = [
            server_tile((5.05, yy), name=n, h=1.0)
            for yy, n in zip((2.05, 0.8, -0.45, -1.7), W.SYSTEMS, strict=True)
        ]
        hosts = [  # inside a host, one client per server: four ports each
            host_tile((-5.0, yy), name=n, h=1.35, clients=len(servers))
            for yy, n in zip((1.85, 0.2, -1.45), W.HOSTS, strict=True)
        ]
        cables = [
            Line(port.get_right(), sv.socket.get_left()).set_stroke(STEEL, width=2.5, opacity=0.8)
            for h in hosts
            for port, sv in zip(h.ports, servers, strict=True)
        ]
        assert len(cables) == W.BESPOKE and len(hosts) + len(servers) == W.SHARED

        # ---- 6.1 the payoff ----------------------------------------------------------------------- #
        self.voice(
            "That is the payoff. Wrap a system once, and every host that speaks the "
            "protocol can use it. Three hosts and four systems: seven pieces to build, "
            "not twelve."
        )
        self.play(
            *self.chapter("6 · Trust", HOSTILE_C),
            LaggedStart(*[FadeIn(sv, shift=LEFT * 0.3) for sv in servers], lag_ratio=0.2),
            run_time=1.2,
        )
        self.cue("every host", ambient=lambda rt: throbs(servers, rt, amp=0.03))
        self.play(
            LaggedStart(*[FadeIn(h, shift=RIGHT * 0.3) for h in hosts], lag_ratio=0.2),
            LaggedStart(*[Create(c) for c in cables], lag_ratio=0.08),
            run_time=1.6,
        )
        self.cue("Three hosts", ambient=lambda rt: throbs(hosts, rt, amp=0.03))
        self.play(*[glow(h.box, HOST_C, rt=0.8) for h in hosts], run_time=0.8)
        self.cue("four systems")
        self.play(*[glow(sv.box, SERVER_C, rt=0.8) for sv in servers], run_time=0.8)
        self.cue("seven pieces")
        seven = txt(f"{W.SHARED} pieces to build", fs=30, color=LOOK_C, weight="BOLD")
        twelve = txt(f"not {W.BESPOKE}", fs=24, color=MUTED)
        VGroup(seven, twelve).arrange(RIGHT, buff=0.5, aligned_edge=DOWN).move_to([0, -2.72, 0])
        self.play(  # the seven things somebody writes: three hosts, four servers
            FadeIn(seven, shift=UP * 0.15),
            *[glow(h.box, LOOK_C, 6, rt=0.9) for h in hosts],
            *[glow(sv.box, LOOK_C, 6, rt=0.9) for sv in servers],
            run_time=0.9,
        )
        self.cue("not twelve")
        self.play(  # the twelve connections, which nobody has to write one by one
            FadeIn(twelve, shift=UP * 0.1),
            *[
                ShowPassingFlash(c.copy().set_stroke(INK, width=4, opacity=1), time_width=0.6)
                for c in cables
            ],
            run_time=0.8,
        )
        self.hold(ambient=lambda rt: [Throb(seven, rt, amp=0.05)])

        # ---- 6.2 what you are plugging in ------------------------------------------------------------- #
        self.voice(
            "But look at what you are plugging in. A server's tools are code that can "
            "run with your access. And its descriptions are text your model will read."
        )
        # The same stage as before, with two servers. Below, one the user trusts and
        # already uses: it reads files, its tool is in the context, its client and
        # its cable are in place. Above, the one being plugged in: nobody reviewed it.
        model, host, link = ModelPanel(), HostFrame(), Link()
        mine = model.block(f"tools · {W.FILES_SERVER}", FILES_ROWS, "server")
        cx = (SERVER_X[0] + SERVER_X[1]) / 2
        split = -0.35  # where the upper server's frame ends
        frame = Frame(SERVER_X, SERVER_C, "unknown server", bot=split)
        its_tool = offer("tool", W.POISONED["name"], WIRE_Y)
        unknown = Text("?", font_size=100, color=FAINT, weight="BOLD").move_to([cx, 0.85, 0])
        whose = Chars("found online, not reviewed", fs=17, color=MUTED)
        whose.at(cx - whose.body.width / 2, 0.0)
        trusted = Frame(SERVER_X, SERVER_C, W.FILES_SERVER, top=split - 0.4)
        y_files = split - 0.4 - (TOP - WIRE_Y)  # its tool and socket: as far under its name as above
        files_tool = offer("tool", W.FILES_TOOL["name"], y_files)
        papers = VGroup(*[doc_icon(0.32, STEEL) for _ in range(3)]).arrange(RIGHT, buff=0.16)
        papers.move_to([SERVER_X[0] + 0.3 + papers.width / 2, -2.33, 0])
        theirs = Chars("your files", fs=17, color=MUTED).at(papers.get_right()[0] + 0.22, -2.33)
        y_port = 0.3  # the second client, clear of the consent card below it
        port2 = client_port().move_to([HOST_X[1], y_port, 0])
        sock2 = socket_glyph().move_to([SERVER_X[0] - 0.17, y_files, 0])
        plug2 = plug_glyph()
        plug2.shift([sock2.get_left()[0] - 0.04 - plug2.body.get_right()[0], y_files, 0])
        cable2 = polyline(  # an elbow in the free lane between the host and the servers
            port2.get_right(), [GAP_X, y_port, 0], [GAP_X, y_files, 0], plug2.body.get_left()
        ).set_stroke(STEEL, width=5)
        wire2 = [cable2, sock2, plug2, port2]
        for m in wire2:
            m.set_z_index(Z_LINK)
        stage = [
            *model.furniture(), mine, *host.furniture(), *frame.mobs(), its_tool, unknown, whose,
            *trusted.mobs(), files_tool, papers, theirs, *wire2,
        ]  # fmt: skip
        home = link.plug.get_center().copy()
        link.plug.move_to(link.parked())
        self.play(*[FadeOut(m) for m in self.mobjects if m.z_index < Z_HEAD], run_time=0.5)
        self.foot = self.note(POISON_NOTE)
        self.play(
            *[FadeIn(m) for m in stage],
            FadeIn(link.port),
            FadeIn(link.name),
            FadeIn(link.socket),
            FadeIn(self.foot),
            run_time=0.7,
        )
        self.play(  # the plug goes in as the narrator says so
            Create(link.cable),
            link.plug.animate.move_to(home),
            run_time=self.span("in. A server's", floor=0.7, cap=1.5),
        )
        self.cue("A server's tools are code", ambient=lambda rt: [Throb(unknown, rt, amp=0.08)])
        gear = its_tool.icon.get_center()
        spin = spinner(gear)

        def turning(rt):
            return Rotate(spin, angle=-TAU * rt / 1.1, about_point=gear, rate_func=linear, run_time=rt)

        self.play(FadeIn(spin), glow(its_tool.box, LOOK_C, 5, rt=0.4), run_time=0.4)
        self.cue("with your access", ambient=lambda rt: [turning(rt), Throb(unknown, rt, amp=0.08)])
        yours = link.cable.copy().set_stroke(USER_C, width=8).set_z_index(Z_LINK + 1)
        self.play(  # the user's own rights, handed to that code
            glow(host.avatar[0], USER_C, 6, rt=0.9),
            Succession(Wait(0.25), ShowPassingFlash(yours, time_width=0.6, run_time=0.65)),
            turning(0.9),
        )
        self.play(glow(its_tool.box, USER_C, 6, rt=0.7), turning(0.7))
        self.cue("its descriptions are text", ambient=lambda rt: [turning(rt)])
        self.play(FadeOut(spin), run_time=0.2)
        back, labs = self.exchange(link, "tools/list", 1, flash=its_tool)
        evil = model.block("tools · unknown server", POISON_ROWS, "server")
        self.play(FadeTransform(back, evil), *[FadeOut(m) for m in labs], run_time=0.7)
        self.cue("your model will read", ambient=lambda rt: [Throb(evil, rt, amp=0.02)])
        self.play(model.reading(0.9), Throb(model.chip, 0.9, amp=0.2, period=0.45))
        self.hold(ambient=lambda rt: [Throb(evil, rt, amp=0.02), Throb(model.chip, rt, amp=0.1)])

        # ---- 6.3 untrusted, unless you trust the server ---------------------------------------------- #
        self.voice(
            "A dishonest server can hide an instruction there, and the model may follow "
            "it, using a tool from a server you trust. So the specification says: treat "
            "a description as untrusted, unless you trust the server it came from. Keep "
            "a human in the loop, and connect only servers you trust."
        )
        # all the user wants: it goes into the context like any other message
        said = host.say(ASKS_BUBBLE)
        ask = model.block("user", ASKS_ROWS, "user")
        self.play(FadeIn(said, shift=UP * 0.15), run_time=0.4)
        self.play(FadeIn(ask, shift=LEFT * 0.4), run_time=0.4)
        self.cue("hide an instruction")
        order = [
            mark(evil.rows[1], "Before any answer,", HOSTILE_C),
            mark(evil.rows[2], color=HOSTILE_C),
            mark(evil.rows[3], color=HOSTILE_C),
        ]
        self.play(LaggedStart(*[FadeIn(m) for m in order], lag_ratio=0.3), run_time=0.8)
        self.cue("the model may follow", ambient=lambda rt: throbs(order, rt, amp=0.03))
        self.play(model.reading(0.8), Throb(model.chip, 0.8, amp=0.2, period=0.4))
        steal = model.block("tool call", STOLEN_ROWS, "model")
        typing = steal.typed(1.0)
        self.play(FadeIn(steal, shift=RIGHT * 0.2), run_time=0.3)
        self.play(typing, Throb(model.chip, 1.0, amp=0.14, period=0.5))
        self.cue("using a tool")
        # the path the stranger named, in a call to the server the user trusts: its
        # tool lights up in the context and on that server, and so does the way there
        taken = mark(steal.rows[1], json.dumps(STOLEN_PATH), HOSTILE_C)
        there = cable2.copy().set_stroke(LOOK_C, width=8).set_z_index(Z_LINK + 1)
        self.play(
            FadeIn(taken, run_time=0.3),
            glow(mine.box, LOOK_C),
            glow(files_tool.box, LOOK_C, 5),
            ShowPassingFlash(there, time_width=0.6, run_time=1.0),
        )
        card = host.consent(W.FILES_SERVER, STOLEN_TOOL, STOLEN_PATH, danger=True)
        ghost = steal.rows[0].copy()
        self.play(  # the host catches the call, and asks, as it did in scene 3
            ghost.animate.move_to(card.tool.get_center()).set_opacity(0.0),
            *[FadeIn(m) for m in card.mobs()],
            run_time=0.6,
        )
        self.remove(ghost)

        def waiting(rt):  # the card waits for its answer: time to read it
            return [
                Throb(host.avatar, rt, amp=0.25),
                *throbs([card.deny, card.allow], rt, amp=0.035),
            ]

        self.cue("treat a description", ambient=waiting)
        verdict = stamp("UNTRUSTED", HOSTILE_C, fs=30).move_to(unknown)
        quote = self.note(TRUST_NOTE)
        self.play(
            FadeIn(verdict, scale=1.5),
            FadeOut(unknown),
            FadeOut(self.foot, run_time=0.3),
            Succession(Wait(0.3), FadeIn(quote, run_time=0.4)),
        )
        self.foot = quote
        self.cue("unless you trust", ambient=lambda rt: [*waiting(rt), Throb(verdict, rt, amp=0.05)])
        self.play(  # and here is one the user does trust
            glow(trusted.box, USER_C),
            glow(mine.box, USER_C),
            Throb(verdict, 1.0, amp=0.05),
        )
        self.cue("Keep a human", ambient=lambda rt: [*waiting(rt), Throb(verdict, rt, amp=0.05)])
        self.play(
            Throb(host.avatar, 0.9, amp=0.3, period=0.45),
            Indicate(card.deny, color=INK, scale_factor=1.12, run_time=0.9),
        )
        self.cue("in the loop")
        no = card.pressed("deny")
        self.play(tap_ring(card.deny.get_center()), Succession(Wait(0.12), FadeIn(no, run_time=0.2)))
        by = badge_on(steal, "user")  # who decided, marked as in scene 4
        denied = Chars("denied", fs=16, color=INK, weight="MEDIUM")
        denied.ending_at(by.get_left()[0] - 0.12, by.get_center()[1])
        self.play(  # refused: the call is never sent
            *[FadeOut(m) for m in (*card.mobs(), no, taken)],
            steal.animate.fade(0.75),
            FadeIn(denied, shift=LEFT * 0.1),
            FadeIn(by, scale=0.5),
            run_time=0.5,
        )
        self.cue("connect only servers", ambient=lambda rt: [Throb(verdict, rt, amp=0.05)])
        dim = [frame.box, its_tool, whose, link.socket]
        name_off = frame.tag.copy()  # the name dims, its plate stays whole: a faded
        name_off[1].fade(0.7)  # plate would let the frame's border show through it
        self.play(  # unplugged: the stranger's text leaves the context with it
            *self.aside("Connect only the servers you trust."),
            link.plug.animate(run_time=0.8).move_to(link.parked()),
            Uncreate(link.cable, run_time=0.8),
            *[FadeOut(m, run_time=0.8) for m in order],
            evil.animate(run_time=0.8).fade(0.8),
            Transform(frame.tag, name_off, run_time=0.8),
            *[m.animate(run_time=0.8).fade(0.7) for m in dim],
        )
        self.settle(ambient=lambda rt: [Throb(host.avatar, rt, amp=0.15), Throb(by, rt, amp=0.2)])
        self.wipe()

    # ====================================================================== #
    # 7 · The whole picture
    # ====================================================================== #
    def scene_recap(self):
        s = self.st_call()
        self.voice(
            "A model that only reads and writes text. A host that carries its requests. "
            "Servers that do the work. And one protocol between them."
        )
        self.play(
            *self.chapter("7 · The whole picture", LOOK_C),
            *[FadeIn(m) for m in s.mobs],
            run_time=0.9,
        )
        self.play(glow(s.model.frame.box, MODEL_C), Throb(s.model.chip, 1.0, amp=0.2, period=0.5))
        self.cue("A host that carries", ambient=lambda rt: [Throb(s.model.chip, rt, amp=0.12)])
        self.play(glow(s.host.frame.box, HOST_C), Throb(s.host.avatar, 1.0, amp=0.2, period=0.5))
        self.cue("Servers that do", ambient=lambda rt: [Throb(s.link.port, rt, amp=0.2)])
        self.play(glow(s.server.frame.box, SERVER_C), Throb(s.n_late, 1.0, amp=0.15, period=0.5))
        self.cue("And one protocol", ambient=lambda rt: [Throb(s.n_late, rt, amp=0.1)])
        flash = s.link.cable.copy().set_stroke(LOOK_C, width=9).set_z_index(Z_LINK + 2)
        self.play(
            *self.aside("That protocol is MCP, the Model Context Protocol."),
            ShowPassingFlash(flash, time_width=0.7, run_time=1.0),
            glow(s.link.port, LOOK_C, 6),
            glow(s.link.socket[0], LOOK_C, 6),
        )
        self.settle(
            ambient=lambda rt: [Throb(s.link.port, rt, amp=0.25), Throb(s.link.plug, rt, amp=0.12)]
        )
        self.wipe()


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


class Doors(_Flat):
    def construct(self):
        self.scene_doors()


class Anywhere(_Flat):
    def construct(self):
        self.scene_anywhere()


class Trust(_Flat):
    def construct(self):
        self.scene_trust()


class Recap(_Flat):
    def construct(self):
        self.scene_recap()


class Outro(_Flat):
    def construct(self):
        self.play_outro()
