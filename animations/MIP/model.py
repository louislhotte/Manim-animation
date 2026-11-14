"""model.py: the courier problem as a mixed-integer program, solved four ways.

The problem (an orienteering problem with time windows, one or several couriers):

* every courier starts at a known place at minute 0 and has ``SHIFT`` minutes;
* every order pays a fee, and delivering it means riding to its restaurant, waiting
  for the meal, riding to the customer, handing it over;
* a delivery must happen inside the order's time window: not before the meal can be
  there, not after the time promised to the customer or the end of the shift;
* maximise the fees collected.

The model (``demo/course.py`` holds it; the film shows that file's model block and
``solve_gurobi`` executes the very same lines):

    x[i, j] = 1 if a courier rides from stop i straight to order j      (binary)
    t[j]    = the minute order j is delivered                           (continuous)

    maximise   sum of pay[j] * x[i, j]
    subject to each courier leaves at most once,
               each order is delivered at most once,
               an order is left only if it was reached,
               x[i, j] = 1  =>  t[j] >= t[i] + mins[i, j],
               t[j] inside its window.

Cross-checks, all asserted in ``generate_assets.py``:

* ``solve_highs``: the same problem as matrices, through SciPy's HiGHS (big-M
  instead of indicator constraints);
* ``branch_and_bound``: our own branch and bound on the LP relaxation, after our
  own presolve; its tree is the one the film draws;
* ``brute_force``: every feasible course of one courier, enumerated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SHIFT = 60.0  # minutes
PICKUP = 2.0  # minutes at the counter
DROP = 2.0  # minutes at the door
EPS = 1e-6

DEMO = Path(__file__).resolve().parent / "demo" / "course.py"


def model_source():
    """The model block of ``demo/course.py``: the lines the film shows."""
    lines = DEMO.read_text().splitlines()
    a = next(k for k, s in enumerate(lines) if s.startswith("# --- model"))
    b = next(k for k, s in enumerate(lines) if s.startswith("# --- end of model"))
    return lines[a + 1 : b]


@dataclass
class Instance:
    """One problem: ``couriers`` and ``orders`` are lists of stop names; ``mins`` maps
    a ride (i, j) to the minutes between the delivery of i (or the courier's start)
    and the delivery of j; ``early`` / ``late`` bound the delivery minute of j."""

    couriers: list
    orders: list
    pay: dict
    mins: dict
    early: dict
    late: dict
    meta: dict = field(default_factory=dict)

    @property
    def stops(self):
        return [*self.couriers, *self.orders]

    @property
    def rides(self):
        return list(self.mins)

    def lb(self, i):
        return 0.0 if i in self.couriers else self.early[i]

    def ub(self, i):
        return 0.0 if i in self.couriers else self.late[i]


def presolve(inst):
    """What can be decided before any search: a ride that can never fit the windows
    is removed, and a window opens no earlier than the earliest possible arrival.
    Repeated until nothing changes. Returns the smaller instance."""
    early, late, mins = dict(inst.early), dict(inst.late), dict(inst.mins)
    changed = True
    while changed:
        changed = False

        def lb(i):
            return 0.0 if i in inst.couriers else early[i]

        for i, j in list(mins):
            if lb(i) + mins[i, j] > late[j] + 1e-9:
                del mins[i, j]
                changed = True
        for j in inst.orders:
            arrivals = [lb(i) + mins[i, jj] for (i, jj) in mins if jj == j]
            if not arrivals:  # nobody can reach it: it cannot be left either
                for r in [r for r in mins if r[0] == j]:
                    del mins[r]
                    changed = True
            elif min(arrivals) > early[j] + 1e-9:
                early[j] = min(arrivals)
                changed = True
    return Instance(inst.couriers, inst.orders, inst.pay, mins, early, late, inst.meta)


# --------------------------------------------------------------------------- #
# the matrices (HiGHS and our own branch and bound share them)
# --------------------------------------------------------------------------- #
def matrices(inst):
    """max c.z  s.t.  A z <= b,  lo <= z <= hi, with z = (x of every ride, t of every
    order). Returns c, A, b, lo, hi and the two index maps."""
    rides, orders = inst.rides, inst.orders
    xi = {r: k for k, r in enumerate(rides)}
    ti = {j: len(rides) + k for k, j in enumerate(orders)}
    n = len(rides) + len(orders)
    c = np.zeros(n)
    for (_, j), k in xi.items():
        c[k] = inst.pay[j]
    rows, rhs = [], []

    def row(coefs, b):
        r = np.zeros(n)
        for k, v in coefs:
            r[k] += v
        rows.append(r)
        rhs.append(b)

    for cour in inst.couriers:  # a courier leaves at most once
        row([(xi[r], 1.0) for r in rides if r[0] == cour], 1.0)
    for j in orders:  # an order is delivered at most once
        row([(xi[r], 1.0) for r in rides if r[1] == j], 1.0)
    for j in orders:  # an order is left only if it was reached
        row(
            [(xi[r], 1.0) for r in rides if r[0] == j]
            + [(xi[r], -1.0) for r in rides if r[1] == j],
            0.0,
        )
    for i, j in rides:  # x = 1  =>  t[j] >= t[i] + mins   (big-M, as tight as it gets)
        big = inst.ub(i) + inst.mins[i, j] - inst.lb(j)
        if big <= EPS:
            continue  # true whatever x is
        coefs = [(xi[i, j], big), (ti[j], -1.0)]
        if i in ti:
            coefs.append((ti[i], 1.0))
        row(coefs, big - inst.mins[i, j])
    lo = np.zeros(n)
    hi = np.ones(n)
    for j, k in ti.items():
        lo[k], hi[k] = inst.early[j], inst.late[j]
    return c, np.array(rows), np.array(rhs), lo, hi, xi, ti


def courses_of(inst, x):
    """The chosen rides ``{(i, j): 0/1}`` as one list of orders per courier."""
    nxt = {i: j for (i, j), v in x.items() if v > 0.5}
    out = {}
    for c in inst.couriers:
        seq, i = [], c
        while i in nxt:
            i = nxt[i]
            seq.append(i)
        out[c] = seq
    return out


def timing(inst, courier, seq):
    """Delivery minutes of ``seq`` ridden as early as possible, or None if a
    delivery misses its window."""
    t, i, out = 0.0, courier, []
    for j in seq:
        t = max(t + inst.mins[i, j], inst.early[j])
        if t > inst.late[j] + 1e-9:
            return None
        out.append(t)
        i = j
    return out


def check(inst, courses):
    """A plan is real: every order at most once, every delivery inside its window."""
    seen = [j for seq in courses.values() for j in seq]
    assert len(seen) == len(set(seen)), "an order is delivered twice"
    for c, seq in courses.items():
        assert timing(inst, c, seq) is not None, f"{c} misses a window"
    return True


def revenue(inst, courses):
    return round(sum(inst.pay[j] for seq in courses.values() for j in seq), 2)


# --------------------------------------------------------------------------- #
# 1. Gurobi: the model as the film shows it
# --------------------------------------------------------------------------- #
def solve_gurobi(inst, log=None, record=False, **params):
    """Run the model block of ``demo/course.py`` on ``inst``. With ``record`` the
    solve is repeated with a callback that notes every new best plan and how the
    two bounds move (the first, plain run is the one whose log is kept)."""
    import gurobipy as gp
    from gurobipy import GRB

    env = gp.Env(params={"LogToConsole": 0, **({"LogFile": str(log)} if log else {})})
    for k, v in params.items():
        env.setParam(k, v)
    stops = inst.stops
    space = {
        "gp": _WithEnv(gp, env),
        "GRB": GRB,
        "couriers": inst.couriers,
        "orders": inst.orders,
        "stops": stops,
        "rides": inst.rides,
        "pay": inst.pay,
        "mins": inst.mins,
        "early": {i: inst.lb(i) for i in stops},
        "late": {i: inst.ub(i) for i in stops},
    }
    exec("\n".join(model_source()), space)  # noqa: S102 (our own file, shown on screen)
    m, x = space["m"], space["x"]

    out = {
        "status": m.Status,
        "optimal": m.Status == GRB.OPTIMAL,
        "obj": round(m.ObjVal, 2) if m.SolCount else None,
        "bound": round(m.ObjBound, 4),
        "gap": m.MIPGap if m.SolCount else None,
        "nodes": int(m.NodeCount),
        "runtime": m.Runtime,
        "work": m.Work,
        "x": {r: round(x[r].X) for r in inst.rides} if m.SolCount else {},
        "vars": m.NumVars,
        "binaries": m.NumBinVars,
        "rows": m.NumConstrs,
        "indicators": m.NumGenConstrs,
    }
    if record:
        rides = inst.rides
        xs = [x[r] for r in rides]
        plans, trace = [], []

        def hook(mod, where):
            if where == GRB.Callback.MIPSOL:
                vals = mod.cbGetSolution(xs)
                plans.append(
                    {
                        "time": mod.cbGet(GRB.Callback.RUNTIME),
                        "obj": mod.cbGet(GRB.Callback.MIPSOL_OBJ),
                        "nodes": int(mod.cbGet(GRB.Callback.MIPSOL_NODCNT)),
                        "x": {
                            r: 1 for r, v in zip(rides, vals, strict=True) if v > 0.5
                        },
                    }
                )
            elif where == GRB.Callback.MIP:
                trace.append(
                    (
                        mod.cbGet(GRB.Callback.RUNTIME),
                        mod.cbGet(GRB.Callback.MIP_OBJBST),
                        mod.cbGet(GRB.Callback.MIP_OBJBND),
                        int(mod.cbGet(GRB.Callback.MIP_NODCNT)),
                    )
                )

        # silence the second run without touching the log file: ``LogFile = ""``
        # here drops whatever the first run had not flushed yet (the district's log
        # lost its last third, summary included)
        m.Params.OutputFlag = 0
        m.reset()
        m.optimize(hook)
        assert round(m.ObjVal, 2) == out["obj"], (m.ObjVal, out["obj"])
        out["plans"], out["trace"] = plans, trace
        out["runtime_recorded"] = m.Runtime
    m.dispose()
    env.dispose()
    return out


class _WithEnv:
    """``gp`` whose ``Model(name)`` is created in our environment (log file, no
    console output), so that the model block itself stays exactly as shown."""

    def __init__(self, gp, env):
        self._gp, self._env = gp, env

    def Model(self, name=""):  # noqa: N802 (gurobipy's name)
        return self._gp.Model(name, env=self._env)

    def __getattr__(self, k):
        return getattr(self._gp, k)


# --------------------------------------------------------------------------- #
# 2. HiGHS (inside SciPy): the same problem as matrices
# --------------------------------------------------------------------------- #
def solve_highs(inst, time_limit=None):
    from scipy.optimize import Bounds, LinearConstraint, milp

    c, A, b, lo, hi, xi, ti = matrices(inst)
    integrality = np.zeros(len(c))
    integrality[: len(xi)] = 1
    opts = {"time_limit": time_limit} if time_limit else {}
    res = milp(
        -c,
        constraints=LinearConstraint(A, -np.inf, b),
        integrality=integrality,
        bounds=Bounds(lo, hi),
        options=opts,
    )
    x = {r: round(res.x[k]) for r, k in xi.items()} if res.x is not None else {}
    return {
        "optimal": res.status == 0,
        "obj": round(-res.fun, 2) if res.x is not None else None,
        "x": x,
    }


# --------------------------------------------------------------------------- #
# 3. our own branch and bound (the tree the film draws)
# --------------------------------------------------------------------------- #
def branch_and_bound(inst, max_nodes=200_000):
    """Plain branch and bound on the LP relaxation of ``inst`` (presolve it first):
    no cutting planes, no heuristics.

    * branch on the most fractional ride: one child takes it, the other leaves it;
    * plunge ("take it" first, depth first) until a first real plan gives a floor,
      then always open the branch with the highest ceiling;
    * a branch whose ceiling is not above the floor is closed unexplored.

    Returns the nodes in the order they were visited. Each has ``parent``,
    ``depth``, ``take`` (1 / 0: the decision that leads to it), ``ride`` (the ride
    that decision is about), ``kind`` (branch / plan / pruned / infeasible), ``lp``
    (was a relaxation solved), ``bound``, ``x`` (the non-zero rides), and the
    ``floor`` and ``ceiling`` of the whole search after it."""
    from scipy.optimize import linprog

    c, A, b, lo0, hi0, xi, ti = matrices(inst)
    rides = inst.rides
    nx = len(rides)
    nodes, floor, best_x = [], -math.inf, None
    todo = [(None, None, {}, math.inf)]  # (parent, (ride, take), fixings, ceiling)
    while todo and len(nodes) < max_nodes:
        if floor == -math.inf:
            k = len(todo) - 1  # plunge
        else:  # best ceiling first; the most recent of equals
            k = max(range(len(todo)), key=lambda q: (todo[q][3], q))
        parent, fix, fixed, inherited = todo.pop(k)
        node = {
            "id": len(nodes),
            "parent": parent,
            "depth": 0 if parent is None else nodes[parent]["depth"] + 1,
            "ride": fix[0] if fix else None,
            "take": fix[1] if fix else None,
            "lp": False,
            "x": {},
        }
        nodes.append(node)
        if inherited <= floor + EPS:  # closed without solving anything
            node.update(kind="pruned", bound=inherited)
        else:
            lo, hi = lo0.copy(), hi0.copy()
            for r, v in fixed.items():
                lo[xi[r]] = hi[xi[r]] = v
            res = linprog(
                -c, A_ub=A, b_ub=b, bounds=np.column_stack([lo, hi]), method="highs"
            )
            node["lp"] = True
            if res.status != 0:
                node.update(kind="infeasible", bound=None)
            else:
                z = res.x
                bound = -float(res.fun)
                node["bound"] = bound
                node["x"] = {rides[q]: float(z[q]) for q in range(nx) if z[q] > 1e-7}
                node["t"] = {j: float(z[q]) for j, q in ti.items()}
                frac = np.abs(z[:nx] - np.rint(z[:nx]))
                q = int(np.argmax(frac))
                if bound <= floor + EPS:
                    node["kind"] = "pruned"
                elif frac[q] < 1e-6:  # a whole plan: a real course
                    node["kind"] = "plan"
                    floor, best_x = bound, {r: round(z[xi[r]]) for r in rides}
                    node["incumbent"] = True
                else:
                    node.update(kind="branch", var=rides[q])
                    todo.append(
                        (node["id"], (rides[q], 0), {**fixed, rides[q]: 0}, bound)
                    )
                    todo.append(
                        (node["id"], (rides[q], 1), {**fixed, rides[q]: 1}, bound)
                    )
        node["floor"] = None if floor == -math.inf else floor
        open_best = max((s[3] for s in todo), default=-math.inf)
        node["ceiling"] = max(open_best, floor) if todo or best_x else None
    return {
        "nodes": nodes,
        "obj": round(floor, 2) if best_x else None,
        "x": best_x,
        "complete": not todo,
        "lps": sum(1 for n in nodes if n["lp"]),
    }


def relaxation(inst):
    """The LP relaxation at the root: (value, x)."""
    from scipy.optimize import linprog

    c, A, b, lo, hi, xi, _ = matrices(inst)
    res = linprog(-c, A_ub=A, b_ub=b, bounds=np.column_stack([lo, hi]), method="highs")
    return -float(res.fun), {r: float(res.x[k]) for r, k in xi.items()}


# --------------------------------------------------------------------------- #
# 4. brute force (one courier): every feasible course
# --------------------------------------------------------------------------- #
def brute_force(inst, keep=False):
    assert len(inst.couriers) == 1
    c0 = inst.couriers[0]
    best = {"obj": 0.0, "seq": [], "ties": 1}
    count = 0
    every = []

    def walk(i, t, seq, pay):
        nonlocal count
        for j in inst.orders:
            if j in seq or (i, j) not in inst.mins:
                continue
            tj = max(t + inst.mins[i, j], inst.early[j])
            if tj > inst.late[j] + 1e-9:
                continue
            count += 1
            p = round(pay + inst.pay[j], 2)
            if keep:
                every.append(([*seq, j], p))
            if p > best["obj"] + 1e-9:
                best.update(obj=p, seq=[*seq, j], ties=1)
            elif abs(p - best["obj"]) < 1e-9:
                best["ties"] += 1
            walk(j, tj, [*seq, j], p)

    walk(c0, 0.0, [], 0.0)
    out = {**best, "feasible": count, "sequences": sequences(len(inst.orders))}
    if keep:
        out["all"] = every
    return out


def sequences(n):
    """How many ways to pick some of ``n`` orders and put them in a sequence."""
    return sum(math.perm(n, k) for k in range(1, n + 1))


def greedy(inst, rule="pay"):
    """What a dispatcher does by instinct, one order at a time: among the (courier,
    order) pairs that still fit, take the best-paid order (``pay``) or the one that
    can be delivered soonest (``soon``). Repeat until nothing fits."""
    taken = set()
    state = {c: (c, 0.0) for c in inst.couriers}
    out = {c: [] for c in inst.couriers}
    while True:
        cands = []
        for c, (i, t) in state.items():
            for j in inst.orders:
                if j in taken or (i, j) not in inst.mins:
                    continue
                tj = max(t + inst.mins[i, j], inst.early[j])
                if tj <= inst.late[j] + 1e-9:
                    key = (-inst.pay[j], tj) if rule == "pay" else (tj, -inst.pay[j])
                    cands.append((key, c, j, tj))
        if not cands:
            return out
        _, c, j, tj = min(cands, key=lambda q: q[0])
        taken.add(j)
        out[c].append(j)
        state[c] = (j, tj)
