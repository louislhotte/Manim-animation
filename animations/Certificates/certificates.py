"""Certificates: how a server proves who it is.

A film made to be narrated: the voice explains, the screen shows the objects (a key,
a name, a card with four fields, a seal, a fingerprint as a row of coloured cells) and
almost no sentences. Flat scenes, no camera.

STORYBOARD (question | hero visual | what moves)

    1 A key is not a name   why is a public key not enough?   a browser, and two
                            servers that both say "shop.example" | two keys travel
                            to the browser, a question mark; then a name and a key
                            are bound in a card, sealed, and the lock closes
    2 A signed statement    what is in a certificate, and what is a signature?   the
                            card, large, and its fingerprint: 32 cells, one per byte
                            of a real SHA-256 | the four fields are hashed, the
                            authority's private key turns the fingerprint into a seal,
                            the seal is checked against the fingerprint; one letter
                            changes and all 32 bytes change; a forger's key fails
    3 A chain of trust      who vouches for the authority?   three cards one above
                            the other, and the roots a device ships with | a card
                            appears for each issuer, the root points at itself, one
                            cell of the store lights up, keys fly down to open seals
    4 What the browser      what happens on every connection?   three gates | the
      checks                card passes them; three broken cards stop, each with
                            Chrome's error name; a copied card cannot sign the
                            handshake's fresh random numbers; lifetimes shrink from
                            398 days to 47, a loop renews

Motif: the certificate card (a key, a name, an issuer, a seal). A hollow key is
public, a solid key is private. A seal has the colour of its signer. Blue is the
browser, orange the shop, purple the issuing authority, green the root and whatever
is trusted, gold the thing to look at, red what fails.

What is real: see ``facts.py``. The certificates are an illustration written by hand
(the screen says so); the fingerprint is a real SHA-256 of the card's four lines; the
checks of scene 4 are evaluated on the fields; the lifetimes are those of
CA/Browser Forum ballot SC-081v3, cited on screen. An independent review of every
line and label was applied (README, "Two simplifications").

Scenes render alone (``./render.sh seal --quick --check``) or stitched
(``./render.sh``). Pacing: ``CERT_WPS`` (the narrator's words per second), ``CERT_QUICK``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from manimx import *

from kit import *  # noqa: F403
import facts as F

# One note per scene: each says what is real in the picture above it, no more.
NOTE = "Illustration: certificates drawn for the film."
SEAL_NOTE = (
    "Illustration. The fingerprint is the real SHA-256 of the card's four lines "
    "(the key as a placeholder)."
)
CHECK_NOTE = "Illustration: certificates drawn for the film. Error names as Chrome prints them."
LIFE_NOTE = (
    "Maximum lifetime of a public TLS server certificate: "
    "CA/Browser Forum ballot SC-081v3 (2025)."
)
ROOT_NOTE = (
    f"{F.ROOTS_HERE} roots: /etc/ssl/cert.pem, the macOS bundle for command-line tools. "
    "Browsers ship their own lists."
)


class _Common(NarratedMixin):
    pace = Pace.from_env("CERT", read=2.6, delay=1.0, anim_slow=1.0, end_hold=2.0)
    TITLE = "Certificates"
    SUBTITLE = "How a server proves who it is"
    TAGLINE = "a name, a key, and a signature you can check"
    RECAP = "A name, a key, a seal, and a root you already hold."
    TRACE_ENV = "CERT_TRACE"
    WPS = float(os.environ.get("CERT_WPS", 2.6))  # the narrator: 156 words a minute
    VO_PAD = 0.7

    def intro_emblem(self):
        g = seal(CA_C, r=0.4)
        pad = Rectangle(width=0.7, height=0.1).set_stroke(opacity=0).set_fill(opacity=0)
        low = Rectangle(width=0.1, height=0.3).set_stroke(opacity=0).set_fill(opacity=0)
        return VGroup(g, pad.next_to(g, RIGHT, buff=0), low.next_to(g, DOWN, buff=0))

    def chapter(self, label, color=GOLD, note=None):
        """The animations that bring in the section header and the source note."""
        head = self.section_header(label, color).set_z_index(12)
        anims = [FadeIn(head, shift=DOWN * 0.2)]
        self.foot = None
        if note:
            self.foot = self.note(note)
            anims.append(FadeIn(self.foot))
        return anims

    def fly(self, mob, target, rt=0.7, **kw):
        """A copy of ``mob`` flies to ``target`` and dissolves there: "this goes in"."""
        ghost = mob.copy().set_z_index(8)
        return Succession(
            ghost.animate(run_time=rt, **kw).move_to(target).set_opacity(0.0),
            FadeOut(ghost, run_time=0.02),
        )


class _Flat(_Common, Scene):
    # ====================================================================== #
    # 1 · A key is not a name
    # ====================================================================== #
    def scene_claim(self):
        br = browser((-4.2, -0.1))
        lock0 = lock_icon(MUTED, shut=False).move_to(br.lock_at)
        shop = server_icon().move_to([5.45, 1.45, 0])
        fake = server_icon().move_to([5.45, -1.75, 0])
        shop_tag = name_tag(F.HOST).next_to(shop, UP, buff=0.14)
        fake_tag = name_tag(F.HOST).next_to(fake, UP, buff=0.14)
        shop_key = key_icon(SHOP_C).next_to(shop, LEFT, buff=0.38)
        fake_key = key_icon(BAD).next_to(fake, LEFT, buff=0.38)
        a = br.box.get_right()
        wire1 = Line(a + UP * 0.3, shop_key.get_left() + LEFT * 0.2).set_stroke(FAINT, width=3)
        wire2 = Line(a + DOWN * 0.3, fake_key.get_left() + LEFT * 0.2).set_stroke(FAINT, width=3)
        p1, p2 = br.page + LEFT * 1.0, br.page + RIGHT * 1.0

        # ---- 1.1 a key, then another -------------------------------------------------- #
        self.voice(
            "Your browser connects to shop dot example, and a server answers with its "
            "public key. But anyone can make a key, and anyone can claim a name."
        )
        self.play(
            *self.chapter("1 · A key is not a name", SHOP_C, NOTE),
            FadeIn(br, shift=RIGHT * 0.2),
            FadeIn(lock0),
            run_time=0.8,
        )
        self.cue("a server answers", ambient=lambda rt: [Throb(lock0, rt, amp=0.35, period=0.8)])
        self.play(
            Create(wire1),
            FadeIn(shop, shift=LEFT * 0.2),
            FadeIn(shop_tag),
            FadeIn(shop_key, scale=0.5),
            run_time=0.7,
        )
        k1 = shop_key.copy()
        self.play(k1.animate.move_to(p1), run_time=self.span("But anyone", floor=0.9, cap=1.6))
        self.cue("anyone can make a key")
        self.play(FadeIn(fake, shift=LEFT * 0.2), FadeIn(fake_key, scale=0.5), run_time=0.6)
        self.cue("claim a name", ambient=lambda rt: [Throb(fake_key, rt, amp=0.12)])
        self.play(FadeIn(fake_tag, scale=1.3), Create(wire2), run_time=0.6)
        k2 = fake_key.copy()
        self.play(k2.animate.move_to(p2), run_time=0.9)
        self.hold(ambient=lambda rt: throbs([shop_tag, fake_tag], rt, amp=0.06))

        # ---- 1.2 which one? --------------------------------------------------------------- #
        self.voice(
            "Two servers, two keys, the same claim. Nothing here tells the browser "
            "which one is the shop."
        )
        ask = Text("?", font_size=84, color=LOOK_C, weight="BOLD").move_to(br.page + UP * 0.05)
        self.play(
            k1.animate.shift(LEFT * 0.3),
            k2.animate.shift(RIGHT * 0.3),
            FadeIn(ask, scale=1.6),
            run_time=0.6,
        )
        self.cue("the same claim", ambient=lambda rt: throbs([k1, k2], rt, amp=0.1))
        self.play(glow(shop_tag[0], LOOK_C, 5), glow(fake_tag[0], LOOK_C, 5), run_time=1.0)
        self.hold(ambient=lambda rt: throbs([ask, k1, k2], rt, amp=0.2))

        # ---- 1.3 a certificate ------------------------------------------------------------- #
        self.voice(
            "A certificate settles it. It is a statement that this key belongs to this "
            "name, signed by someone the browser already trusts."
        )
        card = mini_cert(F.HOST, F.ISSUER, SHOP_C, CA_C, (0.72, 1.45), w=4.6)
        stamp_ = card.seal
        card.remove(stamp_)
        slot = seal_slot(0.34).move_to(stamp_)
        self.play(FadeIn(card, shift=UP * 0.2), FadeIn(slot), run_time=0.6)
        self.cue("this key belongs", ambient=lambda rt: [Throb(slot, rt, amp=0.35, period=0.8)])
        self.play(
            self.fly(shop_key, card.key.get_center()),
            self.fly(shop_tag, card.title.get_center()),
            glow(card.box, LOOK_C),
        )
        self.cue("signed by someone")
        self.play(FadeOut(slot, run_time=0.2), FadeIn(stamp_, scale=2.2, run_time=0.45))
        self.play(glow(stamp_[0], CA_C, 5), run_time=0.8)
        self.cue("already trusts")
        lock1 = lock_icon(GOOD).move_to(br.lock_at)
        self.play(
            VGroup(card, stamp_).animate.scale(0.74).move_to(br.page + UP * 0.2),
            FadeOut(k1),
            FadeOut(ask),
            k2.animate.set_opacity(0.3).move_to(br.page + DOWN * 0.82 + RIGHT * 1.3),
            run_time=1.0,
        )
        no = make_cross(BAD, sw=7, scale=1.2).move_to(k2)
        self.play(
            FadeOut(lock0, run_time=0.2),
            FadeIn(lock1, scale=1.6, run_time=0.4),
            FadeIn(no, scale=1.5, run_time=0.4),
        )
        self.settle(ambient=lambda rt: [Throb(lock1, rt, amp=0.2)])
        self.wipe()

    # ====================================================================== #
    # 2 · A signed statement
    # ====================================================================== #
    def scene_seal(self):
        assert F.BYTES_CHANGED == len(F.FP) == 32, "the narration says nothing matches"
        cert = Cert((-4.05, -0.1))
        x0, cell = -0.7, 0.225
        ya, yb = 0.55, -1.0
        end = x0 + 32 * cell

        def caption(text, y, color=MUTED):
            return put(line_txt(text, fs=18, color=color), x0, y + 0.55)

        def verdict(text, color, mark_):
            icon = mark_(color, sw=8, scale=1.15).move_to([x0 + 0.32, yb - 0.98, 0])
            words = put(line_txt(text, fs=23, color=color, weight="MEDIUM"), x0 + 0.85, yb - 0.98)
            return icon, words

        def fields_in(rt=0.9, name=None):
            """The four values go into the hash (``name``: the name as it now reads)."""
            values = [name or cert.values[0], *cert.values[1:]]
            return [
                self.fly(v, [x0 + 0.4, ya, 0], rt=rt, rate_func=rate_functions.ease_in_quad)
                for v in values
            ]

        def cells_in(row, rt=0.9, lag=0.03):
            return LaggedStart(*[FadeIn(c, scale=0.3) for c in row], lag_ratio=lag, run_time=rt)

        # ---- 2.1 four fields ----------------------------------------------------------------- #
        self.voice(
            "Inside, four fields matter: the name, the public key, the dates between "
            "which it is valid, and who issued it."
        )
        self.play(
            *self.chapter("2 · A signed statement", CA_C, SEAL_NOTE),
            FadeIn(cert.box, shift=UP * 0.2),
            FadeIn(cert.title),
            Create(cert.rule),
            FadeIn(cert.slot),
            run_time=0.8,
        )
        hot = None
        for i, phrase in enumerate(("the name", "the public key", "the dates", "who issued")):
            self.cue(phrase, ambient=(lambda rt: [Throb(hot, rt, amp=0.02)]) if hot else None)
            new = cert.row_box(i)
            show = [
                FadeIn(cert.labels[i], shift=RIGHT * 0.15),
                FadeIn(cert.values[i], shift=RIGHT * 0.15),
            ]
            if hot is None:
                hot = new
                self.play(FadeIn(hot), *show, run_time=0.45)
            else:
                self.play(Transform(hot, new), *show, run_time=0.45)
        self.hold(ambient=lambda rt: [Throb(hot, rt, amp=0.02)])

        # ---- 2.2 hashed, then signed --------------------------------------------------------- #
        self.voice(
            "The issuer is a certificate authority. Once it has checked that the shop "
            "controls the name, it hashes those fields into a fingerprint, and signs the "
            "fingerprint with its own private key. That signature is the seal."
        )
        ca_box = RoundedRectangle(width=5.0, height=1.0, corner_radius=0.18)
        ca_box.set_stroke(CA_C, width=3).set_fill(mix(CA_C, BG, 0.86), opacity=1)
        ca_box.move_to([2.9, 2.15, 0])
        ca_name = put(
            line_txt("certificate authority", fs=22, color=CA_C, weight="BOLD"),
            ca_box.get_left()[0] + 0.34, 2.15,
        )  # fmt: skip
        ca_key = key_icon(CA_C, private=True).move_to([ca_box.get_right()[0] - 0.76, 2.15, 0])
        self.play(
            FadeOut(hot),
            FadeIn(ca_box, shift=DOWN * 0.2),
            FadeIn(ca_name),
            FadeIn(ca_key, scale=0.5),
            run_time=0.7,
        )
        self.cue("controls the name", ambient=lambda rt: [Throb(ca_key, rt, amp=0.12)])
        ok = make_tick(CA_C, sw=6, scale=1.0).move_to([cert.box.get_right()[0] - 0.5, cert.ys[0], 0])
        self.play(glow(cert.row_box(0, CA_C), CA_C, 4), FadeIn(ok, scale=1.6), run_time=0.9)
        self.cue("it hashes those fields")
        fp_a = strip(F.FP, cell, left=(x0, ya))
        cap_a = caption("fingerprint of the four fields (SHA-256)", ya)
        hexa = line_txt(" ".join(f"{b:02x}" for b in F.FP[:8]) + " …", fs=17, font=MONO, color=MUTED)
        hexa.shift([end - hexa.get_right()[0], ya - 0.52 - hexa.get_center()[1], 0])
        self.play(*fields_in(0.9), FadeIn(cap_a), run_time=0.9)
        self.play(cells_in(fp_a), FadeIn(hexa), run_time=self.span("and signs", floor=0.9, cap=1.6))
        self.cue("signs the fingerprint")
        the_seal = seal(CA_C, 0.42).move_to(cert.seal_at)
        press = ca_key.copy()
        self.play(press.animate.move_to([x0 + 16 * cell, ya + 0.02, 0]).scale(1.2), run_time=0.6)
        pack = VGroup(fp_a, press)
        self.play(
            pack.animate.scale(0.08).move_to(cert.seal_at),
            FadeOut(cap_a),
            FadeOut(hexa),
            FadeOut(cert.slot),
            run_time=0.8,
        )
        self.remove(pack)
        self.play(FadeIn(the_seal, scale=2.4), run_time=0.4)
        self.cue("That signature", ambient=lambda rt: [Throb(the_seal, rt, amp=0.1)])
        self.play(glow(the_seal[0], LOOK_C, 5), run_time=1.0)
        self.hold(ambient=lambda rt: [Throb(the_seal, rt, amp=0.1)])

        # ---- 2.3 check the seal against the fingerprint -------------------------------------- #
        # The picture is how an RSA signature is checked (the public key gives back the
        # fingerprint that was signed). The words stay true for every scheme: the seal
        # is checked against the fingerprint.
        self.voice(
            "Anyone holding the authority's public key can check the seal against the "
            "fingerprint. They agree: the certificate is intact."
        )
        pub = key_icon(CA_C).move_to(ca_key.get_center() + DOWN * 1.1)
        self.play(FadeOut(ok), TransformFromCopy(ca_key, pub), run_time=0.6)
        self.cue("check the seal", ambient=lambda rt: [Throb(pub, rt, amp=0.12)])
        fp_b = strip(F.FP, cell, left=(x0, yb))
        cap_b = caption("fingerprint the seal was made from", yb, CA_C)
        fp_b.save_state()
        fp_b.scale(0.08).move_to(cert.seal_at)
        # beside the issuer's name, against the seal: whose key opens whose seal
        self.play(pub.animate.scale(0.6).move_to(cert.seal_at + LEFT * 0.98), run_time=0.6)
        self.play(Restore(fp_b), FadeIn(cap_b), run_time=0.8)
        self.cue("against the fingerprint")
        fp_a = strip(F.FP, cell, left=(x0, ya))
        cap_a = caption("fingerprint of the four fields (SHA-256)", ya)
        self.play(*fields_in(0.7), FadeIn(cap_a), run_time=0.7)
        self.play(cells_in(fp_a, 0.7), run_time=0.7)
        self.cue("They agree")
        scan = VGroup(  # one stroke per row: nothing sweeps across the caption between them
            *[Line([x0, y_ + 0.36, 0], [x0, y_ - 0.36, 0]) for y_ in (ya, yb)]
        ).set_stroke(LOOK_C, width=4)
        same, same_t = verdict(f"{len(F.FP)} of 32 bytes match", GOOD, make_tick)
        self.play(FadeIn(scan), run_time=0.15)
        self.play(scan.animate.shift(RIGHT * 32 * cell), run_time=1.0, rate_func=linear)
        self.play(FadeOut(scan), FadeIn(same, scale=1.6), FadeIn(same_t, shift=RIGHT * 0.1), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(same, rt, amp=0.15)])

        # ---- 2.4 one letter ------------------------------------------------------------------ #
        self.voice(
            "Change a single letter, and nothing matches any more. And without the "
            "authority's private key, nobody can make a new seal."
        )
        k = next(i for i, (c, d) in enumerate(zip(F.HOST, F.TAMPERED, strict=True)) if c != d)
        old = cert.letter(k)
        patch = Rectangle(width=old.width + 0.07, height=0.4).set_stroke(width=0)
        patch.set_fill(PANEL, opacity=1).move_to([old.get_center()[0], cert.ys[0], 0])
        new = line_txt(F.TAMPERED[k], fs=22, font=MONO, color=BAD)
        new.move_to([old.get_center()[0], cert.ys[0], 0])
        self.cue("a single letter")
        self.play(FadeIn(patch, run_time=0.15), FadeIn(new, scale=1.8, run_time=0.4))
        changed = Cert((-4.05, -0.1), F.TAMPERED).values[0]  # what is hashed now
        self.play(*fields_in(0.6, name=changed), FadeOut(same), FadeOut(same_t), run_time=0.6)
        olds = [c.get_fill_color() for c in fp_a]
        news = [byte_color(b) for b in F.FP_BAD]

        def recolour(m, a):
            for i, (c, o, n) in enumerate(zip(m, olds, news, strict=True)):
                c.set_fill(interpolate_color(o, n, float(np.clip(a * 1.7 - i / 32 * 0.7, 0, 1))))

        diff, diff_t = verdict(f"{F.BYTES_CHANGED} of 32 bytes differ", BAD, make_cross)
        # the seal keeps its signer's colour: it is still the authority's, it no longer fits
        broken = make_cross(BAD, sw=9, scale=1.7).move_to(cert.seal_at)
        self.play(UpdateFromAlphaFunc(fp_a, recolour), run_time=1.0)
        self.play(
            FadeIn(diff, scale=1.6),
            FadeIn(diff_t, shift=RIGHT * 0.1),
            FadeIn(broken, scale=1.5),
            run_time=0.5,
        )
        self.cue(
            "nobody can make",
            ambient=lambda rt: [Throb(broken, rt, amp=0.12), Throb(fp_a, rt, amp=0.03, period=0.9)],
        )
        under_seal = cert.seal_at + DOWN * 1.07  # below the card, under its seal
        forger = key_icon(BAD, private=True).move_to(under_seal + RIGHT * 1.6)
        nope = make_cross(INK, sw=8, scale=1.5).move_to(under_seal)
        self.play(FadeIn(forger, shift=LEFT * 0.4), run_time=0.4)
        self.play(forger.animate.move_to(under_seal), run_time=0.5)
        self.play(
            Wiggle(broken, scale_value=1.15, rotation_angle=0.05 * TAU),
            forger.animate.set_opacity(0.4),
            FadeIn(nope, scale=1.6),
            run_time=0.7,
        )
        self.settle(
            ambient=lambda rt: [Throb(nope, rt, amp=0.2), Throb(fp_a, rt, amp=0.03, period=0.9)]
        )
        self.wipe()

    # ====================================================================== #
    # 3 · A chain of trust
    # ====================================================================== #
    def scene_chain(self):
        cx, w = -4.1, 4.8
        leaf = mini_cert(F.HOST, F.ISSUER, SHOP_C, CA_C, (cx, -1.95), w=w)
        mid = mini_cert(F.ISSUER, F.ROOT, CA_C, ROOT_C, (cx, 0.05), w=w)
        root = mini_cert(F.ROOT, F.ROOT, ROOT_C, ROOT_C, (cx, 2.05), w=w)
        sx = leaf.seal.get_center()[0]
        up1 = arr([sx, leaf.box.get_top()[1], 0], [sx, mid.box.get_bottom()[1], 0], color=CA_C, sw=5, buff=0.06)
        up2 = arr([sx, mid.box.get_top()[1], 0], [sx, root.box.get_bottom()[1], 0], color=ROOT_C, sw=5, buff=0.06)
        loop = Arc(radius=0.3, start_angle=-0.8 * PI, angle=1.6 * PI, color=ROOT_C)
        loop.set_stroke(ROOT_C, width=5).set_fill(opacity=0)
        loop.move_arc_center_to([root.box.get_right()[0] + 0.38, 2.05, 0])
        loop.add_tip(tip_length=0.18, tip_width=0.18)
        grid = trust_grid((3.55, 0.05))
        store = line_txt("roots this device already holds", fs=21, weight="MEDIUM")
        store.move_to([3.55, grid.get_top()[1] + 0.5, 0])
        count = line_txt(f"{F.ROOTS_HERE} in this Mac's command-line bundle", fs=19, color=ROOT_C)
        count.move_to([3.55, grid.get_bottom()[1] - 0.46, 0])
        mine = grid[48]  # first column: the link reaches it without crossing the store
        here = mine.copy().set_fill(ROOT_C, opacity=1).scale(1.25)
        way = Line(loop.get_right() + RIGHT * 0.25, here.get_left() + LEFT * 0.1)
        link = DashedLine(way.get_start(), way.get_end(), dash_length=0.13)
        link.set_stroke(ROOT_C, width=3.5)

        # ---- 3.1 who vouches for the authority? ------------------------------------------------ #
        self.voice(
            "But who vouches for the authority? Another certificate: its key is signed "
            "by a root authority. And the root signs itself."
        )
        self.play(
            *self.chapter("3 · A chain of trust", ROOT_C, NOTE),
            FadeIn(leaf, shift=UP * 0.2),
            run_time=0.8,
        )
        who = SurroundingRectangle(leaf.by, buff=0.09, corner_radius=0.08, color=LOOK_C)
        who.set_stroke(LOOK_C, width=3).set_fill(LOOK_C, opacity=0.12)
        self.play(FadeIn(who), run_time=0.4)
        self.cue(
            "Another certificate",
            ambient=lambda rt: [Throb(who, rt, amp=0.1, period=0.9), Throb(leaf, rt, amp=0.03, period=0.9)],
        )
        self.play(FadeIn(mid, shift=DOWN * 0.25), GrowArrow(up1), FadeOut(who), run_time=0.8)
        self.cue("a root authority", ambient=lambda rt: [Throb(up1, rt, amp=0.08)])
        self.play(FadeIn(root, shift=DOWN * 0.25), GrowArrow(up2), run_time=0.8)
        self.cue("signs itself", ambient=lambda rt: [Throb(up2, rt, amp=0.08)])
        self.play(Create(loop), glow(root.box, ROOT_C), run_time=1.0)
        self.hold(ambient=lambda rt: [Throb(loop, rt, amp=0.1)])

        # ---- 3.2 the root is already there ----------------------------------------------------- #
        self.voice(
            "That would prove nothing, except for one thing. The root is already on "
            "your device: operating systems and browsers ship with more than a hundred "
            "of them."
        )
        self.cue("The root is already", ambient=lambda rt: [Throb(loop, rt, amp=0.14)])
        foot2 = self.note(ROOT_NOTE)
        self.play(
            LaggedStart(*[FadeIn(c, scale=0.4) for c in grid], lag_ratio=0.012),
            FadeIn(store, shift=DOWN * 0.1),
            FadeOut(self.foot, run_time=0.3),
            Succession(Wait(0.35), FadeIn(foot2, run_time=0.4)),
            run_time=self.span("more than a hundred", floor=1.2, cap=2.2),
        )
        self.play(FadeIn(count, shift=UP * 0.1), run_time=0.4)
        self.play(FadeIn(here, scale=2.2), Create(link), run_time=0.8)
        self.hold(ambient=lambda rt: [Throb(here, rt, amp=0.3)])

        # ---- 3.3 the climb ----------------------------------------------------------------------- #
        self.voice(
            "So the browser climbs. Each seal is checked with the key of the certificate "
            "above, until it reaches a root it already holds."
        )
        tx = leaf.box.get_right()[0] + 0.48
        ticks = [make_tick(GOOD, sw=7, scale=1.05).move_to([tx, y, 0]) for y in (-1.95, 0.05)]
        self.cue("Each seal")
        self.play(self.fly(mid.key, leaf.seal.get_center(), rt=0.7), glow(leaf.box, LOOK_C), run_time=0.9)
        self.play(FadeIn(ticks[0], scale=1.7), run_time=0.3)
        self.cue("the certificate above")
        self.play(self.fly(root.key, mid.seal.get_center(), rt=0.7), glow(mid.box, LOOK_C), run_time=0.9)
        self.play(FadeIn(ticks[1], scale=1.7), run_time=0.3)
        self.cue("a root it already holds")
        dot = glow_dot(LOOK_C, r=0.09)
        held = make_tick(GOOD, sw=7, scale=1.05).move_to(here.get_center() + DOWN * 0.55 + LEFT * 0.45)
        self.play(glow(root.box, LOOK_C), Travel(dot, way, run_time=0.9), run_time=0.9)
        self.play(ripple(here, color=GOOD, buff=0.08, grow=1.9), FadeIn(held, scale=1.7), run_time=0.8)
        self.settle(ambient=lambda rt: [Throb(here, rt, amp=0.3), *throbs(ticks, rt, amp=0.12)])
        self.wipe()

    # ====================================================================== #
    # 4 · What the browser checks
    # ====================================================================== #
    def scene_checks(self):
        names = ("chain", "dates", "name")
        y = 0.25
        gates = [
            gate(x, word, y=y)
            for x, word in zip((-4.25, 0.0, 4.25), ("trusted root", "dates", "name"), strict=True)
        ]
        proof = (
            "it leads to a root on this device",
            f"today is {F.day(F.TODAY)}",
            f"you typed {F.HOST}",
        )

        def token(at, seal_c=CA_C, k=0.56, name=F.HOST, issuer=F.ISSUER):
            t = mini_cert(name, issuer, SHOP_C, seal_c, (0, 0), w=4.8).scale(k)
            return t.move_to(at).set_z_index(6)

        def under(i, text, dy, **kw):
            return keep_inside(line_txt(text, **kw).move_to([gates[i].x, y + dy, 0]))

        # ---- 4.1 three checks ------------------------------------------------------------------- #
        self.voice(
            "On every connection, the browser checks at least three things. The chain "
            "reaches a root it trusts. Today is inside the validity dates. The name "
            "matches the address you typed."
        )
        self.play(*self.chapter("4 · What the browser checks", CLIENT_C, CHECK_NOTE), run_time=0.6)
        self.play(
            LaggedStart(*[FadeIn(g, shift=UP * 0.25) for g in gates], lag_ratio=0.5),
            run_time=self.span("The chain reaches", floor=1.5, cap=3.4),
        )
        assert all(F.checks().values())
        tok = token([gates[0].x, y, 0])
        lit, notes = [], []
        for i, phrase in enumerate(("a root it trusts", "the validity dates", "The name matches")):
            self.cue(phrase, ambient=(lambda rt: [Throb(tok, rt, amp=0.05)]) if i else None)
            lamp, why = lamp_on(gates[i], GOOD), under(i, proof[i], -1.75, fs=19, color=MUTED)
            if i == 0:
                self.play(FadeIn(tok, shift=RIGHT * 0.5), run_time=0.6)
            else:
                self.play(tok.animate.move_to([gates[i].x, y, 0]), run_time=0.6)
            self.play(
                FadeIn(lamp, scale=1.8),
                FadeIn(why, shift=UP * 0.1),
                glow(gates[i].arch, GOOD),
                run_time=0.6,
            )
            lit.append(lamp)
            notes.append(why)
        self.hold(ambient=lambda rt: [*throbs(lit, rt, amp=0.3), Throb(tok, rt, amp=0.08)])

        # ---- 4.2 three ways to fail ------------------------------------------------------------- #
        self.voice(
            "Fail any one of them, and the browser stops you: an issuer it does not "
            "know, a date that has passed, or a name that does not match."
        )
        self.play(*[FadeOut(m) for m in (tok, *lit, *notes)], run_time=0.5)
        reasons = {
            "chain": f"no root on this device vouches for {F.BROKEN['chain']['issuer']}",
            "dates": f"expired on {F.day(F.EXPIRED_ON)}",
            "name": f"{F.TAMPERED} is not {F.HOST}",
        }
        shown = []
        # one clause per failure, long enough for its error name to be read
        phrases = ("an issuer it does not", "a date that has passed", "a name that does not")
        for i, (check, phrase) in enumerate(zip(names, phrases, strict=True)):
            assert not F.checks(**F.BROKEN[check])[check]
            if i == 0:  # "fail any one of them": each gate can turn red
                self.cue(
                    phrase,
                    ambient=lambda rt: [
                        LaggedStart(*[glow(g.arch, BAD, 5) for g in gates], lag_ratio=0.45, run_time=rt)
                    ],
                )
            else:
                self.cue(phrase)
            wrong = F.BROKEN[check]  # the card shows what is wrong with it, when it can
            bad = token(
                [gates[0].x, y, 0],
                seal_c=MUTED if check == "chain" else CA_C,
                name=wrong.get("name", F.HOST),
                issuer=wrong.get("issuer", F.ISSUER),
            )
            red = lamp_on(gates[i], BAD)
            chip_ = keep_inside(error_chip(F.ERRORS[check], [gates[i].x, y - 1.8, 0]))
            why = line_txt(reasons[check], fs=18, color=MUTED)
            keep_inside(why.move_to([chip_.get_center()[0], y - 2.45, 0]))
            greens = [lamp_on(gates[j], GOOD) for j in range(i)]
            if i == 0:
                self.play(*[FadeOut(m) for m in shown], FadeIn(bad, shift=RIGHT * 0.5), run_time=0.45)
            else:
                self.play(
                    *[FadeOut(m) for m in shown],
                    bad.animate.move_to([gates[i].x, y, 0]),
                    *[FadeIn(g) for g in greens],
                    run_time=0.45,
                )
            self.play(
                FadeIn(red, scale=1.8),
                FadeIn(chip_, shift=UP * 0.1),
                FadeIn(why),
                glow(gates[i].arch, BAD),
                run_time=0.55,
            )
            shown = [bad, red, chip_, why, *greens]
        self.hold(ambient=lambda rt: [Throb(shown[2], rt, amp=0.04)])

        # ---- 4.3 a copy is not enough ----------------------------------------------------------- #
        self.voice(
            "One last thing: a certificate is public, so anyone can copy it. That is why "
            "the server must also sign this handshake, fresh random numbers included, "
            "with the private key that never leaves it."
        )
        br = browser((-4.4, -0.3), w=4.2, h=3.0)
        lock = lock_icon(MUTED, shut=False).move_to(br.lock_at)
        shop = server_icon(1.3).move_to([5.6, 1.45, 0])
        fake = server_icon(1.3).move_to([5.6, -1.75, 0])
        priv = key_icon(SHOP_C, private=True).next_to(shop, LEFT, buff=0.3)
        c1 = token([1.85, 1.45, 0])
        c2_home = np.array([1.85, -1.75, 0.0])
        a = br.box.get_right()
        w1 = Line(a + UP * 0.3, c1.get_left() + LEFT * 0.15).set_stroke(FAINT, width=3)
        w2 = Line(a + DOWN * 0.3, c2_home + LEFT * (c1.width / 2 + 0.15)).set_stroke(FAINT, width=3)
        self.play(*[FadeOut(m) for m in (*shown, *gates)], run_time=0.5)
        self.play(
            FadeIn(br, shift=RIGHT * 0.2),
            FadeIn(lock),
            FadeIn(shop),
            FadeIn(fake),
            FadeIn(priv, scale=0.5),
            FadeIn(c1),
            Create(w1),
            Create(w2),
            run_time=0.8,
        )
        self.cue("anyone can copy it", ambient=lambda rt: [Throb(c1, rt, amp=0.06)])
        c2 = c1.copy()
        self.play(c2.animate.move_to(c2_home), run_time=0.9)
        self.cue("fresh random numbers", ambient=lambda rt: [Throb(c2, rt, amp=0.06)])
        ask = strip(F.CHALLENGE, 0.26, 0.4).move_to(br.page)
        self.play(LaggedStart(*[FadeIn(c, scale=0.3) for c in ask], lag_ratio=0.08), run_time=0.6)
        q1, q2 = ask.copy(), ask.copy()
        # the numbers travel to the servers: a private key signs where it lives
        at1 = np.array([4.5, shop.get_bottom()[1] - 0.38, 0.0])
        at2 = np.array([4.5, fake.get_bottom()[1] - 0.38, 0.0])
        self.play(q1.animate.move_to(at1), q2.animate.move_to(at2), run_time=0.9)
        self.cue("with the private key")
        sig = seal(SHOP_C, 0.26).move_to(q1.get_right() + RIGHT * 0.4)
        self.play(Indicate(priv, color=INK, scale_factor=1.35), FadeIn(sig, scale=2.2), run_time=0.9)
        yes = make_tick(GOOD, sw=7, scale=1.0).move_to(br.page + UP * 0.55 + RIGHT * 1.55)
        no = make_cross(BAD, sw=7, scale=1.0).move_to(br.page + DOWN * 0.55 + RIGHT * 1.55)
        none = line_txt("no private key", fs=20, color=BAD, weight="MEDIUM")
        none.shift([q2.get_left()[0] - 0.3 - none.get_right()[0], at2[1] - none.get_center()[1], 0])
        self.play(
            VGroup(q1, sig).animate.scale(0.85).move_to(br.page + UP * 0.55 + LEFT * 0.25),
            FadeIn(none, shift=UP * 0.1),
            run_time=0.9,
        )
        shut = lock_icon(GOOD).move_to(br.lock_at)
        self.play(
            FadeIn(yes, scale=1.6),
            q2.animate.scale(0.85).move_to(br.page + DOWN * 0.55 + LEFT * 0.25).set_opacity(0.35),
            run_time=0.7,
        )
        self.play(FadeIn(no, scale=1.6), FadeOut(lock, run_time=0.2), FadeIn(shut, scale=1.5), run_time=0.4)
        self.hold(ambient=lambda rt: [Throb(priv, rt, amp=0.15)])

        # ---- 4.4 shorter every year ------------------------------------------------------------- #
        self.voice(
            "And a site's certificate expires on purpose, sooner and sooner: two hundred "
            "days at most in twenty twenty-six, forty-seven from twenty twenty-nine. So "
            "renewal has to be automated: a program proves it controls the name, and "
            "collects a fresh certificate."
        )
        life = self.note(LIFE_NOTE)
        self.play(
            *[FadeOut(m) for m in self.mobjects if m.z_index < 12],
            FadeOut(self.foot),
            run_time=0.5,
        )
        unit, left = 7.0 / 398, -2.9
        rows = []
        for i, (start, days) in enumerate(F.MAX_DAYS.items()):
            ry = 1.7 - 1.05 * i
            now = days == F.LIMIT_TODAY
            when = line_txt(
                f"{'since' if start <= F.TODAY else 'from'} {start:%B %Y}",
                fs=20, color=INK if now else MUTED,
            )  # fmt: skip
            when.shift([left - 0.3 - when.get_right()[0], ry - when.get_center()[1], 0])
            bar = Rectangle(width=days * unit, height=0.55).set_stroke(width=0)
            bar.set_fill(LOOK_C if now else STEEL, opacity=1.0 if now else 0.55)
            bar.move_to([left + days * unit / 2, ry, 0])
            value = put(
                line_txt(f"{days} days", fs=23, weight="BOLD", color=LOOK_C if now else INK),
                left + days * unit + 0.25, ry,
            )  # fmt: skip
            rows.append((when, bar, value))
        self.play(
            FadeIn(life),
            *[FadeIn(r[0], shift=RIGHT * 0.15) for r in rows[:2]],
            *[GrowFromEdge(r[1], LEFT) for r in rows[:2]],
            *[FadeIn(r[2]) for r in rows[:2]],
            run_time=self.span("two hundred", floor=1.2, cap=2.6),
        )
        self.cue("forty-seven", ambient=lambda rt: [Throb(rows[1][2], rt, amp=0.1)])
        self.play(
            *[FadeIn(r[0], shift=RIGHT * 0.15) for r in rows[2:]],
            *[GrowFromEdge(r[1], LEFT) for r in rows[2:]],
            *[FadeIn(r[2]) for r in rows[2:]],
            run_time=1.0,
        )
        self.cue("So renewal", ambient=lambda rt: [Throb(rows[3][2], rt, amp=0.08)])
        turn = Arc(radius=0.4, start_angle=0.25 * PI, angle=1.5 * PI, color=GOOD)
        turn.set_stroke(GOOD, width=6).set_fill(opacity=0)
        centre = np.array([rows[3][2].get_right()[0] + 1.0, rows[3][1].get_center()[1], 0.0])
        turn.move_arc_center_to(centre)
        turn.add_tip(tip_length=0.22, tip_width=0.22)
        self.play(FadeIn(turn, scale=0.5), run_time=0.4)

        def turning(rt):
            return Rotate(turn, angle=-TAU * rt / 1.6, about_point=centre, rate_func=linear, run_time=rt)

        self.cue("collects a fresh", ambient=lambda rt: [turning(rt)])
        fresh = token(centre + RIGHT * 2.3, k=0.5)
        self.play(FadeIn(fresh, shift=RIGHT * 0.4, scale=0.6), turning(0.7), run_time=0.7)
        self.settle(ambient=lambda rt: [turning(rt), Throb(fresh, rt, amp=0.07)])
        self.wipe()


# ---- renderable scenes ---------------------------------------------------------------- #
class Intro(_Flat):
    def construct(self):
        self.over_card(
            "Certificates. How does a server prove who it is? With a name, a key, and "
            "a signature that anyone can check."
        )
        self.play_intro()


class Claim(_Flat):
    def construct(self):
        self.scene_claim()


class Seal(_Flat):
    def construct(self):
        self.scene_seal()


class Chain(_Flat):
    def construct(self):
        self.scene_chain()


class Checks(_Flat):
    def construct(self):
        self.scene_checks()


class Outro(_Flat):
    def construct(self):
        self.play_outro()
