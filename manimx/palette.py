"""The house palette: one dark theme shared by every explainer in the series.

Neutral roles (``BG`` … ``BAD``) are identical in all films. The four hues are
the series' recurring colour *language* (the Transformer's Q/K/V, RBAC's
users/roles, …); give them a semantic alias in your film, e.g.
``Q_C = SKY`` or ``ROLE_C = LILAC``, so the meaning stays readable.

Names deliberately avoid Manim's own colour constants (``BLUE``, ``TEAL``,
``PURPLE``, ``ORANGE``) so a star-import never silently recolours a film.
``GOLD`` is the one intentional exception: the house gold replaces Manim's.
"""

# --- neutrals -------------------------------------------------------------- #
BG = "#0E1117"  # dark slate background
PANEL = "#151A23"  # card / panel fill
INK = "#F5F3EF"  # warm white: body text
MUTED = "#8A93A6"  # secondary text, arrows, axes
FAINT = "#3A4152"  # gridlines, inactive strokes
CODE_BG = "#0A0E15"  # code-panel body
CODE_BAR = "#141C29"  # code-panel title bar

# --- status ---------------------------------------------------------------- #
GOLD = "#FFD166"  # accent, rules under titles, "the one to look at"
ACCENT = GOLD
GOOD = "#3DD68C"  # allowed / correct / cheap
BAD = "#FF5C5C"  # denied / wrong / wasted

# --- the series hues --------------------------------------------------------- #
SKY = "#5B8DEF"  # queries, users, the byline
MINT = "#2EC4B6"  # keys, permissions, data at rest
LILAC = "#C792EA"  # tokens, roles, the hero indirection
AMBER = "#FF8C42"  # attention, danger, heat

# --- type ------------------------------------------------------------------ #
FONT = "Helvetica Neue"  # every Text; set as the default in manimx.text
MONO = "Menlo"  # code, identifiers, numbers that must line up
