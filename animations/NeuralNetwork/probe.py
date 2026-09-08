"""Throwaway probe: validate the shared glyphs / network / flow visually."""
from nn_common import *


class Probe(NNBase):
    def construct(self):
        # row of glyphs + labeled examples
        gl = VGroup(car_glyph(), plane_glyph(), ship_glyph()).arrange(RIGHT, buff=1.0)
        gl.to_edge(UP, buff=0.6)
        self.add(gl)
        exs = VGroup(*[labeled_example(n) for n in ("car", "plane", "ship")]).arrange(RIGHT, buff=0.4)
        exs.next_to(gl, DOWN, buff=0.4).shift(LEFT * 3.2)
        self.add(exs)

        # pixel grid + prob bars
        pg = pixel_grid(DATA.pixel_img, cell=0.16).scale(1.0).move_to([2.2, -0.6, 0])
        self.add(pg)
        pb = prob_bars(DATA.untrained_probs).scale(0.8).next_to(pg, RIGHT, buff=0.8)
        self.add(pb)

        # network
        net = build_network([144, 8, 3], width=4.6, height=2.6).to_edge(DOWN, buff=0.3).shift(LEFT * 3.0)
        net.style_edges(seed=1, settled=True)
        self.add(net)
        self.wait(0.2)
        self.flow(net, color=GOLD, rt=0.5)
        self.flow(net, color=WARN, reverse=True, rt=0.5)
        self.wait(0.3)
