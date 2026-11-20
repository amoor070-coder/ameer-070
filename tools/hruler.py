"""'المسطرة الأفقية': balance each letter's width against the Alexandria/Plex average,
relative to this font's own median proportion (keeps our identity, fixes the outliers).
Widening/narrowing is done at the column with the least ink (horizontal strokes only) so stroke
thickness never changes; tails/sidebearings used when no such column exists."""
import sys, numpy as np
sys.path.insert(0, '/home/claude/fa')
from fontTools.ttLib import TTFont
from wt import OUT, W, DOTMAX, WT
from hmeasure import table
ALPHA, THR = 0.6, 0.10
def F_ours_body(n):
    """(xmin of body, -, rsb) on the live (edited) glyph, dots excluded"""
    g = glyf[n]; co = g.coordinates; xs = []
    for idx in contours(g):
        px = [co[i][0] for i in idx]; py = [co[i][1] for i in idx]
        if max(px) - min(px) < DOTMAX and max(py) - min(py) < DOTMAX: continue
        xs += px
    return (min(xs), max(xs), hmtx[n][0] - max(xs))
tt = TTFont(OUT); glyf = tt['glyf']; hmtx = tt['hmtx']
def contours(g):
    out = []; s = 0
    for e in g.endPtsOfContours:
        out.append(list(range(s, e + 1))); s = e + 1
    return out
def coverage(g, x0, x1):
    """vertical ink per x-column (sampled every 4 units) for the big contours, by scanline polygon fill"""
    co = g.coordinates; xs = np.arange(x0, x1, 4)
    cov = np.zeros(len(xs))
    for idxs in contours(g):
        pts = [co[i] for i in idxs]
        w_ = max(p[0] for p in pts) - min(p[0] for p in pts); h_ = max(p[1] for p in pts) - min(p[1] for p in pts)
        if w_ < DOTMAX and h_ < DOTMAX: continue
        n = len(pts)
        area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(n))
        sgn = -1 if area > 0 else 1        # counters subtract
        for k, x in enumerate(xs):
            ys = []
            for i in range(n):
                (xa, ya), (xb, yb) = pts[i - 1], pts[i]
                if (xa <= x < xb) or (xb <= x < xa):
                    ys.append(ya + (x - xa) * (yb - ya) / (xb - xa))
            ys.sort()
            cov[k] += sgn * sum(ys[j + 1] - ys[j] for j in range(0, len(ys) - 1, 2))
    return xs, cov
def remap(g, f):
    co = g.coordinates
    for idxs in contours(g):
        xs = [co[i][0] for i in idxs]; ys = [co[i][1] for i in idxs]
        if max(xs) - min(xs) < DOTMAX and max(ys) - min(ys) < DOTMAX:
            c = (max(xs) + min(xs)) / 2; d = f(c) - c
            for i in idxs: co[i] = (round(co[i][0] + d), co[i][1])
        else:
            for i in idxs: co[i] = (round(f(co[i][0])), co[i][1])
    g.recalcBounds(glyf)
log = []
def stretch(n, delta, flat=0.4):
    """widen/narrow the shape by delta at a clean column (horizontal strokes only)."""
    r = _stretch(n, delta, 0.4)
    return r or _stretch(n, delta, 0.65)
def _stretch(n, delta, flat):
    g = glyf[n]
    x0, x1 = g.xMin, g.xMax; w = x1 - x0
    xs, cov = coverage(g, x0 + 0.12 * w, x1 - 0.12 * w)
    band = max(60, 2.2 * abs(delta)); win = max(1, int(band / 4)); best = None
    for i in range(0, max(1, len(xs) - win)):
        seg = cov[i:i + win]
        if len(seg) and seg.max() <= 2.8 * W and seg.max() - seg.min() <= flat * W:
            ctr = abs((xs[i] + band / 2) - (x0 + x1) / 2)
            if best is None or ctr < best[1]: best = (xs[i], ctr)
    if not best: return None
    a = best[0]; b = a + band
    remap(g, lambda x: x if x <= a else (x + delta if x >= b else a + (x - a) * (band + delta) / band))
    return f'stretch@{a:.0f}'
def tail(n, delta):
    """narrow a letter whose left part is a descending tail (reh/zain/waw): compress only the tail side."""
    g = glyf[n]; co = g.coordinates
    lows = []
    for idx in contours(g):
        px = [co[i][0] for i in idx]; py = [co[i][1] for i in idx]
        if max(px) - min(px) < DOTMAX and max(py) - min(py) < DOTMAX: continue   # dots are not a tail
        lows += [co[i][0] for i in idx if co[i][1] < -60]
    if not lows or delta >= 0: return None
    a = g.xMin; b = max(lows) - 0.2 * (max(lows) - a)       # tail region
    if b - a < 120: return None
    k = (b - a + delta) / (b - a)
    remap(g, lambda x: (x if x >= b else b - (b - x) * k) + delta)   # keep the right (joining) edge on the advance
    return f'tail x{k:.2f}'
m, rows = table(OUT)
for r in rows:
    n, form = r['n'], r['form']
    if n.startswith(('alef', 'lam')) or n in ('heh.init', 'heh.medi'): continue
    g = glyf[n]
    if g.isComposite() or not g.numberOfContours: continue
    adv0 = hmtx[n][0]; how = []
    # 1) the shape itself
    if abs(r['rel'] - 1) >= 0.12:
        widen = r['rel'] < 1
        k_ = (0.6 if widen else 0.4) * (0.6 if form in ('init', 'medi') else 1.0)
        delta = round(k_ * (m * r['tw'] - r['w']))
        delta = max(-0.25 * r['w'], min(0.3 * r['w'], delta))
        h = stretch(n, delta) if widen else (tail(n, delta) or stretch(n, delta))
        if h:
            hmtx[n] = (int(round(adv0 + delta)), glyf[n].xMin); how.append(f'{h} {delta:+.0f}')
    # 2) spacing on the free sides only
    g = glyf[n]; adv = hmtx[n][0]
    body_l = r['lsb'] + (g.xMin - r['lsb'] if False else 0)
    from measure import F
    if form in ('isol', 'fina'):
        cur = F_ours_body(n)[0]
        d = 0.5 * (r['tlsb'] - cur)
        if abs(r['tlsb'] - cur) > 25:
            remap(g, lambda x: x + d); hmtx[n] = (int(round(adv + d)), g.xMin); adv = hmtx[n][0]; how.append(f'lsb {d:+.0f}')
    if form in ('isol', 'init'):
        cur = F_ours_body(n)[2]
        d = 0.5 * (r['trsb'] - cur)
        if abs(r['trsb'] - cur) > 25:
            hmtx[n] = (int(round(adv + d)), g.xMin); how.append(f'rsb {d:+.0f}')
    if how: log.append(f"{n}: {adv0} -> {hmtx[n][0]}  " + ', '.join(how))
# alef + madda: same advance as the plain alef, madda centred on the stem (overhangs like the references)
for s in ('isol', 'fina'):
    n, base = f'alefMadda.{s}', f'alef.{s}'
    g = glyf[n]; adv = hmtx[base][0]; gb = glyf[base]
    stem_c = (gb.xMin + gb.xMax) / 2
    big = [idx for idx in contours(g) if max(g.coordinates[i][1] for i in idx) - min(g.coordinates[i][1] for i in idx) > 300]
    sx = [g.coordinates[i][0] for idx in big for i in idx]
    d = stem_c - (min(sx) + max(sx)) / 2
    remap(g, lambda x: x + d); hmtx[n] = (adv, g.xMin); log.append(f'{n}: adv -> {adv} (madda overhang)')
tt.save(OUT)
print('\n'.join(log)); print(len(log), 'glyphs balanced (h-ruler)', WT, 'median', round(m, 3))
