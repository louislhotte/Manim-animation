"""Pacing: how long things stay on screen.

Two separate knobs, because they answer different questions:

* ``delay``  scales ``beat(t)``, the small pauses *between* animation steps.
* ``read``   is the absolute hold of ``read(k)`` after a block of text lands,
  so a first-time viewer can actually read it (~3 s per caption).

plus ``anim_slow`` (every ``play()`` run_time is stretched by it, so motion is
never abrupt) and ``end_hold`` (``settle()`` holds a finished scene before the
wipe). ``MX_QUICK=1`` collapses everything for fast layout iterations; the
real cadence is the non-quick values.

Rule of thumb: a line of prose needs ~2 s on screen, a formula / code panel /
dense diagram 3-4 s *after* it finishes drawing. When in doubt, add a beat.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def quick_mode(prefix: str = "MX") -> bool:
    """True when ``<prefix>_QUICK=1`` (or the global ``MX_QUICK=1``) is set."""
    return os.environ.get(f"{prefix}_QUICK", os.environ.get("MX_QUICK", "0")) == "1"


def _env_float(prefix: str, name: str, default: float) -> float:
    raw = os.environ.get(f"{prefix}_{name}", os.environ.get(f"MX_{name}"))
    return float(raw) if raw not in (None, "") else default


@dataclass(frozen=True)
class Pace:
    """Pacing for one film. Attach it to the base scene as ``pace = Pace(...)``.

    ``stretch`` selects how ``play()`` applies ``anim_slow``:
      * ``"given"``: scale an explicit ``run_time=``; leave defaults alone.
      * ``"infer"``: also infer the run_time from the animations and scale it.
      * ``None``: never touch run_time (films tuned without stretching).
    ``card`` is the ``card_wait`` multiplier as ``(quick, normal)``.
    """

    quick: bool = False
    delay: float = 1.1
    read: float = 3.0
    anim_slow: float = 1.3
    end_hold: float = 2.4
    card: tuple[float, float] = (0.3, 1.0)
    stretch: str | None = "given"

    @classmethod
    def from_env(
        cls,
        prefix: str = "MX",
        *,
        delay: float = 1.1,
        read: float = 3.0,
        anim_slow: float = 1.3,
        end_hold: float = 2.4,
        card: tuple[float, float] = (0.3, 1.0),
        stretch: str | None = "given",
    ) -> Pace:
        """House defaults, overridable per film and per run.

        Env overrides (film prefix first, then the global ``MX_``):
        ``<P>_QUICK``, ``<P>_DELAY``, ``<P>_READ``.
        """
        q = quick_mode(prefix)
        return cls(
            quick=q,
            delay=_env_float(prefix, "DELAY", 0.28 if q else delay),
            read=_env_float(prefix, "READ", 0.35 if q else read),
            anim_slow=1.0 if q else anim_slow,
            end_hold=0.2 if q else end_hold,
            card=card,
            stretch=stretch,
        )
