"""lab.py: the film's laboratory. Two programs on this machine, real sockets, and a
relay in the middle that sees (and can change) every byte.

Nothing here leaves the machine: every socket is bound or connected to the loopback
address. What the film states about bytes, handshakes, errors and the kernel's
behaviour is measured here by ``generate_assets.py`` and asserted in the scenes;
what cannot be seen without administrator rights (TCP headers, loss on a real link)
comes from the model in ``tcpsim.py`` and is labelled as a model.

Each experiment returns plain data (JSON-ready).
"""

from __future__ import annotations

import errno
import json
import os
import re
import select
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "demo"))

import client  # noqa: E402
import pki  # noqa: E402
import proxy  # noqa: E402
import server  # noqa: E402
import x25519 as kx  # noqa: E402

LOOP = "127.0.0.1"
NOBODY = "127.0.0.2"  # loopback, but no interface owns it: packets vanish (macOS)
TOKEN = "lea-4f1c9a"


def ms(seconds: float) -> float:
    return round(seconds * 1000, 3)


# --------------------------------------------------------------------------- #
# the tap
# --------------------------------------------------------------------------- #
class Tap:
    """A relay between client and server. ``log`` holds every piece it forwarded:
    (seconds since the first byte, ">" to the server or "<" to the client, bytes).

    ``alter(way, piece)`` may return different bytes. With ``records=True`` the
    stream is cut into TLS records first, so a piece is one whole record.
    """

    def __init__(self, upstream_port: int, alter=None, records: bool = False):
        self.upstream, self.alter, self.records = (LOOP, upstream_port), alter, records
        self.log, self.t0, self.threads = [], None, []
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((LOOP, 0))
        self.sock.listen(8)
        self.port = self.sock.getsockname()[1]

    def start(self):
        threading.Thread(target=self._accept, daemon=True).start()
        return self

    def _accept(self):
        while True:
            try:
                near, _ = self.sock.accept()
            except OSError:
                return
            far = socket.create_connection(self.upstream)
            for src, dst, way in ((near, far, ">"), (far, near, "<")):
                t = threading.Thread(
                    target=self._pump, args=(src, dst, way), daemon=True
                )
                t.start()
                self.threads.append(t)

    def _pump(self, src, dst, way):
        buf = b""
        while True:
            try:
                data = src.recv(65536)
            except OSError:
                break
            if not data:
                break
            if self.t0 is None:
                self.t0 = time.perf_counter()
            if self.records:
                buf += data
                pieces = []
                while len(buf) >= 5 and len(buf) >= 5 + int.from_bytes(buf[3:5], "big"):
                    n = 5 + int.from_bytes(buf[3:5], "big")
                    pieces.append(buf[:n])
                    buf = buf[n:]
            else:
                pieces = [data]
            for piece in pieces:
                seen = piece
                if self.alter is not None:
                    piece = self.alter(way, piece)
                self.log.append((time.perf_counter() - self.t0, way, seen, piece))
                try:
                    dst.sendall(piece)
                except OSError:
                    return
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass

    def stream(self, way: str, sent: bool = False) -> bytes:
        """Everything that went one way (as seen, or as sent on after ``alter``)."""
        return b"".join(row[3 if sent else 2] for row in self.log if row[1] == way)

    def settle(self):
        for t in self.threads:
            t.join(1.0)
        self.sock.close()
        return self


def ask(port: int, raw: bytes):
    """One plain HTTP request on a fresh connection."""
    with socket.create_connection((LOOP, port)) as s:
        s.sendall(raw)
        status, headers, body, _ = client.read_response(s)
    return status, headers, body


def printable(data: bytes) -> str:
    """Bytes as an eavesdropper's screen shows them: text where it is text."""
    return "".join(chr(b) if 32 <= b < 127 else "·" for b in data)


# --------------------------------------------------------------------------- #
# 1. HTTP in the clear
# --------------------------------------------------------------------------- #
def plain_http() -> dict:
    srv = server.Server().start()
    tap = Tap(srv.port).start()
    status, headers, body = ask(tap.port, client.request)
    tap.settle()
    up, down = tap.stream(">"), tap.stream("<")
    assert up == client.request, "the tap saw exactly what the client sent"
    head = down[: down.index(b"\r\n\r\n") + 4]
    assert down == head + body

    map_request = client.request.replace(
        b"/courses/lea ", b"/courses/lea/map "
    ).replace(b"application/json", b"image/x-portable-pixmap")
    m_status, m_headers, m_body = ask(srv.port, map_request)
    m_head = (
        f"HTTP/1.1 {m_status.split(' ', 1)[1]}\r\nContent-Type: {m_headers['content-type']}\r\n"
        f"Content-Length: {m_headers['content-length']}\r\n\r\n"
    ).encode()
    srv.stop()
    return {
        "request": client.request.decode(),
        "status": status,
        "head": head.decode(),
        "body": body.decode(),
        "bytes": {"request": len(up), "head": len(head), "body": len(body)},
        "token_on_the_wire": TOKEN.encode() in up,
        "map": {
            "request": map_request.decode(),
            "status": m_status,
            "head": m_head.decode(),
            "bytes": {"head": len(m_head), "body": len(m_body)},
            "content_type": m_headers["content-type"],
        },
    }


# --------------------------------------------------------------------------- #
# 2. status codes, keep-alive
# --------------------------------------------------------------------------- #
def status_codes() -> list[dict]:
    srv = server.Server().start()
    cases = [
        ("ok", client.request),
        ("unknown", client.request.replace(b"/courses/lea ", b"/courses/zoe ")),
        (
            "anonymous",
            client.request.replace(f"Authorization: Bearer {TOKEN}\r\n".encode(), b""),
        ),
        ("bug", client.request.replace(b"/courses/lea ", b"/courses/lea/eta ")),
    ]
    out = []
    for label, raw in cases:
        status, _headers, body = ask(srv.port, raw)
        out.append(
            {
                "case": label,
                "request_line": raw.split(b"\r\n", 1)[0].decode(),
                "has_token": b"Authorization" in raw,
                "status": status.split(" ", 1)[1],
                "body": body.decode(),
            }
        )
    srv.stop()
    return out


def keep_alive(n: int = 3) -> dict:
    """``n`` requests on one connection, then ``n`` connections with one request each."""
    srv = server.Server().start()
    with socket.create_connection((LOOP, srv.port)) as s:
        rest, reused = b"", []
        for _ in range(n):
            t = time.perf_counter()
            s.sendall(client.request)
            status, _h, _b, rest = client.read_response(s, rest)
            reused.append(ms(time.perf_counter() - t))
            assert status.endswith("200 OK")
    one = srv.accepted
    fresh = []
    for _ in range(n):
        t = time.perf_counter()
        status, _h, _b = ask(srv.port, client.request)
        fresh.append(ms(time.perf_counter() - t))
    many = srv.accepted - one
    srv.stop()
    assert one == 1 and many == n
    return {
        "requests": n,
        "connections_when_reused": one,
        "connections_when_fresh": many,
        "ms_reused": reused,
        "ms_fresh": fresh,
    }


# --------------------------------------------------------------------------- #
# 3. what a tap can do to plain HTTP
# --------------------------------------------------------------------------- #
def eavesdrop() -> dict:
    srv = server.Server().start()

    # (a) change the answer on its way back
    def cheat(way, piece):
        return piece.replace(b'"earns":24.4', b'"earns":2.44') if way == "<" else piece

    tap = Tap(srv.port, alter=cheat).start()
    status, _h, body = ask(tap.port, client.request)
    tap.settle()
    told = json.loads(body)

    # (b) reuse the token it read
    seen = tap.stream(">")
    stolen = re.search(rb"Authorization: Bearer (\S+)", seen).group(1).decode()
    replay = (
        f"GET /courses/lea HTTP/1.1\r\nHost: {server.HOST}\r\nAuthorization: Bearer {stolen}\r\n\r\n"
    ).encode()
    r_status, _h, r_body = ask(srv.port, replay)
    srv.stop()
    assert status.endswith("200 OK") and told["earns"] == 2.44
    assert r_status.endswith("200 OK") and json.loads(r_body)["earns"] == 24.4
    return {
        "screen": printable(seen),
        "stolen_token": stolen == TOKEN,
        "altered": {
            "sent": 24.4,
            "received": told["earns"],
            "status": status.split(" ", 1)[1],
        },
        "replay": {
            "status": r_status.split(" ", 1)[1],
            "courier": json.loads(r_body)["courier"],
        },
    }


# --------------------------------------------------------------------------- #
# 4. HTTPS: the handshake and the records, seen from the wire
# --------------------------------------------------------------------------- #
RECORD_TYPES = {
    20: "change_cipher_spec",
    21: "alert",
    22: "handshake",
    23: "application_data",
}
GROUPS = {"001d": "x25519", "0017": "secp256r1", "11ec": "X25519MLKEM768"}
SUITES = {"1301": "TLS_AES_128_GCM_SHA256", "1302": "TLS_AES_256_GCM_SHA384",
          "1303": "TLS_CHACHA20_POLY1305_SHA256"}  # fmt: skip


def read_hello(body: bytes) -> dict:
    """What anyone on the path can read in a ClientHello / ServerHello."""
    kind, p = body[0], 4
    p += 2 + 32  # legacy version, random
    p += 1 + body[p]  # session id
    out = {"message": {1: "ClientHello", 2: "ServerHello"}[kind]}
    if kind == 1:
        n = int.from_bytes(body[p : p + 2], "big")
        out["suites"] = [
            SUITES.get(body[i : i + 2].hex(), body[i : i + 2].hex())
            for i in range(p + 2, p + 2 + n, 2)
        ]
        p += 2 + n
        p += 1 + body[p]  # compression methods
    else:
        out["suite"] = SUITES.get(body[p : p + 2].hex(), body[p : p + 2].hex())
        p += 3
    end = p + 2 + int.from_bytes(body[p : p + 2], "big")
    p += 2
    while p < end:
        etype, elen = struct.unpack(">HH", body[p : p + 4])
        data = body[p + 4 : p + 4 + elen]
        p += 4 + elen
        if etype == 0:  # server_name
            out["server_name"] = data[5:].decode()
        elif etype == 51:  # key_share
            share = data[2:] if kind == 1 else data
            out["group"] = GROUPS.get(share[:2].hex(), share[:2].hex())
            out["key_share"] = share[4 : 4 + int.from_bytes(share[2:4], "big")].hex()
        elif etype == 43:  # supported_versions
            out["tls13"] = b"\x03\x04" in data
    return out


def https() -> dict:
    files = pki.ensure()
    srv = server.Server(
        tls=server.tls_context(files["chain"], files["leaf_key"])
    ).start()
    tap = Tap(srv.port, records=True).start()
    context = client.trust(files["root"])

    # the film's five lines, timed one by one
    t = [time.perf_counter()]
    ip, port = LOOP, tap.port
    sock = socket.create_connection((ip, port))
    t.append(time.perf_counter())
    tls = context.wrap_socket(sock, server_hostname=client.host)
    t.append(time.perf_counter())
    tls.sendall(client.request)
    reply = client.read_reply(tls)
    t.append(time.perf_counter())
    version, suite = tls.version(), tls.cipher()[0]
    tls.close()
    tap.settle()
    srv.stop()

    records = []
    for when, way, seen, _sent in tap.log:
        kind = RECORD_TYPES[seen[0]]
        row = {"ms": ms(when), "way": way, "type": kind, "bytes": len(seen)}
        if kind == "handshake":
            row.update(read_hello(seen[5:]))
            row["screen"] = printable(seen)
        records.append(row)
    up = [r for r in records if r["way"] == ">"]
    down = [r for r in records if r["way"] == "<"]
    hello, server_hello = up[0], down[0]
    sealed_request = next(
        row
        for row in tap.log
        if row[1] == ">" and len(row[2]) == 5 + len(client.request) + 17
    )
    sealed_reply = next(
        row for row in tap.log if row[1] == "<" and len(row[2]) == 5 + len(reply) + 17
    )

    assert reply.startswith(b"HTTP/1.1 200 OK") and version == "TLSv1.3"
    assert hello["message"] == "ClientHello" and hello["server_name"] == client.host
    assert hello["group"] == server_hello["group"] == "x25519"
    assert client.request not in tap.stream(">") and b"lea" not in tap.stream(
        ">"
    ).replace(client.host.encode(), b""), (
        "nothing of the request is readable on the wire"
    )
    assert b"HTTP/1.1" not in tap.stream("<") and b"ramen" not in tap.stream("<")
    assert server.HOST.encode() not in tap.stream("<"), (
        "TLS 1.3 hides the certificate too"
    )

    # flights: who speaks, in which order
    flights, last = [], None
    for r in records:
        if r["way"] != last:
            flights.append({"way": r["way"], "ms": r["ms"], "bytes": 0, "records": 0})
            last = r["way"]
        flights[-1]["bytes"] += r["bytes"]
        flights[-1]["records"] += 1
    return {
        "version": version,
        "suite": suite,
        "records": records,
        "flights": flights,
        "client_hello": {
            k: hello[k]
            for k in ("bytes", "server_name", "group", "key_share", "suites", "screen")
        },
        "server_hello": {
            k: server_hello[k] for k in ("bytes", "group", "key_share", "suite")
        },
        "handshake_bytes": {
            "client": sum(r["bytes"] for r in up[:-1]),
            "server": sum(r["bytes"] for r in down if r["ms"] < up[-1]["ms"]),
        },
        "request": {
            "plain_bytes": len(client.request),
            "record_bytes": len(sealed_request[2]),
            "overhead": len(sealed_request[2]) - len(client.request),
            "screen": printable(sealed_request[2]),
            "hex": sealed_request[2].hex(),
        },
        "reply": {
            "plain_bytes": len(reply),
            "record_bytes": len(sealed_reply[2]),
            "screen": printable(sealed_reply[2]),
        },
        "loopback_ms": {
            "tcp": ms(t[1] - t[0]),
            "tls": ms(t[2] - t[1]),
            "http": ms(t[3] - t[2]),
        },
    }


def tls_failures() -> dict:
    """Four ways HTTPS says no, with the exact words of this machine's TLS library."""
    files = pki.ensure()
    context = client.trust(files["root"])
    out = {}

    def attempt(port):
        try:
            return {
                "reply": client.call(context, lookup=lambda _name: (LOOP, port))
                .split(b"\r\n")[0]
                .decode()
            }
        except ssl.SSLCertVerificationError as exc:
            return {
                "error": type(exc).__name__,
                "reason": exc.verify_message,
                "text": str(exc),
            }
        except ssl.SSLError as exc:
            return {"error": type(exc).__name__, "reason": exc.reason, "text": str(exc)}

    # one bit changed on the way back
    srv = server.Server(
        tls=server.tls_context(files["chain"], files["leaf_key"])
    ).start()
    hit = []

    def flip(way, record):
        if way == "<" and record[0] == 23 and len(record) == 5 + 154 + 17 and not hit:
            hit.append(len(record))
            mid = len(record) // 2
            return record[:mid] + bytes([record[mid] ^ 0x01]) + record[mid + 1 :]
        return record

    tap = Tap(srv.port, alter=flip, records=True).start()
    out["one_bit_flipped"] = attempt(tap.port)
    tap.settle()
    srv.stop()
    assert hit and "error" in out["one_bit_flipped"], "the flipped record was rejected"

    # three certificates that must be refused
    for label, chain, key in (
        ("impostor", "impostor_chain", "impostor_key"),
        ("other_name", "othername_chain", "othername_key"),
        ("expired", "expired_chain", "expired_key"),
    ):
        bad = server.Server(tls=server.tls_context(files[chain], files[key])).start()
        out[label] = attempt(bad.port)
        bad.stop()
        assert out[label].get("error") == "SSLCertVerificationError", (
            label,
            out[label],
        )
    return out


def certificates() -> dict:
    files = pki.ensure()
    chain = [pki.describe(files[name]) for name in ("leaf", "issuing", "root")]
    assert (
        chain[0]["issuer"] == chain[1]["subject"]
        and chain[1]["issuer"] == chain[2]["subject"]
    )
    assert chain[2]["issuer"] == chain[2]["subject"], "a root signs itself"
    store = ssl.create_default_context().cert_store_stats()
    return {"chain": chain, "trusted_on_this_machine": store["x509_ca"]}


# --------------------------------------------------------------------------- #
# 5. key agreement, checked against OpenSSL
# --------------------------------------------------------------------------- #
def key_agreement() -> dict:
    kx.self_test()
    raw = {}
    for who in ("a", "b"):
        key = pki.HOME / f"kx_{who}.key"
        pki.openssl("genpkey", "-algorithm", "X25519", "-out", key)
        pki.openssl("pkey", "-in", key, "-pubout", "-out", pki.HOME / f"kx_{who}.pub")
        der = subprocess.run(
            ["openssl", "pkey", "-in", str(key), "-outform", "DER"],
            capture_output=True,
            check=True,
        )
        pub = subprocess.run(
            ["openssl", "pkey", "-in", str(key), "-pubout", "-outform", "DER"],
            capture_output=True,
            check=True,
        )
        raw[who] = (der.stdout[-32:], pub.stdout[-32:])
    derived = {}
    for me, peer in (("a", "b"), ("b", "a")):
        done = subprocess.run(
            ["openssl", "pkeyutl", "-derive", "-inkey", str(pki.HOME / f"kx_{me}.key"),
             "-peerkey", str(pki.HOME / f"kx_{peer}.pub")],
            capture_output=True, check=True,
        )  # fmt: skip
        derived[me] = done.stdout
    (sa, pa), (sb, pb) = raw["a"], raw["b"]
    assert kx.x25519(sa) == pa and kx.x25519(sb) == pb, (
        "our public values match OpenSSL's"
    )
    ours_a, ours_b = kx.x25519(sa, pb), kx.x25519(sb, pa)
    assert ours_a == ours_b == derived["a"] == derived["b"], (
        "both sides, both libraries: one key"
    )
    # the private numbers stay in the cache folder; only what crossed the wire and
    # the (throwaway) result are kept
    return {
        "public_client": pa.hex(),
        "public_server": pb.hex(),
        "shared": ours_a.hex(),
    }


# --------------------------------------------------------------------------- #
# 6. the kernel: first window, a closed port, silence
# --------------------------------------------------------------------------- #
TCP_CONNECTION_INFO = 0x106  # macOS
_INFO = "<BBBB12II7Q"
_FIELDS = (
    "state snd_wscale rcv_wscale pad options flags rto maxseg ssthresh cwnd snd_wnd "
    "snd_sbbytes rcv_wnd rttcur srtt rttvar bits txpackets txbytes txretransmitbytes "
    "rxpackets rxbytes rxoutoforderbytes txretransmitpackets"
).split()


def tcp_info(sock) -> dict:
    raw = sock.getsockopt(
        socket.IPPROTO_TCP, TCP_CONNECTION_INFO, struct.calcsize(_INFO)
    )
    return dict(zip(_FIELDS, struct.unpack(_INFO, raw), strict=True))


def kernel() -> dict:
    out = {}
    lst = socket.socket()
    lst.bind((LOOP, 0))
    lst.listen(1)
    port = lst.getsockname()[1]
    c = socket.socket()
    c.connect((LOOP, port))
    a, _ = lst.accept()
    first = tcp_info(a)
    a.sendall(b"\0" * 90_000)
    got = 0
    while got < 90_000:
        got += len(c.recv(65536))
    time.sleep(0.05)
    after = tcp_info(a)
    out["first_window"] = {
        "segment_bytes": first["maxseg"],
        "window_bytes": first["cwnd"],
        "segments": first["cwnd"] / first["maxseg"],
        "after_90kB_bytes": after["cwnd"],
        "client_port": c.getsockname()[1],
        "server_port": port,
    }
    c.close()
    a.close()
    lst.close()

    # nobody listens on that port any more: the machine itself says no
    c = socket.socket()
    t0 = time.perf_counter()
    try:
        c.connect((LOOP, port))
        raise AssertionError("expected a refusal")
    except ConnectionRefusedError as exc:
        out["refused"] = {
            "ms": ms(time.perf_counter() - t0),
            "error": type(exc).__name__,
            "text": str(exc),
            "errno": errno.errorcode[exc.errno],
        }
    c.close()

    # a name that is no address: the exact error a failed DNS lookup raises, with no query sent
    try:
        socket.getaddrinfo("api.dispatch.exampel", 443, flags=socket.AI_NUMERICHOST)
        raise AssertionError("expected a failure")
    except socket.gaierror as exc:
        out["no_such_name"] = {"error": "socket.gaierror", "text": str(exc)}
    return out


def silence(patience: float = 3.0, full: bool = True) -> dict:
    """Connect to an address where nothing answers: what the caller sees with a
    timeout of its own, and how long the kernel itself keeps trying (``full``)."""
    out = {}
    t0 = time.perf_counter()
    try:
        socket.create_connection((NOBODY, 9), timeout=patience)
        raise AssertionError("expected silence")
    except TimeoutError as exc:
        out["with_timeout"] = {
            "patience_s": patience,
            "s": round(time.perf_counter() - t0, 3),
            "error": type(exc).__name__,
            "text": str(exc),
        }
    if not full:
        return out
    c = socket.socket()
    c.setblocking(False)
    t0 = time.perf_counter()
    assert c.connect_ex((NOBODY, 9)) == errno.EINPROGRESS
    timers, last = [], None
    while True:
        _r, w, x = select.select([], [c], [c], 0.02)
        now = time.perf_counter() - t0
        if w or x:
            code = c.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            out["kernel"] = {"gave_up_s": round(now, 2), "errno": errno.errorcode[code],
                             "error": "TimeoutError",
                             "text": f"[Errno {code}] {os.strerror(code)}"}  # fmt: skip
            break
        rto = tcp_info(c)["rto"]
        if rto != last:
            timers.append({"s": round(now, 2), "timer_ms": rto})
            last = rto
        if now > 200:
            raise AssertionError("the kernel never gave up")
    c.close()
    out["timers"] = timers
    # SYNs: one at 0, then one each time the current timer runs out
    syn, t, i = [0.0], 0.0, 0
    while True:
        while i + 1 < len(timers) and timers[i + 1]["s"] <= t + 0.2:
            i += 1
        t += timers[i]["timer_ms"] / 1000
        if t >= out["kernel"]["gave_up_s"]:
            break
        syn.append(round(t, 2))
    out["syn_s"] = syn
    return out


# --------------------------------------------------------------------------- #
# 7. a proxy in front: 502 and 504
# --------------------------------------------------------------------------- #
def gateway(slow: float = 3.4, patience: float = 3.0) -> dict:
    out = {}
    up = server.Server().start()
    px = proxy.Proxy(up.port, patience=patience).start()
    t0 = time.perf_counter()
    status, _h, body = ask(px.port, client.request)
    out["healthy"] = {"status": status.split(" ", 1)[1], "s": round(time.perf_counter() - t0, 4),
                      "earns": json.loads(body)["earns"]}  # fmt: skip
    up.stop()  # the API process is gone: its port is closed
    time.sleep(0.05)
    t0 = time.perf_counter()
    status, _h, body = ask(px.port, client.request)
    out["upstream_down"] = {"status": status.split(" ", 1)[1], "s": round(time.perf_counter() - t0, 4),
                            "body": body.decode().strip()}  # fmt: skip
    px.stop()

    slow_up = server.Server(delay=slow).start()
    px = proxy.Proxy(slow_up.port, patience=patience).start()
    t0 = time.perf_counter()
    status, _h, body = ask(px.port, client.request)
    out["upstream_slow"] = {"status": status.split(" ", 1)[1], "s": round(time.perf_counter() - t0, 3),
                            "body": body.decode().strip(), "upstream_needs_s": slow,
                            "proxy_waits_s": patience}  # fmt: skip
    px.stop()
    slow_up.stop()
    assert out["healthy"]["status"] == "200 OK"
    assert out["upstream_down"]["status"] == "502 Bad Gateway"
    assert out["upstream_slow"]["status"] == "504 Gateway Timeout"
    return out


def curl_verbose(port: int = 8443) -> str | None:
    """What ``curl -v`` prints for the same request (kept for the README)."""
    files = pki.ensure()
    try:
        srv = server.Server(
            port, tls=server.tls_context(files["chain"], files["leaf_key"])
        ).start()
    except OSError:
        return None
    done = subprocess.run(
        ["curl", "-sv", "--cacert", str(files["root"]), "--resolve", f"{client.host}:{port}:{LOOP}",
         f"https://{client.host}:{port}/courses/lea", "-H", f"Authorization: Bearer {TOKEN}",
         "-H", "Accept: application/json"],
        capture_output=True, text=True, timeout=20,
    )  # fmt: skip
    srv.stop()
    if done.returncode:
        return None
    return done.stderr.replace(str(files["root"]), "demo-root.pem") + done.stdout + "\n"


if __name__ == "__main__":
    for fn in (plain_http, status_codes, keep_alive, eavesdrop, https, tls_failures, certificates,
               key_agreement, kernel, gateway):  # fmt: skip
        print(f"\n== {fn.__name__}")
        print(json.dumps(fn(), indent=1)[:2600])
    print("\n== silence (short)")
    print(json.dumps(silence(full=False), indent=1))
