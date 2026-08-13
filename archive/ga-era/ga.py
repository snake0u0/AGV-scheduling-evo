"""GA skeleton, faithful to the DCGA structure (Han 2024) so comparisons are fair.

The only thing that varies between B1/B2/P is the AGV rule passed to decode; the
GA operators, population size, and time budget are identical. Creativity here would
undermine the ablation, so this deliberately mirrors the paper.
"""
import random
import time

from simulator.evaluator import decode


class Chromosome:
    __slots__ = ("OS", "MS", "fitness")

    def __init__(self, OS, MS, fitness=None):
        self.OS = OS
        self.MS = MS
        self.fitness = fitness

    def copy(self):
        return Chromosome(list(self.OS), list(self.MS), self.fitness)


def random_chromosome(inst, rng, ms_init="random", greedy_p=0.8):
    """ms_init='greedy' biases each gene towards the shortest-processing-time machine
    with probability greedy_p, keeping the rest random so the population still varies.
    Used to test whether the machine-selection search is failing for want of any
    structural signal at all (2026-07-31 diagnosis)."""
    OS = [j for j, ops in enumerate(inst.jobs) for _ in ops]
    rng.shuffle(OS)
    MS = []
    for ops in inst.jobs:
        for o in range(len(ops)):
            alts = ops[o]
            if ms_init == "greedy" and len(alts) > 1 and rng.random() < greedy_p:
                MS.append(min(range(len(alts)), key=lambda i: alts[i][1]))
            else:
                MS.append(rng.randrange(len(alts)))
    return Chromosome(OS, MS)


# --- crossover --------------------------------------------------------------

def pox(os1, os2, n_jobs, rng):
    """Precedence-preserving order crossover on the operation sequence.
    Jobs in a random subset keep their positions from parent 1; the rest are
    filled in parent 2's order. Preserves each job's operation count -> always
    feasible. (The reference repo's POX returned its parents unchanged - a bug;
    this one is unit-tested in test_ga_operators.)"""
    jobs = list(range(n_jobs))
    rng.shuffle(jobs)
    keep = set(jobs[:max(1, n_jobs // 2)])

    child = [None] * len(os1)
    for i, j in enumerate(os1):
        if j in keep:
            child[i] = j
    fill = [j for j in os2 if j not in keep]
    it = iter(fill)
    for i in range(len(child)):
        if child[i] is None:
            child[i] = next(it)
    return child


def uniform_ms(ms1, ms2, rng):
    """Uniform crossover on the machine-selection string."""
    return [a if rng.random() < 0.5 else b for a, b in zip(ms1, ms2)]


# --- mutation ---------------------------------------------------------------

def mutate_os(os_, rng):
    """One of swap / insert / inversion, chosen at random."""
    os_ = list(os_)
    n = len(os_)
    if n < 2:
        return os_
    op = rng.randrange(3)
    a, b = sorted(rng.sample(range(n), 2))
    if op == 0:                                  # swap
        os_[a], os_[b] = os_[b], os_[a]
    elif op == 1:                                # insert
        g = os_.pop(b)
        os_.insert(a, g)
    else:                                        # inversion
        os_[a:b + 1] = reversed(os_[a:b + 1])
    return os_


def mutate_ms(ms, inst, rng, rate=0.1):
    """Reassign some operations to another eligible machine."""
    ms = list(ms)
    idx = 0
    for ops in inst.jobs:
        for o in range(len(ops)):
            if len(ops[o]) > 1 and rng.random() < rate:
                ms[idx] = rng.randrange(len(ops[o]))
            idx += 1
    return ms


# --- GA loop ----------------------------------------------------------------

class GA:
    def __init__(self, inst, rule, pop_size=100, n_gen=100, pc=0.9, pm=0.1,
                 n_elite=10, seed=0, time_limit=None, ms_init="random"):
        self.inst = inst
        self.rule = rule
        self.pop_size = pop_size
        self.n_gen = n_gen
        self.pc = pc
        self.pm = pm
        self.n_elite = n_elite
        self.rng = random.Random(seed)
        self.time_limit = time_limit    # wall-clock seconds; n_gen becomes an upper cap
        self.ms_init = ms_init
        self.n_gen_done = 0
        self.n_evals = 0                # exact count; elites carry their fitness over
        self.last_improve_gen = 0       # generation of the last improvement to the best

    def evaluate(self, c):
        if c.fitness is None:
            _, sched = decode(self.inst, c.OS, c.MS, self.rule)
            c.fitness = sched.cmax
            self.n_evals += 1
        return c.fitness

    def tournament(self, pop):
        a, b = self.rng.sample(pop, 2)
        return a if a.fitness <= b.fitness else b

    def run(self):
        deadline = None if self.time_limit is None else time.time() + self.time_limit
        pop = [random_chromosome(self.inst, self.rng, self.ms_init)
               for _ in range(self.pop_size)]
        for c in pop:
            self.evaluate(c)
        best = min(pop, key=lambda c: c.fitness).copy()
        history = [best.fitness]

        for g in range(self.n_gen):
            if deadline is not None and time.time() >= deadline:
                break
            self.n_gen_done = g + 1
            pop.sort(key=lambda c: c.fitness)
            nxt = [c.copy() for c in pop[:self.n_elite]]        # elitism
            while len(nxt) < self.pop_size:
                p1, p2 = self.tournament(pop), self.tournament(pop)
                if self.rng.random() < self.pc:
                    OS = pox(p1.OS, p2.OS, self.inst.n_jobs, self.rng)
                    MS = uniform_ms(p1.MS, p2.MS, self.rng)
                else:
                    OS, MS = list(p1.OS), list(p1.MS)
                if self.rng.random() < self.pm:
                    OS = mutate_os(OS, self.rng)
                    MS = mutate_ms(MS, self.inst, self.rng)
                nxt.append(Chromosome(OS, MS))
            pop = nxt
            for c in pop:
                self.evaluate(c)
            gen_best = min(pop, key=lambda c: c.fitness)
            if gen_best.fitness < best.fitness:
                best = gen_best.copy()
                self.last_improve_gen = g + 1
            history.append(best.fitness)

        return best, history
