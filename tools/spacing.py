"""'مسطرة الفراغ': keep a clear gap between neighbouring letters (every Arabic pair, shaped).
Connected pairs get a slightly longer join (kashida) on the overhanging letter; unconnected pairs get side bearing.
Two passes: measure -> fix -> measure."""
import sys, numpy as np
sys.path.insert(0, '/home/claude/fa')
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import RecordingPen
import pathops
from wt import OUT, W, WT
import pairs
from draw import set_glyph
G = 0.35 * W
def deficits():
    pairs.CACHE.clear()
    res = pairs.scan(OUT)
    L, R = {}, {}
    for d, t, n1, n2, joined in res:
        if d >= G: continue
        df = G - d
        if joined:
            L.setdefault(n2, []).append(df)                 # the right glyph opens its join on the left
        else:
            if not n2.endswith(('.init', '.medi')): L.setdefault(n2, []).append(df / 2)
            if not n1.endswith(('.medi', '.fina')): R.setdefault(n1, []).append(df / 2)
    agg = lambda v: min(1.0 * W, float(np.percentile(v, 90)))
    return {k: agg(v) for k, v in L.items()}, {k: agg(v) for k, v in R.items()}, len([r for r in res if r[0] < G])
def glyph_path(tt, n):
    gs = tt.getGlyphSet(); p = pathops.Path(); gs[n].draw(p.getPen()); return p
def apply(L, R):
    tt = TTFont(OUT); hm = tt['hmtx']
    for n, d in L.items():
        d = round(d)
        if d < 3: continue
        p = glyph_path(tt, n); adv = hm[n][0]
        q = pathops.Path(); rp = RecordingPen(); p.draw(rp)
        pen = q.getPen()
        for op, a in rp.value: getattr(pen, op)(*[(x + d, y) for x, y in a])
        if n.endswith(('.init', '.medi')):            # extend the join so the connection stays continuous
            r = pathops.Path(); rp_ = r.getPen()
            rp_.moveTo((-8, 0)); rp_.lineTo((d + 0.5 * W, 0)); rp_.lineTo((d + 0.5 * W, W)); rp_.lineTo((-8, W)); rp_.closePath()
            q = pathops.op(q, r, pathops.PathOp.UNION)
        set_glyph(tt, n, q, adv=adv + d)
    for n, d in R.items():
        d = round(d)
        if d < 3: continue
        adv, lsb = hm[n]; hm[n] = (adv + d, lsb)
    tt.save(OUT)
for it in range(2):
    L, R, nbad = deficits()
    print(f'{WT} pass {it+1}: tight pairs {nbad}, fixing {len(L)} left / {len(R)} right sides')
    apply(L, R)
L, R, nbad = deficits(); print(f'{WT} after: tight pairs {nbad}')
