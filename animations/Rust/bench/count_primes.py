"""The Python half of the real benchmark shown in the film.

Counts primes below LIMIT by plain trial division — deliberately the same
algorithm, line for line, as bench/count_primes.rs. Single thread, no
libraries. Times the pure function (best of REPS) and prints JSON.
"""
import json
import sys
import time


def count_primes(limit):
    count = 0
    for n in range(2, limit):
        is_prime = True
        d = 2
        while d * d <= n:
            if n % d == 0:
                is_prime = False
                break
            d += 1
        if is_prime:
            count += 1
    return count


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    best = float("inf")
    count = 0
    for _ in range(reps):
        t0 = time.perf_counter()
        count = count_primes(limit)
        best = min(best, time.perf_counter() - t0)
    print(json.dumps({"count": count, "best_s": best}))
