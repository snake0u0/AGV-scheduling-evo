"""Unit tests for the GA operators, especially POX (the reference repo's POX was
dead code that returned its parents unchanged). Run: python -m fjspt.test_ga_operators"""
import random

from .ga import mutate_os, pox, uniform_ms


def op_counts(seq):
    c = {}
    for j in seq:
        c[j] = c.get(j, 0) + 1
    return c


def main():
    rng = random.Random(0)
    n_jobs = 5
    # OS for 5 jobs with 3 ops each
    base = [j for j in range(n_jobs) for _ in range(3)]
    ok = True

    # POX: preserves per-job operation counts, and actually recombines
    changed = 0
    for _ in range(200):
        p1, p2 = list(base), list(base)
        rng.shuffle(p1); rng.shuffle(p2)
        child = pox(p1, p2, n_jobs, rng)
        if op_counts(child) != op_counts(base):
            print(f"FAIL POX: op counts not preserved: {op_counts(child)}")
            ok = False
            break
        if child != p1:
            changed += 1
    if changed == 0:
        print("FAIL POX: child never differs from parent 1 (the dead-code bug)")
        ok = False
    else:
        print(f"POX: op counts preserved, child differs from parent1 in {changed}/200 cases")

    # uniform MS crossover: each gene comes from one of the two parents
    m1 = [0, 1, 2, 3]
    m2 = [3, 2, 1, 0]
    for _ in range(50):
        child = uniform_ms(m1, m2, rng)
        if any(c not in (a, b) for c, a, b in zip(child, m1, m2)):
            print("FAIL uniform_ms: gene not from either parent")
            ok = False
            break
    else:
        print("uniform_ms: every gene inherited from one parent")

    # OS mutation: preserves op counts
    for _ in range(200):
        child = mutate_os(base, rng)
        if op_counts(child) != op_counts(base):
            print("FAIL mutate_os: op counts not preserved")
            ok = False
            break
    else:
        print("mutate_os: op counts preserved")

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
