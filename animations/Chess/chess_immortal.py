"""The Immortal Game — a cinematic, house-style chess replay.

A self-explanatory (no voice-over) film that replays the most famous game in
chess history move by move:

    Adolf Anderssen  vs.  Lionel Kieseritzky
    London, 1851 · King's Gambit

Anderssen sacrifices a bishop, BOTH rooks and finally his queen, then mates with
three minor pieces (18.Bd6‼ … 22.Qf6+‼ … 23.Be7#). The animation plays all 45
half-moves on a persistent board with:

  * a build-up of the board (frame, squares, coordinates) and the opening army,
  * smooth piece glides — knights hop along an arc — with soft capture flashes,
  * last-move highlighting and a red pulse whenever a king is in check,
  * a running "move badge" (number + notation) and a story caption that lingers
    long enough to read,
  * a captured-material tray so the viewer *sees* White pouring pieces away,
  * extra emphasis (a glowing arrow + a long pause) on the three brilliancies,
  * a final "why it's mate" breakdown — every escape square covered — and a card.

Rendering / fonts
------------------
Chess pieces are Unicode glyphs from the *filled* set (♚♛♜♝♞♟) recoloured — ivory
for White, charcoal for Black — so both armies read cleanly on either square
colour. They're drawn with a symbol font that actually carries the glyphs
("Arial Unicode MS" on macOS, "Apple Symbols" as a fallback). Everything else
uses ``Text`` (Pango), never ``Tex`` — no LaTeX toolchain required.

Scenes are exposed individually (``Intro``, ``Game``, ``Outro``) and as one film
(``Immortal``).

Env knobs:
    CHESS_QUICK=1   shorten every reading hold for a fast sanity render
    CHESS_PLIES=N   stop after N half-moves (dev aid; default = whole game)
"""
from __future__ import annotations

import os

import numpy as np
import manimpango
from manim import *

# --------------------------------------------------------------------------- #
# Crisp text — Manim quantises glyph positions badly below ~20 pt, giving uneven
# letter/word spacing. Render at a large base size and scale the mobject *down*.
# Shadows manim's ``Text`` so every call in this module benefits automatically.
# (Single-glyph chess pieces are built from ``_BaseText`` directly, since a lone
# glyph has no inter-letter spacing to mangle and needs the symbol font.)
# --------------------------------------------------------------------------- #
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


# ---- pick a font that actually carries the chess glyphs -------------------- #
def _pick_symbol_font():
    fonts = set(manimpango.list_fonts())
    for cand in ("Arial Unicode MS", "Apple Symbols", "DejaVu Sans", "Symbola",
                 "Segoe UI Symbol", "Noto Sans Symbols2"):
        if cand in fonts:
            return cand
    return None  # let Pango fall back and hope for the best


SYMFONT = _pick_symbol_font()

# Filled glyph set, used for *both* colours (recoloured per side).
GLYPH = {"K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞", "P": "♟"}

QUICK = os.environ.get("CHESS_QUICK") == "1"
PLIES_CAP = int(os.environ.get("CHESS_PLIES", "999"))
# One knob for pacing. Every reading "hold" is scaled by DELAY; QUICK collapses
# them for a fast iteration render. At the default it's a relaxed rhythm that
# keeps the whole film around 3½ minutes with time to read the key moments.
DELAY = 0.32 if QUICK else 1.15

# ---- palette (house style, chess-flavoured) ------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text
FAINT = "#39404E"       # dividers / guides
GOLD = "#FFC94D"        # highlights / the brilliancies
RED = "#E5484D"         # check / mate / danger

LIGHT_SQ = "#E9DFC7"    # light squares (warm ivory)
DARK_SQ = "#48685A"     # dark squares (muted teal-green)
HL = "#FFD166"          # last-move highlight (gold wash)
WOOD = "#241C15"        # board frame (dark walnut)
WOOD_EDGE = "#C9A24B"   # thin gold rim on the frame
COORD = "#B4AB90"       # rank/file coordinate labels

PIECE_W = "#F3ECDA"     # White pieces — warm ivory
PIECE_W_S = "#20242B"   #   … dark outline
PIECE_B = "#23262C"     # Black pieces — charcoal
PIECE_B_S = "#CFC9BB"   #   … light outline

WHITE_NAME = "#E7D9B0"  # Anderssen accent
BLACK_NAME = "#9FB6C9"  # Kieseritzky accent

# ---- board geometry ------------------------------------------------------- #
SQ = 0.70                       # square side (board is 8·SQ = 5.6 units)
BOARD_C = np.array([-3.45, -0.30, 0.0])   # board centre (left of the panel)

# panel anchors (everything with x>0)
PANEL_CX = 3.45
BADGE_Y = 2.35
DIV_Y = 1.82
NOTE_LEFT = 0.35
NOTE_TOP = 1.52
TRAY_X0 = 0.62
TRAY_STEP = 0.44


# ========================================================================== #
# The game — Anderssen vs. Kieseritzky, London 1851 (all 45 half-moves)
# ========================================================================== #
def mv(color, frm, to, san, note=None, cap=False, chk=False, mate=False,
       star=0, arrow=False):
    """One half-move. ``star``: 0 plain · 1 gold notation · 2 brilliancy.

    ``arrow`` draws a glowing trajectory arrow (reserved for the brilliancies)."""
    return dict(color=color, frm=frm, to=to, san=san, note=note, cap=cap,
                chk=chk, mate=mate, star=star, arrow=arrow)


GAME = [
    mv('w', 'e2', 'e4', 'e4', "The King's Pawn opens — both armies race for the centre."),
    mv('b', 'e7', 'e5', 'e5'),
    mv('w', 'f2', 'f4', 'f4', "The King's Gambit: White offers a pawn to blast open the f-file.", star=1),
    mv('b', 'e5', 'f4', 'e×f4', "Black accepts the gambit.", cap=True),
    mv('w', 'f1', 'c4', 'Bc4', "The bishop takes aim at f7 — Black's tender spot."),
    mv('b', 'd8', 'h4', 'Qh4+', "A brazen check. White can no longer castle.", chk=True),
    mv('w', 'e1', 'f1', 'Kf1', "The king just steps aside."),
    mv('b', 'b7', 'b5', 'b5', "The Bishop's counter-gambit — a pawn to deflect the bishop."),
    mv('w', 'c4', 'b5', 'B×b5', cap=True),
    mv('b', 'g8', 'f6', 'Nf6'),
    mv('w', 'g1', 'f3', 'Nf3', "White develops with tempo, hitting the queen."),
    mv('b', 'h4', 'h6', 'Qh6'),
    mv('w', 'd2', 'd3', 'd3', "Quietly opening lines for the pieces."),
    mv('b', 'f6', 'h5', 'Nh5', "The knight lunges at f4 and g3."),
    mv('w', 'f3', 'h4', 'Nh4', "Chasing the queen and eyeing the f5 outpost."),
    mv('b', 'h6', 'g5', 'Qg5'),
    mv('w', 'h4', 'f5', 'Nf5', "The knight plants itself deep in Black's camp.", star=1),
    mv('b', 'c7', 'c6', 'c6', "Black hits the bishop and frees the queen's escape."),
    mv('w', 'g2', 'g4', 'g4', "White ignores the threats and storms forward.", star=1),
    mv('b', 'h5', 'f6', 'Nf6'),
    mv('w', 'h1', 'g1', 'Rg1', "A quiet rook lift — and the bishop is left hanging.", star=1),
    mv('b', 'c6', 'b5', 'c×b5', "Black snatches the bishop…", cap=True),
    mv('w', 'h2', 'h4', 'h4', "…but the pawn-storm crashes on."),
    mv('b', 'g5', 'g6', 'Qg6'),
    mv('w', 'h4', 'h5', 'h5', "Kicking the queen again — tempo after tempo."),
    mv('b', 'g6', 'g5', 'Qg5'),
    mv('w', 'd1', 'f3', 'Qf3', "Threatening B×f4, which would trap the queen."),
    mv('b', 'f6', 'g8', 'Ng8', "The knight slinks home to defend."),
    mv('w', 'c1', 'f4', 'B×f4', "Winning the pawn back and baring Black's queen.", cap=True),
    mv('b', 'g5', 'f6', 'Qf6'),
    mv('w', 'b1', 'c3', 'Nc3', "The last piece joins — every White man now points at Black."),
    mv('b', 'f8', 'c5', 'Bc5', "Black develops with a threat against f2."),
    mv('w', 'c3', 'd5', 'Nd5', "Forking the queen and the c7-square.", star=1),
    mv('b', 'f6', 'b2', 'Q×b2', "Black grabs a pawn and attacks White's rook.", cap=True),
    mv('w', 'f4', 'd6', 'Bd6‼', "The immortal move. White ignores BOTH rooks and buries the bishop on d6.", star=2, arrow=True),
    mv('b', 'c5', 'g1', 'B×g1', "Black helps himself to the first rook.", cap=True),
    mv('w', 'e4', 'e5', 'e5', "Slamming the door — the queen can't rush back to defend."),
    mv('b', 'b2', 'a1', 'Q×a1+', "And the second rook falls, with check.", cap=True, chk=True),
    mv('w', 'f1', 'e2', 'Ke2', "The king tiptoes away — and now White threatens mate.", star=1),
    mv('b', 'b8', 'a6', 'Na6', "A desperate guard for the c7-square."),
    mv('w', 'f5', 'g7', 'N×g7+', "Check! The net draws tight.", cap=True, chk=True),
    mv('b', 'e8', 'd8', 'Kd8', "The king is herded to d8."),
    mv('w', 'f3', 'f6', 'Qf6+‼', "The queen sacrifice — hurled in to tear open the last escape.", chk=True, star=2, arrow=True),
    mv('b', 'g8', 'f6', 'N×f6', "Forced — the knight must take the queen.", cap=True),
    mv('w', 'd6', 'e7', 'Be7#', "Checkmate. Three minor pieces deliver the final blow.", mate=True, star=2, arrow=True),
]

# The mating net (used by the finale breakdown).
MATE_KING = 'd8'
MATE_CHECKER = 'e7'          # bishop giving check
MATE_ESCAPES = ['c7', 'e7', 'e8']   # squares the king would flee to / capture on
MATE_GUARDS = {'c7': 'd5', 'e7': 'd5', 'e8': 'g7'}   # who covers each


# ========================================================================== #
# Base scene — shared helpers, board, move engine, intro / outro
# ========================================================================== #
class _Base(Scene):
    def setup(self):
        self.camera.background_color = BG
        self.pieces = {}     # square -> piece mobject
        self.codes = {}      # square -> code like 'wK'
        self.king = {}       # 'w'/'b' -> square
        self.tray_count = {'w': 0, 'b': 0}
        self.hl = None       # current last-move highlight
        self.badge = VGroup()
        self.note_grp = VGroup()
        self.arrow_last = None   # mating arrow, kept for the finale
        self.ply = 0

    # ---- timing ----------------------------------------------------------- #
    def hold(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- geometry --------------------------------------------------------- #
    def sq_center(self, s):
        f = ord(s[0]) - 97
        r = int(s[1]) - 1
        return BOARD_C + np.array([(f - 3.5) * SQ, (r - 3.5) * SQ, 0.0])

    # ---- text ------------------------------------------------------------- #
    def wrap(self, s, fs=25, color=INK, width=34, center=False):
        words, lines, cur = s.split(), [], ""
        for w in words:
            if not cur or len(cur) + 1 + len(w) <= width:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        grp = VGroup(*[Text(l, font_size=fs, color=color) for l in lines])
        if center:
            grp.arrange(DOWN, buff=0.22)
        else:
            grp.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        return grp

    # ---- pieces ----------------------------------------------------------- #
    def make_piece(self, code):
        color, t = code[0], code[1]
        m = _BaseText(GLYPH[t], font=SYMFONT, font_size=96)
        m.scale_to_fit_height(SQ * 0.72)
        if color == 'w':
            m.set_fill(PIECE_W, 1).set_stroke(PIECE_W_S, 1.1)
        else:
            m.set_fill(PIECE_B, 1).set_stroke(PIECE_B_S, 1.1)
        m.set_z_index(10)
        return m

    # ====================================================================== #
    # Board build-up
    # ====================================================================== #
    def build_board(self):
        self.sqmob = {}
        squares = VGroup()
        for f in range(8):
            for r in range(8):
                s = chr(97 + f) + str(r + 1)
                col = DARK_SQ if (f + r) % 2 == 0 else LIGHT_SQ
                m = Square(SQ).set_fill(col, 1).set_stroke(width=0)
                m.move_to(self.sq_center(s)).set_z_index(0)
                self.sqmob[s] = m
                squares.add(m)

        half = 4 * SQ
        frame = RoundedRectangle(
            width=8 * SQ + 0.46, height=8 * SQ + 0.46, corner_radius=0.10,
            fill_color=WOOD, fill_opacity=1, stroke_color=WOOD_EDGE, stroke_width=2.5,
        ).move_to(BOARD_C).set_z_index(-1)
        rim = RoundedRectangle(
            width=8 * SQ + 0.10, height=8 * SQ + 0.10, corner_radius=0.03,
            stroke_color=WOOD_EDGE, stroke_width=1.4, fill_opacity=0,
        ).move_to(BOARD_C).set_z_index(1)

        coords = VGroup()
        for f in range(8):
            lab = Text(chr(97 + f), font_size=18, color=COORD)
            lab.move_to(BOARD_C + np.array([(f - 3.5) * SQ, -half - 0.5, 0]))
            coords.add(lab)
        for r in range(8):
            lab = Text(str(r + 1), font_size=18, color=COORD)
            lab.move_to(BOARD_C + np.array([-half - 0.5, (r - 3.5) * SQ, 0]))
            coords.add(lab)

        self.play(FadeIn(frame, scale=0.96), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(m) for m in squares],
                              lag_ratio=0.012, run_time=1.6))
        self.play(Create(rim), LaggedStart(*[FadeIn(m) for m in coords],
                  lag_ratio=0.03), run_time=0.8)
        self.board_frame = VGroup(frame, rim, coords)

    def place_army(self, fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"):
        army = VGroup()
        for i, row in enumerate(fen.split('/')):
            rank = 8 - i
            f = 0
            for ch in row:
                if ch.isdigit():
                    f += int(ch)
                    continue
                color = 'w' if ch.isupper() else 'b'
                code = color + ch.upper()
                s = chr(97 + f) + str(rank)
                piece = self.make_piece(code).move_to(self.sq_center(s))
                self.pieces[s] = piece
                self.codes[s] = code
                if ch.upper() == 'K':
                    self.king[color] = s
                army.add(piece)
                f += 1
        self.play(LaggedStart(*[FadeIn(p, shift=DOWN * 0.18, scale=0.85) for p in army],
                              lag_ratio=0.03, run_time=2.2))

    # ---- side panel scaffolding ------------------------------------------ #
    def build_panel(self):
        title = Text("The Immortal Game", font_size=29, color=INK, weight="BOLD")
        title.move_to([BOARD_C[0], 3.55, 0])
        sub = Text("Anderssen   –   Kieseritzky      ·      London 1851",
                   font_size=19, color=MUTED)
        sub.move_to([BOARD_C[0], 3.13, 0])

        divider = Line([NOTE_LEFT, DIV_Y, 0], [6.8, DIV_Y, 0],
                       stroke_color=FAINT, stroke_width=2)

        self.tray_labels = VGroup(
            Text("White's losses", font_size=19, color=WHITE_NAME),
            Text("Black's losses", font_size=19, color=BLACK_NAME),
        )
        self.tray_labels[0].move_to([NOTE_LEFT + 1.05, -1.75, 0])
        self.tray_labels[1].move_to([NOTE_LEFT + 1.05, -2.72, 0])
        self.tray_y = {'w': -2.15, 'b': -3.12}   # 'w' row = White pieces captured

        self.play(FadeIn(title, shift=DOWN * 0.15),
                  FadeIn(sub, shift=DOWN * 0.1), run_time=0.9)
        self.play(Create(divider),
                  LaggedStart(*[FadeIn(l) for l in self.tray_labels], lag_ratio=0.3),
                  run_time=0.7)
        self.panel_static = VGroup(title, sub, divider, self.tray_labels)

    # ====================================================================== #
    # The move engine
    # ====================================================================== #
    def make_badge(self, no, color, san, star, mate):
        dot = Circle(radius=0.11, fill_opacity=1,
                     fill_color=(PIECE_W if color == 'w' else PIECE_B),
                     stroke_color=MUTED, stroke_width=1.4)
        num = Text(f"{no}." if color == 'w' else f"{no}…", font_size=30, color=MUTED)
        col = RED if mate else (GOLD if star else INK)
        sanm = Text(san, font_size=42, color=col, weight="BOLD")
        row = VGroup(dot, num, sanm).arrange(RIGHT, buff=0.22)
        row.move_to([PANEL_CX, BADGE_Y, 0]).set_z_index(15)
        return row

    def highlight_squares(self, frm, to):
        g = VGroup()
        for s in (frm, to):
            m = Square(SQ).set_fill(HL, 0.34).set_stroke(width=0)
            m.move_to(self.sq_center(s)).set_z_index(5)
            g.add(m)
        return g

    def glow_arrow(self, p1, p2, color=GOLD):
        a = Arrow(p1, p2, buff=SQ * 0.30, color=color, stroke_width=8,
                  max_tip_length_to_length_ratio=0.16,
                  max_stroke_width_to_length_ratio=7)
        glow = a.copy().set_stroke(color, width=20, opacity=0.22).set_fill(color, 0.22)
        return VGroup(glow, a).set_z_index(20)

    def tray_slot(self, cap_color):
        idx = self.tray_count[cap_color]
        self.tray_count[cap_color] += 1
        x = TRAY_X0 + idx * TRAY_STEP
        return np.array([x, self.tray_y[cap_color], 0])

    def pulse_king(self, ksq, persist=False):
        ring = Square(SQ * 0.98).move_to(self.sq_center(ksq))
        ring.set_stroke(RED, 5).set_fill(RED, 0.0).set_z_index(6)
        self.play(FadeIn(ring, scale=1.18), run_time=0.24)
        if persist:
            return ring
        self.play(ring.animate.set_stroke(opacity=0.0).scale(1.12), run_time=0.4)
        self.remove(ring)
        return None

    def play_move(self, m):
        frm, to = m['frm'], m['to']
        fc, tc = self.sq_center(frm), self.sq_center(to)
        piece = self.pieces[frm]
        code = self.codes[frm]
        is_knight = code[1] == 'N'
        no = self.ply // 2 + 1

        # --- 1) badge + highlight + (optional) caption -------------------- #
        new_hl = self.highlight_squares(frm, to)
        new_badge = self.make_badge(no, m['color'], m['san'], m['star'], m['mate'])
        pre = [FadeIn(new_hl)]
        if self.hl is not None:
            pre.append(FadeOut(self.hl))
        pre.append(FadeOut(self.badge))
        pre.append(FadeIn(new_badge))
        if m['note']:
            grp = self.wrap(m['note'])
            grp.align_to([NOTE_LEFT, 0, 0], LEFT).align_to([0, NOTE_TOP, 0], UP)
            grp.set_z_index(15)
            pre.append(FadeOut(self.note_grp))
            pre.append(FadeIn(grp))
            self.note_grp = grp
        self.play(*pre, run_time=0.4)
        self.hl, self.badge = new_hl, new_badge

        # --- 2) capture + glide ------------------------------------------- #
        move_anims = []
        captured = self.pieces.get(to)
        if captured is not None:
            cap_color = self.codes[to][0]
            slot = self.tray_slot(cap_color)
            factor = (SQ * 0.34) / captured.height
            captured.set_z_index(9)
            move_anims.append(
                captured.animate.move_to(slot).scale(factor).set_opacity(0.9))
            self.pieces.pop(to)
            self.codes.pop(to)

        if is_knight:
            mover = MoveAlongPath(piece, ArcBetweenPoints(fc, tc, angle=PI * 0.30),
                                  rate_func=smooth)
        else:
            mover = piece.animate(rate_func=smooth).move_to(tc)

        if m['cap']:
            self.play(mover, *move_anims,
                      Flash(tc, color=RED, flash_radius=SQ * 0.62, line_length=0.16,
                            num_lines=12, time_width=0.6),
                      run_time=0.64)
        else:
            self.play(mover, *move_anims, run_time=0.62 if is_knight else 0.55)

        # --- 3) state update ---------------------------------------------- #
        self.pieces.pop(frm)
        self.codes.pop(frm)
        self.pieces[to] = piece
        self.codes[to] = code
        if code[1] == 'K':
            self.king[code[0]] = to

        # --- 4) check / emphasis ------------------------------------------ #
        arrow = None
        if m['arrow']:
            arrow = self.glow_arrow(fc, tc, RED if m['mate'] else GOLD)
            self.play(Create(arrow),
                      Indicate(piece, color=(RED if m['mate'] else GOLD),
                               scale_factor=1.22), run_time=0.7)

        if m['chk'] and not m['mate']:
            self.pulse_king(self.king['w' if m['color'] == 'b' else 'b'])

        # --- 5) reading hold ---------------------------------------------- #
        if m['note']:
            base = min(3.0, 1.15 + len(m['note']) / 46.0)
            if m['star'] >= 2:
                base += 1.4
            self.hold(base)
        else:
            self.hold(0.32)

        if arrow is not None and not m['mate']:
            self.play(FadeOut(arrow), run_time=0.4)
        elif arrow is not None and m['mate']:
            self.arrow_last = arrow   # keep the mating arrow for the finale

        self.ply += 1


# ========================================================================== #
# Intro / Outro cards (house style, chess-flavoured)
# ========================================================================== #
class _Cards(_Base):
    def _writer(self, anchor):
        w = Text("Created by Ptolémé", font_size=26, color=BLACK_NAME)
        w.move_to([anchor[0], anchor[1], 0])
        return w

    def play_intro(self):
        title = Text("The Immortal Game", font_size=56, color=INK, weight="BOLD")
        title.move_to([0, 1.15, 0])
        line = Line([title.get_left()[0] - 0.8, 0, 0],
                    [title.get_right()[0] + 0.8, 0, 0])
        line.next_to(title, DOWN, buff=0.35).set_stroke(GOLD, 3)

        # a white king and a black king slide in to flank the title
        wk = self.make_piece('wK').scale_to_fit_height(0.85).move_to([-8, 1.15, 0])
        bk = self.make_piece('bK').scale_to_fit_height(0.85).move_to([8, 1.15, 0])

        names = VGroup(
            Text("Adolf Anderssen", font_size=30, color=WHITE_NAME, weight="BOLD"),
            Text("vs.", font_size=24, color=MUTED),
            Text("Lionel Kieseritzky", font_size=30, color=BLACK_NAME, weight="BOLD"),
        ).arrange(RIGHT, buff=0.4)
        names.next_to(line, DOWN, buff=0.5)
        venue = Text("London · 1851 · King's Gambit", font_size=24, color=MUTED)
        venue.next_to(names, DOWN, buff=0.3)
        writer = self._writer([0, venue.get_y() - 0.85, 0])

        self.play(Write(title), Create(line), run_time=1.6)
        self.play(wk.animate.next_to(title, LEFT, buff=0.5),
                  bk.animate.next_to(title, RIGHT, buff=0.5),
                  rate_func=rush_from, run_time=1.1)
        self.play(FadeIn(names, shift=UP * 0.15), run_time=0.9)
        self.play(FadeIn(venue), run_time=0.6)
        self.card_wait(1.0)
        self.play(FadeIn(writer, shift=UP * 0.25), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(title, line, wk, bk, names, venue, writer)),
                  run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        header.move_to([0, 0.6, 0])
        line = Line([header.get_left()[0] - 0.8, 0, 0],
                    [header.get_right()[0] + 0.8, 0, 0])
        line.next_to(header, DOWN, buff=0.35).set_stroke(GOLD, 3)
        writer = self._writer([0, line.get_y() - 0.7, 0])
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.8)
        self.play(FadeIn(writer, shift=UP * 0.25), run_time=1.0)
        self.card_wait(1.9)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.2)
        self.card_wait(0.3)


# ========================================================================== #
# The game scene
# ========================================================================== #
class _GameScene(_Cards):
    def play_game(self):
        self.build_board()
        self.build_panel()
        self.place_army()
        self.hold(0.6)

        for m in GAME[:PLIES_CAP]:
            self.play_move(m)

        if PLIES_CAP >= len(GAME):
            self.checkmate_finale()

    # ---- "why it's mate" breakdown + closing card ------------------------ #
    def checkmate_finale(self):
        king_ring = self.pulse_king(MATE_KING, persist=True)

        # mark every escape / capture square the king would love to use
        marks = VGroup()
        for s in MATE_ESCAPES:
            ring = Square(SQ * 0.9).move_to(self.sq_center(s))
            ring.set_stroke(RED, 4).set_fill(RED, 0.14).set_z_index(6)
            cross = VGroup(
                Line(UL, DR).set_length(SQ * 0.5),
                Line(UR, DL).set_length(SQ * 0.5),
            ).set_stroke(RED, 4).move_to(self.sq_center(s)).set_z_index(7)
            marks.add(VGroup(ring, cross))

        # swap the caption to the mate explanation
        note = self.wrap("Every flight square is covered — d8 attacked, "
                         "c7 and e7 by the knight on d5, e8 by the knight on g7. "
                         "No escape.", width=34)
        note.align_to([NOTE_LEFT, 0, 0], LEFT).align_to([0, NOTE_TOP, 0], UP)
        note.set_z_index(15)
        self.play(FadeOut(self.note_grp), FadeIn(note), run_time=0.5)
        self.note_grp = note

        self.play(LaggedStart(*[GrowFromCenter(mk) for mk in marks],
                              lag_ratio=0.25), run_time=1.2)
        self.hold(1.6)

        banner = Text("CHECKMATE", font_size=54, color=RED, weight="BOLD")
        banner.move_to(BOARD_C)
        halo = banner.copy().set_stroke(RED, 14, opacity=0.28).set_fill(opacity=0)
        banner_grp = VGroup(halo, banner).set_z_index(30)
        self.play(FadeIn(banner_grp, scale=1.3), run_time=0.7)
        self.hold(2.2)

        # clear the whole board, then present a clean closing card
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        self.hold(0.3)

        head = Text("“The Immortal Game”", font_size=46, color=GOLD, weight="BOLD")
        head.move_to([0, 2.05, 0])
        summary = self.wrap(
            "White sacrificed a bishop, both rooks and the queen — "
            "then checkmated with a bishop and two knights.",
            fs=30, width=44, color=INK, center=True)
        summary.move_to([0, 0.35, 0])
        foot = Text("Anderssen  –  Kieseritzky   ·   London, 1851",
                    font_size=24, color=MUTED)
        foot.move_to([0, -1.75, 0])
        self.play(FadeIn(head, shift=DOWN * 0.15), run_time=0.9)
        self.play(FadeIn(summary), run_time=0.9)
        self.play(FadeIn(foot, shift=UP * 0.1), run_time=0.7)
        self.hold(3.0)
        self.play(FadeOut(VGroup(head, summary, foot)), run_time=1.0)


# ========================================================================== #
# Public scenes
# ========================================================================== #
class Intro(_GameScene):
    def construct(self):
        self.play_intro()


class Game(_GameScene):
    def construct(self):
        self.play_game()


class Outro(_GameScene):
    def construct(self):
        self.play_outro()


class Immortal(_GameScene):
    """The whole film: intro card → the game → outro card."""

    def construct(self):
        self.play_intro()
        self.play_game()
        self.wipe(0.6)
        self.play_outro()


if __name__ == "__main__":
    Immortal().render()
