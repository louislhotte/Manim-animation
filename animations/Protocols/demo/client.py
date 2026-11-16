"""demo/client.py: one HTTPS request, the long way: five lines, one per step.

    python demo/server.py --tls      # in one terminal
    python demo/client.py            # in another

The block between the two marks is what the film shows, and what its laboratory
(``lab.py``) runs: the film cannot drift from the code. The last of the five lines
reads one whole response (``read_reply``), not just "whatever has arrived". On the real Internet the
first line would be a DNS query; in this demo both programs live on one machine,
so the "phone book" is a table with a single entry.
"""

from __future__ import annotations

import re
import socket
import ssl
import sys
from pathlib import Path

host = "api.dispatch.example"
request = (
    b"GET /courses/lea HTTP/1.1\r\n"
    b"Host: api.dispatch.example\r\n"
    b"Authorization: Bearer lea-4f1c9a\r\n"
    b"Accept: application/json\r\n"
    b"\r\n"
)

PHONE_BOOK = {host: ("127.0.0.1", 8443)}


def lookup(name):
    """Stands in for DNS: the address and port behind a name."""
    return PHONE_BOOK[name]


def trust(root_certificate) -> ssl.SSLContext:
    """The client's side of TLS: the authorities it trusts (here: the demo's root)."""
    ctx = ssl.create_default_context(cafile=str(root_certificate))
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.set_ecdh_curve("X25519")
    return ctx


def call(ctx, lookup=lookup):
    # --- the film's five lines ---------------------------------------------------
    ip, port = lookup(host)
    sock = socket.create_connection((ip, port))
    tls = ctx.wrap_socket(sock, server_hostname=host)
    tls.sendall(request)
    reply = read_reply(tls)
    # ------------------------------------------------------------------------------
    tls.close()
    return reply


def read_reply(conn) -> bytes:
    """One whole HTTP response, as bytes: the head up to the empty line, then as many
    bytes of body as its Content-Length announces.

    A single ``recv`` would only return what has arrived so far. TCP delivers a
    stream of bytes, not messages: it is HTTP that says where a message ends.
    """
    data = b""
    while b"\r\n\r\n" not in data:
        data += _more(conn)
    head, _, body = data.partition(b"\r\n\r\n")
    need = int(re.search(rb"content-length: *(\d+)", head, re.IGNORECASE).group(1))
    while len(body) < need:
        body += _more(conn)
    return head + b"\r\n\r\n" + body[:need]


def _more(conn) -> bytes:
    chunk = conn.recv(65536)
    if not chunk:
        raise ConnectionError("the connection closed before the reply was complete")
    return chunk


def read_response(conn, buf=b""):
    """A whole HTTP response from a connection: (status line, headers, body, rest)."""
    while b"\r\n\r\n" not in buf:
        chunk = conn.recv(65536)
        if not chunk:
            raise ConnectionError("the connection closed before the headers ended")
        buf += chunk
    head, buf = buf.split(b"\r\n\r\n", 1)
    status, *lines = head.decode("latin-1").split("\r\n")
    headers = {
        k.strip().lower(): v.strip() for k, v in (h.split(":", 1) for h in lines)
    }
    need = int(headers.get("content-length", 0))
    while len(buf) < need:
        chunk = conn.recv(65536)
        if not chunk:
            raise ConnectionError("the connection closed before the body ended")
        buf += chunk
    return status, headers, buf[:need], buf[need:]


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pki

    print(call(trust(pki.ensure()["root"])).decode())
