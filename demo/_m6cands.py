C1 = '''def priority(item, bins):
    r = bins - item
    s = 1.0 - 0.001 * r
    s[r < 20] = -0.5 - 0.05 * r[r < 20]
    s[r <= 6] = 3.0 - 0.35 * r[r <= 6]
    s[r == 0] = 8.0
    return s'''

C2 = '''def priority(item, bins):
    r = bins - item
    s = -r
    s[(r > 0) & (r < 20)] -= 200.0
    s[r == 0] += 400.0
    return s'''

C3 = '''def priority(item, bins):
    r = bins - item
    tight = np.maximum(6.0 - r, 0.0)
    s = tight * tight + 0.001 * r
    s[(r > 6) & (r < 20)] = -1.0
    return s'''

C4 = '''def priority(item, bins):
    r = bins - item
    s = r * 0.001
    s[r < 20] = -10.0 + r[r < 20] * 0.001
    s[r <= 5] = 5.0 - r[r <= 5]
    s[r == 0] = 50.0
    return s'''

C5 = '''def priority(item, bins):
    r = bins - item
    s = -np.sqrt(r + 1.0)
    s[(r > 0) & (r < 20)] = -5.0 - 0.1 * r[(r > 0) & (r < 20)]
    s[r == 0] = 100.0
    return s'''

C6 = '''def priority(item, bins):
    r = bins - item
    s = np.full(len(bins), 0.99)
    s[r < 20] = 0.90 - 0.02 * r[r < 20]
    s[r <= 6] = 2.0 - 0.3 * r[r <= 6]
    s[r == 0] = 5.0
    return s'''

CANDS = [("C1", C1), ("C2", C2), ("C3", C3), ("C4", C4), ("C5", C5), ("C6", C6)]
