"""demo/proxy.py: a reverse proxy in fifty lines, to see where 502 and 504 come from.

A load balancer or gateway is a server that answers by asking another server. When
that other server (the *upstream*) cannot be reached, or takes too long, the proxy
has no answer to relay, and says so with a status of its own:

    502 Bad Gateway       the upstream refused the connection or answered garbage
    504 Gateway Timeout   the upstream did not answer within the proxy's patience

(This proxy, nginx and the cloud load balancers answer 502 to a refused upstream;
HAProxy and Envoy answer 503 Service Unavailable in the same situation.)

Loopback only, one request per connection, no TLS: just enough to produce the two
codes for real.
"""

from __future__ import annotations

import socket
import threading

LOOPBACK = "127.0.0.1"


def _answer(conn, status, text):
    body = text.encode()
    conn.sendall(
        f"HTTP/1.1 {status}\r\nContent-Type: text/plain\r\nContent-Length: {len(body)}\r\n\r\n".encode()
        + body
    )


class Proxy:
    def __init__(self, upstream_port: int, patience: float = 3.0, port: int = 0):
        self.upstream, self.patience = (LOOPBACK, upstream_port), patience
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((LOOPBACK, port))
        self.sock.listen(16)
        self.port = self.sock.getsockname()[1]

    def start(self):
        threading.Thread(target=self._accept, daemon=True).start()
        return self

    def _accept(self):
        while True:
            try:
                conn, _peer = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._relay, args=(conn,), daemon=True).start()

    def _relay(self, conn):
        with conn:
            request = b""
            while b"\r\n\r\n" not in request:
                chunk = conn.recv(65536)
                if not chunk:
                    return
                request += chunk
            try:
                with socket.create_connection(
                    self.upstream, timeout=self.patience
                ) as up:
                    up.sendall(request)
                    reply = up.recv(65536)  # the demo's answers fit in one read
            except ConnectionRefusedError:
                return _answer(
                    conn, "502 Bad Gateway", "upstream refused the connection\n"
                )
            except TimeoutError:
                return _answer(
                    conn, "504 Gateway Timeout", "upstream did not answer in time\n"
                )
            conn.sendall(reply)

    def stop(self):
        self.sock.close()
