"""demo/server.py: the dispatch API of the film, written on raw sockets.

    python demo/server.py            # plain HTTP on 127.0.0.1:8080
    python demo/server.py --tls      # HTTPS on 127.0.0.1:8443 (throwaway certificates)

HTTP is text over a TCP connection, so the standard library's ``socket`` is all a
server needs: accept a connection, read bytes up to the blank line, answer with a
status line, headers, a blank line and a body. With ``--tls`` the very same loop
runs inside ``ssl``: that is all HTTPS adds on this side.

The server listens on the loopback address only: nothing outside this machine can
reach it. It sends only the headers the film talks about (a production server would
add ``Date``, ``Server``, cache rules ...).
"""

from __future__ import annotations

import json
import re
import socket
import ssl
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOST = "api.dispatch.example"  # the name in the certificate and in the Host header
LOOPBACK = "127.0.0.1"
JSON = "application/json"

COURSES = json.loads((HERE / "courses.json").read_text())
MAP_FILE = HERE.parent / "assets" / "course_map.ppm"
TOKENS = {
    "lea-4f1c9a": "lea"
}  # made up for the demo: the server exists on loopback only


def compact(obj) -> bytes:
    return json.dumps(obj, separators=(",", ":")).encode()


def respond(method: str, path: str, headers: dict) -> tuple[str, str, bytes]:
    """One request in, one response out: (status, content type, body)."""
    if path == "/health":
        return "200 OK", "text/plain", b"ok\n"
    token = headers.get("authorization", "").removeprefix("Bearer ")
    if token not in TOKENS:
        return "401 Unauthorized", JSON, compact({"error": "who is asking?"})
    match = re.fullmatch(r"/courses/([a-z]+)(/map|/eta)?", path)
    if method != "GET" or not match:
        return "404 Not Found", JSON, compact({"error": "no such resource"})
    name, what = match.groups()
    if name not in COURSES:
        return "404 Not Found", JSON, compact({"error": "no such courier"})
    if what == "/map":
        return "200 OK", "image/x-portable-pixmap", MAP_FILE.read_bytes()
    if what == "/eta":  # the bug of the film: a course that has not started yet
        km_left, km_per_min = 4.2, 0.0
        return "200 OK", JSON, compact({"minutes": km_left / km_per_min})
    return "200 OK", JSON, compact(COURSES[name])


def converse(conn, delay: float = 0.0, log=None) -> None:
    """One connection, any number of requests: HTTP/1.1 keeps it open by default."""
    buf = b""
    while True:
        while b"\r\n\r\n" not in buf:
            chunk = conn.recv(65536)
            if not chunk:
                return
            buf += chunk
        head, buf = buf.split(b"\r\n\r\n", 1)
        request_line, *lines = head.decode("latin-1").split("\r\n")
        method, path, _version = request_line.split(" ")
        headers = {
            k.strip().lower(): v.strip() for k, v in (h.split(":", 1) for h in lines)
        }
        try:
            status, ctype, body = respond(method, path, headers)
        except Exception as exc:  # a bug in a handler is the server's fault: 5xx
            status, ctype = "500 Internal Server Error", JSON
            body = compact({"error": type(exc).__name__})
        if delay:
            time.sleep(delay)
        if log is not None:
            log.append((request_line, status))
        head = f"HTTP/1.1 {status}\r\nContent-Type: {ctype}\r\nContent-Length: {len(body)}\r\n\r\n"
        conn.sendall(head.encode() + body)
        if headers.get("connection", "").lower() == "close":
            return


class Server:
    """``Server(port).start()`` serves in the background; ``.stop()`` closes the door."""

    def __init__(
        self, port: int = 0, tls: ssl.SSLContext | None = None, delay: float = 0.0
    ):
        self.tls, self.delay, self.log = tls, delay, []
        self.accepted = 0  # connections so far
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((LOOPBACK, port))  # a program takes a port ...
        self.sock.listen(16)  # ... and waits for connections
        self.port = self.sock.getsockname()[1]

    def start(self):
        threading.Thread(target=self._accept, daemon=True).start()
        return self

    def _accept(self):
        while True:
            try:
                conn, _peer = self.sock.accept()  # one new socket per connection
            except OSError:
                return
            self.accepted += 1
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn):
        try:
            if self.tls is not None:
                conn = self.tls.wrap_socket(conn, server_side=True)
            converse(conn, self.delay, self.log)
        except (OSError, ssl.SSLError):
            pass  # the other side went away, or refused our certificate
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def stop(self):
        self.sock.close()


def tls_context(chain: Path, key: Path) -> ssl.SSLContext:
    """What the server needs for HTTPS: its certificate chain and its private key."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(str(chain), str(key))
    ctx.set_ecdh_curve("X25519")  # one classic key exchange, so the film can show it
    return ctx


if __name__ == "__main__":
    tls = None
    if "--tls" in sys.argv:
        sys.path.insert(0, str(HERE))
        import pki

        files = pki.ensure()
        tls = tls_context(files["chain"], files["leaf_key"])
    server = Server(8443 if tls else 8080, tls).start()
    print(
        f"listening on {LOOPBACK}:{server.port} ({'HTTPS' if tls else 'HTTP'}); Ctrl-C stops it"
    )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
