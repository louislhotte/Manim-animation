"""sim.py: a small, honest model of what Terraform does with the film's example.

No Terraform binary and no cloud account are involved (the film was built without
downloading either). Instead this module *computes* everything the film shows from
the real configuration in ``demo/``:

* it parses the ``resource`` blocks of ``demo/main.tf`` and the references between
  them, and builds the dependency graph from those references;
* it keeps the three things Terraform reconciles as plain dictionaries: the
  desired configuration, the **state** (address -> id + recorded attributes) and a
  pretend **cloud** (id -> real attributes);
* ``plan`` refreshes the state from the cloud, diffs it against the configuration
  and classifies every resource (create / update in place / replace / destroy), the
  way Terraform does; ``apply`` walks the graph, runs what is ready in parallel and
  records the new ids in the state;
* the formatters print those results in the Terraform CLI's own wording
  (``# aws_instance.web[2] will be created``, ``Plan: 1 to add, ...``).

What is illustrative: resource ids (random, seeded) and durations (typical orders of
magnitude, see ``SECONDS``). What is computed: the graph, the walk order, every
plan and every count. The scenes assert the facts they state.
"""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

DEMO = Path(__file__).resolve().parent / "demo"
UNKNOWN = "(known after apply)"

# Arguments whose change cannot be applied to a live resource (the provider marks
# them "ForceNew"): Terraform must destroy the resource and create a new one.
FORCE_NEW = {
    "aws_vpc": {"cidr_block"},
    "aws_subnet": {"vpc_id", "cidr_block"},
    "aws_security_group": {"name", "vpc_id"},
    "aws_instance": {"ami", "subnet_id"},
    "aws_s3_bucket": {"bucket", "bucket_prefix"},
}
ID_PREFIX = {
    "aws_vpc": "vpc-",
    "aws_subnet": "subnet-",
    "aws_security_group": "sg-",
    "aws_instance": "i-",
}
# The AWS API call behind each create (what the provider sends for one block).
API_CALL = {
    "aws_vpc": "CreateVpc",
    "aws_subnet": "CreateSubnet",
    "aws_security_group": "CreateSecurityGroup",
    "aws_instance": "RunInstances",
    "aws_s3_bucket": "CreateBucket",
}
# Illustrative durations in seconds (typical orders of magnitude on AWS, not measured).
SECONDS = {
    "create": {
        "aws_vpc": 2,
        "aws_subnet": 1,
        "aws_security_group": 2,
        "aws_instance": 13,
        "aws_s3_bucket": 2,
    },
    "update": {"aws_instance": 31},
    "delete": {
        "aws_vpc": 1,
        "aws_subnet": 1,
        "aws_security_group": 1,
        "aws_instance": 30,
        "aws_s3_bucket": 1,
    },
}
PARALLELISM = 10  # Terraform's default for -parallelism


# --------------------------------------------------------------------------- #
# the configuration: blocks, arguments, references
# --------------------------------------------------------------------------- #
@dataclass
class Block:
    type: str
    name: str
    lines: list[str]  # the block's source lines, verbatim
    args: dict[str, str] = field(default_factory=dict)  # argument -> source text
    refs: list[str] = field(default_factory=list)  # addresses it references

    @property
    def address(self) -> str:
        return f"{self.type}.{self.name}"

    @property
    def count(self) -> int | None:
        return int(self.args["count"]) if "count" in self.args else None

    def instances(self) -> list[str]:
        n = self.count
        if n is None:
            return [self.address]
        return [f"{self.address}[{i}]" for i in range(n)]


_HEAD = re.compile(r'^resource "(\w+)" "(\w+)" \{$')
_ARG = re.compile(r"^  (\w+)\s*=\s*(.+)$")
_REF = re.compile(r"\b(aws_\w+)\.(\w+)\.\w+")


def parse(text: str) -> list[Block]:
    """The ``resource`` blocks of a Terraform file (the subset of HCL the film uses:
    one level of arguments, lists, references)."""
    blocks, cur, pending = [], None, None
    for raw in text.splitlines():
        if cur is None:
            m = _HEAD.match(raw)
            if m:
                cur = Block(m.group(1), m.group(2), [raw])
            continue
        cur.lines.append(raw)
        if raw == "}":
            blocks.append(cur)
            cur = None
            continue
        if pending is not None:  # inside a multi-line list
            cur.args[pending] += " " + raw.strip()
            if raw.strip() == "]":
                pending = None
            continue
        m = _ARG.match(raw)
        if m:
            cur.args[m.group(1)] = m.group(2).strip()
            if m.group(2).strip() == "[":
                pending = m.group(1)
    for b in blocks:
        for t, n in _REF.findall("\n".join(b.lines[1:])):
            a = f"{t}.{n}"
            if a not in b.refs:
                b.refs.append(a)
    return blocks


def with_arg(blocks: list[Block], address: str, arg: str, value: str) -> list[Block]:
    """A copy of the configuration with one argument edited (what "change the file"
    means). The block's source line is rewritten too, keeping its alignment."""
    out = copy.deepcopy(blocks)
    b = next(b for b in out if b.address == address)
    old = b.args[arg]
    b.args[arg] = value
    for i, line in enumerate(b.lines):
        m = _ARG.match(line)
        if m and m.group(1) == arg:
            b.lines[i] = line[: line.index("=") + 2] + value
            break
    else:
        raise KeyError(f"{address} has no single-line argument {arg} (was {old})")
    return out


def graph(blocks: list[Block]) -> dict[str, list[str]]:
    """address -> the addresses it depends on (its references)."""
    known = {b.address for b in blocks}
    g = {b.address: [r for r in b.refs if r in known] for b in blocks}
    for a, deps in g.items():
        assert a not in deps, f"{a} references itself"
    return g


def ranks(g: dict[str, list[str]]) -> dict[str, int]:
    """Longest path from a root: resources of equal rank can be built together."""
    memo: dict[str, int] = {}

    def rank(a: str) -> int:
        if a not in memo:
            memo[a] = 1 + max((rank(d) for d in g[a]), default=-1)
        return memo[a]

    return {a: rank(a) for a in g}


def base(address: str) -> str:
    """``aws_instance.web[1]`` -> ``aws_instance.web``."""
    return address.split("[")[0]


def rtype(address: str) -> str:
    return address.split(".")[0]


def sort_key(address: str):
    """Terraform lists resources by address, instance keys in numeric order."""
    m = re.match(r"(.+)\[(\d+)\]$", address)
    return (m.group(1), int(m.group(2))) if m else (address, -1)


# --------------------------------------------------------------------------- #
# the pretend cloud and the state
# --------------------------------------------------------------------------- #
class Cloud:
    """id -> the real attributes of an object. Ids are random but seeded."""

    def __init__(self, seed: int = 11):
        self.objects: dict[str, dict] = {}
        self._rng = random.Random(seed)

    def new_id(self, rtype_: str, attrs: dict) -> str:
        if rtype_ == "aws_s3_bucket":  # a bucket's id is its name
            if "bucket" in attrs:
                return attrs["bucket"]
            # bucket_prefix: the provider appends a unique suffix (a timestamp)
            return attrs["bucket_prefix"] + "".join(
                self._rng.choices("0123456789", k=26)
            )
        # like real AWS ids: a prefix, then 17 hex digits starting with 0
        return (
            ID_PREFIX[rtype_]
            + "0"
            + "".join(self._rng.choices("0123456789abcdef", k=16))
        )

    def create(self, rtype_: str, attrs: dict) -> str:
        oid = self.new_id(rtype_, attrs)
        assert oid not in self.objects, oid
        self.objects[oid] = dict(attrs)
        return oid


def _literal(src: str):
    s = src.strip()
    if s.startswith('"'):
        return s.strip('"')
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return None


def desired(
    blocks: list[Block], state: dict, replaced: frozenset = frozenset()
) -> dict:
    """address -> the attributes the configuration asks for, references resolved
    through the state where the target already exists (else ``UNKNOWN``)."""

    def resolve(src: str):
        lit = _literal(src)
        if lit is not None:
            return lit
        found = [f"{t}.{n}" for t, n in _REF.findall(src)]
        vals = [
            state[a]["id"] if a in state and a not in replaced else UNKNOWN
            for a in found
        ]
        return vals if src.strip().startswith("[") else vals[0]

    out = {}
    for b in blocks:
        attrs = {k: resolve(v) for k, v in b.args.items() if k != "count"}
        for addr in b.instances():
            out[addr] = dict(attrs)
    return out


@dataclass
class Action:
    address: str
    kind: str  # create | update | replace | delete
    changes: dict  # attribute -> (before, after)

    @property
    def symbol(self) -> str:
        return {"create": "+", "update": "~", "replace": "-/+", "delete": "-"}[
            self.kind
        ]

    @property
    def headline(self) -> str:
        what = {
            "create": "will be created",
            "update": "will be updated in-place",
            "replace": "must be replaced",
            "delete": "will be destroyed",
        }[self.kind]
        return f"# {self.address} {what}"

    @property
    def resource_line(self) -> str:
        t, n = base(self.address).split(".")
        return f'{self.symbol} resource "{t}" "{n}" {{'

    def change_lines(self) -> list[str]:
        """``~ attr = before -> after`` for every changed argument (spacing condensed;
        the real CLI pads every name to the longest attribute of the resource)."""
        out = []
        for k, (a, b) in self.changes.items():
            q = lambda v: v if v == UNKNOWN else f'"{v}"'  # noqa: E731
            line = f"~ {k} = {q(a)} -> {q(b)}"
            if self.kind == "replace" and k in FORCE_NEW[rtype(self.address)]:
                line += " # forces replacement"
            out.append(line)
        return out


@dataclass
class Plan:
    actions: list[Action]
    drift: list[tuple[str, str]]  # (address, "changed" | "deleted") found by refresh
    refreshed: dict  # the state after reading the real objects

    def count(self, *kinds) -> int:
        return sum(a.kind in kinds for a in self.actions)

    @property
    def summary(self) -> str:
        if not self.actions:
            return "No changes. Your infrastructure matches the configuration."
        add = self.count("create", "replace")
        chg = self.count("update")
        rm = self.count("delete", "replace")
        return f"Plan: {add} to add, {chg} to change, {rm} to destroy."

    def of(self, address: str) -> Action:
        return next(a for a in self.actions if a.address == address)


def plan(blocks: list[Block], state: dict, cloud: Cloud) -> Plan:
    """Refresh the state from the cloud, then diff it against the configuration."""
    refreshed, drift = {}, []
    for addr, entry in state.items():
        real = cloud.objects.get(entry["id"])
        if real is None:
            drift.append((addr, "deleted"))
            continue
        if real != entry["attrs"]:
            drift.append((addr, "changed"))
        refreshed[addr] = {"id": entry["id"], "attrs": dict(real)}

    want = desired(blocks, refreshed)
    # a reference to a resource that must be replaced is unknown until it exists again
    for _ in range(len(blocks)):
        repl = frozenset(
            base(a)
            for a, w in want.items()
            if a in refreshed
            and any(
                refreshed[a]["attrs"].get(k) != v and k in FORCE_NEW[rtype(a)]
                for k, v in w.items()
            )
        )
        again = desired(blocks, refreshed, repl)
        if again == want:
            break
        want = again

    actions = []
    for addr in sorted(set(want) | set(refreshed), key=sort_key):
        if addr not in refreshed:
            actions.append(
                Action(addr, "create", {k: (None, v) for k, v in want[addr].items()})
            )
        elif addr not in want:
            actions.append(Action(addr, "delete", {}))
        else:
            have = refreshed[addr]["attrs"]
            ch = {
                k: (have.get(k), v) for k, v in want[addr].items() if have.get(k) != v
            }
            if ch:
                forced = any(k in FORCE_NEW[rtype(addr)] for k in ch)
                actions.append(Action(addr, "replace" if forced else "update", ch))
    return Plan(actions, drift, refreshed)


@dataclass
class Event:
    address: str
    kind: str  # create | update | delete
    t0: int
    t1: int
    id: str

    @property
    def start_line(self) -> str:
        verb = {"create": "Creating", "update": "Modifying", "delete": "Destroying"}[
            self.kind
        ]
        tail = "" if self.kind == "create" else f" [id={self.id}]"
        return f"{self.address}: {verb}...{tail}"

    @property
    def done_line(self) -> str:
        secs = f"{self.t1 - self.t0}s"
        if self.kind == "create":
            return f"{self.address}: Creation complete after {secs} [id={self.id}]"
        if self.kind == "update":
            return f"{self.address}: Modifications complete after {secs} [id={self.id}]"
        return f"{self.address}: Destruction complete after {secs}"


def apply(blocks: list[Block], state: dict, cloud: Cloud, p: Plan):
    """Carry out a plan: walk the dependency graph, start whatever is ready (up to
    ``PARALLELISM`` at once), write every result into the state.

    Returns ``(new_state, events, summary_line)``. Destroys run in reverse
    dependency order; a replacement destroys, then creates.
    """
    g = graph(blocks)
    state = {a: copy.deepcopy(e) for a, e in p.refreshed.items()}
    todo = []  # (address, kind)
    for a in p.actions:
        if a.kind == "replace":
            todo += [(a.address, "delete"), (a.address, "create")]
        else:
            todo.append((a.address, a.kind))

    def deps(addr, kind):
        """The steps that must be finished before this one may start."""
        b = base(addr)
        if kind == "delete":  # after everything that depends on it is gone
            users = [x for x, ds in g.items() if b in ds]
            return [(x, k) for x, k in todo if k == "delete" and base(x) in users]
        need = [(x, k) for x, k in todo if k != "delete" and base(x) in g.get(b, [])]
        if (addr, "delete") in todo:  # the "then create" half of a replacement
            need.append((addr, "delete"))
        return need

    done: dict[tuple[str, str], int] = {}
    running: list[tuple[int, str, str, int]] = []  # (t_end, address, kind, t_start)
    events: list[Event] = []
    t = 0
    left = list(todo)
    while left or running:
        ready = [s for s in left if all(d in done and done[d] <= t for d in deps(*s))]
        for addr, kind in ready:
            if len(running) >= PARALLELISM:
                break
            left.remove((addr, kind))
            running.append((t + SECONDS[kind][rtype(addr)], addr, kind, t))
        assert running, f"dependency cycle among {left}"
        running.sort()
        t_end, addr, kind, t0 = running.pop(0)
        t = t_end
        if kind == "delete":
            oid = state.pop(addr)["id"]
            cloud.objects.pop(oid, None)
        elif kind == "create":
            attrs = desired(blocks, state)[addr]
            assert UNKNOWN not in str(attrs), (addr, attrs)
            oid = cloud.create(rtype(addr), attrs)
            state[addr] = {"id": oid, "attrs": dict(attrs)}
        else:
            attrs = desired(blocks, state)[addr]
            oid = state[addr]["id"]
            cloud.objects[oid] = dict(attrs)
            state[addr] = {"id": oid, "attrs": dict(attrs)}
        done[(addr, kind)] = t
        events.append(Event(addr, kind, t0, t, oid))
    events.sort(key=lambda e: (e.t1, sort_key(e.address)))
    n = {k: sum(e.kind == k for e in events) for k in ("create", "update", "delete")}
    summary = (
        f"Apply complete! Resources: {n['create']} added, {n['update']} changed, "
        f"{n['delete']} destroyed."
    )
    return state, events, summary


def short(oid: str, keep: int = 8) -> str:
    """``vpc-0b7c2e9a41d3f5a68`` -> ``vpc-0b7c2e9a…`` (for narrow labels)."""
    if "-" not in oid or not re.search(r"-[0-9a-f]{17}$", oid):
        return oid
    head, hexa = oid.rsplit("-", 1)
    return f"{head}-{hexa[:keep]}…"


# --------------------------------------------------------------------------- #
# the film's story, computed once and asserted
# --------------------------------------------------------------------------- #
@dataclass
class Step:
    """One edit (to the file or to the cloud) and what Terraform makes of it."""

    blocks: list[Block]
    plan: Plan
    state: dict  # after apply
    events: list[Event]
    summary: str  # "Apply complete! ..."

    @property
    def seconds(self) -> int:
        return max(e.t1 for e in self.events)


def _run(blocks, state, cloud) -> Step:
    p = plan(blocks, state, cloud)
    new_state, events, summary = apply(blocks, state, cloud, p)
    again = plan(blocks, new_state, cloud)
    assert not again.actions, again.actions  # applying a plan converges
    assert again.summary.startswith("No changes.")
    return Step(blocks, p, new_state, events, summary)


SOURCE = (DEMO / "main.tf").read_text()
CONFIG = parse(SOURCE)
GRAPH = graph(CONFIG)
RANKS = ranks(GRAPH)
ADDRESSES = [b.address for b in CONFIG]  # in file order
assert ADDRESSES == [
    "aws_vpc.main",
    "aws_subnet.public",
    "aws_security_group.web",
    "aws_instance.web",
    "aws_s3_bucket.assets",
]
assert "\n\n".join("\n".join(b.lines) for b in CONFIG) + "\n" == SOURCE  # nothing lost
assert GRAPH == {
    "aws_vpc.main": [],
    "aws_subnet.public": ["aws_vpc.main"],
    "aws_security_group.web": ["aws_vpc.main"],
    "aws_instance.web": ["aws_subnet.public", "aws_security_group.web"],
    "aws_s3_bucket.assets": [],
}
WAVES = [
    [a for a in ADDRESSES if RANKS[a] == r] for r in range(max(RANKS.values()) + 1)
]
assert WAVES == [
    ["aws_vpc.main", "aws_s3_bucket.assets"],
    ["aws_subnet.public", "aws_security_group.web"],
    ["aws_instance.web"],
]

CLOUD = Cloud()

# 1. the first apply: everything is new
FIRST = _run(CONFIG, {}, CLOUD)
assert FIRST.plan.summary == "Plan: 6 to add, 0 to change, 0 to destroy."
assert FIRST.summary == "Apply complete! Resources: 6 added, 0 changed, 0 destroyed."
CLOUD_AFTER_FIRST = copy.deepcopy(CLOUD)
# ... and applying the same file again changes nothing
AGAIN = plan(CONFIG, FIRST.state, CLOUD_AFTER_FIRST)
_same, _none, AGAIN_SUMMARY = apply(
    CONFIG, FIRST.state, copy.deepcopy(CLOUD_AFTER_FIRST), AGAIN
)
assert AGAIN.summary == "No changes. Your infrastructure matches the configuration."
assert not _none and _same == FIRST.state
assert AGAIN_SUMMARY == "Apply complete! Resources: 0 added, 0 changed, 0 destroyed."
SERIAL_SECONDS = sum(e.t1 - e.t0 for e in FIRST.events)
assert (FIRST.seconds, SERIAL_SECONDS) == (17, 33)  # the graph walk vs one at a time
_started = {e.address: e.t0 for e in FIRST.events}
_ended = {e.address: e.t1 for e in FIRST.events}
for _b in CONFIG:  # nothing starts before what it references exists
    for _a in _b.instances():
        assert all(
            _ended[x] <= _started[_a]
            for d in GRAPH[_b.address]
            for x in next(b for b in CONFIG if b.address == d).instances()
        )

# 2. change the file: two servers become three
SCALED = with_arg(CONFIG, "aws_instance.web", "count", "3")
SCALE = _run(SCALED, FIRST.state, CLOUD)
assert SCALE.plan.summary == "Plan: 1 to add, 0 to change, 0 to destroy."
assert [a.address for a in SCALE.plan.actions] == ["aws_instance.web[2]"]

# 3. a setting that can change in place: the instance type
RESIZED = with_arg(SCALED, "aws_instance.web", "instance_type", '"t3.small"')
RESIZE = _run(RESIZED, SCALE.state, CLOUD)
assert RESIZE.plan.summary == "Plan: 0 to add, 3 to change, 0 to destroy."
assert {a.kind for a in RESIZE.plan.actions} == {"update"}

# 4. a setting that cannot: the machine image forces a replacement
REIMAGED = with_arg(RESIZED, "aws_instance.web", "ami", '"ami-07d1e5b9"')
REIMAGE = _run(REIMAGED, RESIZE.state, CLOUD)
assert REIMAGE.plan.summary == "Plan: 3 to add, 0 to change, 3 to destroy."
assert {a.kind for a in REIMAGE.plan.actions} == {"replace"}
assert all(
    REIMAGE.state[a]["id"] != RESIZE.state[a]["id"]
    for a in ("aws_instance.web[0]", "aws_instance.web[1]", "aws_instance.web[2]")
)

# 5. drift: someone resizes one server by hand, in the console
DRIFT_ADDR = "aws_instance.web[1]"
DRIFT_ID = REIMAGE.state[DRIFT_ADDR]["id"]
CLOUD.objects[DRIFT_ID]["instance_type"] = "t3.large"
DRIFT_PLAN = plan(REIMAGED, REIMAGE.state, CLOUD)
assert DRIFT_PLAN.drift == [(DRIFT_ADDR, "changed")]
assert DRIFT_PLAN.summary == "Plan: 0 to add, 1 to change, 0 to destroy."
assert DRIFT_PLAN.of(DRIFT_ADDR).changes == {"instance_type": ("t3.large", "t3.small")}
DRIFT = _run(REIMAGED, REIMAGE.state, CLOUD)
assert CLOUD.objects[DRIFT_ID]["instance_type"] == "t3.small"  # put back
FINAL = DRIFT

# 6. one module, three environments (demo/envs/*/main.tf call demo/modules/web)
MODULE_SOURCE = (DEMO / "modules" / "web" / "main.tf").read_text()
_var = re.search(r'^variable "servers" \{\n(?:.*\n)*?\}$', MODULE_SOURCE, re.M)
MODULE_INPUT = _var.group(0).split("\n")  # the module's one input, as written
assert MODULE_INPUT[0] == 'variable "servers" {' and "var.servers" in MODULE_SOURCE
ENVS = {}
for _env in ("dev", "staging", "prod"):
    _call = (DEMO / "envs" / _env / "main.tf").read_text()
    _n = int(re.search(r"servers\s*=\s*(\d+)", _call).group(1))
    _key = re.search(
        r'key\s*=\s*"([^"]+)"', (DEMO / "envs" / _env / "backend.tf").read_text()
    )
    _blocks = parse(MODULE_SOURCE.replace("var.servers", str(_n)))
    assert [b.address for b in _blocks] == ADDRESSES and graph(_blocks) == GRAPH
    _step = _run(_blocks, {}, Cloud(seed=100 + _n))
    ENVS[_env] = {
        "call": _call.rstrip("\n").split("\n"),
        "servers": _n,
        "state_key": _key.group(1),  # every environment keeps its own state
        "resources": len(_step.state),
        "summary": _step.summary,
    }
assert {e: v["servers"] for e, v in ENVS.items()} == {"dev": 1, "staging": 2, "prod": 4}
assert {e: v["resources"] for e, v in ENVS.items()} == {
    "dev": 5,
    "staging": 6,
    "prod": 8,
}
assert len({v["state_key"] for v in ENVS.values()}) == 3


if __name__ == "__main__":  # python sim.py: print the whole story
    for title, step in (
        ("first apply", FIRST),
        ("count 2 -> 3", SCALE),
        ("instance_type", RESIZE),
        ("ami", REIMAGE),
        ("drift", DRIFT),
    ):
        print(f"\n=== {title}")
        for a in step.plan.actions:
            print("  ", a.headline)
            if a.kind != "create":
                for line in a.change_lines():
                    print("       ", line)
        print("  ", step.plan.summary)
        for e in step.events:
            print(f"   {e.t0:3d}-{e.t1:3d}  {e.done_line}")
        print("  ", step.summary)
    print("\n=== environments")
    for env, v in ENVS.items():
        print(f"   {env:8s} servers={v['servers']}  {v['summary']}")
