"""demo/pki.py: a throwaway certificate authority for the demo, made with ``openssl``.

A real server gets its certificate from an authority that every phone and laptop
already trusts. The demo plays all the parts: a root, an issuing authority signed by
the root, and the server's certificate signed by the issuing authority. It also
makes three certificates that must be refused: one signed by nobody known, one for
another name, one that has expired.

Keys and certificates are written OUTSIDE the repository (``~/.cache/manimx/
protocols-pki`` by default, or ``$PROTOCOLS_PKI``): private keys never belong in a
project folder. They are worthless anywhere but in this demo.

Needs the ``openssl`` command line, 3.4 or later (for ``-not_before``).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

HOST = "api.dispatch.example"
HOME = Path(
    os.environ.get("PROTOCOLS_PKI")
    or Path.home() / ".cache" / "manimx" / "protocols-pki"
)
ROOT_SUBJ = "/O=Demo Trust Services/CN=Demo Root CA"
ISSUING_SUBJ = "/O=Demo Trust Services/CN=Demo Issuing CA"


def openssl(*args) -> str:
    done = subprocess.run(["openssl", *map(str, args)], capture_output=True, text=True)
    if done.returncode:
        raise SystemExit(f"openssl {' '.join(map(str, args))}\n{done.stderr}")
    return done.stdout


def _key(name):
    path = HOME / f"{name}.key"
    openssl(
        "genpkey",
        "-algorithm",
        "EC",
        "-pkeyopt",
        "ec_paramgen_curve:P-256",
        "-out",
        path,
    )
    return path


def _ext(name, text):
    path = HOME / f"{name}.ext"
    path.write_text(text)
    return path


def _leaf(name, host, ca="issuing", days=90, window=None):
    """A server certificate for ``host`` signed by ``ca``."""
    key = _key(name)
    csr = HOME / f"{name}.csr"
    openssl("req", "-new", "-key", key, "-out", csr, "-subj", f"/CN={host}")
    ext = _ext(
        name,
        f"subjectAltName=DNS:{host}\nbasicConstraints=CA:FALSE\n"
        "keyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\n",
    )
    when = (
        ["-not_before", window[0], "-not_after", window[1]]
        if window
        else ["-days", days]
    )
    openssl(
        "x509", "-req", "-in", csr, "-CA", HOME / f"{ca}.pem", "-CAkey", HOME / f"{ca}.key",
        "-CAcreateserial", "-out", HOME / f"{name}.pem", *when, "-extfile", ext,
    )  # fmt: skip
    chain = HOME / f"{name}_chain.pem"
    chain.write_text(
        (HOME / f"{name}.pem").read_text() + (HOME / f"{ca}.pem").read_text()
    )
    return chain


def build() -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    # the root: signs itself, and lives in the client's trust store
    openssl(
        "req", "-x509", "-new", "-key", _key("root"), "-out", HOME / "root.pem", "-days", 3650,
        "-subj", ROOT_SUBJ, "-addext", "basicConstraints=critical,CA:TRUE",
        "-addext", "keyUsage=critical,keyCertSign,cRLSign",
    )  # fmt: skip
    # the issuing authority: signed by the root
    openssl(
        "req",
        "-new",
        "-key",
        _key("issuing"),
        "-out",
        HOME / "issuing.csr",
        "-subj",
        ISSUING_SUBJ,
    )
    openssl(
        "x509", "-req", "-in", HOME / "issuing.csr", "-CA", HOME / "root.pem",
        "-CAkey", HOME / "root.key", "-CAcreateserial", "-out", HOME / "issuing.pem",
        "-days", 1825, "-extfile",
        _ext("issuing", "basicConstraints=critical,CA:TRUE,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\n"),
    )  # fmt: skip
    _leaf("leaf", HOST)  # the server's certificate
    _leaf("othername", "api.other.example")  # a valid chain, for another name
    _leaf("expired", HOST, window=("20260101000000Z", "20260401000000Z"))
    # an impostor: the right name, signed by itself
    openssl(
        "req", "-x509", "-new", "-key", _key("impostor"), "-out", HOME / "impostor.pem",
        "-days", 90, "-subj", f"/CN={HOST}", "-addext", f"subjectAltName=DNS:{HOST}",
    )  # fmt: skip
    (HOME / "impostor_chain.pem").write_text((HOME / "impostor.pem").read_text())
    openssl(
        "verify",
        "-CAfile",
        HOME / "root.pem",
        "-untrusted",
        HOME / "issuing.pem",
        HOME / "leaf.pem",
    )


def ensure() -> dict:
    """Paths of the demo's keys and certificates (built on first use)."""
    if not (HOME / "impostor_chain.pem").exists():
        build()
    files = {
        "root": HOME / "root.pem",
        "issuing": HOME / "issuing.pem",
        "leaf": HOME / "leaf.pem",
    }
    for name in ("leaf", "othername", "expired", "impostor"):
        files[f"{name}_key"] = HOME / f"{name}.key"
        files["chain" if name == "leaf" else f"{name}_chain"] = (
            HOME / f"{name}_chain.pem"
        )
    return files


def describe(path) -> dict:
    """The fields of a certificate the film shows, read back with ``openssl``."""
    text = openssl(
        "x509", "-in", path, "-noout", "-subject", "-issuer", "-dates", "-ext",
        "subjectAltName,basicConstraints", "-nameopt", "RFC2253",
    )  # fmt: skip
    out = {}
    for line in text.splitlines():
        for key in ("subject", "issuer", "notBefore", "notAfter"):
            if line.startswith(key + "="):
                out[key] = line.split("=", 1)[1].strip()
        if "DNS:" in line:
            out["names"] = [p.strip().removeprefix("DNS:") for p in line.split(",")]
        if "CA:" in line:
            out["ca"] = "CA:TRUE" in line
    pub = openssl("x509", "-in", path, "-noout", "-text")
    out["key"] = "EC P-256" if "prime256v1" in pub else "?"
    out["signature"] = next(
        (
            ln.split(":", 1)[1].strip()
            for ln in pub.splitlines()
            if "Signature Algorithm" in ln
        ),
        "?",
    )
    out["bytes"] = len(ssl_der(path))
    return out


def ssl_der(path) -> bytes:
    import ssl

    return ssl.PEM_cert_to_DER_cert(
        Path(path).read_text().split("-----END CERTIFICATE-----")[0]
        + "-----END CERTIFICATE-----\n"
    )


if __name__ == "__main__":
    for name, path in ensure().items():
        print(f"{name:16s} {path}")
