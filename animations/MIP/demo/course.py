"""The courier problem as a mixed-integer program, in gurobipy.

This is the model the film shows, character for character (the block between the
two markers), and the one ``generate_assets.py`` runs for real.

    python course.py                # Lea's hour: one courier, eight orders
    python course.py district       # the 11th arrondissement: 8 couriers, 32 orders

Data (``../assets/story.json``, written by ``generate_assets.py``, at full precision:
with the same Gurobi version and machine, the log printed here is the one the film
shows for Lea's hour, and the district explores the same 31,577 nodes):

    couriers, orders   names of the stops; stops = couriers + orders
    rides              every pair (i, j): "after stop i, deliver order j next"
    pay[j]             what order j pays, in euros
    mins[i, j]         minutes between the delivery of i and the delivery of j
                       (ride to j's restaurant, pick up, ride to the customer, hand over)
    early[j], late[j]  the window in which order j can be delivered (minute of the
                       shift); a courier's own stop has early = late = 0

Needs gurobipy (``pip install gurobipy``). The size-limited licence that comes with
the package is enough: both models stay under 2,000 variables.
"""

import json
import sys
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

which = sys.argv[1] if len(sys.argv) > 1 else "hero"
data = json.loads((Path(__file__).parent / "../assets/story.json").read_text())[which]
couriers, orders = data["couriers"], [o["name"] for o in data["orders"]]
stops = couriers + orders
pay = {o["name"]: o["pay"] for o in data["orders"]}
mins = {tuple(k.split("|")): v for k, v in data["mins"].items()}
rides = list(mins)
early = {
    **{c: 0.0 for c in couriers},
    **{o["name"]: o["early"] for o in data["orders"]},
}
late = {**{c: 0.0 for c in couriers}, **{o["name"]: o["late"] for o in data["orders"]}}

# fmt: off
# --- model -------------------------------------------------------------------
m = gp.Model("courses")
x = m.addVars(rides, vtype=GRB.BINARY)
t = m.addVars(stops, lb=early, ub=late)
m.setObjective(gp.quicksum(
    pay[j] * x[i, j] for i, j in rides),
    GRB.MAXIMIZE)
m.addConstrs(x.sum(c, "*") <= 1
             for c in couriers)
m.addConstrs(x.sum("*", j) <= 1
             for j in orders)
m.addConstrs(
    x.sum(j, "*") <= x.sum("*", j)
    for j in orders)
m.addConstrs(
    (x[i, j] == 1) >>
    (t[j] >= t[i] + mins[i, j])
    for i, j in rides)
m.optimize()
# --- end of model ------------------------------------------------------------
# fmt: on

# The courses, ridden as early as possible (the solver only has to place every
# delivery somewhere inside its window: t[j].X is one valid minute, not the earliest).
nxt = {i: j for i, j in rides if x[i, j].X > 0.5}
for c in couriers:
    course, i, minute = [], c, 0.0
    while i in nxt:
        j = nxt[i]
        minute = max(minute + mins[i, j], early[j])
        assert minute <= late[j] + 1e-6
        clock = (
            f"{20 + int(minute) // 60}:{int(minute) % 60:02d}"  # as the film shows it
        )
        course.append(f"{j} ({clock}, {pay[j]:.2f} EUR)")
        i = j
    print(f"{c}: " + (" -> ".join(course) or "stays put"))
print(f"revenue {m.ObjVal:.2f} EUR, proven optimal: {m.Status == GRB.OPTIMAL}")
