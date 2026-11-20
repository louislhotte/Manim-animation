"""What the Certificates film states, and what it computes.

THE CERTIFICATES ON SCREEN ARE AN ILLUSTRATION. Nothing was generated with a
certificate tool and no key exists: the fields are written here by hand, with names
from the reserved ``.example`` domain, and the film says so at the bottom of the
screen. Three things are real:

* every fingerprint is the SHA-256 (``hashlib``) of the text shown on the card, so
  changing one letter really changes it, and the number of bytes that differ is
  counted, not chosen;
* the checks of the last scene are evaluated on these fields (dates against
  ``TODAY``, name against the address typed);
* the facts with a source below.

    python facts.py        # prints everything the narration and the screen state
"""

import hashlib
from datetime import date, timedelta

TODAY = date(2026, 11, 20)  # the day the film was made: "today" on screen
HOST = "shop.example"  # the address the user types
ISSUER = "Example CA"
ROOT = "Example Root"
NOT_BEFORE = date(2026, 10, 1)

# Maximum lifetime of a publicly trusted TLS server certificate, by date of issue
# (authorities' own certificates and private ones are not bound by it).
# Source: CA/Browser Forum ballot SC-081v3 (adopted 11 April 2025); 398 days was the
# limit since 1 September 2020.
MAX_DAYS = {
    date(2020, 9, 1): 398,
    date(2026, 3, 15): 200,
    date(2027, 3, 15): 100,
    date(2029, 3, 15): 47,
}
LIMIT_TODAY = [d for start, d in MAX_DAYS.items() if start <= TODAY][-1]
# one day under the limit: both ends of the period count
NOT_AFTER = NOT_BEFORE + timedelta(days=LIMIT_TODAY - 1)

# Root certificates in /etc/ssl/cert.pem on the Mac that rendered the film (counted
# with grep on 2026-11-20). That file is the macOS bundle for command-line tools
# (LibreSSL, curl): Safari uses the system keychain, Chrome and Firefox their own
# lists, each with its own count.
ROOTS_HERE = 128

# How Chrome names the three failures (its error page prints NET::<name>).
ERRORS = {
    "chain": "ERR_CERT_AUTHORITY_INVALID",
    "dates": "ERR_CERT_DATE_INVALID",
    "name": "ERR_CERT_COMMON_NAME_INVALID",
}


def day(d: date) -> str:
    return f"{d.day} {d:%b %Y}"


def fields(name=HOST, not_after=NOT_AFTER, issuer=ISSUER):
    """The four fields of the card, as (label, text shown)."""
    return [
        ("name", name),
        ("public key", "the shop's public key"),
        ("valid", f"{day(NOT_BEFORE)} to {day(not_after)}"),
        ("issued by", issuer),
    ]


def signed_text(name=HOST) -> bytes:
    """What the authority hashes: the fields, one per line."""
    return "\n".join(f"{k}: {v}" for k, v in fields(name)).encode()


def fingerprint(name=HOST) -> bytes:
    return hashlib.sha256(signed_text(name)).digest()


TAMPERED = "sh0p.example"  # one letter changed
FP, FP_BAD = fingerprint(), fingerprint(TAMPERED)
BYTES_CHANGED = sum(a != b for a, b in zip(FP, FP_BAD, strict=True))
BITS_CHANGED = sum(bin(a ^ b).count("1") for a, b in zip(FP, FP_BAD, strict=True))
# Eight bytes that stand for the fresh random numbers of a handshake (a real client
# random is 32 bytes): what the server signs, together with the rest of the handshake.
CHALLENGE = hashlib.sha256(f"challenge {TODAY}".encode()).digest()[:8]

# The three broken certificates of the last scene, and the check each one fails.
EXPIRED_ON = TODAY - timedelta(days=1)  # a certificate that ended yesterday


def checks(name=HOST, not_after=NOT_AFTER, issuer=ISSUER, typed=HOST, today=TODAY):
    """The browser's three checks on these fields: {check: passed}."""
    return {
        "chain": issuer == ISSUER,  # an issuer that leads to a root the device holds
        "dates": NOT_BEFORE <= today <= not_after,
        "name": name == typed,
    }


BROKEN = {
    "chain": {"issuer": "Unknown CA"},  # an issuer no root on the device vouches for
    "dates": {"not_after": EXPIRED_ON},
    "name": {"name": TAMPERED},
}

assert all(checks().values())
for failing, change in BROKEN.items():
    outcome = checks(**change)
    assert not outcome[failing] and sum(outcome.values()) == 2, failing
assert (NOT_AFTER - NOT_BEFORE).days + 1 == LIMIT_TODAY == 200
assert NOT_BEFORE < EXPIRED_ON < TODAY < NOT_AFTER
assert FP != FP_BAD and len(FP) == 32 and BYTES_CHANGED >= 30
assert sum(c != d for c, d in zip(HOST, TAMPERED, strict=True)) == 1
assert list(MAX_DAYS.values()) == [398, 200, 100, 47]

if __name__ == "__main__":
    print("signed text:\n" + signed_text().decode())
    print("fingerprint        ", FP.hex())
    print("after one letter   ", FP_BAD.hex())
    print(f"{BYTES_CHANGED} of 32 bytes differ, {BITS_CHANGED} of 256 bits")
    print("valid", day(NOT_BEFORE), "to", day(NOT_AFTER), f"({LIMIT_TODAY} days)")
    print("challenge", CHALLENGE.hex())
    print("checks", checks(), {k: checks(**v) for k, v in BROKEN.items()})
