"""manimx: the shared house library of the Manim explainer series.

``from manimx import *`` gives a film everything ``from manim import *`` does,
plus the house layer:

* crisp ``Text`` (rendered at >= 60 pt, scaled down) and the house font;
* the palette (``BG INK MUTED FAINT PANEL GOLD GOOD BAD SKY MINT LILAC AMBER``);
* ``Pace`` + ``ExplainerScene`` / ``Explainer3DScene`` / ``ExplainerMixin``
  (pacing, captions, wipes, intro/outro cards, code-line focus);
* glyphs (``chip pill stamp plate arr wire make_tick make_cross dot_label``),
  ``code_panel``, data-as-picture primitives (``heatmap vcells prob_bars
  live_number``) and frame-safety helpers (``keep_inside fit_in_frame``).

See ``.claude/skills/manim-explainer/SKILL.md`` for how to build a film with it
and ``tools/render_lib.sh`` for rendering. Two names intentionally replace
Manim's: ``Text`` (crisp) and ``GOLD`` (the house gold).
"""

import manim as _manim
from manim import *  # noqa: F403

from .code import CODE_FS, COMMENT, FUNC, KW, NUM, PLAIN, STR, code_panel, hl_lines
from .components import (
    arr,
    chip,
    dot_label,
    make_cross,
    make_tick,
    pill,
    plate,
    stamp,
    wire,
)
from .data import heatmap, live_number, prob_bars, vcells
from .layout import (
    CAPTION_W,
    CAPTION_Y,
    HEADER_CLEAR_Y,
    SAFE,
    fit_in_frame,
    keep_inside,
)
from .pacing import Pace, quick_mode
from .palette import (
    ACCENT,
    AMBER,
    BAD,
    BG,
    CODE_BAR,
    CODE_BG,
    FAINT,
    FONT,
    GOLD,
    GOOD,
    INK,
    LILAC,
    MINT,
    MONO,
    MUTED,
    PANEL,
    SKY,
)
from .scene import (
    BYLINE,
    ExplainerCameraScene,
    Explainer3DScene,
    ExplainerMixin,
    ExplainerScene,
    rule_under,
)
from .text import (
    TEXT_BASE,
    BaseText,
    Text,
    _BaseText,
    _safe_t2c,
    _TEXT_BASE,
    clamp_width,
    mono,
    mtext,
    safe_t2c,
    txt,
)

__all__ = [
    # text
    "Text",
    "BaseText",
    "_BaseText",
    "TEXT_BASE",
    "_TEXT_BASE",
    "txt",
    "mono",
    "mtext",
    "safe_t2c",
    "_safe_t2c",
    "clamp_width",
    # palette
    "BG",
    "PANEL",
    "INK",
    "MUTED",
    "FAINT",
    "CODE_BG",
    "CODE_BAR",
    "GOLD",
    "ACCENT",
    "GOOD",
    "BAD",
    "SKY",
    "MINT",
    "LILAC",
    "AMBER",
    "FONT",
    "MONO",
    # pacing + scenes
    "Pace",
    "quick_mode",
    "ExplainerMixin",
    "ExplainerScene",
    "Explainer3DScene",
    "ExplainerCameraScene",
    "rule_under",
    "BYLINE",
    # glyphs, code, data, layout
    "chip",
    "pill",
    "stamp",
    "plate",
    "arr",
    "wire",
    "make_tick",
    "make_cross",
    "dot_label",
    "code_panel",
    "hl_lines",
    "PLAIN",
    "COMMENT",
    "KW",
    "STR",
    "FUNC",
    "NUM",
    "CODE_FS",
    "heatmap",
    "vcells",
    "prob_bars",
    "live_number",
    "SAFE",
    "HEADER_CLEAR_Y",
    "CAPTION_Y",
    "CAPTION_W",
    "keep_inside",
    "fit_in_frame",
]
# ...plus everything `from manim import *` exports (house names above win).
__all__ += sorted({n for n in dir(_manim) if not n.startswith("_")} - set(__all__))
_HOUSE = tuple(__all__[: __all__.index("fit_in_frame") + 1])
