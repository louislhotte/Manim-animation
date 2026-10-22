#!/usr/bin/env python3
"""Machine-check the Jacobian-conjecture counterexample used in this film.

No third-party dependencies — exact integer/rational arithmetic in pure Python.
It confirms the two facts the animation rests on:

  1. det(DF) is *exactly* the nonzero constant -2   (the hypothesis holds), and
  2. three distinct points collapse to one image     (F is not injective),

so F : C^3 -> C^3 satisfies the conjecture's hypothesis yet is not invertible.

    F1 = (1+z1*z2)**3*z3 + z2**2*(1+z1*z2)*(4+3*z1*z2)
    F2 = z2 + 3*z1*(1+z1*z2)**2*z3 + 3*z1*z2**2*(4+3*z1*z2)
    F3 = 2*z1 - 3*z1**2*z2 - z1**3*z3

Counterexample: L. Alpöge with Claude Fable 5 (Anthropic), 2026; digested by
Terence Tao, "A digestion of the Jacobian conjecture counterexample" (2026).

Run:  python3 verify.py
"""
from fractions import Fraction as Fr

# ---- a tiny exact multivariate-polynomial engine in z1,z2,z3 -------------- #
# a polynomial is a dict {(e1,e2,e3): coefficient(Fraction)}


def var(i):
    e = [0, 0, 0]
    e[i] = 1
    return {tuple(e): Fr(1)}


def const(c):
    return {(0, 0, 0): Fr(c)}


def add(a, b):
    r = dict(a)
    for k, v in b.items():
        r[k] = r.get(k, Fr(0)) + v
    return {k: v for k, v in r.items() if v != 0}


def mul(a, b):
    r = {}
    for ka, va in a.items():
        for kb, vb in b.items():
            k = (ka[0] + kb[0], ka[1] + kb[1], ka[2] + kb[2])
            r[k] = r.get(k, Fr(0)) + va * vb
    return {k: v for k, v in r.items() if v != 0}


def powp(a, n):
    r = const(1)
    for _ in range(n):
        r = mul(r, a)
    return r


def dpar(a, i):
    """partial derivative with respect to variable i."""
    r = {}
    for k, v in a.items():
        if k[i] > 0:
            nk = list(k)
            c = k[i]
            nk[i] -= 1
            r[tuple(nk)] = r.get(tuple(nk), Fr(0)) + v * c
    return {k: v for k, v in r.items() if v != 0}


z1, z2, z3 = var(0), var(1), var(2)
one = const(1)
u = add(one, mul(z1, z2))                              # 1 + z1*z2

F1 = add(mul(powp(u, 3), z3),
         mul(mul(powp(z2, 2), u), add(const(4), mul(const(3), mul(z1, z2)))))
F2 = add(add(z2, mul(mul(const(3), mul(z1, powp(u, 2))), z3)),
         mul(mul(const(3), mul(z1, powp(z2, 2))), add(const(4), mul(const(3), mul(z1, z2)))))
F3 = add(add(mul(const(2), z1), mul(const(-3), mul(powp(z1, 2), z2))),
         mul(const(-1), mul(powp(z1, 3), z3)))
F = [F1, F2, F3]


def det3(M):
    def t(a, b, c):
        return mul(mul(M[0][a], M[1][b]), M[2][c])
    pos = add(add(t(0, 1, 2), t(1, 2, 0)), t(2, 0, 1))
    neg = add(add(t(2, 1, 0), t(0, 2, 1)), t(1, 0, 2))
    return add(pos, {k: -v for k, v in neg.items()})


def total_degree(P):
    return max((sum(k) for k in P), default=0)


def evaluate(P, pt):
    s = Fr(0)
    for (e1, e2, e3), c in P.items():
        s += c * pt[0] ** e1 * pt[1] ** e2 * pt[2] ** e3
    return s


def main():
    print("degrees of (F1, F2, F3):", [total_degree(f) for f in F])

    J = [[dpar(F[r], c) for c in range(3)] for r in range(3)]
    D = det3(J)
    is_minus_two = (D == {(0, 0, 0): Fr(-2)})
    print("det(DF) =", {k: str(v) for k, v in D.items()},
          "-> exactly -2 (a nonzero constant)?", is_minus_two)

    pts = [(Fr(0), Fr(0), Fr(-1, 4)),
           (Fr(1), Fr(-3, 2), Fr(13, 2)),
           (Fr(-1), Fr(3, 2), Fr(13, 2))]
    images = []
    for p in pts:
        img = tuple(evaluate(f, p) for f in F)
        images.append(img)
        print(f"F({str(p[0]):>4}, {str(p[1]):>5}, {str(p[2]):>5}) = "
              f"({img[0]}, {img[1]}, {img[2]})")
    collide = all(im == images[0] for im in images) and len(set(pts)) == 3
    print("three distinct inputs, one image (not injective)?", collide)

    ok = is_minus_two and collide
    print("\nCOUNTEREXAMPLE VERIFIED" if ok else "\nVERIFICATION FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
