"""tcpsim.py: a small, honest model of TCP, for the pictures a laptop cannot record.

Seeing real TCP headers needs a packet capture, which needs administrator rights;
and loss on a real link cannot be ordered up. So the film's packet-level pictures
come from this model. It follows the standard's rules, simplified where it changes
nothing to the story:

* three-way handshake: SYN, SYN-ACK, ACK (RFC 9293);
* data in segments of at most ``mss`` bytes, numbered by the offset of their first
  byte; the receiver answers every segment with a cumulative ACK: "I have
  everything before byte N" (no delayed ACKs, no SACK);
* congestion control (RFC 5681, RFC 6928): the window starts at ten segments and
  grows by one segment per ACK (it doubles every round trip: "slow start"); three
  duplicate ACKs trigger a fast retransmit, the window is cut to half of what was
  in flight, and then grows by about one segment per round trip (during the
  recovery itself the film plots that halved window, ``shown``, not the cwnd that
  the standard inflates by one segment per duplicate ACK);
* the path: a fixed one-way delay, and a bottleneck that lets one segment through
  every ``seg_ms`` (so a burst leaves as a train, not as a single flash). Chosen
  segments are dropped once; ACKs are never lost. No retransmission timer: the
  scenario always leaves three later segments to trigger the fast retransmit.

Times are milliseconds. Everything is deterministic.
"""

from __future__ import annotations

import heapq
import math


def handshake(
    rtt_ms: float, client_isn: int, server_isn: int, t0: float = 0.0
) -> list[dict]:
    """SYN, SYN-ACK, ACK: who sends what, when, with which numbers."""
    d = rtt_ms / 2
    return [
        {
            "flags": "SYN",
            "way": ">",
            "t0": t0,
            "t1": t0 + d,
            "seq": client_isn,
            "ack": None,
        },
        {
            "flags": "SYN-ACK",
            "way": "<",
            "t0": t0 + d,
            "t1": t0 + 2 * d,
            "seq": server_isn,
            "ack": client_isn + 1,
        },
        {
            "flags": "ACK",
            "way": ">",
            "t0": t0 + 2 * d,
            "t1": t0 + 3 * d,
            "seq": client_isn + 1,
            "ack": server_isn + 1,
        },
    ]


def transfer(
    total: int,
    rtt_ms: float,
    mss: int = 1460,
    first_window: int = 10,
    seg_ms: float = 0.584,
    lose: tuple[int, ...] = (),
    t0: float = 0.0,
) -> dict:
    """Send ``total`` bytes from the server to the client; ``lose`` lists the
    segments (by index) whose first transmission is dropped on the way.

    Returns ``data`` (one row per transmitted segment), ``acks`` (one row per ACK),
    ``window`` (the sender's congestion window over time) and ``facts``.
    """
    d = rtt_ms / 2
    n_seg = math.ceil(total / mss)
    events, order = [], 0  # (time, tie-break, kind, payload)

    def push(t, kind, payload):
        nonlocal order
        order += 1
        heapq.heappush(events, (t, order, kind, payload))

    # sender
    una, nxt = 0, 0
    cwnd, ssthresh = float(first_window * mss), math.inf
    dup, recover, link_free = 0, None, t0
    # receiver
    have, rcv_nxt, last_ack = set(), 0, None
    data, acks, window = [], [], []
    dropped = set(lose)

    def note(t):
        # ``shown``: what the sender allows itself. During fast recovery the standard
        # inflates cwnd by one segment per duplicate ACK (bookkeeping for the segments
        # that have left the network); the window it has really fallen back to is
        # ssthresh, half of what was in flight.
        window.append(
            {
                "t": t,
                "cwnd": cwnd / mss,
                "shown": (ssthresh if recover is not None else cwnd) / mss,
                "una": una,
                "nxt": nxt,
                "ssthresh": None if math.isinf(ssthresh) else ssthresh / mss,
            }
        )

    def send(t, seq, again=False):
        nonlocal link_free
        length = min(mss, total - seq)
        start = max(t, link_free)
        link_free = start + seg_ms
        index = seq // mss
        lost = index in dropped and not again
        if lost:
            dropped.discard(index)
        row = {"i": index, "seq": seq, "len": length, "t0": start, "t1": None if lost else start + d,
               "again": again, "lost": lost}  # fmt: skip
        data.append(row)
        if not lost:
            push(start + d, "data", row)

    def pump(t):
        nonlocal nxt
        while nxt < total and nxt - una + min(mss, total - nxt) <= cwnd + 1e-9:
            send(t, nxt)
            nxt += min(mss, total - nxt)

    note(t0)
    pump(t0)
    note(t0)
    guard = 0
    while events:
        guard += 1
        assert guard < 100_000, "the model is stuck (a loss nothing can report?)"
        t, _, kind, row = heapq.heappop(events)
        if kind == "data":  # at the receiver
            have.add(row["seq"])
            while rcv_nxt in have:
                rcv_nxt += min(mss, total - rcv_nxt)
            ack = {
                "ack": rcv_nxt,
                "t0": t,
                "t1": t + d,
                "dup": rcv_nxt == last_ack,
                "for": row["i"],
            }
            last_ack = rcv_nxt
            acks.append(ack)
            row["delivered_to"] = rcv_nxt
            push(t + d, "ack", ack)
            continue
        # an ACK reaches the sender
        if row["ack"] > una:
            got = row["ack"] - una
            una, dup = row["ack"], 0
            if recover is not None:
                if una >= recover:  # everything sent before the loss is confirmed
                    cwnd, recover = ssthresh, None
                else:  # NewReno: a partial ACK names the next hole
                    send(t, una, again=True)
                    cwnd = max(mss, cwnd - got + mss)
            elif cwnd < ssthresh:
                cwnd += min(got, mss)  # slow start: one more segment per ACK
            else:
                cwnd += mss * mss / cwnd  # congestion avoidance
        elif row["ack"] == una and nxt > una:
            dup += 1
            if dup == 3 and recover is None:  # fast retransmit, fast recovery
                ssthresh = max((nxt - una) / 2, 2 * mss)
                recover = nxt
                row["triggers_resend"] = True
                send(t, una, again=True)
                cwnd = ssthresh + 3 * mss
            elif recover is not None:
                cwnd += mss
        pump(t)
        note(t)
    assert una == total and rcv_nxt == total, "every byte was delivered and confirmed"

    # facts the film states
    rounds = {}
    for row in data:
        if not row["again"]:
            rounds.setdefault(int((row["t0"] - t0 + 1e-6) // rtt_ms), []).append(
                row["i"]
            )
    lost_rows = [r for r in data if r["lost"]]
    resent = [r for r in data if r["again"]]
    return {
        "data": data,
        "acks": acks,
        "window": window,
        "facts": {
            "bytes": total,
            "segments": n_seg,
            "mss": mss,
            "rtt_ms": rtt_ms,
            "seg_ms": seg_ms,
            "flights": [len(v) for _, v in sorted(rounds.items())],
            "lost": [r["i"] for r in lost_rows],
            "resent": [{"i": r["i"], "t0": r["t0"], "t1": r["t1"]} for r in resent],
            "duplicate_acks": sum(1 for a in acks if a["dup"]),
            "done_ms": max(a["t1"] for a in acks) - t0,
            "last_byte_ms": max(r["t1"] for r in data if r["t1"] is not None) - t0,
            "round_trips": (max(r["t1"] for r in data if r["t1"] is not None) - t0 + d)
            / rtt_ms,
        },
    }


if __name__ == "__main__":
    for lose in ((), (92,)):
        f = transfer(230_497, 105.0, lose=lose)["facts"]
        print(f"lose={lose}: flights {f['flights']}, {f['segments']} segments, last byte after "
              f"{f['last_byte_ms']:.1f} ms = {f['last_byte_ms'] / f['rtt_ms']:.2f} round trips; "
              f"dup acks {f['duplicate_acks']}, resent {f['resent']}")  # fmt: skip


# --------------------------------------------------------------------------- #
# the network alone: best effort
# --------------------------------------------------------------------------- #
ROWS = ("a", "b", "c")  # three lanes of routers between the two ends
COLS = (4, 3, 2, 1)  # column 4 is next to the server, column 1 next to the phone


def best_effort(
    n: int,
    seg_ms: float = 0.584,
    seed: int = 11,
    t0: float = 0.0,
    slow_service: float = 1.35,
    slow_room: int = 5,
) -> dict:
    """``n`` packets sent back to back across a small network of routers, with no
    transport protocol to look after them.

    Each router forwards a packet to a router of the next column: usually the one
    in its own lane, sometimes a neighbour (routes are chosen per packet). Lanes
    are not equally fast, so packets overtake each other. One router (``b2``) has
    a slow outgoing link and room for only a few waiting packets: when its queue
    is full, the next packet is dropped. That is all "best effort" means.
    """
    import random

    rng = random.Random(seed)
    hop_ms = {
        "a": 11.0,
        "b": 9.4,
        "c": 12.6,
    }  # delay of a link, by the lane it arrives in
    slow = "b2"
    last_hop = 9.0
    free_at, waiting = 0.0, []  # the slow router: when its link is free, who waits
    packets = []
    # process in order of arrival at each router: simulate hop by hop with an event list
    events, order = [], 0

    def push(t, i, node):
        nonlocal order
        order += 1
        heapq.heappush(events, (t, order, i, node))

    for i in range(n):
        packets.append(
            {"i": i, "hops": [("S", t0 + i * seg_ms, t0 + i * seg_ms)], "lost_at": None}
        )
        lane = rng.choices(ROWS, weights=(0.3, 0.45, 0.25))[0]
        push(t0 + i * seg_ms + hop_ms[lane], i, f"{lane}{COLS[0]}")

    while events:
        t, _, i, node = heapq.heappop(events)
        pk = packets[i]
        if node == "P":
            pk["hops"].append(("P", t, t))
            continue
        depart = t + 0.3
        if node == slow:
            waiting[:] = [w for w in waiting if w > t]  # who is still queued at time t
            if len(waiting) >= slow_room:
                pk["hops"].append((node, t, t))
                pk["lost_at"] = node
                continue
            depart = max(t, free_at) + slow_service
            free_at = depart
            waiting.append(depart)
        pk["hops"].append((node, t, depart))
        lane, col = node[0], int(node[1])
        if col == 1:
            push(depart + last_hop, i, "P")
            continue
        r = ROWS.index(lane)
        options = [ROWS[k] for k in (r - 1, r, r + 1) if 0 <= k < 3]
        weights = [0.72 if o == lane else 0.28 / (len(options) - 1) for o in options]
        nxt = rng.choices(options, weights=weights)[0]
        push(depart + hop_ms[nxt], i, f"{nxt}{col - 1}")

    arrived = sorted(
        (pk["hops"][-1][1], pk["i"]) for pk in packets if pk["lost_at"] is None
    )
    late, top = 0, -1
    for _, i in arrived:
        if i < top:
            late += 1
        top = max(top, i)
    return {
        "packets": packets,
        "facts": {
            "sent": n,
            "arrived": len(arrived),
            "lost": [pk["i"] for pk in packets if pk["lost_at"]],
            "overtaken": late,
            "first_ms": arrived[0][0] - t0,
            "last_ms": arrived[-1][0] - t0,
            "slow_router": slow,
            "queue_room": slow_room,
        },
    }
