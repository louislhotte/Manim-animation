"""Yjs & CRDTs: how people and AI agents edit one document at the same time.

STORYBOARD (one line per scene: question | hero visual | what moves | takeaway)

    1 together   How can two people and an agent write in one document at once?
                 | a Tiptap-style editor filling the frame, three live carets
                 | all three type at once (keys vs streamed tokens), text reflows; the
                   paragraph becomes three private copies wired through a relay, each
                   a little ahead of the others, then equal again
                 | Each writer edits a private copy. A CRDT makes the copies agree.
    2 positions  Why can't the copies just send "insert at index 3"?
                 | two rows of big character cells under an index ruler
                 | insert(2,"D") and insert(3,"s") cross and land: CRDsT vs CRDTs; an
                   OT server rewrites the 3 into a 4; then the indexes fall away
                 | An index is only true on the copy that produced it.
    3 items      What does Yjs send instead?
                 | the same rows as Yjs items: every character carries an id; the
                   real Item struct; the real 10-byte update
                 | ids stamp in, a run splits around D, items cross and attach by
                   origin, both rows converge; the word they converged on spells out
                   Conflict-free Replicated Data Types
                 | Indexes move. Ids never do.
    4 samespot   What if two writers type at the same position at the same time?
                 | Ada's and the agent's rows, two runs anchored on the same item
                 | both type at once (keys vs tokens), each run is one item, the tie
                   is broken by client id, identically on both copies
                 | Each copy decided alone, by the same blind rule.
    5 offline    What happens when someone loses the connection?
                 | two rows, the link between them, state-vector bars
                 | the link snaps, both sides keep editing, state vectors are
                   compared, only the missing items travel, a tombstone anchors Bob
                 | Both copies converge. Nobody had to resolve anything.
    6 anyorder   Why can't a flaky network corrupt it?
                 | the story's 8 real updates delivered to three copies in three
                   orders; a 40,320-pixel map of every possible order
                 | early updates wait, sentences assemble differently, end identical;
                   the map is recoloured by result: one colour, one sentence
                 | 40,320 delivery orders, one document.
    7 numbers    Does it stay small and fast, and how does it compare?
                 | the length of a real paper over its 259,778 keystrokes; the same
                   trace on Yjs, Loro and Automerge; weekly downloads to scale
                 | the curve draws, Yjs replays it in real time (0.93 s), keystrokes
                   collapse into items, bars race, v13 runs from 2020 to today
                 | Second on every axis, and the stable choice: v13 since 2020.
    8 stack      Where do Tiptap and Hocuspocus fit, and the agent?
                 | the real client / server / agent code beside the live pipeline
                   Tiptap > Y.Doc > provider > Hocuspocus > database
                 | each highlighted line lights its layer, edits travel the pipeline,
                   the agent joins as a third peer; back in the editor the three
                   writers type the film's sentence
                 | Tiptap edits. Yjs merges. Hocuspocus relays and remembers.

Persistent motif: three writers (Ada, Bob, the Agent: one colour each, everywhere) and
one sentence built item by item across scenes 2-6, "CRDTs merge all edits, even
offline", always drawn as the real Yjs list of items with their ids. It is the result
every delivery order ends on (scene 6) and the last line typed in the editor (scene 8).

Real data (all baked by generate_assets.py, asserted there and here):
  assets/story.json  the story run on real Yjs 13.6 (items, ids, update bytes, state
                     vectors, all 40,320 delivery orders)
  assets/stack.json  real Tiptap 3 editors + a headless agent on a real Hocuspocus 4
                     server (the editor text of scenes 1 and 8, awareness, defaults)
  assets/bench.json  the Kleppmann & Beresford editing trace (automerge-perf, CC BY
                     4.0) replayed on Yjs, Loro and Automerge
  assets/npm.json    npm registry: release dates and last week's downloads
The algorithm is YATA: Nicolaescu, Jahns, Derntl, Klamma (GROUP 2016).

Pacing: every caption swap is an animation that plays under the motion (``cap``), and
``hold`` then waits only for what is left of its reading time (chars / 16 + 0.9 s),
filled with ambient motion where one is given. ``YJ_TRACE=1`` prints the time each
caption stays up; ``tools/motioncheck.py`` finds the freezes.

Scenes render alone (``./render.sh items --quick --check``) or as one film
(``./render.sh full``). ``YJ_QUICK=1`` (or ``--quick``) collapses the holds. After a fix
inside an updater or an animation, render with ``--no-cache``: Manim's partial-movie
cache only sees the state at the start of each play.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

import numpy as np
from kit import *
from manimx import *

HERE = Path(__file__).resolve().parent


def _asset(name):
    return json.loads((HERE / "assets" / f"{name}.json").read_text())


STORY, STACK, BENCH, NPM = (_asset(n) for n in ("story", "stack", "bench", "npm"))

# ---- the editor document of scenes 1 and 8: what the real Tiptap run produced ---- #
DOC = re.findall(r"<(?:h1|p)>(.*?)</(?:h1|p)>", STACK["after_agent"]["ada"])
H1_TEXT = "Release notes"
P1_PARTS = ("Live collaboration ", "finally ", "ships this week.")
P2_PARTS = ("Summary: we ", "can ", "all edit at once", " and stay in sync.")
assert DOC == [H1_TEXT, "".join(P1_PARTS), "".join(P2_PARTS)], DOC
assert STACK["after_agent"]["ada"] == STACK["after_agent"]["bob"]
TOKENS = STACK["tokens"]  # what the agent streamed, token by token
assert "".join(TOKENS) == P2_PARTS[0] + P2_PARTS[2] + P2_PARTS[3]
TOK1 = [len(t) for t in TOKENS[:6]]  # "Summary: we all edit at once"
TOK2 = [len(t) for t in TOKENS[6:]]  # " and stay in sync."
assert sum(TOK1) == len(P2_PARTS[0] + P2_PARTS[2]) and sum(TOK2) == len(P2_PARTS[3])


# ---- scene 2: what index-based edits do, computed rather than typed in ---------- #
def splice(s, i, ch):
    return s[:i] + ch + s[i:]


SNAPS = STORY["snaps"]
BASE = SNAPS["crt"]["ada"]["text"]  # "CRT": what both copies start from
ADA_OP, BOB_OP = (2, "D"), (3, "s")  # the two concurrent edits, as (index, letter)
ADA_LOCAL, BOB_LOCAL = splice(BASE, *ADA_OP), splice(BASE, *BOB_OP)
ADA_NAIVE, BOB_NAIVE = splice(ADA_LOCAL, *BOB_OP), splice(BOB_LOCAL, *ADA_OP)
# Operational Transformation, insert against an earlier insert: shift right if it
# landed at or before our index (the classic transform function)
OT_INDEX = BOB_OP[0] + 1 if ADA_OP[0] <= BOB_OP[0] else BOB_OP[0]
ADA_OT = splice(ADA_LOCAL, OT_INDEX, BOB_OP[1])
assert BASE == "CRT" and (ADA_LOCAL, BOB_LOCAL) == ("CRDT", "CRTs")
assert (ADA_NAIVE, BOB_NAIVE) == ("CRDsT", "CRDTs") and ADA_NAIVE != BOB_NAIVE
assert (OT_INDEX, ADA_OT) == (4, "CRDTs") and ADA_OT == BOB_NAIVE
assert ADA_LOCAL == SNAPS["concurrent_local"]["ada"]["text"]
assert BOB_LOCAL == SNAPS["concurrent_local"]["bob"]["text"]


def op_chip(index, ch, peer, fs=22):
    """An index-based edit as it travels: ``insert(3, "s")``. ``.digit`` is the index."""
    t = Text(
        f'insert({index}, "{ch}")',
        font=MONO,
        font_size=fs,
        color=INK,
        disable_ligatures=True,
    )
    t[7].set_color(GOLD)
    t[10:13].set_color(peer.color)
    box = RoundedRectangle(
        width=t.width + 0.44,
        height=0.62,
        corner_radius=0.14,
        stroke_color=peer.color,
        stroke_width=2.5,
        fill_color=peer.color,
        fill_opacity=0.12,
    ).move_to(t)
    g = VGroup(box, t)
    g.box, g.text, g.digit = box, t, t[7]
    return g


# ---- scenes 3-6: the story as real Yjs produced it ------------------------------ #
UPD = {u["key"]: u for u in STORY["updates"]}  # the eight updates, by key
ITEM = {k: (u["structs"][0] if u["structs"] else None) for k, u in UPD.items()}
assert ITEM["d"] == {
    "id": [1, 3],
    "len": 1,
    "origin": [1, 1],
    "right": [1, 2],
    "str": "D",
}
assert ITEM["s"] == {
    "id": [2, 0],
    "len": 1,
    "origin": [1, 2],
    "right": None,
    "str": "s",
}
S_BYTES = bytes.fromhex(UPD["s"]["hex"].replace(" ", ""))  # Bob's "s", as sent
assert len(S_BYTES) == UPD["s"]["bytes"] == 10
assert S_BYTES[2:4] == bytes([2, 0])  # the id 2:0
assert S_BYTES[5:7] == bytes([1, 2])  # the origin 1:2
assert S_BYTES[7:9] == bytes([1, ord("s")])  # one character: "s"


def shape(items):
    """A replica as ``[(text, client, clock, deleted), ...]``: what a row must show."""
    return [(i["str"], i["id"][0], i["id"][1], i["deleted"]) for i in items]


def row_shape(row):
    return [(b.text, b.peer.cid, b.clock, b.dead > 0.5) for b in row.real()]


def card_for(key, fs=24):
    """The Item card of one of the story's updates."""
    it = ITEM[key]
    return item_card(
        PEERS[it["id"][0]],
        it["id"],
        it["origin"],
        it["right"],
        it["str"],
        fs=fs,
        w=4.15,
    )


def col_ring(block, i, color=GOLD):
    """A highlight around character ``i`` of a block: the letter and its id tag."""
    top, bot = block.y + block.h / 2 + 0.07, block.y - block.h / 2 - 0.52
    ring = RoundedRectangle(
        width=block.col + 0.06,
        height=top - bot,
        corner_radius=0.1,
        stroke_color=color,
        stroke_width=3.5,
    ).set_fill(opacity=0)
    return ring.move_to([block.col_x(i), (top + bot) / 2, 0])


def col_mark(block, i, color=GOLD):
    """A wash over character ``i`` of a block, exactly one column wide (a ring would
    cut into the neighbouring glyph: in Menlo a letter fills its whole cell)."""
    mark = RoundedRectangle(
        width=block.col,
        height=block.h - 0.12,
        corner_radius=0.06,
        stroke_color=color,
        stroke_width=2.5,
        fill_color=color,
        fill_opacity=0.24,
    )
    return mark.move_to([block.col_x(i), block.y, 0])


def byte_strip(data, fs=20, w=0.48, gap=0.04):
    """Raw bytes as a row of hex cells; ``strip[i]`` is ``VGroup(box, text)``."""
    cells = VGroup()
    for b in data:
        box = RoundedRectangle(
            width=w,
            height=0.5,
            corner_radius=0.07,
            stroke_color=FAINT,
            stroke_width=1.5,
            fill_color=PANEL,
            fill_opacity=1,
        )
        cells.add(VGroup(box, mono(f"{b:02x}", fs=fs, color=MUTED).move_to(box)))
    return cells.arrange(RIGHT, buff=gap)


# ---- scene 8: the three files of the real stack (what demo/stack.mjs runs) -------- #
CLIENT_JS = [
    (0, "const ydoc = new Y.Doc()"),
    (0, "const provider = new HocuspocusProvider({"),
    (1, 'url: "ws://127.0.0.1:1234",'),
    (1, 'name: "notes", document: ydoc,'),
    (0, "})"),
    (0, "const editor = new Editor({ extensions: ["),
    (1, "StarterKit.configure({ undoRedo: false }),"),
    (1, "Collaboration.configure({ document: ydoc }),"),
    (1, "CollaborationCaret.configure({"),
    (2, 'provider, user: { name: "Ada" },'),
    (1, "}),"),
    (0, "] })"),
]
SERVER_JS = [
    (0, "const storage = new Database({"),
    (1, "fetch: (d) => db.get(d.documentName),"),
    (1, "store: (d) => db.set(d.documentName, d.state),"),
    (0, "})"),
    (0, "const server = new Server({"),
    (1, "port: 1234,"),
    (1, "extensions: [storage],"),
    (0, "})"),
    (0, "server.listen()"),
]
AGENT_JS = [
    (0, "const ydoc = new Y.Doc()"),
    (0, "const provider = new HocuspocusProvider({"),
    (1, 'url: "ws://127.0.0.1:1234",'),
    (1, 'name: "notes", document: ydoc,'),
    (0, "})"),
    (0, 'provider.setAwarenessField("user", me)'),
    (0, ""),
    (0, "for await (const token of stream) {"),
    (1, "write(ydoc, token) // a plain Yjs insert"),
    (0, "}"),
]
JS_T2C = {
    "const ": KW,
    "new ": KW,
    "for ": KW,
    "await ": KW,
    " of ": KW,
    "Y.Doc": FUNC,
    "HocuspocusProvider": FUNC,
    "Editor": FUNC,
    "StarterKit": FUNC,
    "CollaborationCaret": FUNC,
    "Collaboration": FUNC,
    "Database": FUNC,
    "Server": FUNC,
    "configure": FUNC,
    "listen": FUNC,
    "setAwarenessField": FUNC,
    "write": FUNC,
    '"ws://127.0.0.1:1234"': STR,
    '"notes"': STR,
    '"Ada"': STR,
    '"user"': STR,
    "1234,": NUM,
    "false": NUM,
    "// a plain Yjs insert": COMMENT,
}
assert STACK["defaults"]["debounce"] == 2000  # "2 seconds after the last change"
assert {a["user"]["name"] for a in STACK["awareness"]} == {"Ada", "Bob", "Agent"}
assert STACK["caret_labels_in_ada_editor"] == [
    "Agent"
]  # the agent's caret, in a real editor
assert (
    STACK["after_reconnect"]["ada"]
    == STACK["after_reconnect"]["bob"]
    == STACK["after_restart"]
)


class _Base(ExplainerScene):
    pace = Pace.from_env("YJ", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "Yjs & CRDTs"
    SUBTITLE = "How people and AI agents edit one document at the same time"
    TAGLINE = "CRDTs, with Tiptap and Hocuspocus"
    RECAP = "Give every character an identity, and every copy converges."
    SCENES = (
        "together",
        "positions",
        "items",
        "samespot",
        "offline",
        "anyorder",
        "numbers",
        "stack",
    )

    # ---- shared helpers --------------------------------------------------- #
    def intro_emblem(self):
        """The three writers, at the end of the title rule."""
        g = VGroup(*[avatar(p, r=0.17) for p in (ADA, BOB, AGENT)]).arrange(
            RIGHT, buff=-0.07
        )
        pad = Rectangle(
            width=g.width + 0.3, height=0.1, stroke_opacity=0, fill_opacity=0
        )
        return VGroup(
            g, pad.next_to(g, RIGHT, buff=0)
        )  # the card centres this box on the rule's end

    READ_CPS, READ_BASE = 16.0, 0.9  # reading time of a caption: chars / 16 + 0.9 s

    def cap(self, text, rt=0.45, at=0.0, **kw):
        """The caption swap as an animation, to play *while* something else moves.

        ``at`` = how long after the start of its play the swap happens (a caption
        scheduled inside a ``Succession``), so reading time is counted from there.
        """
        new = self.say(text, **kw)
        new.set_z_index(20)
        # The FadeIn always sits in a Succession: a bare animation that ends before its
        # play does is re-applied at alpha = 1 on every later frame, which would undo a
        # FadeOut of this caption scheduled later in the same play (``at``).
        if self._cap is None:
            anims = [Succession(FadeIn(new, shift=UP * 0.1))]
        else:  # out, then in: two sentences never sit on top of each other
            anims = [
                FadeOut(self._cap, shift=UP * 0.1, run_time=0.45),
                Succession(Wait(0.4), FadeIn(new, shift=UP * 0.1, run_time=0.6)),
            ]
        self._cap = new
        self._cap_t0 = self.renderer.time + at
        self._cap_need = len(text) / self.READ_CPS + self.READ_BASE
        self._note(text, at)
        return AnimationGroup(*anims, run_time=rt)

    def lead(self, text, wait=0.7, **kw):
        """A caption that lands *before* the motion it describes (read, then watch)."""
        self.play(self.cap(text, **kw))
        self.wait(0.1 if self.pace.quick else wait)

    def hold(self, extra=0.0, floor=0.3, ambient=None):
        """Keep the caption up until it has had its reading time.

        ``ambient(rt)`` returns animations lasting ``rt``: the hold then moves (the
        item being discussed breathes, packets keep flowing) instead of freezing.
        """
        left = max(floor, self._cap_need + extra - (self.renderer.time - self._cap_t0))
        if self.pace.quick:
            left = min(left, 0.3)
        if ambient is not None and left >= 0.8:
            self.play(*ambient(left))
        else:
            self.wait(left)

    @staticmethod
    def then(anim, after):
        """``anim``, ``after`` seconds into its play: "this leaves, then that arrives".
        Two different pictures never share a spot, not even for half a second."""
        return Succession(Wait(after), anim)

    def settle(self, ambient=None):
        """End of a scene: the last caption's reading time, plus a breath."""
        if getattr(self, "_cap", None) is None:
            return super().settle()
        self.hold(extra=0.5, ambient=ambient)

    def wave(self, *rows, rt=2.4):
        """Light up the same item on every copy, one item after the other: the copies
        hold the same list, in the same order."""
        cols = list(zip(*[r.real() for r in rows], strict=True))
        each = max(0.6, rt / (1 + 0.4 * (len(cols) - 1)))
        self.play(
            LaggedStart(
                *[
                    AnimationGroup(*[Breathe(b, each, period=each) for b in col])
                    for col in cols
                ],
                lag_ratio=0.4,
            ),
            run_time=rt,
        )

    # ---- YJ_TRACE=1: print how long every caption stays up (a reading-time check) -- #
    def _note(self, text, at=0.0):
        if os.environ.get("YJ_TRACE"):
            self.__dict__.setdefault("_caps", []).append(
                (self.renderer.time + at, text)
            )

    def wipe(self, rt=None):
        caps = self.__dict__.pop("_caps", None)
        if caps:
            end = self.renderer.time
            print(f"\n== captions of {type(self).__name__} (ends at {end:.1f} s)")
            for (t0, text), (t1, _) in zip(caps, caps[1:] + [(end, "")], strict=True):
                need = len(text) / self.READ_CPS + self.READ_BASE
                flag = "  <-- SHORT" if t1 - t0 < need - 0.12 else ""
                print(
                    f"  {t0:6.1f}  {t1 - t0:4.1f} s (needs {need:3.1f})  {len(text):3d} ch  {text}{flag}"
                )
        super().wipe(rt)

    def header(self, label, color):
        h = self.section_header(label, color)
        self.play(FadeIn(h, shift=DOWN * 0.2), run_time=0.5)
        return h

    # ====================================================================== #
    # 1 · One page, three writers
    # ====================================================================== #
    def scene_together(self):
        self.header("1 · One page, three writers", GOLD)

        win = EditorWindow(w=11.4, h=4.5, title="notes").move_to([0, -0.32, 0])
        h1 = win.line(0.98, [(H1_TEXT, ADA, 0)], fs=40, weight="BOLD")
        p1 = win.line(
            1.95, [(P1_PARTS[0], BOB, 0), (P1_PARTS[1], ADA, 0), (P1_PARTS[2], BOB, 0)]
        )
        p2 = win.line(
            2.8,
            [
                (P2_PARTS[0], AGENT, 0),
                (P2_PARTS[1], BOB, 0),
                (P2_PARTS[2], AGENT, 0),
                (P2_PARTS[3], AGENT, 0),
            ],
        )
        c_ada = win.caret(ADA).follow_spans(h1, h1.spans)
        c_bob = win.caret(BOB, show=0).follow_spans(p1, [p1.spans[0], p1.spans[2]])
        c_ag = win.caret(AGENT, show=0).follow_spans(
            p2, [p2.spans[0], p2.spans[2], p2.spans[3]]
        )
        a_ada, av_w = win.join(ADA, shown=True)
        a_bob, _ = win.join(BOB)
        a_ag, _ = win.join(AGENT)

        # --- one long take: three writers, overlapping, under two captions ----- #
        self.play(FadeIn(win, shift=UP * 0.15), run_time=0.6)
        C2 = 5.3
        self.play(
            self.cap("Two people and an AI agent write on one page, at the same time."),
            Type(h1.spans, cps=9, seed=1),  # Ada types the title
            Succession(  # Bob joins and writes the first paragraph, key by key
                Wait(0.5),
                AnimationGroup(Pop(a_bob, av_w), Tween(c_bob, show=1.0, run_time=0.25)),
                Wait(0.3),
                Type([p1.spans[0], p1.spans[2]], cps=6.2, seed=2),
            ),
            Succession(  # the agent joins and streams the second one, token by token
                Wait(1.5),
                AnimationGroup(Pop(a_ag, av_w), Tween(c_ag, show=1.0, run_time=0.25)),
                Wait(0.4),
                Type([p2.spans[0], p2.spans[2]], chunks=TOK1, tps=1.7),
            ),
            Succession(  # Ada jumps into Bob's sentence while he is still typing it
                Wait(5.4),
                Do(lambda: c_ada.follow_spans(p1, [p1.spans[1]])),
                Type(p1.spans[1], cps=7.5, seed=4),
            ),
            Succession(
                Wait(C2),
                self.cap("Nobody waits for a lock. Nothing gets overwritten.", at=C2),
            ),
        )
        self.hold()

        # --- the reveal: three private copies of the last paragraph ---------- #
        K = 24 / 26  # the paragraph, a touch smaller, inside a strip
        SX, SW, SH, BUS = -1.25, 10.9, 1.02, 5.25
        ys = {ADA.cid: 1.3, BOB.cid: -0.15, AGENT.cid: -1.6}
        right = SX + SW / 2

        win.body.remove(p2, c_ag)
        c_bob2 = Caret(BOB, show=0).follow_spans(p2, [p2.spans[1]])
        para = VGroup(p2, c_ag, c_bob2)
        panel = RoundedRectangle(
            width=SW,
            height=SH,
            corner_radius=0.14,
            stroke_color=FAINT,
            stroke_width=2,
            fill_color=WINDOW_BG,
            fill_opacity=1,
        ).move_to([SX, ys[BOB.cid], 0])
        panel.set_fill(opacity=0).set_stroke(opacity=0)  # unseen until the strip forms
        # Draw order matters here. The nested animations of the long take split the
        # window into its parts in ``scene.mobjects``; without this ``add`` the FadeOut
        # below would re-add it *on top* of the paragraph that has to survive it.
        self.add(win)
        self.add(panel, para)
        self.play(Tween(c_ada, show=0.0), Tween(c_bob, show=0.0), run_time=0.2)
        a0 = p2.anchor.get_center()
        goal = np.array([-4.85, ys[BOB.cid] - 0.2, 0])
        self.play(  # the window leaves; its last paragraph stays behind...
            self.cap("The trick: each writer edits a private copy of the page."),
            FadeOut(win, shift=UP * 0.3),
            run_time=0.45,
        )
        self.play(  # ...and settles into a strip of its own
            panel.animate.set_fill(opacity=1).set_stroke(opacity=1),
            para.animate.scale(K, about_point=a0).shift(goal - a0),
            run_time=0.7,
        )
        strips = {BOB.cid: VGroup(panel, para)}
        for cid in (ADA.cid, AGENT.cid):
            strips[cid] = strips[BOB.cid].copy()
            self.add(strips[cid])
        self.bring_to_front(strips[BOB.cid])  # the copies slide out from behind it
        labels = VGroup()
        for cid, y in ys.items():
            peer = PEERS[cid]
            lab = VGroup(
                avatar(peer, r=0.19),
                Text(peer.name, font_size=17, color=INK, weight="MEDIUM"),
            ).arrange(RIGHT, buff=0.12)
            lab.move_to([SX - SW / 2 + 0.25 + lab.width / 2, y, 0])
            labels.add(lab)
        relay = server_glyph().move_to([BUS, ys[BOB.cid], 0])
        relay_lab = Text("relay", font_size=16, color=MUTED).next_to(
            relay, RIGHT, buff=0.1
        )
        wires = VGroup(
            polyline([right, ys[1], 0], [BUS, ys[1], 0], [BUS, ys[2] + 0.33, 0]),
            Line([right, ys[2], 0], [BUS - 0.46, ys[2], 0]),
            polyline([right, ys[3], 0], [BUS, ys[3], 0], [BUS, ys[2] - 0.33, 0]),
        ).set_stroke(MUTED, width=2.5, opacity=0.8)
        self.play(
            strips[ADA.cid].animate.shift(UP * (ys[1] - ys[2])),
            strips[AGENT.cid].animate.shift(DOWN * (ys[2] - ys[3])),
            run_time=0.7,
        )
        self.play(
            *[strips[c][0].animate.set_stroke(PEERS[c].color, width=2.5) for c in ys],
            LaggedStart(
                *[FadeIn(lab, shift=RIGHT * 0.1) for lab in labels], lag_ratio=0.15
            ),
            *[Create(w) for w in wires],
            FadeIn(relay, scale=0.8),
            FadeIn(relay_lab),
            run_time=0.8,
        )
        self.hold()

        # --- local first: an edit shows on its own copy, then on the others -- #
        def line(cid):
            return strips[cid][1][0]

        def route(a, b):
            return polyline(
                [right, ys[a], 0], [BUS, ys[a], 0], [BUS, ys[b], 0], [right, ys[b], 0]
            )

        def packets(src, n, every, start=0.04):
            out = []
            for dst in ys:
                if dst != src:
                    for j in range(n):
                        dot = glow_dot(PEERS[src].color, r=0.07)
                        out.append(
                            Succession(
                                Wait(start + j * every),
                                Travel(
                                    dot, route(src, dst), run_time=LAG, rate_func=linear
                                ),
                            )
                        )
            return out

        LAG, TPS, bob_cps = 0.6, 1.25, 5.5
        differ = status_pill("copies differ", GOLD, fs=17).move_to([5.55, 2.25, 0])
        agree = status_pill("copies agree", GOOD, fs=17).move_to(differ)
        # round 1: the agent streams. Its own copy is always a little ahead.
        self.play(
            self.cap(
                "A keystroke lands on its own copy first, then travels to the others."
            ),
            FadeIn(differ, shift=DOWN * 0.1, run_time=0.3),
            Type(line(AGENT.cid).spans[3], chunks=TOK2, tps=TPS),
            *[
                Succession(Wait(LAG), Type(line(c).spans[3], chunks=TOK2, tps=TPS))
                for c in (ADA.cid, BOB.cid)
            ],
            *packets(AGENT.cid, len(TOK2), 1 / TPS),
        )
        self.play(
            FadeOut(differ, shift=UP * 0.1, run_time=0.15),
            self.then(FadeIn(agree, shift=UP * 0.1, run_time=0.2), 0.15),
        )
        self.hold()

        # round 2: Bob edits inside the agent's sentence. For a moment, only he has it.
        self.play(
            self.cap("For a moment the copies differ. Then they must agree again."),
            Tween(strips[BOB.cid][1][2], show=1.0, run_time=0.2),
            run_time=0.45,
        )
        self.wait(0.1 if self.pace.quick else 0.5)
        n_can = len(P2_PARTS[1])
        self.play(
            Type(line(BOB.cid).spans[1], cps=bob_cps, seed=5),
            FadeOut(agree, shift=DOWN * 0.1, run_time=0.15),
            self.then(FadeIn(differ, shift=DOWN * 0.1, run_time=0.2), 0.15),
            *packets(BOB.cid, n_can, 1 / bob_cps, start=0.1),
            *[
                Succession(
                    Wait(LAG + 0.1),
                    Tween(strips[c][1][2], show=1.0, run_time=0.12),
                    Type(line(c).spans[1], cps=bob_cps, seed=5),
                )
                for c in (ADA.cid, AGENT.cid)
            ],
        )
        assert len({line(c).text_now() for c in ys}) == 1  # the three copies agree
        self.play(
            FadeOut(differ, shift=UP * 0.1, run_time=0.15),
            self.then(FadeIn(agree, shift=UP * 0.1, run_time=0.25), 0.15),
            *[
                strips[c][0].animate(run_time=0.4).set_stroke(GOOD, width=3.5)
                for c in ys
            ],
        )
        self.play(ripple(*[strips[c][0] for c in ys], grow=1.03))
        self.hold()
        self.play(
            self.cap(
                "A CRDT, a conflict-free replicated data type, guarantees it. Yjs is one."
            ),
            *[strips[c][0].animate.set_stroke(PEERS[c].color, width=2.5) for c in ys],
            FadeOut(agree),
            run_time=0.5,
        )
        tabs = VGroup()  # what each private copy really is (scene 8 comes back to it)
        for c in ys:
            t = mono("Y.Doc", fs=17, color=GOLD)
            tab = VGroup(
                RoundedRectangle(
                    width=t.width + 0.34,
                    height=0.36,
                    corner_radius=0.09,
                    stroke_color=GOLD,
                    stroke_width=2,
                    fill_color=BG,
                    fill_opacity=1,
                ),
                t,
            )
            t.move_to(tab[0])
            tabs.add(
                tab.move_to(strips[c][0].get_corner(UL) + RIGHT * 0.85)
            )  # clear of the carets
        self.play(
            LaggedStart(*[FadeIn(t, scale=0.6) for t in tabs], lag_ratio=0.45),
            run_time=1.5,
        )
        self.settle(
            ambient=lambda t: [Throb(tab, t, period=1.2, amp=0.1) for tab in tabs]
        )
        self.wipe()

    # ====================================================================== #
    # 2 · Why positions break
    # ====================================================================== #
    def scene_positions(self):
        self.header("2 · Why positions break", BAD)
        X0, YA, YB, CHIP_X = -5.15, 1.2, -1.3, 4.25
        CELL = dict(fs=58, col=1.04, pad=0.13, h=1.3, ids="none")
        PITCH, HALF = 1.04 + 0.26 + 0.16, (1.04 + 0.26) / 2
        MID = (YA + YB) / 2

        def cell(ch, peer, n=None):
            return Block(ch, peer, 0, n=n, **CELL)

        def col_x(k):
            return X0 + k * PITCH + HALF

        rows, rulers, labs = {}, {}, VGroup()
        for peer, y, side in ((ADA, YA, 1), (BOB, YB, -1)):
            rows[peer.cid] = ItemRow([X0, y, 0], gap=0.16).push(
                *[cell(c, ADA) for c in BASE]
            )
            ruler = VGroup(
                *[
                    mono(str(k), fs=20, color=MUTED).move_to(
                        [col_x(k), y + side * 0.95, 0]
                    )
                    for k in range(5)
                ]
            )
            for k in range(len(BASE), 5):
                ruler[k].set_opacity(0)
            rulers[peer.cid] = ruler
            labs.add(peer_label(peer, fs=20, r=0.22).move_to([-6.1, y, 0]))
        ra, rb = rows[ADA.cid], rows[BOB.cid]
        idx_word = mono("index", fs=18, color=MUTED)
        idx_word.next_to(rulers[ADA.cid][0], LEFT, buff=0.45)
        self.play(
            self.cap("Two copies of one word. Every character sits at an index."),
            LaggedStart(
                *[FadeIn(lab, shift=RIGHT * 0.15) for lab in labs], lag_ratio=0.2
            ),
            FadeIn(ra, shift=UP * 0.1),
            FadeIn(rb, shift=UP * 0.1),
            FadeIn(rulers[ADA.cid]),
            FadeIn(rulers[BOB.cid]),
            FadeIn(idx_word),
            run_time=0.8,
        )
        self.play(  # count the indexes, on both copies
            LaggedStart(
                *[
                    AnimationGroup(
                        Indicate(rulers[ADA.cid][k], color=GOLD, scale_factor=1.7),
                        Indicate(rulers[BOB.cid][k], color=GOLD, scale_factor=1.7),
                    )
                    for k in range(len(BASE))
                ],
                lag_ratio=0.6,
            ),
            run_time=1.8,
        )
        self.hold()

        # --- both edit their own copy, at the same instant -------------------- #
        ca = Caret(ADA).follow_after(
            ra.blocks[1]
        )  # in the gaps: one cell per character
        cb = Caret(BOB).follow_after(rb.blocks[2])
        self.play(
            self.cap(
                "Ada inserts D at index 2. At the same instant, Bob adds s at index 3."
            ),
            FadeIn(ca),
            FadeIn(cb),
            run_time=0.45,
        )
        self.wait(0.1 if self.pace.quick else 0.9)
        d = ra.insert(2, cell("D", ADA, n=0))
        s = rb.insert(3, cell("s", BOB, n=0))
        ca.follow_after(d)
        cb.follow_after(s)
        chip_a = op_chip(*ADA_OP, ADA).move_to([CHIP_X, YA, 0])
        chip_b = op_chip(*BOB_OP, BOB).move_to([CHIP_X, YB, 0])
        self.play(
            Type(d, run_time=0.5, jitter=0),
            Type(s, run_time=0.5, jitter=0),
            rulers[ADA.cid][3].animate(run_time=0.4).set_opacity(1),
            rulers[BOB.cid][3].animate(run_time=0.4).set_opacity(1),
            Succession(Wait(0.45), FadeIn(chip_a, shift=RIGHT * 0.2, run_time=0.4)),
            Succession(Wait(0.45), FadeIn(chip_b, shift=RIGHT * 0.2, run_time=0.4)),
        )
        self.hold()

        # --- they tell each other: just an index and a letter ------------------ #
        wire = Line([CHIP_X, YA - 0.34, 0], [CHIP_X, YB + 0.34, 0])
        wire.set_stroke(MUTED, width=2.5, opacity=0.8)
        down = Line([CHIP_X - 0.13, YA - 0.34, 0], [CHIP_X - 0.13, YB + 0.34, 0])
        up = Line([CHIP_X + 0.13, YB + 0.34, 0], [CHIP_X + 0.13, YA - 0.34, 0])
        got_a = op_chip(*BOB_OP, BOB).move_to(chip_a)  # what Ada receives
        got_b = op_chip(*ADA_OP, ADA).move_to(chip_b)  # what Bob receives
        self.play(
            self.cap("Each copy tells the other what it did: an index and a letter."),
            Create(wire),
            FadeOut(ca),
            FadeOut(cb),
            run_time=0.5,
        )
        self.play(
            Travel(glow_dot(ADA.color, r=0.1), down, run_time=1.0),
            Travel(glow_dot(BOB.color, r=0.1), up, run_time=1.0),
            Succession(  # each copy's own chip leaves, then the one it received arrives
                Wait(0.75),
                AnimationGroup(
                    FadeOut(chip_a, scale=0.9),
                    FadeOut(chip_b, scale=0.9),
                    run_time=0.18,
                ),
                AnimationGroup(
                    FadeIn(got_a, scale=1.1), FadeIn(got_b, scale=1.1), run_time=0.22
                ),
            ),
        )
        # Bob applies Ada's edit: index 2 still means the same place for him
        d2 = cell("D", ADA).place(CHIP_X - 2.0, YB)
        self.play(
            Indicate(rulers[BOB.cid][ADA_OP[0]], color=GOLD, scale_factor=1.7),
            Indicate(got_b.digit, color=GOLD, scale_factor=1.5),
            run_time=0.6,
        )
        self.play(
            Dock(
                rb,
                d2,
                ADA_OP[0],
                appear=True,
                run_time=0.8,
                rate_func=rate_functions.ease_out_cubic,
            ),
            FadeOut(got_b, shift=LEFT * 0.4, run_time=0.4),
            rulers[BOB.cid][4].animate(run_time=0.4).set_opacity(1),
        )
        assert rb.text_now() == BOB_NAIVE
        self.hold()

        # --- ...but for Ada, index 3 has moved ------------------------------------ #
        s2 = cell("s", BOB).place(CHIP_X - 2.0, YA)
        self.lead(
            "On Ada's copy, index 3 is no longer the end. The s lands before the T."
        )
        self.play(
            Indicate(rulers[ADA.cid][BOB_OP[0]], color=GOLD, scale_factor=1.7),
            Indicate(got_a.digit, color=GOLD, scale_factor=1.5),
            run_time=0.7,
        )
        self.play(
            Dock(
                ra,
                s2,
                BOB_OP[0],
                appear=True,
                run_time=0.8,
                rate_func=rate_functions.ease_out_cubic,
            ),
            FadeOut(got_a, shift=LEFT * 0.4, run_time=0.4),
            FadeOut(wire, run_time=0.4),
            rulers[ADA.cid][4].animate(run_time=0.4).set_opacity(1),
        )
        assert ra.text_now() == ADA_NAIVE
        self.hold(ambient=lambda t: [Breathe(s2, t)])

        # --- the column-by-column verdict --------------------------------------- #
        def verdict(a, b):
            marks = VGroup()
            for k, (x, y) in enumerate(zip(a, b, strict=True)):
                ok = x == y
                link = Line([col_x(k), YA - 0.72, 0], [col_x(k), YB + 0.72, 0])
                link.set_stroke(GOOD if ok else BAD, width=2, opacity=0.45)
                mark = (
                    make_tick(GOOD, sw=6, scale=0.9)
                    if ok
                    else make_cross(BAD, sw=6, scale=0.9)
                )
                mark.move_to([col_x(k), MID, 0])
                marks.add(VGroup(link, plate(mark, pad_x=0.1, pad_y=0.1, op=1.0)))
            return marks

        bad = verdict(ADA_NAIVE, BOB_NAIVE)
        wrong = [ra.blocks[3], ra.blocks[4], rb.blocks[3], rb.blocks[4]]
        self.play(
            self.cap("Same two edits, two different words. The copies have diverged."),
            LaggedStart(*[FadeIn(m, scale=0.7) for m in bad], lag_ratio=0.18),
            run_time=1.1,
        )
        self.hold(ambient=lambda rt: [Breathe(b, rt) for b in wrong])

        # --- Operational Transformation: a central server repairs the index ----- #
        server = server_glyph(w=0.9, h=0.68).move_to([6.25, MID, 0])
        server_lab = Text("server", font_size=17, color=MUTED)
        server_lab.next_to(server, DOWN, buff=0.1).shift(LEFT * 0.58)
        chip = op_chip(*BOB_OP, BOB).move_to([CHIP_X, YB, 0])
        self.play(
            self.cap(
                "Operational Transformation (Google Docs) lets a server rewrite the 3 into a 4."
            ),
            FadeOut(bad),
            Tween(s2, p=0.0, glow=0.0, run_time=0.5),
            rulers[ADA.cid][4].animate.set_opacity(0),
            FadeIn(chip, shift=RIGHT * 0.2),
            FadeIn(server, scale=0.8),
            FadeIn(server_lab),
            run_time=0.6,
        )
        ra.drop(s2)
        self.wait(0.1 if self.pace.quick else 0.5)
        self.play(chip.animate.move_to([CHIP_X, MID, 0]), run_time=0.7)
        new_chip = op_chip(OT_INDEX, BOB_OP[1], BOB).move_to(chip)
        new_digit = new_chip.digit.copy()
        self.play(  # never FadeOut a nested glyph: it would split the chip in the scene
            chip.digit.animate.set_opacity(0).shift(UP * 0.2),
            FadeIn(new_digit, shift=UP * 0.2),
            Indicate(server.leds, color=GOLD, scale_factor=1.8),
            Flash(
                new_digit.get_center(), color=GOLD, line_length=0.14, flash_radius=0.26
            ),
            run_time=0.7,
        )
        self.remove(chip, new_digit)
        self.add(new_chip)
        self.wait(0.1 if self.pace.quick else 0.5)
        self.play(new_chip.animate.move_to([CHIP_X, YA, 0]), run_time=0.7)
        s3 = cell("s", BOB).place(CHIP_X - 2.0, YA)
        good = verdict(ADA_OT, BOB_NAIVE)
        self.play(
            Dock(
                ra,
                s3,
                OT_INDEX,
                appear=True,
                run_time=0.8,
                rate_func=rate_functions.ease_out_cubic,
            ),
            FadeOut(new_chip, shift=LEFT * 0.4, run_time=0.4),
            rulers[ADA.cid][4].animate(run_time=0.4).set_opacity(1),
            Succession(
                Wait(0.6),
                LaggedStart(
                    *[FadeIn(m, scale=0.7) for m in good], lag_ratio=0.12, run_time=0.7
                ),
            ),
        )
        assert ra.text_now() == ADA_OT == rb.text_now()
        self.hold()

        # ...and every edit of every copy has to pass through it
        end = ra.x1 - ra.gap + 0.25
        sx, top, bot = (
            server.get_center()[0],
            server.get_top()[1],
            server.get_bottom()[1],
        )
        net = VGroup(
            polyline([end, YA, 0], [sx, YA, 0], [sx, top, 0]),
            polyline([end, YB, 0], [sx, YB, 0], [sx, bot, 0]),
        ).set_stroke(MUTED, width=2.5, opacity=0.8)
        back = [
            polyline([sx, top, 0], [sx, YA, 0], [end, YA, 0]),
            polyline([sx, bot, 0], [sx, YB, 0], [end, YB, 0]),
        ]

        def traffic(
            t,
        ):  # every edit goes up to the server, then back down to the other copy
            half = t / 2
            return [
                stream(net[0], ADA.color, n=3, run_time=half),
                stream(net[1], BOB.color, n=3, run_time=half),
                Succession(Wait(half), stream(back[1], ADA.color, n=3, run_time=half)),
                Succession(Wait(half), stream(back[0], BOB.color, n=3, run_time=half)),
                Succession(
                    Wait(half * 0.5),
                    Indicate(server.leds, color=GOLD, scale_factor=1.8, run_time=half),
                ),
            ]

        self.play(
            self.cap(
                "It works as long as every edit passes through that one server, in order."
            ),
            Create(net[0]),
            Create(net[1]),
            run_time=0.7,
        )
        self.hold(ambient=traffic)
        self.play(
            self.cap("A CRDT takes the other road. It removes the index altogether."),
            FadeOut(VGroup(server, server_lab, net)),
            run_time=0.6,
        )
        self.play(
            LaggedStart(*[FadeOut(m, scale=0.6) for m in good], lag_ratio=0.2),
            run_time=0.9,
        )
        self.play(  # the indexes fall away, one by one
            LaggedStart(
                *[
                    AnimationGroup(
                        rulers[ADA.cid][k].animate.shift(UP * 0.35).set_opacity(0),
                        rulers[BOB.cid][k].animate.shift(DOWN * 0.35).set_opacity(0),
                    )
                    for k in range(5)
                ],
                lag_ratio=0.35,
            ),
            FadeOut(idx_word),
            run_time=2.6,
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 3 · Every character gets an identity
    # ====================================================================== #
    def scene_items(self):
        self.header("3 · Every character gets an identity", GOLD)
        X0, YA, YB, CARD_X, GAP = -5.15, 1.3, -1.45, 4.55, 0.14
        CELL = dict(fs=54, col=1.0, pad=0.12, h=1.2, ids="each", tag_fs=20)
        MID, WIRE_X = (YA + YB) / 2 - 0.17, 1.85
        snap = rate_functions.ease_out_cubic

        def blk(text, peer, clock, **kw):
            return Block(text, peer, clock, **{**CELL, **kw})

        ra = ItemRow([X0, YA, 0], gap=GAP).push(blk(BASE, ADA, 0))
        rb = ItemRow([X0, YB, 0], gap=GAP).push(blk(BASE, ADA, 0))
        for r in (ra, rb):
            r.blocks[0].tag_n = 0
            r.layout()
        labs = VGroup(
            peer_label(ADA, fs=20, r=0.22).move_to([-6.1, YA, 0]),
            peer_label(BOB, fs=20, r=0.22).move_to([-6.1, YB, 0]),
        )
        self.play(
            self.cap("Yjs never sends an index. Every character gets a permanent id."),
            FadeIn(labs, shift=RIGHT * 0.15),
            FadeIn(ra, shift=UP * 0.1),
            FadeIn(rb, shift=UP * 0.1),
            run_time=0.7,
        )
        self.wait(0.1 if self.pace.quick else 0.6)
        self.play(  # the ids stamp in, one character at a time
            Tween(ra.blocks[0], tag_n=3.0, rate_func=linear),
            Tween(rb.blocks[0], tag_n=3.0, rate_func=linear),
            run_time=1.5,
        )
        self.hold(
            ambient=lambda t: [Breathe(ra.blocks[0], t), Breathe(rb.blocks[0], t)]
        )

        # --- what an id is ------------------------------------------------------ #
        parts = VGroup(
            mono("1", fs=64, color=ADA.color),
            mono(":", fs=64, color=MUTED),
            mono("0", fs=64, color=INK),
        )
        for m, x in zip(parts, (-1.25, 0, 1.25), strict=True):
            m.move_to([CARD_X + x, 1.45, 0])
        notes = VGroup(
            Text("client id", font_size=22, color=INK, weight="MEDIUM"),
            Text("clock", font_size=22, color=INK, weight="MEDIUM"),
            Text("who typed it", font_size=18, color=MUTED),
            Text("that client's counter", font_size=18, color=MUTED),
        )
        for m, x, y in zip(
            notes, (-1.25, 1.25, -1.25, 1.25), (0.72, 0.72, 0.32, 0.32), strict=True
        ):
            m.move_to([CARD_X + x, y, 0])
        legend = VGroup(parts, notes)
        first = col_ring(ra.blocks[0], 0)
        self.play(
            self.cap(
                "An id is who typed the character, plus that client's own counter."
            ),
            Create(first),
            LaggedStart(*[FadeIn(m, shift=UP * 0.12) for m in parts], lag_ratio=0.2),
            LaggedStart(*[FadeIn(m) for m in notes], lag_ratio=0.15),
            run_time=1.0,
        )
        # the ring walks along the run: the counter goes 0, 1, 2
        for i in (1, 2, 0):
            self.play(first.animate.move_to(col_ring(ra.blocks[0], i)), run_time=0.45)
            self.wait(0.05 if self.pace.quick else 0.25)
        self.hold()

        # --- Ada inserts D: the item names its neighbours ------------------------ #
        card_d = card_for("d").move_to([CARD_X, YA + 0.1, 0])
        ca = Caret(ADA).follow_col(ra.blocks[0], 2)
        self.play(  # the legend leaves before the card takes its place
            self.cap(
                "An insert names its neighbours: D goes after 1:1 and before 1:2."
            ),
            FadeOut(legend, run_time=0.25),
            FadeOut(first, run_time=0.25),
            Succession(Wait(0.25), FadeIn(ca, run_time=0.35)),
            Succession(Wait(0.25), FadeIn(card_d, shift=LEFT * 0.3, run_time=0.4)),
        )
        self.wait(0.1 if self.pace.quick else 0.5)
        r1, r2 = col_ring(ra.blocks[0], 1), col_ring(ra.blocks[0], 2)
        self.play(
            Indicate(card_d.f_origin, color=GOLD, scale_factor=1.35),
            Create(r1),
            run_time=0.7,
        )
        self.play(
            Indicate(card_d.f_right, color=GOLD, scale_factor=1.35),
            Create(r2),
            run_time=0.7,
        )
        cr, t = ra.split(ra.blocks[0], 2)  # Yjs splits the run where the item lands
        d = blk("D", ADA, 3).place(
            card_d.f_content.get_left()[0] - 0.4, card_d.get_center()[1]
        )
        self.play(
            FadeOut(r1, run_time=0.3),
            FadeOut(r2, run_time=0.3),
            FadeOut(ca, run_time=0.3),
            Tween(cr, gap=GAP, run_time=0.8),
            Dock(ra, d, 1, appear=True, run_time=0.9, rate_func=snap),
        )
        assert row_shape(ra) == shape(SNAPS["concurrent_local"]["ada"]["items"])
        self.hold(ambient=lambda t: [Breathe(d, t)])

        # --- at the same instant, Bob adds s ------------------------------------ #
        card_s = card_for("s").move_to([CARD_X, YB + 0.1, 0])
        cb = Caret(BOB).follow_block(rb.blocks[0])
        r3 = col_ring(rb.blocks[0], 2)
        self.play(
            self.cap("At the same instant, Bob's s only says: I come after 1:2."),
            FadeIn(cb),
            FadeIn(card_s, shift=LEFT * 0.3),
            run_time=0.6,
        )
        self.wait(0.1 if self.pace.quick else 0.4)
        self.play(
            Indicate(card_s.f_origin, color=GOLD, scale_factor=1.35),
            Create(r3),
            run_time=0.7,
        )
        s = blk("s", BOB, 0).place(
            card_s.f_content.get_left()[0] - 0.4, card_s.get_center()[1]
        )
        self.play(
            FadeOut(r3, run_time=0.3),
            FadeOut(cb, run_time=0.3),
            Dock(rb, s, 1, appear=True, run_time=0.9, rate_func=snap),
        )
        assert row_shape(rb) == shape(SNAPS["concurrent_local"]["bob"]["items"])
        self.hold(ambient=lambda t: [Breathe(s, t)])

        # --- the two items cross on the wire -------------------------------------- #
        ea, eb = (
            ra.x1 - GAP + 0.18,
            rb.x1 - GAP + 0.18,
        )  # just past each row's last item
        link = [[ea, YA, 0], [WIRE_X, YA, 0], [WIRE_X, YB, 0], [eb, YB, 0]]
        wire = polyline(*link).set_stroke(MUTED, width=2.5, opacity=0.8)
        got_a, got_b = card_for("s").move_to(card_d), card_for("d").move_to(card_s)
        self.play(
            self.cap("The two items cross on the wire."),
            Create(wire),
            run_time=0.5,
        )
        self.play(
            Travel(glow_dot(ADA.color, r=0.1), polyline(*link), run_time=1.1),
            Travel(glow_dot(BOB.color, r=0.1), polyline(*link[::-1]), run_time=1.1),
            Succession(  # the cards swap places: out, then in
                Wait(0.8),
                AnimationGroup(
                    FadeOut(card_d), FadeOut(card_s), FadeOut(wire), run_time=0.2
                ),
                AnimationGroup(FadeIn(got_a), FadeIn(got_b), run_time=0.25),
            ),
        )
        self.hold()

        # --- Ada's copy: T moved, but it is still 1:2 ----------------------------- #
        tb, off = ra.find(ADA, 2)
        r4 = col_ring(tb, off)
        self.lead(
            "On Ada's copy the T has moved, but it is still 1:2. The s follows it."
        )
        self.play(
            Indicate(got_a.f_origin, color=GOLD, scale_factor=1.35),
            Create(r4),
            run_time=0.8,
        )
        s2 = blk("s", BOB, 0).place(
            got_a.f_content.get_left()[0] - 0.4, got_a.get_center()[1]
        )
        self.play(
            FadeOut(r4, run_time=0.3),
            Dock(
                ra,
                s2,
                ra.blocks.index(tb) + 1,
                appear=True,
                run_time=0.9,
                rate_func=snap,
            ),
            FadeOut(got_a, run_time=0.5),
        )
        self.hold(ambient=lambda t: [Breathe(tb, t), Breathe(s2, t)])

        # --- Bob's copy: the run splits, D slides in ------------------------------- #
        crt = rb.blocks[0]
        r5, r6 = col_ring(crt, 1), col_ring(crt, 2)
        self.lead("Bob's copy finds 1:1 and 1:2, and slides the D in between.")
        self.play(
            Indicate(got_b.f_origin, color=GOLD, scale_factor=1.35),
            Indicate(got_b.f_right, color=GOLD, scale_factor=1.35),
            Create(r5),
            Create(r6),
            run_time=0.8,
        )
        cr2, t2 = rb.split(crt, 2)
        d2 = blk("D", ADA, 3).place(
            got_b.f_content.get_left()[0] - 0.4, got_b.get_center()[1]
        )
        self.play(
            FadeOut(r5, run_time=0.3),
            FadeOut(r6, run_time=0.3),
            Tween(cr2, gap=GAP, run_time=0.8),
            Dock(rb, d2, 1, appear=True, run_time=0.9, rate_func=snap),
            FadeOut(got_b, run_time=0.5),
        )
        merged = shape(SNAPS["concurrent_merged"]["ada"]["items"])
        assert row_shape(ra) == row_shape(rb) == merged
        assert ra.text_now() == rb.text_now() == "CRDTs"
        self.hold(ambient=lambda t: [Breathe(d2, t)])

        cols = [b.col_x(i) for b in ra.real() for i in range(len(b.text))]
        ticks = VGroup()
        for x in cols:
            link_ = Line([x, YA - 1.0, 0], [x, YB + 0.66, 0]).set_stroke(
                GOOD, width=2, opacity=0.4
            )
            mark = make_tick(GOOD, sw=6, scale=0.85).move_to([x, MID, 0])
            ticks.add(VGroup(link_, plate(mark, pad_x=0.1, pad_y=0.1, op=1.0)))
        self.play(
            self.cap("Indexes move. Ids never do. Both copies read CRDTs."),
            LaggedStart(*[FadeIn(m, scale=0.7) for m in ticks], lag_ratio=0.12),
            run_time=0.9,
        )
        self.play(
            ripple(ra, rb, buff=0.16, grow=1.03)
        )  # stays clear of the name labels
        self.wave(ra, rb, rt=2.2)
        self.hold()

        # --- what actually travelled: 10 bytes ------------------------------------- #
        strip = byte_strip(S_BYTES).move_to([4.1, 0.15, 0])
        title = VGroup(
            Text("Bob's update, byte for byte", font_size=20, color=MUTED),
            Text(f"{len(S_BYTES)} bytes", font_size=26, color=GOLD, weight="BOLD"),
        )
        title[0].next_to(strip, UP, buff=0.3).align_to(strip, LEFT)
        title[1].next_to(strip, UP, buff=0.26).align_to(strip, RIGHT)
        groups = [
            ((2, 4), BOB.color, "id 2:0"),
            ((5, 7), ADA.color, "origin 1:2"),
            ((8, 9), STR, '"s"'),
        ]
        notes = VGroup()
        for (i, j), c, label in groups:
            cells = strip[i:j]
            bar = Line(
                cells.get_corner(DL) + DOWN * 0.1, cells.get_corner(DR) + DOWN * 0.1
            )
            bar.set_stroke(c, width=3)
            lab = mono(label, fs=19, color=c).next_to(bar, DOWN, buff=0.12)
            notes.add(VGroup(bar, lab))
        self.play(
            self.cap("Bob's whole edit is a 10-byte Yjs update."),
            FadeIn(title, shift=UP * 0.1),
            LaggedStart(*[FadeIn(c, shift=UP * 0.12) for c in strip], lag_ratio=0.08),
            run_time=1.1,
        )
        hl = []
        for (i, j), c, _ in groups:
            for cellg in strip[i:j]:
                hl += [
                    cellg[0].animate.set_stroke(c, width=2.5).set_fill(c, opacity=0.2),
                    cellg[1].animate.set_color(INK),
                ]
        self.play(
            *hl,
            LaggedStart(*[FadeIn(n, shift=UP * 0.1) for n in notes], lag_ratio=0.35),
            run_time=1.3,
        )
        self.hold()

        # --- the word both copies converged on is the name of the thing ------------- #
        full = "Conflict-free Replicated Data Types"
        phrase = Text(
            full, font_size=34, color=INK, weight="MEDIUM", disable_ligatures=True
        )
        assert len(phrase) == len(full)  # one glyph per character, spaces included
        phrase.move_to([X0 + 0.04, MID - 0.03, 0], aligned_edge=LEFT)
        cuts, i = [], 0
        for w in full.split(" "):
            cuts.append((i, i + len(w)))
            i += len(w) + 1
        cuts[-1] = (
            cuts[-1][0],
            cuts[-1][1] - 1,
        )  # "Type", then its plural s on its own
        cuts.append((len(full) - 1, len(full)))
        pieces = [phrase[a:b] for a, b in cuts]
        for pc in pieces:
            pc[0].set_color(GOLD)

        def letters(row):
            return [(b, k) for b in row.real() for k in range(len(b.text))]

        # the cells C, R, D, T, s are exactly the gold letters of the phrase
        assert [b.text[k] for b, k in letters(ra)] == [full[a] for a, _ in cuts]
        beats = []
        for pc, (ba, ka), (bb, kb) in zip(
            pieces, letters(ra), letters(rb), strict=True
        ):
            ma, mb = col_mark(ba, ka), col_mark(bb, kb)
            beats.append(
                AnimationGroup(
                    Succession(FadeIn(ma, run_time=0.2), FadeOut(ma, run_time=0.5)),
                    Succession(FadeIn(mb, run_time=0.2), FadeOut(mb, run_time=0.5)),
                    FadeIn(pc, shift=UP * 0.12, run_time=0.45),
                )
            )
        self.play(
            self.cap(
                "Items that merge like this form a CRDT. Yjs calls its algorithm YATA."
            ),
            FadeIn(self.cite("YATA: Nicolaescu, Jahns, Derntl, Klamma. GROUP 2016")),
            FadeOut(ticks),
            FadeOut(VGroup(strip, title, notes)),
            run_time=0.5,
        )
        self.play(LaggedStart(*beats, lag_ratio=0.8), run_time=3.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 4 · Same position, same instant
    # ====================================================================== #
    def scene_samespot(self):
        self.header("4 · Same position, same instant", AGENT.color)
        X0, YA, YB, GAP = -5.3, 1.42, -1.38, 0.09
        CELL = dict(fs=36, pad=0.1, h=0.86, ids="start", tag_fs=18, show_len=True)
        start = SNAPS["concurrent_merged"]["ada"]["items"]
        merged = SNAPS["samespot_merged"]["ada"]["items"]
        im, io = ITEM["merge"], ITEM["order"]
        snap = rate_functions.ease_out_cubic
        # the facts this scene states, straight from the Yjs run
        assert (
            im["origin"] == io["origin"] == [BOB.cid, 0]
            and im["right"] is io["right"] is None
        )
        assert [i["id"][0] for i in merged[-2:]] == sorted([ADA.cid, AGENT.cid])

        def blk(text, peer, clock, **kw):
            return Block(text, peer, clock, **{**CELL, **kw})

        def base_row(y):
            row = ItemRow([X0, y, 0], gap=GAP)
            return row.push(
                *[blk(i["str"], PEERS[i["id"][0]], i["id"][1]) for i in start]
            )

        ra, rg = base_row(YA), base_row(YB)
        labs = VGroup(peer_label(ADA, fs=20, r=0.22), peer_label(AGENT, fs=20, r=0.22))
        for lab, y in zip(labs, (YA, YB), strict=True):  # avatars on one vertical line
            lab.move_to([-6.75 + lab.width / 2, y, 0])
        m = ra.insert(len(ra.blocks), blk(im["str"], ADA, im["id"][1], n=0))
        o = rg.insert(len(rg.blocks), blk(io["str"], AGENT, io["id"][1], n=0))
        ca, cg = Caret(ADA).follow_block(m), Caret(AGENT).follow_block(o)
        self.play(
            self.cap("Ada and the agent both start typing right after the s."),
            FadeIn(labs, shift=RIGHT * 0.15),
            FadeIn(ra, shift=UP * 0.1),
            FadeIn(rg, shift=UP * 0.1),
            FadeIn(ca),
            FadeIn(cg),
            run_time=0.7,
        )
        self.wait(0.1 if self.pace.quick else 0.9)
        half = len(" merge")  # each writer's first word, then the second
        self.play(
            Type(m, to=half, cps=2.6, seed=6),  # Ada, key by key
            Type(
                o, to=len(" in any"), chunks=[3, 4], tps=0.85
            ),  # the agent, token by token
        )
        self.hold()
        self.play(
            self.cap("A run typed in one go is one item: a start id and a length."),
            Type(m, run_time=2.5, seed=7),  # the rest of Ada's run
            Succession(Wait(1.2), Type(o, chunks=[6], tps=1.4)),
        )
        assert row_shape(ra) == shape(SNAPS["samespot_local"]["ada"]["items"])
        assert row_shape(rg) == shape(SNAPS["samespot_local"]["agent"]["items"])
        self.hold()

        # --- the tie: both runs hang on the same item --------------------------- #
        def origin_tag(b):
            t = VGroup(mono("origin", fs=18, color=MUTED), id_text(im["origin"], fs=18))
            t.arrange(RIGHT, buff=0.02)
            return t.move_to([b.x + t.width / 2 + 0.02, b.y + b.h / 2 + 0.24, 0])

        sa, sg = ra.find(BOB, 0)[0], rg.find(BOB, 0)[0]
        tags = VGroup(origin_tag(m), origin_tag(o))
        rings = VGroup(col_mark(m, 0), col_mark(o, 0))
        self.play(
            self.cap(
                "Only their first characters compete: both name 2:0 as their origin."
            ),
            FadeOut(ca),
            FadeOut(cg),
            FadeIn(tags, shift=UP * 0.1),
            FadeIn(rings, scale=1.15),
            run_time=0.7,
        )
        self.hold(ambient=lambda rt: [Breathe(sa, rt), Breathe(sg, rt)])

        # --- the rule, applied by each copy on its own --------------------------- #
        duel = VGroup(
            VGroup(
                avatar(ADA, r=0.25), mono("client 1", fs=20, color=ADA.color)
            ).arrange(DOWN, buff=0.1),
            Text("<", font_size=48, color=GOLD, weight="BOLD"),
            VGroup(
                avatar(AGENT, r=0.25), mono("client 3", fs=20, color=AGENT.color)
            ).arrange(DOWN, buff=0.1),
        ).arrange(RIGHT, buff=0.32)
        rule = Text("lower client id goes first", font_size=20, color=GOLD)
        comp = VGroup(duel, rule).arrange(DOWN, buff=0.13).move_to([4.85, -0.02, 0])
        self.play(
            self.cap(
                "Client ids break the tie: the lower one goes first, on every copy."
            ),
            FadeOut(tags),
            FadeOut(rings),
            FadeIn(comp, shift=LEFT * 0.2),
            run_time=0.6,
        )
        self.wait(0.1 if self.pace.quick else 0.9)
        o2 = o.clone()
        self.play(
            Dock(ra, o2, len(ra.blocks), run_time=1.1, rate_func=snap)
        )  # after Ada's run
        self.wait(0.1 if self.pace.quick else 0.3)
        m2 = m.clone()
        self.play(
            Dock(rg, m2, rg.blocks.index(o), run_time=1.1, rate_func=snap)
        )  # before its own
        assert row_shape(ra) == row_shape(rg) == shape(merged)
        self.hold()

        final = SNAPS["samespot_merged"]["ada"]["text"]
        line = LiveLine(
            [(i["str"], PEERS[i["id"][0]]) for i in merged],
            fs=36,
            tint="author",
            at=[X0 + 0.05, -0.17, 0],
        )
        assert line.text_now() == final == ra.text_now() == rg.text_now()
        tick = make_tick(GOOD, sw=7).next_to(line.end_point(), RIGHT, buff=0.3)
        self.play(
            self.cap(
                "Each copy decided alone, by the same blind rule. Both read the same sentence."
            ),
            FadeIn(line, shift=UP * 0.1),
            Create(tick),
            run_time=0.7,
        )
        self.play(ripple(ra, rg, buff=0.14, grow=1.03))
        self.play(Circumscribe(comp, color=GOLD, buff=0.1), run_time=1.0)
        self.wave(ra, rg, rt=2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 5 · Losing the connection
    # ====================================================================== #
    def scene_offline(self):
        self.header("5 · Losing the connection", BAD)
        X0, YT, YB, GAP, LX = -6.4, 1.6, -1.62, 0.1, -5.9
        CELL = dict(fs=26, pad=0.09, h=0.7, ids="start", tag_fs=16, show_len=True)
        before = SNAPS["samespot_merged"]["ada"]["items"]
        hs = STORY["handshake"]
        sv_on = {int(k): v for k, v in hs["sv_online"].items()}
        sv_bob = {int(k): v for k, v in hs["sv_bob"].items()}
        ia, ik = ITEM["all"], ITEM["offline"]
        snap = rate_functions.ease_out_cubic
        # the facts this scene states, straight from the Yjs run
        assert sv_on == {1: 16, 2: 1, 3: 17} and sv_bob == {1: 16, 2: 15, 3: 13}
        assert (hs["to_online"]["bytes"], hs["to_bob"]["bytes"]) == (23, 19)
        assert UPD["del"]["ds"] == hs["to_bob"]["ds"] == {"3": [[0, 13]]}
        assert ik["origin"] == [
            AGENT.cid,
            12,
        ]  # Bob typed after the phrase's last letter
        assert [x["str"] for x in hs["to_online"]["structs"]] == [ik["str"]]
        assert [x["str"] for x in hs["to_bob"]["structs"]] == [ia["str"]]

        def blk(text, peer, clock, **kw):
            return Block(text, peer, clock, **{**CELL, **kw})

        def row(y):
            r = ItemRow([X0, y, 0], gap=GAP)
            return r.push(
                *[blk(i["str"], PEERS[i["id"][0]], i["id"][1]) for i in before]
            )

        rt, rb = row(YT), row(YB)
        lab_t = VGroup(
            avatar(ADA, r=0.2),
            avatar(AGENT, r=0.2),
            Text("Ada and the agent", font_size=20, color=INK, weight="MEDIUM"),
        ).arrange(RIGHT, buff=0.12)
        lab_t[1].shift(LEFT * 0.2)
        lab_t[2].shift(LEFT * 0.2)
        lab_t.move_to([X0 + lab_t.width / 2, YT + 0.83, 0])
        pill_t = status_pill("online", GOOD).next_to(lab_t, RIGHT, buff=0.25)
        lab_b = peer_label(BOB, fs=20, r=0.2)
        lab_b.move_to([X0 + lab_b.width / 2, YB - 1.0, 0])
        pill_on = status_pill("online", GOOD).next_to(lab_b, RIGHT, buff=0.25)
        pill_off = status_pill("offline", BAD).next_to(lab_b, RIGHT, buff=0.25)
        link_on = wifi(GOOD).move_to([LX, 0.0, 0])
        link_off = wifi(BAD, off=True).move_to([LX, 0.0, 0])
        seg = VGroup(
            Line([LX, YT - 0.78, 0], [LX, 0.42, 0]),
            Line([LX, -0.42, 0], [LX, YB + 0.45, 0]),
        ).set_stroke(GOOD, width=3, opacity=0.8)
        path_up = Line([LX, YB + 0.45, 0], [LX, YT - 0.78, 0])
        path_dn = Line([LX, YT - 0.78, 0], [LX, YB + 0.45, 0])

        def chatter(t):  # the live link: packets both ways
            return [
                stream(path_up, BOB.color, n=3, run_time=t * 0.9),
                Succession(
                    Wait(t * 0.1), stream(path_dn, AGENT.color, n=3, run_time=t * 0.9)
                ),
            ]

        self.play(
            self.cap("Everyone is in sync. Then Bob's train enters a tunnel."),
            FadeIn(VGroup(lab_t, pill_t, lab_b, pill_on), shift=RIGHT * 0.15),
            FadeIn(rt, shift=UP * 0.1),
            FadeIn(rb, shift=UP * 0.1),
            FadeIn(link_on),
            FadeIn(seg),
            run_time=0.7,
        )
        self.play(*chatter(1.7))
        self.play(  # the link drops; the pill flips with it (out, then in)
            FadeOut(link_on, scale=0.7, run_time=0.4),
            FadeIn(link_off, scale=1.3, run_time=0.4),
            seg.animate(run_time=0.4).set_stroke(BAD, opacity=0.3),
            FadeOut(pill_on, shift=UP * 0.1, run_time=0.15),
            self.then(FadeIn(pill_off, shift=UP * 0.1, run_time=0.2), 0.15),
        )
        self.play(
            Wiggle(link_off, scale_value=1.15, rotation_angle=0.03 * TAU), run_time=0.6
        )
        self.hold()

        # --- both sides keep editing --------------------------------------------- #
        kb = rb.insert(len(rb.blocks), blk(ik["str"], BOB, ik["id"][1], n=0))
        cb = Caret(BOB, show=0).follow_block(kb)
        self.add(cb)
        C2 = 4.1
        self.play(
            self.cap("Bob keeps typing. His edits land on his own copy."),
            Tween(cb, show=1.0, run_time=0.2),
            Succession(Wait(0.7), Type(kb, cps=3.4, seed=8)),  # 14 keys, about 4 s
            Succession(
                Wait(C2),
                self.cap(
                    "Meanwhile the agent adds a word, and Ada deletes a whole phrase.",
                    at=C2,
                ),
            ),
            Wait(C2 + 0.9),
        )
        # the agent's word lands inside Ada's run: Yjs splits that item, at that moment
        left, right = rt.split(rt.find(ADA, 4)[0], 7)
        al = rt.insert(rt.blocks.index(right), blk(ia["str"], AGENT, ia["id"][1], n=0))
        ob = rt.find(AGENT, 0)[0]
        ob.sel_color = ADA.color
        cg = Caret(AGENT, show=0).follow_block(al)
        ca = Caret(ADA, show=0).follow_block(ob)
        self.add(cg, ca)
        self.play(
            Succession(  # the agent slips a word into Ada's run
                Tween(cg, show=1.0, run_time=0.15),
                AnimationGroup(
                    Tween(left, gap=GAP, run_time=0.4), Type(al, chunks=[4], tps=1.2)
                ),
            ),
            Succession(  # Ada selects the agent's phrase and deletes it
                Wait(1.4),
                Tween(ca, show=1.0, run_time=0.15),
                Tween(ob, sel=1.0, run_time=0.6),
                Wait(0.25),
                Tween(ob, dead=1.0, sel=0.0, run_time=0.6),
            ),
        )
        assert row_shape(rt) == shape(SNAPS["offline"]["online"]["items"])
        assert row_shape(rb) == shape(SNAPS["offline"]["bob"]["items"])
        self.hold()

        # --- back online: state vectors first ------------------------------------- #
        P = dict(vmax=17, w=2.7, fs=19, row_h=0.44, thick=0.6)
        p_on = SVPanel(sv_on, title="state vector: the others", **P).place(-2.3, 0.3)
        p_bob = SVPanel(sv_bob, title="state vector: Bob", **P).place(2.7, 0.3)
        for panel in (p_on, p_bob):  # the bars will count up to each clock
            for bar in panel.bars.values():
                bar.v = 0.0
            panel.refresh()
        self.play(
            self.cap(
                "Back online, each side sends a state vector: its latest clock per client."
            ),
            FadeOut(link_off, scale=1.3, run_time=0.4),
            FadeIn(link_on, scale=0.7, run_time=0.4),
            seg.animate(run_time=0.4).set_stroke(GOOD, opacity=0.8),
            FadeOut(pill_off, shift=UP * 0.1, run_time=0.15),
            self.then(FadeIn(pill_on, shift=UP * 0.1, run_time=0.2), 0.15),
            *[Tween(c, show=0.0, run_time=0.4) for c in (ca, cg, cb)],
            FadeIn(p_on, shift=DOWN * 0.25, run_time=0.7),
            FadeIn(p_bob, shift=UP * 0.25, run_time=0.7),
        )
        self.remove(ca, cg, cb)
        self.play(
            *[
                Tween(p_on.bars[c], v=float(v), run_time=1.3, rate_func=snap)
                for c, v in sv_on.items()
            ],
            *[
                Tween(p_bob.bars[c], v=float(v), run_time=1.3, rate_func=snap)
                for c, v in sv_bob.items()
            ],
        )
        self.hold(ambient=chatter)

        # --- the diff: exactly what each side lacks --------------------------------- #
        p_on.bars[BOB.cid].ghost = sv_bob[BOB.cid]
        p_bob.bars[AGENT.cid].ghost = sv_on[AGENT.cid]
        g_on = p_on.bar_point(BOB.cid, (sv_on[BOB.cid] + sv_bob[BOB.cid]) / 2)
        g_bob = p_bob.bar_point(AGENT.cid, (sv_on[AGENT.cid] + sv_bob[AGENT.cid]) / 2)
        d1 = mono(f"+{sv_bob[BOB.cid] - sv_on[BOB.cid]}", fs=18, color=INK).move_to(
            g_on
        )
        d2 = mono(f"+{sv_on[AGENT.cid] - sv_bob[AGENT.cid]}", fs=18, color=INK).move_to(
            g_bob
        )
        self.lead("Comparing the two shows exactly what each side is missing.")
        self.play(
            Tween(p_on.bars[BOB.cid], ghost_op=1.0),
            Tween(p_bob.bars[AGENT.cid], ghost_op=1.0),
            FadeIn(d1, scale=0.7),
            FadeIn(d2, scale=0.7),
            run_time=0.7,
        )
        self.hold(ambient=lambda t: [Breathe(kb, t), Breathe(al, t)])

        # --- only the missing items travel ------------------------------------------- #
        up, dn = kb.clone(), al.clone()
        up.place(g_on[0] - up.full_w / 2, g_on[1])
        dn.place(g_bob[0] - dn.full_w / 2, g_bob[1])
        self.lead(
            "So only the missing items travel: 23 bytes one way, 19 the other.",
            wait=0.5,
        )
        lb, rbk = rb.split(
            rb.find(ADA, 4)[0], 7
        )  # Bob's copy splits the run as the word lands
        self.play(
            FadeOut(d1),
            FadeOut(d2),
            Dock(
                rt,
                up,
                len(rt.blocks),
                appear=True,
                run_time=1.3,
                lift=0.5,
                rate_func=snap,
            ),
            Dock(
                rb, dn, rb.blocks.index(rbk), appear=True, run_time=1.3, rate_func=snap
            ),
            Tween(lb, gap=GAP, run_time=0.9),
            Tween(
                p_on.bars[BOB.cid], v=float(sv_bob[BOB.cid]), ghost_op=0.0, run_time=1.3
            ),
            Tween(
                p_bob.bars[AGENT.cid],
                v=float(sv_on[AGENT.cid]),
                ghost_op=0.0,
                run_time=1.3,
            ),
        )
        # ...plus the delete set: a range of ids, no content
        ob_b = rb.find(AGENT, 0)[0]
        chip_t = VGroup(
            mono("delete", fs=17, color=MUTED),
            id_text([AGENT.cid, 0], fs=17),
            mono("×13", fs=17, color=MUTED),
        ).arrange(RIGHT, buff=0.08)
        chip_box = RoundedRectangle(
            width=chip_t.width + 0.4,
            height=0.42,
            corner_radius=0.12,
            stroke_color=BAD,
            stroke_width=2,
            fill_color=BAD,
            fill_opacity=0.1,
        ).move_to(chip_t)
        chip = VGroup(  # on an opaque plate: it passes close under the state vectors
            chip_box.copy().set_stroke(width=0).set_fill(BG, opacity=1),
            chip_box,
            chip_t,
        ).move_to([-4.3, YB + 0.6, 0])
        self.play(FadeIn(chip, scale=0.8), run_time=0.35)
        self.play(chip.animate.move_to(ob_b.center_point() + UP * 0.6), run_time=0.8)
        self.play(
            FadeOut(chip, shift=DOWN * 0.3, run_time=0.35),
            Tween(ob_b, dead=1.0, run_time=0.6),
        )
        final_items = SNAPS["final"]["ada"]["items"]
        assert row_shape(rt) == row_shape(rb) == shape(final_items)
        self.hold()

        # --- the edge case: Bob typed after text that no longer exists ------------- #
        tomb = rt.find(AGENT, 0)[0]
        ring = col_mark(tomb, len(tomb.text) - 1)
        otag = VGroup(mono("origin", fs=17, color=MUTED), id_text(ik["origin"], fs=17))
        otag.arrange(RIGHT, buff=0.02)
        otag.move_to([up.x + otag.width / 2 + 0.02, up.y + up.h / 2 + 0.24, 0])
        self.play(
            self.cap(
                "Bob typed after a phrase Ada deleted. Its tombstone still holds the place."
            ),
            FadeIn(ring, scale=1.15),
            FadeIn(otag, shift=UP * 0.1),
            run_time=0.7,
        )
        self.hold(ambient=lambda t: [Breathe(tomb, t)])

        # --- converged ----------------------------------------------------------------- #
        final = SNAPS["final"]["ada"]["text"]
        line = LiveLine(
            [(i["str"], PEERS[i["id"][0]]) for i in final_items if not i["deleted"]],
            fs=38,
            tint="author",
            at=[0, -0.1, 0],
        )
        line.shift(LEFT * (line.x1 / 2 + 0.25))
        line.layout()
        assert line.text_now() == final == rt.text_now() == rb.text_now()
        tick = make_tick(GOOD, sw=7).next_to(line.end_point(), RIGHT, buff=0.3)
        self.play(
            self.cap("Both copies converge. Nobody had to resolve anything."),
            FadeOut(VGroup(p_on, p_bob, ring, otag, link_on, seg), run_time=0.35),
            self.then(FadeIn(line, shift=UP * 0.1, run_time=0.45), 0.35),
            self.then(Create(tick, run_time=0.45), 0.35),
        )
        self.play(ripple(rt, rb, buff=0.16, grow=1.012))
        self.wave(rt, rb, rt=2.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 6 · Any order
    # ====================================================================== #
    def scene_anyorder(self):
        self.header("6 · Any order, any network", MINT)
        perms = STORY["perms"]
        traces = STORY["traces"]
        keys = [u["key"] for u in STORY["updates"]]  # as it happened: 1..8
        final_items = SNAPS["final"]["ada"]["items"]
        final = SNAPS["final"]["ada"]["text"]
        # the facts this scene states
        assert perms["count"] == 40320 == math.factorial(len(keys))
        assert perms["distinct_texts"] == 1 and perms["distinct_states"] == 1
        assert perms["text"] == final and STORY["dups"]["distinct_texts"] == 1
        assert all(t["steps"][-1]["text"] == final for t in traces)
        waited = np.array([int(c) for c in perms["waited"]], dtype=np.uint8)
        assert (
            len(waited) == 40320
            and int((waited == 0).sum()) == 40320 - perms["needed_pending"]
        )

        # --- the eight updates of the story, numbered as they happened ----------- #
        def chip_for(key):
            u = UPD[key]
            if u["structs"]:
                it = u["structs"][0] if key != "crt" else {"str": BASE}
                return Block(
                    it["str"], PEERS[u["by"]], 0, fs=18, pad=0.09, h=0.5, ids="none"
                )
            t = VGroup(
                mono("delete", fs=16, color=MUTED),
                id_text([AGENT.cid, 0], fs=16),
                mono("\u00d713", fs=16, color=MUTED),
            ).arrange(RIGHT, buff=0.06)
            box = RoundedRectangle(
                width=t.width + 0.3,
                height=0.5,
                corner_radius=0.09,
                stroke_color=PEERS[u["by"]].color,
                stroke_width=2.2,
                fill_color=PEERS[u["by"]].color,
                fill_opacity=0.08,
            ).move_to(t)
            return VGroup(box, t)

        chips = [chip_for(k) for k in keys]
        widths = [c.w if isinstance(c, Block) else c.width for c in chips]
        gap = 0.26
        x = -(sum(widths) + gap * (len(chips) - 1)) / 2
        nums = VGroup()
        top = VGroup()
        for i, (c, w) in enumerate(zip(chips, widths, strict=True)):
            if isinstance(c, Block):
                c.place(x, 2.0)
            else:
                c.move_to([x + w / 2, 2.0, 0])
            nums.add(mono(str(i + 1), fs=17, color=MUTED).move_to([x + w / 2, 2.47, 0]))
            top.add(c)
            x += w + gap

        # --- three fresh copies, three arrival orders ------------------------------ #
        LY = [0.75, -0.5, -1.75]
        SQ, SX, TX = 0.52, -5.3, -0.6

        def square(n, peer):
            box = RoundedRectangle(
                width=0.44,
                height=0.44,
                corner_radius=0.09,
                stroke_color=FAINT,
                stroke_width=2.2,
            ).set_fill(peer.color, opacity=0)
            d = mono(str(n), fs=21, color=FAINT).move_to(box)
            g = VGroup(box, d)
            g.box, g.digit, g.peer = box, d, peer
            return g

        def arrive(sq, applied):
            c = sq.peer.color
            if applied:
                return [
                    sq.box.animate.set_stroke(c, opacity=1).set_fill(c, opacity=0.95),
                    sq.digit.animate.set_color(BG),
                ]
            return [
                sq.box.animate.set_stroke(c, opacity=1),
                sq.digit.animate.set_color(c),
            ]

        span_keys = (
            "crt",
            "d",
            "crt",
            "s",
            "merge",
            "all",
            "merge",
            "order",
            "offline",
        )
        spans = [
            (i["str"], PEERS[i["id"][0]], None, k)
            for i, k in zip(final_items, span_keys, strict=True)
        ]
        lanes = []
        for y, tr, name in zip(LY, traces, ("copy A", "copy B", "copy C"), strict=True):
            sqs = VGroup(
                *[
                    square(keys.index(k) + 1, PEERS[UPD[k]["by"]]).move_to(
                        [SX + j * SQ, y, 0]
                    )
                    for j, k in enumerate(tr["order"])
                ]
            )
            line = LiveLine(spans, fs=30, tint="author", at=[TX, y - 0.11, 0])
            for sp in line.spans:
                sp.p = 0.0
            line.layout()
            lab = Text(name, font_size=18, color=MUTED).move_to([-6.25, y, 0])
            lanes.append(dict(sqs=sqs, line=line, lab=lab, tr=tr, y=y))

        def visible(step):
            on = set(step["applied"])
            return {k for k in on if not (k == "order" and "del" in on)}

        head = RoundedRectangle(
            width=SQ + 0.04,
            height=LY[0] - LY[-1] + 0.72,
            corner_radius=0.1,
            stroke_color=GOLD,
            stroke_width=3,
        ).set_fill(GOLD, opacity=0.06)
        head.move_to([SX, (LY[0] + LY[-1]) / 2, 0])
        legend = VGroup(
            square(" ", ADA),
            Text("waiting", font_size=17, color=MUTED),
            square(" ", ADA),
            Text("applied", font_size=17, color=MUTED),
        )
        legend[0].box.set_stroke(ADA.color, opacity=1)
        legend[2].box.set_stroke(ADA.color, opacity=1).set_fill(ADA.color, opacity=0.95)
        legend.arrange(RIGHT, buff=0.14)
        legend[2:].shift(RIGHT * 0.3)
        legend.move_to([4.8, -2.6, 0])

        self.play(
            self.cap(
                "Deliver the eight updates to three fresh copies, each in its own order."
            ),
            LaggedStart(*[FadeIn(c, shift=DOWN * 0.15) for c in top], lag_ratio=0.08),
            FadeIn(nums),
            run_time=0.9,
        )
        self.play(
            *[FadeIn(L["lab"]) for L in lanes],
            *[
                LaggedStart(*[FadeIn(q, scale=0.6) for q in L["sqs"]], lag_ratio=0.07)
                for L in lanes
            ],
            *[FadeIn(L["line"]) for L in lanes],
            FadeIn(legend),
            run_time=0.9,
        )
        self.wait(0.1 if self.pace.quick else 0.4)
        self.play(FadeIn(head), run_time=0.3)

        shown = [set() for _ in lanes]
        applied_sq = [set() for _ in lanes]
        for j in range(len(keys)):
            anims = (
                [head.animate.move_to([SX + j * SQ, head.get_center()[1], 0])]
                if j
                else []
            )
            for li, L in enumerate(lanes):
                step = L["tr"]["steps"][j]
                ok = set(step["applied"])
                for jj in range(
                    j + 1
                ):  # this arrival, plus any that were waiting on it
                    k = L["tr"]["order"][jj]
                    if jj == j and k not in ok:
                        anims += arrive(L["sqs"][jj], False)
                    elif k in ok and jj not in applied_sq[li]:
                        anims += arrive(L["sqs"][jj], True)
                        applied_sq[li].add(jj)
                now = visible(step)
                for sp in L["line"].spans:
                    want = sp.key in now
                    if want != (sp.key in shown[li]):
                        anims.append(Tween(sp, p=1.0 if want else 0.0, run_time=0.42))
                shown[li] = now
            if j == 3:
                anims.append(
                    self.cap(
                        "An update that arrives before the items it refers to simply waits."
                    )
                )
            self.play(*anims, run_time=0.55)
            for li, L in enumerate(lanes):
                assert L["line"].text_now() == L["tr"]["steps"][j]["text"], (li, j)
            self.wait(0.05 if self.pace.quick else 0.4)
        self.hold()
        ticks = VGroup(
            *[
                make_tick(GOOD, sw=6, scale=0.9).next_to(
                    L["line"].end_point(), RIGHT, buff=0.3
                )
                for L in lanes
            ]
        )
        self.play(
            self.cap(
                "Three orders, three different histories, one identical document."
            ),
            FadeOut(head),
            LaggedStart(*[Create(t) for t in ticks], lag_ratio=0.2),
            run_time=0.7,
        )
        self.hold(ambient=lambda t: [Throb(ticks, t, amp=0.12)])

        # --- a duplicate changes nothing --------------------------------------------- #
        dups = VGroup()
        for L, k in zip(lanes, ("merge", "offline", "crt"), strict=True):
            q = square(keys.index(k) + 1, PEERS[UPD[k]["by"]]).move_to(
                [SX + 8 * SQ + 0.08, L["y"], 0]
            )
            dups.add(q)
        strikes = VGroup(
            *[
                Line(
                    q.get_corner(DL) + LEFT * 0.03, q.get_corner(UR) + RIGHT * 0.03
                ).set_stroke(MUTED, width=2.5)
                for q in dups
            ]
        )
        self.play(
            self.cap("A duplicate changes nothing: the copy already holds those ids."),
            run_time=0.45,
        )
        self.play(  # one copy after the other: it arrives, it is recognised, it is dropped
            LaggedStart(
                *[
                    Succession(
                        FadeIn(q, shift=LEFT * 0.5, run_time=0.35),
                        AnimationGroup(*arrive(q, False), run_time=0.25),
                        Wiggle(
                            q,
                            scale_value=1.18,
                            rotation_angle=0.04 * TAU,
                            run_time=0.45,
                        ),
                        Create(k, run_time=0.25),
                    )
                    for q, k in zip(dups, strikes, strict=True)
                ],
                lag_ratio=0.55,
            ),
            run_time=3.2,
        )
        self.hold()

        # --- every possible order: 40,320 pixels --------------------------------------- #
        W, H = 360, 112  # 14 rows per first arrival, 2 rows per second
        assert W * H == perms["count"]
        ramp = [ManimColor(c) for c in RAMP8]  # one hue: more waiting reads lighter
        lut = np.array(
            [[int(255 * v) for v in c.to_rgb()] for c in ramp], dtype=np.uint8
        )
        full = np.zeros((H, W, 4), dtype=np.uint8)
        full[..., :3] = lut[waited.reshape(H, W)]
        full[..., 3] = 255
        dim = np.zeros_like(full)
        dim[..., :3] = [int(255 * v) for v in ManimColor(PANEL).to_rgb()]
        dim[..., 3] = 255
        img = ImageMobject(dim.copy())
        img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
        img.height = 2.9
        img.move_to([-0.55, -0.55, 0])
        frame = SurroundingRectangle(img, color=FAINT, buff=0.04, stroke_width=1.5)
        done, same = ValueTracker(0), ValueTracker(0)
        SAME_C = mix(
            GOOD, PANEL, 0.42
        )  # "the same final bytes": one colour for every order
        same_rgb = [int(255 * v) for v in SAME_C.to_rgb()]

        def reveal(m):
            k = int(done.get_value())
            arr = dim.copy()
            arr.reshape(-1, 4)[:k] = full.reshape(-1, 4)[:k]
            arr[: int(round(same.get_value()))][..., :3] = (
                same_rgb  # rows the scan has passed
            )
            m.pixel_array = arr

        img.add_updater(reveal)
        band_h = img.height / len(keys)
        firsts = VGroup()
        for i, k in enumerate(keys):
            q = square(i + 1, PEERS[UPD[k]["by"]]).scale(0.62)
            q.box.set_stroke(q.peer.color, opacity=1)
            q.digit.set_color(q.peer.color)
            q.move_to(
                [img.get_left()[0] - 0.32, img.get_top()[1] - (i + 0.5) * band_h, 0]
            )
            firsts.add(q)
        first_lab = Text("arrives first", font_size=16, color=MUTED)
        first_lab.next_to(firsts, UP, buff=0.12).align_to(firsts, RIGHT)
        counter = live_number(
            done,
            fmt="{:,.0f}",
            fs=40,
            color=INK,
            weight="BOLD",
            anchor=lambda m: m.move_to([img.get_right()[0] + 1.3, 0.4, 0]),
        )
        c_lab = Text("orders tried", font_size=19, color=MUTED).move_to(
            [img.get_right()[0] + 1.3, -0.07, 0]
        )
        res = (
            VGroup(
                Text("1", font_size=44, color=GOOD, weight="BOLD"),
                Text("result", font_size=19, color=MUTED),
            )
            .arrange(DOWN, buff=0.12)
            .move_to([img.get_right()[0] + 1.3, -1.25, 0])
        )
        sw = VGroup(
            *[Square(0.2, stroke_width=0, fill_color=c, fill_opacity=1) for c in ramp]
        ).arrange(RIGHT, buff=0.03)
        key_l = Text("updates that had to wait:  0", font_size=16, color=MUTED)
        key_r = Text("7", font_size=16, color=MUTED)
        scale = VGroup(key_l, sw, key_r).arrange(RIGHT, buff=0.12)
        scale.next_to(img, DOWN, buff=0.16).align_to(img, LEFT)

        gone = VGroup(
            *[L["sqs"] for L in lanes],
            *[L["lab"] for L in lanes],
            *[L["line"] for L in lanes],
            ticks,
            dups,
            strikes,
            legend,
        )
        self.play(  # the lanes leave, then the map arrives (never one over the other)
            self.cap("Now every possible order: 40,320 of them, one pixel each."),
            FadeOut(gone, run_time=0.4),
            Succession(
                Wait(0.4),
                AnimationGroup(
                    FadeIn(img),
                    FadeIn(frame),
                    FadeIn(firsts),
                    FadeIn(first_lab),
                    FadeIn(c_lab),
                    FadeIn(scale),
                    run_time=0.5,
                ),
            ),
        )
        self.add(counter)
        self.play(
            done.animate.set_value(perms["count"]), run_time=3.2, rate_func=linear
        )
        self.play(FadeIn(res, scale=1.2), run_time=0.4)
        self.add(
            self.cite(
                f"All 40,320 delivery orders replayed on Yjs {STORY['versions']['yjs']}"
            )
        )
        self.hold()
        self.play(
            self.cap(
                "Every single one ends on the same bytes. The order never mattered."
            ),
            Circumscribe(res, color=GOOD, buff=0.14),
            run_time=0.9,
        )
        counter.clear_updaters()
        # recolour the map by what each order ended on: 40,320 pixels, one colour
        scan = Line(img.get_corner(UL), img.get_corner(UR)).set_stroke(INK, width=3)
        same_key = VGroup(
            Square(0.2, stroke_width=0, fill_color=SAME_C, fill_opacity=1),
            Text(
                "final state: the same bytes, in every order", font_size=16, color=MUTED
            ),
        ).arrange(RIGHT, buff=0.12)
        same_key.next_to(img, DOWN, buff=0.16).align_to(img, LEFT)
        self.play(
            FadeIn(scan, run_time=0.35),
            FadeOut(scale, run_time=0.15),
            self.then(FadeIn(same_key, run_time=0.2), 0.15),
        )
        self.play(
            scan.animate(run_time=2.8, rate_func=linear).shift(DOWN * img.height),
            same.animate(run_time=2.8, rate_func=linear).set_value(H),
            LaggedStart(  # each band, as the scan crosses it: whichever update came first
                *[Indicate(q, color=GOLD, scale_factor=1.35) for q in firsts],
                lag_ratio=1.0,
                run_time=2.8,
            ),
        )
        img.clear_updaters()
        one_doc = Text(final, font_size=32, color=INK, weight="BOLD").move_to(img)
        self.play(  # ...and what they all ended on: the film's sentence
            FadeOut(scan, run_time=0.3),
            ripple(frame, buff=0.07, grow=1.02),
            FadeIn(one_doc, scale=0.94, run_time=0.6),
        )
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 7 · Small, fast, stable
    # ====================================================================== #
    def scene_numbers(self):
        self.header("7 · Small, fast, stable", GOLD)
        tr, eng = BENCH["trace"], BENCH["engines"]
        yj, lo, am = eng["yjs"], eng["loro"], eng["automerge"]
        dl = NPM["downloads"]
        # every claim of this scene, asserted against the measurements
        assert tr["edits"] == 259778 and tr["final_chars"] == 104852
        assert yj["structs"] == 10971 and yj["ms"] < 1000  # "under a second"
        assert (
            round(yj["bytes"] / 1000) == 160 and round(tr["final_chars"] / 1000) == 105
        )
        assert lo["ms"] < yj["ms"] < am["ms"]  # Loro replays fastest, Yjs second
        assert lo["load_ms"] < yj["load_ms"] < am["load_ms"]
        assert (
            am["bytes"] < yj["bytes"] < lo["bytes"]
        )  # Automerge saves smallest, Yjs second
        assert round(dl["yjs"] / 1e6, 1) == 15.7 and NPM["yjs"]["latest"].startswith(
            "13."
        )
        assert NPM["yjs"]["v13_date"].startswith("2020-01")

        # --- a real paper, key by key -------------------------------------------- #
        X0, Y0, PW, PH, YMAX = -5.95, -2.2, 8.7, 3.45, 110_000
        K = tr["edits"]
        series = [(0, 0)] + [tuple(x) for x in tr["length_series"]]

        def pt(k, v):
            return np.array([X0 + PW * k / K, Y0 + PH * v / YMAX, 0.0])

        pts = [pt(k, v) for k, v in series]
        ks = np.array([k for k, _ in series], dtype=float)
        vs = np.array([v for _, v in series], dtype=float)
        base = Line(pt(0, 0), pt(K, 0)).set_stroke(FAINT, width=2)
        grid = VGroup(
            *[
                Line(pt(0, v), pt(K, v)).set_stroke(FAINT, width=1, opacity=0.6)
                for v in (50_000, 100_000)
            ]
        )
        yt = VGroup(
            *[
                mono(lab, fs=16, color=MUTED).next_to(pt(0, v), LEFT, buff=0.14)
                for v, lab in ((0, "0"), (50_000, "50K"), (100_000, "100K"))
            ]
        )
        title = VGroup(
            Text(
                "One real paper, written key by key",
                font_size=23,
                color=INK,
                weight="MEDIUM",
            ),
            Text(
                "characters in the document, after every keystroke",
                font_size=17,
                color=MUTED,
            ),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        title.move_to(pt(0, YMAX) + UP * 0.62, aligned_edge=LEFT)
        t = ValueTracker(0.0)
        line = VMobject().set_stroke(MINT, width=3)
        area = VMobject().set_stroke(width=0).set_fill(MINT, opacity=0.12)
        dot = Dot(pt(0, 0), radius=0.07, color=MINT).set_stroke(BG, width=2)

        def now():
            k = t.get_value() * K
            return k, float(np.interp(k, ks, vs))

        def redraw(_):
            k, v = now()
            n = int(np.searchsorted(ks, k, side="right"))
            path = pts[: max(n, 1)] + [pt(k, v)]
            if len(path) < 2:
                path = [pt(0, 0), pt(0, 0) + RIGHT * 1e-3]
            line.set_points_as_corners(path)
            area.set_points_as_corners([*path, pt(k, 0), pt(0, 0), path[0]])
            dot.move_to(pt(k, v))

        line.add_updater(redraw)
        redraw(None)

        def keys_label():
            m = Text(
                f"{now()[0]:,.0f} keystrokes", font_size=21, color=INK, weight="MEDIUM"
            )
            x = float(
                np.clip(pt(now()[0], 0)[0], X0 + m.width / 2, X0 + PW - m.width / 2)
            )
            return m.move_to([x, Y0 - 0.32, 0])

        def chars_label():
            m = Text(
                f"{now()[1]:,.0f} characters", font_size=21, color=INK, weight="MEDIUM"
            )
            m.next_to(dot, UL, buff=0.08)
            if m.get_left()[0] < X0 + 0.12:
                m.shift(RIGHT * (X0 + 0.12 - m.get_left()[0]))
            return m

        keys_n, chars_n = always_redraw(keys_label), always_redraw(chars_label)
        self.play(
            self.cap("A real research paper, as it was written: 259,778 keystrokes."),
            FadeIn(title, shift=UP * 0.1),
            FadeIn(VGroup(base, grid, yt)),
            run_time=0.7,
        )
        cite1 = self.cite(
            "Editing trace: Kleppmann & Beresford, automerge-perf (CC BY 4.0)"
        )
        self.add(area, line, dot, keys_n, chars_n, cite1)
        self.play(t.animate.set_value(1.0), run_time=4.2, rate_func=linear)
        for m in (line, keys_n, chars_n):
            m.clear_updaters()
        self.hold()

        # --- what Yjs makes of it -------------------------------------------------- #
        def tile(value, label):
            v = Text(value, font_size=34, color=INK, weight="BOLD")
            lab = Text(label, font_size=17, color=MUTED)
            return VGroup(v, lab).arrange(DOWN, aligned_edge=LEFT, buff=0.08)

        secs = yj["ms"] / 1000
        tiles = VGroup(
            tile(f"{secs:.2f} s", "to replay every keystroke"),
            tile(
                f"{yj['bytes'] / 1000:.0f} KB",
                f"saved in V2 format (text: {tr['final_chars'] / 1000:.0f} KB)",
            ),
            tile(f"{yj['load_ms']:.0f} ms", "to load it again"),
            tile(f"{yj['structs']:,}", "items in the document"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        head = Text(
            f"Yjs {yj['version']} on this trace",
            font_size=19,
            color=GOLD,
            weight="MEDIUM",
        )
        panel = VGroup(head, tiles).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        panel.move_to([X0 + PW + 0.55, -0.35, 0], aligned_edge=LEFT)

        # the replay, in real time: one sweep across the whole history lasts 0.93 s
        sweep = Line(pt(0, 0), pt(0, YMAX)).set_stroke(GOLD, width=3)
        clock = ValueTracker(0.0)
        replayed = (
            VMobject().set_stroke(width=0).set_fill(GOLD, opacity=0.2).set_z_index(-1)
        )

        def refill(m):
            k = clock.get_value() / secs * K
            n = int(np.searchsorted(ks, k, side="right"))
            path = pts[: max(n, 1)] + [pt(k, float(np.interp(k, ks, vs)))]
            m.set_points_as_corners([*path, pt(k, 0), pt(0, 0), path[0]])

        replayed.add_updater(refill)
        timer = live_number(
            clock,
            fmt="{:.2f} s",
            fs=34,
            color=INK,
            weight="BOLD",
            anchor=lambda m: m.move_to(tiles[0][0], aligned_edge=LEFT),
        )
        zero = Text("0.00 s", font_size=34, color=INK, weight="BOLD")
        zero.move_to(tiles[0][0], aligned_edge=LEFT)
        live = Text("in real time", font_size=17, color=GOLD)
        live.next_to(tiles[0][0], RIGHT, buff=0.22).align_to(tiles[0][0], DOWN)
        self.play(
            self.cap("Yjs replays it all in under a second and saves it in 160 KB."),
            FadeIn(head, shift=LEFT * 0.2),
            FadeIn(zero, shift=LEFT * 0.2),
            FadeIn(tiles[0][1], shift=LEFT * 0.2),
            FadeIn(sweep),
            run_time=0.6,
        )
        self.remove(zero)
        self.add(replayed, timer)
        self.wait(0.1 if self.pace.quick else 0.6)
        self.play(  # the film's clock is the measured one: this sweep lasts 0.93 s
            sweep.animate.shift(RIGHT * PW),
            clock.animate.set_value(secs),
            FadeIn(live, run_time=0.2),
            run_time=secs,
            rate_func=linear,
        )
        timer.clear_updaters()
        replayed.clear_updaters()
        self.remove(timer)
        self.add(tiles[0][0])
        self.play(
            FadeOut(sweep),
            replayed.animate.set_fill(opacity=0),
            Indicate(tiles[0][0], color=GOLD, scale_factor=1.1),
            LaggedStart(
                *[FadeIn(x, shift=LEFT * 0.2) for x in tiles[1:3]], lag_ratio=0.5
            ),
            run_time=1.0,
        )
        self.remove(replayed)
        self.hold()

        # runs collapse: the keystroke count falls to the number of items
        count = ValueTracker(tr["edits"])
        from_lab = Text("keystrokes", font_size=17, color=MUTED).move_to(
            tiles[3][1], aligned_edge=LEFT
        )
        start = Text(f"{tr['edits']:,}", font_size=34, color=INK, weight="BOLD")
        start.move_to(tiles[3][0], aligned_edge=LEFT)
        falling = live_number(
            count,
            fmt="{:,.0f}",
            fs=34,
            color=INK,
            weight="BOLD",
            anchor=lambda m: m.move_to(tiles[3][0], aligned_edge=LEFT),
        )
        self.play(
            self.cap(
                "Runs collapse into items: 259,778 keystrokes become 10,971 items."
            ),
            FadeIn(start, shift=LEFT * 0.2),
            FadeIn(from_lab, shift=LEFT * 0.2),
            run_time=0.6,
        )
        self.remove(start)
        self.add(falling)
        self.wait(0.1 if self.pace.quick else 0.5)
        self.play(
            count.animate.set_value(yj["structs"]),
            run_time=1.8,
            rate_func=rate_functions.ease_in_out_cubic,
        )
        falling.clear_updaters()
        self.remove(falling)
        self.add(tiles[3][0])
        self.play(
            FadeOut(from_lab, shift=UP * 0.1, run_time=0.25),
            self.then(FadeIn(tiles[3][1], shift=UP * 0.1, run_time=0.35), 0.25),
            Circumscribe(tiles[3], color=GOLD, buff=0.1, run_time=0.9),
        )
        self.hold()

        # --- next to the other CRDT libraries -------------------------------------- #
        chart = VGroup(
            title, base, grid, yt, area, line, dot, keys_n, chars_n, panel, cite1, live
        )
        rows = (("Yjs", yj), ("Loro", lo), ("Automerge", am))
        GRAY = "#6B7385"
        TOP, UPSHIFT = 1.2, 0.85  # the comparison starts centred, then makes room

        def bar_row(name, x, y, w, value, hero):
            lab = Text(
                name,
                font_size=21,
                color=INK if hero else MUTED,
                weight="BOLD" if hero else "NORMAL",
            )
            lab.move_to([x, y, 0], aligned_edge=LEFT)
            bar = RoundedRectangle(
                width=w,
                height=0.27,
                corner_radius=min(0.035, w / 2.1),
                stroke_width=0,
                fill_color=GOLD if hero else GRAY,
                fill_opacity=1,
            ).move_to([x + 1.7 + w / 2, y, 0])
            val = Text(value, font_size=21, color=INK if hero else MUTED).next_to(
                bar, RIGHT, buff=0.12
            )
            return lab, bar, val

        def multiple(title_s, key, fmt, x, maxw=1.45):
            vmax = max(e[key] for _, e in rows)
            ttl = Text(title_s, font_size=22, color=INK, weight="MEDIUM")
            ttl.move_to([x, TOP, 0], aligned_edge=LEFT)
            names, bars, vals = VGroup(), [], []
            for i, (name, e) in enumerate(rows):
                w = max(0.035, maxw * e[key] / vmax)
                lab, bar, val = bar_row(
                    name, x, TOP - 0.8 - i * 0.68, w, fmt(e[key]), name == "Yjs"
                )
                names.add(lab)
                bars.append(bar)
                vals.append(val)
            return dict(title=ttl, names=names, bars=bars, vals=vals, key=key)

        m1 = multiple(
            "replay 259,778 keystrokes", "ms", lambda v: f"{v / 1000:.2f} s", -6.65
        )
        m2 = multiple(
            "load the saved document", "load_ms", lambda v: f"{v:.0f} ms", -2.25
        )
        m3 = multiple(
            "size of the saved document", "bytes", lambda v: f"{v / 1000:.0f} KB", 2.4
        )
        note = Text("shorter is better", font_size=17, color=MUTED)
        note.move_to([6.7, TOP + 0.6, 0], aligned_edge=RIGHT)

        def race(m, speed):
            """Bars grow for a time proportional to the value they measure."""
            out = []
            for (_, e), bar, val in zip(rows, m["bars"], m["vals"], strict=True):
                t = max(0.25, e[m["key"]] * speed)
                out.append(
                    Succession(
                        GrowFromEdge(bar, LEFT, run_time=t, rate_func=linear),
                        FadeIn(val, shift=RIGHT * 0.1, run_time=0.25),
                    )
                )
            return out

        cite2 = self.cite(
            f"Measured locally ({BENCH['machine']}): Yjs {yj['version']}, Loro {lo['version']}, "
            f"Automerge {am['version']}. npm, 3 to 9 Nov 2026"
        )
        frames = VGroup(*[VGroup(m["title"], m["names"]) for m in (m1, m2, m3)], note)
        self.play(
            self.cap("Other CRDT libraries make other trade-offs on the same trace."),
            FadeOut(chart, run_time=0.4),
            self.then(
                LaggedStart(
                    *[FadeIn(f, shift=UP * 0.12) for f in frames],
                    lag_ratio=0.15,
                    run_time=0.6,
                ),
                0.4,
            ),
            self.then(FadeIn(cite2, run_time=0.4), 0.4),
        )
        self.play(  # the replay bars grow at half the measured wall-clock speed
            *race(m1, 0.5 / 1000),
            *race(m2, 1.6 / am["load_ms"]),
            *race(m3, 0.7 / lo["bytes"]),
        )
        self.hold()
        yjs_rows = [
            VGroup(m["names"][0], m["bars"][0], m["vals"][0]) for m in (m1, m2, m3)
        ]

        def nod(m, i):  # one row's name and value light up for a moment
            return [
                Indicate(x, color=INK, scale_factor=1.08)
                for x in (m["names"][i], m["vals"][i])
            ]

        self.play(  # in the order of the sentence: Loro's two timings, then Automerge's size
            self.cap(
                "Loro is faster, Automerge is smaller. Yjs comes second on all three."
            ),
            LaggedStart(
                AnimationGroup(*nod(m1, 1), *nod(m2, 1)),
                AnimationGroup(*nod(m3, 2)),
                lag_ratio=0.9,
            ),
            run_time=2.0,
        )
        self.play(
            LaggedStart(
                *[
                    Circumscribe(r, color=GOLD, buff=0.1, time_width=0.6)
                    for r in yjs_rows
                ],
                lag_ratio=0.5,
            ),
            run_time=2.4,
        )
        self.hold()

        # --- and everybody already runs it ------------------------------------------ #
        pk = (
            ("Yjs", dl["yjs"]),
            ("Loro", dl["loro-crdt"]),
            ("Automerge", dl["@automerge/automerge"]),
        )
        DY = -0.9
        d_title = Text(
            "npm downloads, last week", font_size=22, color=INK, weight="MEDIUM"
        )
        d_title.move_to([-6.65, DY, 0], aligned_edge=LEFT)
        d_names, d_bars, d_vals = VGroup(), [], []
        for i, (name, n) in enumerate(pk):
            w = max(0.035, 6.5 * n / dl["yjs"])
            value = f"{n / 1e6:.1f} million" if n >= 1e6 else f"{n / 1e3:.0f} thousand"
            lab, bar, val = bar_row(
                name, -6.65, DY - 0.66 - i * 0.56, w, value, name == "Yjs"
            )
            d_names.add(lab)
            d_bars.append(bar)
            d_vals.append(val)
        # v13, as a timeline: one dot per year since its release
        y0, y1 = int(NPM["yjs"]["v13_date"][:4]), int(NPM["fetched"][:4])
        assert (y0, y1) == (2020, 2026)
        years = VGroup(*[Dot(radius=0.06, color=FAINT) for _ in range(y0, y1 + 1)])
        years.arrange(RIGHT, buff=0.3)
        rail = Line(years[0].get_center(), years[-1].get_center()).set_stroke(
            FAINT, width=2
        )
        v13 = VGroup(
            Text("v13", font_size=46, color=GOLD, weight="BOLD"),
            Text("the same major version", font_size=18, color=MUTED),
            VGroup(rail, years),
        ).arrange(DOWN, buff=0.16)
        v13.add(mono(str(y0), fs=16, color=MUTED).next_to(years[0], DOWN, buff=0.14))
        v13.move_to([5.25, DY - 1.22, 0])
        yr = ValueTracker(y0)  # the year the timeline has reached

        def lit_now():  # the gold part of the rail, and the years already passed
            k = yr.get_value() - y0
            a, b = years[0].get_center(), years[-1].get_center()
            head = a + (b - a) * k / (y1 - y0) + RIGHT * 1e-3
            g = VGroup(Line(a, head).set_stroke(GOLD, width=3))
            g.add(
                *[
                    Dot(years[i].get_center(), radius=0.075, color=GOLD)
                    for i in range(int(k + 1e-6) + 1)
                ]
            )
            return g

        def year_now():  # ...and the year itself, counting at the far end
            m = mono(str(int(yr.get_value() + 1e-6)), fs=16, color=GOLD)
            return m.next_to(years[-1], DOWN, buff=0.14)

        lit, year = always_redraw(lit_now), always_redraw(year_now)
        everything = VGroup(
            frames, *[x for m in (m1, m2, m3) for x in (*m["bars"], *m["vals"])]
        )
        self.play(
            self.cap(
                "And it is stable: 15.7 million downloads a week, on version 13 since 2020."
            ),
            everything.animate.shift(UP * UPSHIFT),
            run_time=0.7,
        )
        self.play(
            FadeIn(VGroup(d_title, d_names), shift=UP * 0.1, run_time=0.5),
            *[
                Succession(
                    Wait(0.3),
                    GrowFromEdge(
                        b,
                        LEFT,
                        run_time=1.6 if i == 0 else 0.3,
                        rate_func=rate_functions.ease_out_cubic,
                    ),
                    FadeIn(v, shift=RIGHT * 0.1, run_time=0.25),
                )
                for i, (b, v) in enumerate(zip(d_bars, d_vals, strict=True))
            ],
            Succession(Wait(1.5), FadeIn(v13, scale=0.9, run_time=0.5)),
        )
        self.add(lit, year)
        self.play(yr.animate.set_value(y1), run_time=2.2, rate_func=linear)  # still v13
        lit.clear_updaters()
        year.clear_updaters()
        self.play(Indicate(v13[0], color=GOLD, scale_factor=1.12), run_time=0.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # 8 · The stack: Tiptap, Yjs, Hocuspocus
    # ====================================================================== #
    def scene_stack(self):
        self.header("8 · The stack: Tiptap, Yjs, Hocuspocus", MINT)
        CX = {ADA.cid: 1.55, BOB.cid: 3.65, AGENT.cid: 5.75}
        Y_NAME, Y_ED, Y_DOC, Y_PROV, Y_SRV, Y_DB = 2.4, 1.7, 0.78, -0.02, -1.25, -2.48
        LW, LH = 1.9, 0.58
        SRV_TOP, SRV_BOT = Y_SRV + 0.4, Y_SRV - 0.4
        MIDX, DBX = CX[BOB.cid], 1.9

        def layer(label, color, x, y, mono_=False, fs=18):
            box = RoundedRectangle(
                width=LW,
                height=LH,
                corner_radius=0.1,
                stroke_color=color,
                stroke_width=2.2,
                fill_color=color,
                fill_opacity=0.13,
            ).move_to([x, y, 0])
            t = (mono if mono_ else txt)(label, fs=fs, color=INK).move_to(box)
            t.set_z_index(3)  # packets pass through the box, behind its label
            g = VGroup(box, t)
            g.box = box
            return g

        cols = {}
        for cid, x in CX.items():
            peer = PEERS[cid]
            name = (
                VGroup(
                    avatar(peer, r=0.16),
                    Text(peer.name, font_size=18, color=INK, weight="MEDIUM"),
                )
                .arrange(RIGHT, buff=0.1)
                .move_to([x, Y_NAME, 0])
            )
            if peer.agent:
                ghost = (
                    DashedVMobject(
                        RoundedRectangle(width=LW, height=LH, corner_radius=0.1),
                        num_dashes=34,
                    )
                    .set_stroke(FAINT, width=2)
                    .move_to([x, Y_ED, 0])
                )
                ed = VGroup(
                    ghost, Text("no editor", font_size=17, color=MUTED).move_to(ghost)
                )
            else:
                ed = layer("Tiptap", INK, x, Y_ED)
            cols[cid] = dict(
                name=name,
                ed=ed,
                doc=layer("Y.Doc", GOLD, x, Y_DOC, mono_=True),
                prov=layer("provider", MINT, x, Y_PROV, mono_=True),
                wire=Line([x, Y_PROV - LH / 2, 0], [x, SRV_TOP, 0]).set_stroke(
                    MINT, width=2.5, opacity=0.8
                ),
            )
        # one baseline for the three names: "Agent" has a descender, which would
        # otherwise lift it a few pixels when its box is centred like the others
        name_top = cols[ADA.cid]["name"][1].get_top()[1]
        for c in cols.values():
            c["name"][1].shift(UP * (name_top - c["name"][1].get_top()[1]))
        srv_box = RoundedRectangle(
            width=CX[AGENT.cid] - CX[ADA.cid] + LW,
            height=0.8,
            corner_radius=0.12,
            stroke_color=MINT,
            stroke_width=2.5,
            fill_color=MINT,
            fill_opacity=0.1,
        ).move_to([MIDX, Y_SRV, 0])
        srv_name = VGroup(
            server_glyph(color=MINT, w=0.62, h=0.44),
            Text("Hocuspocus", font_size=20, color=INK, weight="MEDIUM"),
        ).arrange(RIGHT, buff=0.16)
        srv_name.move_to([srv_box.get_left()[0] + 0.3 + srv_name.width / 2, Y_SRV, 0])
        srv_doc = VGroup(
            RoundedRectangle(
                width=1.25,
                height=0.44,
                corner_radius=0.08,
                stroke_color=GOLD,
                stroke_width=2,
                fill_color=GOLD,
                fill_opacity=0.13,
            ),
            mono("Y.Doc", fs=17, color=INK),
        )
        srv_doc[1].move_to(srv_doc[0])
        srv_doc.move_to([srv_box.get_right()[0] - 0.3 - srv_doc.width / 2, Y_SRV, 0])
        for label in (srv_name, srv_doc[1]):
            label.set_z_index(3)
        server = VGroup(srv_box, srv_name, srv_doc)
        ws_lab = mono("WebSocket", fs=16, color=MUTED)
        ws_lab.move_to(
            [(CX[ADA.cid] + CX[BOB.cid]) / 2, (Y_PROV - LH / 2 + SRV_TOP) / 2, 0]
        )
        db = db_cylinder(MINT, w=1.0, h=0.62).move_to([DBX, Y_DB, 0])
        db_wire = Line([DBX, SRV_BOT, 0], [DBX, db.get_top()[1], 0]).set_stroke(
            MINT, width=2.5, opacity=0.8
        )
        db_lab = Text("database", font_size=17, color=MUTED).next_to(db, LEFT, buff=0.2)
        db_note = mono("saved 2 s after the last edit", fs=16, color=MUTED).next_to(
            db, RIGHT, buff=0.25
        )

        def panel_for(spec, title):
            pan, lines = code_panel(
                spec,
                JS_T2C,
                title=title,
                fs=16,
                indent_unit=0.27,
                line_buff=0.13,
                target_h=4.7,
                target_w=6.3,
                comment="//",
            )
            pan.move_to([-6.85 + pan.width / 2, -0.3, 0])
            return pan, lines

        def route(a, b):
            """Tiptap (or Y.Doc) of ``a`` -> its provider -> the server -> up to ``b``."""
            ya = Y_DOC if PEERS[a].agent else Y_ED
            yb = Y_DOC if PEERS[b].agent else Y_ED
            return polyline(
                [CX[a], ya, 0], [CX[a], Y_SRV, 0], [CX[b], Y_SRV, 0], [CX[b], yb, 0]
            )

        online = [ADA.cid]  # the columns on screen so far: packets only go to those

        def flow(a, n=4, rt=1.5, r=0.07):
            return [
                stream(route(a, b), PEERS[a].color, n=n, run_time=rt, r=r)
                for b in online
                if b != a
            ]

        # --- client.js: Tiptap edits a local Y.Doc -------------------------------- #
        a = cols[ADA.cid]
        pan, lines = panel_for(CLIENT_JS, "client.js")
        self.play(
            self.cap("Every client holds a Y.Doc: the copy you have been watching."),
            FadeIn(pan, shift=RIGHT * 0.2),
            FadeIn(a["name"]),
            run_time=0.6,
        )
        self.focus(pan, lines, [0])
        self.play(FadeIn(a["doc"], scale=0.9), run_time=0.5)
        self.hold(ambient=lambda t: [Throb(a["doc"], t, amp=0.05)])
        self.focus(pan, lines, [5, 6, 7])
        ax, top, bot = CX[ADA.cid], Y_ED - LH / 2, Y_DOC + LH / 2
        bind = VGroup(  # the binding works both ways
            arr(
                [ax - 0.22, top, 0],
                [ax - 0.22, bot, 0],
                color=GOLD,
                sw=4,
                buff=0.03,
                tip=0.15,
            ),
            arr(
                [ax + 0.22, bot, 0],
                [ax + 0.22, top, 0],
                color=GOLD,
                sw=4,
                buff=0.03,
                tip=0.15,
            ),
        )
        self.play(
            self.cap(
                "Tiptap is the editor. Collaboration binds it to the Y.Doc, both ways."
            ),
            FadeIn(a["ed"], shift=DOWN * 0.15),
            GrowArrow(bind[0]),
            GrowArrow(bind[1]),
            run_time=0.6,
        )
        to_doc = Line([ax - 0.22, top + 0.05, 0], [ax - 0.22, bot - 0.05, 0])
        to_ed = Line([ax + 0.22, bot - 0.05, 0], [ax + 0.22, top + 0.05, 0])

        def both_ways(
            t,
        ):  # a keystroke goes down into the Y.Doc; a remote edit comes back up
            half = t / 2
            beat = half * 0.5
            return [
                stream(to_doc, INK, n=3, run_time=half, r=0.045),
                Succession(
                    Wait(half - beat), Throb(a["doc"], beat, period=beat, amp=0.07)
                ),
                Succession(Wait(half), stream(to_ed, INK, n=3, run_time=half, r=0.045)),
                Succession(
                    Wait(2 * half - beat), Throb(a["ed"], beat, period=beat, amp=0.07)
                ),
            ]

        self.hold(ambient=both_ways)
        self.focus(pan, lines, [1, 2, 3, 4])
        self.play(
            self.cap(
                "The Hocuspocus provider syncs the Y.Doc over one WebSocket, carets included."
            ),
            FadeIn(a["prov"], shift=DOWN * 0.15),
            Create(a["wire"]),
            FadeIn(server, shift=UP * 0.15),
            FadeIn(ws_lab),
            run_time=0.7,
        )
        down = polyline(
            [CX[ADA.cid], Y_ED, 0], [CX[ADA.cid], Y_SRV, 0], [MIDX, Y_SRV, 0]
        )
        self.hold(ambient=lambda t: [stream(down, ADA.color, n=4, run_time=t)])

        # --- server.js: the relay that also remembers -------------------------------- #
        b = cols[BOB.cid]
        online.append(BOB.cid)
        pan2, lines2 = panel_for(SERVER_JS, "server.js")
        self.play(
            self.cap(
                "The Hocuspocus server keeps its own copy and relays every update."
            ),
            FadeOut(pan, run_time=0.25),
            FadeOut(self.hlrect, run_time=0.25),
            self.then(FadeIn(pan2, run_time=0.4), 0.25),
            FadeIn(
                VGroup(b["name"], b["ed"], b["doc"], b["prov"]),
                shift=DOWN * 0.15,
                run_time=0.6,
            ),
            Create(b["wire"], run_time=0.6),
        )
        self.hlrect = None
        self.focus(pan2, lines2, [4, 5, 6, 7, 8])
        self.play(
            *flow(ADA.cid, n=4, rt=1.6),
            Succession(Wait(0.5), Indicate(srv_doc, color=GOLD, scale_factor=1.15)),
        )
        self.hold(ambient=lambda t: flow(BOB.cid, n=3, rt=t))
        self.focus(pan2, lines2, [0, 1, 2, 3])
        to_db = polyline([MIDX, Y_SRV, 0], [DBX, Y_SRV, 0], [DBX, db.get_top()[1], 0])
        self.play(
            self.cap(
                "It saves the document as one binary blob, 2 seconds after the last edit."
            ),
            FadeIn(db, shift=UP * 0.15),
            Create(db_wire),
            FadeIn(db_lab),
            FadeIn(db_note),
            Succession(Wait(0.5), stream(to_db, GOLD, n=3, run_time=1.1)),
        )
        self.hold(ambient=lambda t: [Throb(db, t, amp=0.05)])

        # --- agent.js: one more peer, no editor ---------------------------------------- #
        g = cols[AGENT.cid]
        online.append(AGENT.cid)
        pan3, lines3 = panel_for(AGENT_JS, "agent.js")
        self.play(
            self.cap(
                "An agent needs no editor. A Y.Doc and a provider make it one more peer."
            ),
            FadeOut(pan2, run_time=0.25),
            FadeOut(self.hlrect, run_time=0.25),
            self.then(FadeIn(pan3, run_time=0.4), 0.25),
            FadeOut(db_note, run_time=0.25),
            FadeIn(
                VGroup(g["name"], g["ed"], g["doc"], g["prov"]),
                shift=DOWN * 0.15,
                run_time=0.6,
            ),
            Create(g["wire"], run_time=0.6),
        )
        self.hlrect = None
        self.focus(pan3, lines3, [0, 1, 2, 3, 4, 5])
        flags = VGroup()  # its awareness reaches the editors: the agent appears in each
        for cid in (ADA.cid, BOB.cid):
            badge = avatar(AGENT, r=0.15, ring=BG)
            flags.add(
                badge.move_to(
                    cols[cid]["ed"].box.get_corner(UR) + LEFT * 0.08 + DOWN * 0.04
                )
            )
        self.play(
            Indicate(g["doc"], color=GOLD, scale_factor=1.12),
            Indicate(g["prov"], color=MINT, scale_factor=1.12),
            run_time=0.8,
        )
        self.play(
            *[
                stream(route(AGENT.cid, c), AGENT.color, n=2, run_time=0.9)
                for c in (ADA.cid, BOB.cid)
            ],
            Succession(
                Wait(0.6),
                LaggedStart(*[FadeIn(f, scale=0.6) for f in flags], lag_ratio=0.3),
            ),
        )
        self.hold(  # its presence keeps travelling the same road as its edits
            ambient=lambda t: [
                *[
                    stream(route(AGENT.cid, c), AGENT.color, n=3, run_time=t)
                    for c in (ADA.cid, BOB.cid)
                ],
                *[Throb(f, t, period=t / 2, amp=0.3) for f in flags],
            ]
        )
        self.focus(pan3, lines3, [7, 8, 9])
        self.play(
            self.cap(
                "Its tokens are ordinary Yjs inserts. They merge like anyone's keystrokes."
            ),
            *flow(AGENT.cid, n=7, rt=2.6),
            Succession(Wait(0.7), AnimationGroup(*flow(BOB.cid, n=4, rt=1.6))),
            Succession(Wait(1.3), AnimationGroup(*flow(ADA.cid, n=3, rt=1.3))),
        )
        self.hold(ambient=lambda t: flow(AGENT.cid, n=4, rt=t))

        # --- back to the page: three writers, one more line ------------------------------ #
        everything = VGroup(
            pan3,
            self.hlrect,
            server,
            ws_lab,
            db,
            db_wire,
            db_lab,
            bind,
            flags,
            *[v for c in cols.values() for v in c.values()],
        )
        self.hlrect = None
        win = EditorWindow(w=11.4, h=5.0, title="notes").move_to([0, -0.3, 0])
        win.line(0.92, [(H1_TEXT, None)], fs=40, weight="BOLD")
        win.line(1.82, [("".join(P1_PARTS), None)])
        win.line(2.6, [("".join(P2_PARTS), None)])
        fin = SNAPS["final"]["ada"]["items"]
        p3 = win.line(  # the film's sentence, each part in its author's colour
            3.38,
            [(i["str"], PEERS[i["id"][0]], 0) for i in fin if not i["deleted"]],
            tint="author",
        )
        assert "".join(sp.text for sp in p3.spans) == SNAPS["final"]["ada"]["text"]
        cr, d_, t_, s_, mg, al, ed_, off = p3.spans
        for peer in (ADA, BOB, AGENT):
            win.join(peer, shown=True)
        ca = win.caret(ADA).follow_spans(p3, [cr, d_, t_, mg, ed_])
        cb = win.caret(BOB, show=0).follow_spans(p3, [s_, off])
        cg = win.caret(AGENT, show=0).follow_spans(p3, [al])
        self.play(
            self.cap(
                "So people and agents write on the same page, and every copy converges."
            ),
            FadeOut(everything, shift=UP * 0.2, run_time=0.35),
            self.then(FadeIn(win, shift=UP * 0.2, run_time=0.5), 0.35),
        )
        self.play(  # bursts overlap in time, but two name flags never share a spot
            Succession(  # Ada: C R D T, then she lets go
                Type([cr, d_, t_], cps=7, seed=11), Tween(ca, show=0.0, run_time=0.12)
            ),
            Succession(  # Bob: the s, then the end of the sentence
                Wait(0.7),
                Tween(cb, show=1.0, run_time=0.15),
                Type(s_, run_time=0.2),
                Wait(0.2),
                Type(off, cps=8.5, seed=14),
            ),
            Succession(  # Ada again, in the middle, while Bob is still typing at the end
                Wait(1.9),
                Tween(ca, show=1.0, run_time=0.12),
                Type([mg, ed_], cps=9, seed=12),
                Tween(ca, show=0.0, run_time=0.15),
            ),
            Succession(  # the agent slips its word in between hers
                Wait(3.55),
                Tween(cg, show=1.0, run_time=0.15),
                Type(al, chunks=[4], tps=2.2),
            ),
        )
        assert p3.text_now() == SNAPS["final"]["ada"]["text"]
        self.hold()
        self.play(
            self.cap(
                "Tiptap edits. Yjs merges. Hocuspocus relays and remembers.",
                color=GOLD,
                weight="BOLD",
            ),
            *[Tween(c, show=0.0) for c in (cb, cg)],
            run_time=0.6,
        )
        # roll call: every item of the sentence answers in its author's colour
        ay, ch = p3.anchor.get_center()[1], p3.cap_h * p3.scale_now
        marks = [
            RoundedRectangle(
                width=sp.x1 - sp.x0,
                height=ch * 2.2,
                corner_radius=0.06,
                stroke_width=0,
                fill_color=sp.peer.color,
                fill_opacity=0.3,
            ).move_to([(sp.x0 + sp.x1) / 2, ay + ch * 0.42, 0])
            for sp in p3.spans
        ]
        self.play(
            LaggedStart(
                *[
                    Succession(FadeIn(m, run_time=0.25), FadeOut(m, run_time=0.5))
                    for m in marks
                ],
                lag_ratio=0.45,
            ),
            run_time=2.6,
        )
        self.play(  # and the three writers, one last time
            LaggedStart(
                *[Throb(a, 0.6, period=0.6, amp=0.35) for a in win.presence],
                lag_ratio=0.5,
            ),
            run_time=1.3,
        )
        self.settle()
        self.wipe()


# ---- renderable scenes ------------------------------------------------------ #
class Intro(_Base):
    def construct(self):
        self.play_intro()


class Together(_Base):
    def construct(self):
        self.scene_together()


class Positions(_Base):
    def construct(self):
        self.scene_positions()


class Items(_Base):
    def construct(self):
        self.scene_items()


class SameSpot(_Base):
    def construct(self):
        self.scene_samespot()


class Offline(_Base):
    def construct(self):
        self.scene_offline()


class AnyOrder(_Base):
    def construct(self):
        self.scene_anyorder()


class Numbers(_Base):
    def construct(self):
        self.scene_numbers()


class Stack(_Base):
    def construct(self):
        self.scene_stack()


class Outro(_Base):
    def construct(self):
        self.play_outro()


class YjsFilm(_Base):
    def construct(self):
        self.play_all()
