"""x25519.py: the key agreement of TLS 1.3, in plain Python (RFC 7748).

Each side keeps a secret number and publishes ``x25519(secret, 9)``. Each then
combines its own secret with the other's public value, and both land on the same
32 bytes: ``x25519(a, B) == x25519(b, A)``. Someone who saw only ``A`` and ``B``
has no known way to compute them.

The film's bake checks this file against the RFC's test vectors and against
OpenSSL (the library that runs the real handshake), then uses it for the picture
of the two matching keys. Not constant-time: for explanation, never for real keys.
"""

from __future__ import annotations

P = 2**255 - 19
A24 = 121665
BASE = (9).to_bytes(32, "little")


def _scalar(k: bytes) -> int:
    b = bytearray(k)
    b[0] &= 248
    b[31] &= 127
    b[31] |= 64
    return int.from_bytes(b, "little")


def _u(u: bytes) -> int:
    b = bytearray(u)
    b[31] &= 127
    return int.from_bytes(b, "little")


def x25519(k: bytes, u: bytes = BASE) -> bytes:
    """Scalar multiplication on Curve25519 (the Montgomery ladder of RFC 7748)."""
    k_int, x1 = _scalar(k), _u(u)
    x2, z2, x3, z3, swap = 1, 0, x1, 1, 0
    for t in reversed(range(255)):
        bit = (k_int >> t) & 1
        if swap ^ bit:
            x2, x3, z2, z3 = x3, x2, z3, z2
        swap = bit
        a, b = (x2 + z2) % P, (x2 - z2) % P
        aa, bb = a * a % P, b * b % P
        e = (aa - bb) % P
        c, d = (x3 + z3) % P, (x3 - z3) % P
        da, cb = d * a % P, c * b % P
        x3 = (da + cb) ** 2 % P
        z3 = x1 * (da - cb) ** 2 % P
        x2 = aa * bb % P
        z2 = e * (aa + A24 * e) % P
    if swap:
        x2, x3, z2, z3 = x3, x2, z3, z2
    return (x2 * pow(z2, P - 2, P) % P).to_bytes(32, "little")


def self_test() -> None:
    """The Diffie-Hellman example of RFC 7748, section 6.1."""
    h = bytes.fromhex
    a = h("77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a")
    b = h("5dab087e624a8a4b79e17f8b83800ee66f3bb1292618b6fd1c2f8b27ff88e0eb")
    pub_a = h("8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a")
    pub_b = h("de9edb7d7b7dc1b4d35b61c2ece435373f8343c85b78674dadfc7e146f882b4f")
    shared = h("4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742")
    assert x25519(a) == pub_a and x25519(b) == pub_b
    assert x25519(a, pub_b) == shared == x25519(b, pub_a)


if __name__ == "__main__":
    self_test()
    print("x25519: RFC 7748 vectors pass")
