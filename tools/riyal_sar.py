"""Saudi Riyal sign U+20C1 from the official SAMA artwork (Saudi_Riyal_Symbol-2.svg, sama.gov.sa),
adapted per SAMA 'Font Designers' Guidelines': weight and width may change, structure and proportions kept.
 - top of the lam = top of the Latin figures (636), lam sits on the baseline, yaa dots below it
 - stems get the Latin stroke of each weight; bars get a lighter thickness in heavy weights so the gaps stay open
 - extra width is added between alef and lam in heavy weights (alef-lam gap stays smaller than the outer segments)
 - right side-bearing about 1.5x the alef-lam gap
usage: WT=Black python3 riyal_sar.py   (edits the sample TTF in place)"""
import sys, re, pathops, skia
sys.path.insert(0, '/home/claude/fa')
from wt import WT, OUT, CFG
from fontTools.ttLib import TTFont
from fontTools.svgLib.path import parse_path
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen

SVG = '/home/claude/fa/riyal/official.svg'
LAM_BOT, LAM_TOP = 248.0, 1244.0           # official artwork units (y up)
FIG = 636.0                                 # top of Latin figures
K = FIG / (LAM_TOP - LAM_BOT)               # 0.6386
S0 = 131.25 * K                             # official stroke at our size (83.8)
WL = CFG['WL']
BAR = {'Light': 62, 'Regular': 86, 'Bold': 104, 'Black': 112}[WT]
GAP_AL = {'Light': 92, 'Regular': 85, 'Bold': 68, 'Black': 60}[WT]   # alef-lam gap target
LSB, ROUND = 55, 7

def official():
    s = open(SVG).read(); P = pathops.Path()
    for d in re.findall(r'd="([^"]+)"', s):
        parse_path(d, TransformPen(P.getPen(), (1, 0, 0, -1, 0, 1256.39)))
    P.simplify(fix_winding=True); return P

def transform(P, f):
    rp = RecordingPen(); P.draw(rp); Q = pathops.Path(); pen = Q.getPen()
    for op, a in rp.value: getattr(pen, op)(*[f(*p) for p in a])
    return Q

def to_skia(P):
    rp = RecordingPen(); P.draw(rp); sp = skia.Path()
    for op, a in rp.value:
        if op == 'moveTo': sp.moveTo(*a[0])
        elif op == 'lineTo': sp.lineTo(*a[0])
        elif op == 'curveTo': sp.cubicTo(*a[0], *a[1], *a[2])
        elif op == 'qCurveTo':
            pp = list(a)
            while len(pp) > 2:
                mid = ((pp[0][0] + pp[1][0]) / 2, (pp[0][1] + pp[1][1]) / 2); sp.quadTo(*pp[0], *mid); pp = pp[1:]
            sp.quadTo(*pp[0], *pp[1])
        elif op == 'closePath': sp.close()
    return sp

def from_skia(sp):
    P = pathops.Path(); pen = P.getPen()
    it = skia.Path.Iter(sp, False)
    while True:
        verb, pts = it.next()
        if verb == skia.Path.kDone_Verb: break
        if verb == skia.Path.kMove_Verb: pen.moveTo(tuple(pts[0]))
        elif verb == skia.Path.kLine_Verb: pen.lineTo(tuple(pts[1]))
        elif verb == skia.Path.kQuad_Verb: pen.qCurveTo(tuple(pts[1]), tuple(pts[2]))
        elif verb == skia.Path.kConic_Verb:
            q = skia.Path.ConvertConicToQuads(pts[0], pts[1], pts[2], it.conicWeight(), 2)
            for i in range(1, len(q) - 1, 2): pen.qCurveTo(tuple(q[i]), tuple(q[i + 1]))
        elif verb == skia.Path.kCubic_Verb: pen.curveTo(tuple(pts[1]), tuple(pts[2]), tuple(pts[3]))
        elif verb == skia.Path.kClose_Verb: pen.closePath()
    return P

def offset(P, dx, dy, join=skia.Paint.kMiter_Join):
    """anisotropic offset: horizontal edges move dy, vertical edges dx (dx, dy same sign)"""
    if abs(dx) < 0.3 and abs(dy) < 0.3: return P
    r = dy / dx
    Q = transform(P, lambda x, y: (x, y / r))
    sp = to_skia(Q)
    paint = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=2 * abs(dx), StrokeJoin=join, StrokeMiter=2)
    out = skia.Path(); paint.getFillPath(sp, out)
    st = from_skia(out); st.simplify(fix_winding=True)
    R = pathops.op(Q, st, pathops.PathOp.UNION if dx > 0 else pathops.PathOp.DIFFERENCE, fix_winding=True)
    return transform(R, lambda x, y: (x, y * r))

def roundoff(P, r):
    """soften convex corners slightly (font identity): erode then dilate with round joins"""
    A = offset(P, -r, -r, skia.Paint.kRound_Join)
    return offset(A, r, r, skia.Paint.kRound_Join)


def polys(P, steps=20):
    rp = RecordingPen(); P.draw(rp); out = []; cur = []; last = None
    for op, a in rp.value:
        if op == 'moveTo': cur = [a[0]]; last = a[0]
        elif op == 'lineTo': cur.append(a[0]); last = a[0]
        elif op == 'curveTo':
            p0 = last; p1, p2, p3 = a
            for i in range(1, steps + 1):
                t = i / steps; u = 1 - t
                cur.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0], u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
            last = p3
        elif op == 'qCurveTo':
            pts = [last] + list(a)
            # implied on-curve points
            segs = []; q0 = pts[0]
            for i in range(1, len(pts) - 1):
                c = pts[i]; e = pts[i + 1] if i == len(pts) - 2 else ((pts[i][0] + pts[i+1][0]) / 2, (pts[i][1] + pts[i+1][1]) / 2)
                segs.append((q0, c, e)); q0 = e
            for q0_, c, e in segs:
                for i in range(1, steps + 1):
                    t = i / steps; u = 1 - t
                    cur.append((u*u*q0_[0] + 2*u*t*c[0] + t*t*e[0], u*u*q0_[1] + 2*u*t*c[1] + t*t*e[1]))
            last = a[-1]
        elif op in ('closePath', 'endPath'):
            if len(cur) > 2: out.append(cur)
            cur = []
    return out

def _poly_path(ps):
    Q = pathops.Path(); pen = Q.getPen()
    for poly in ps:
        pen.moveTo(poly[0])
        for q in poly[1:]: pen.lineTo(q)
        pen.closePath()
    return Q

def msum(P, d, axis):
    """Minkowski sum with the segment [-d, d] along x (axis=0) or y (axis=1); exact for the flattened outline"""
    v = (d, 0) if axis == 0 else (0, d)
    ps = polys(P); pieces = []
    for poly in ps:
        pieces.append([(x - v[0], y - v[1]) for x, y in poly]); pieces.append([(x + v[0], y + v[1]) for x, y in poly])
        n = len(poly)
        for i in range(n):
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            pieces.append([(ax - v[0], ay - v[1]), (bx - v[0], by - v[1]), (bx + v[0], by + v[1]), (ax + v[0], ay + v[1])])
    R = pathops.Path()
    for pc in pieces:
        Q = _poly_path([pc]); Q.simplify(fix_winding=True)
        R = pathops.op(R, Q, pathops.PathOp.UNION, fix_winding=True)
    return R

def morph(P, d, axis):
    if abs(d) < 0.3: return P
    if d > 0: return msum(P, d, axis)
    e = -d; R = P                                   # erosion: the shape must contain the whole segment
    for i in range(9):
        t = -e + 2 * e * i / 8
        T = transform(P, (lambda x, y, t=t: (x + t, y)) if axis == 0 else (lambda x, y, t=t: (x, y + t)))
        R = pathops.op(R, T, pathops.PathOp.INTERSECTION, fix_winding=True)
    return R


# ---------- parametric rebuild of the official outline (SVG coordinates, y down) ----------
M = -0.21268                      # slope of all bars (dy/dx, y down)
def _slant(p): return ('S', p)    # line through p with slope M
LINES = {
    'Ll': ('V', 396.69, -1), 'Lr': ('V', 528.94, +1), 'Al': ('V', 661.19, -1), 'Ar': ('V', 793.44, +1),
    'At': ('S', (396.69, 636.68), -1), 'Ab': ('S', (62.36, 842.93), +1),
    'Bt': ('S', (1124.13, 752.43), -1), 'Bb': ('S', (661.19, 986.06), +1),
    'Ct': ('S', (396.69, 942.14), -1), 'Cb': ('S', (-0.01, 1161.65), +1),
    'Dt': ('S', (699.62, 1113.02), -1), 'Db': ('S', (661.22, 1256.39), +1),
}
def _moved(name, ds, db):
    kind, a, sg = LINES[name]
    if kind == 'V': return ('V', a + sg * ds)
    return ('S', (a[0], a[1] + sg * db))
def _isect(l1, l2):
    if l1[0] == 'V' and l2[0] == 'V': raise ValueError
    if l1[0] == 'S' and l2[0] == 'V': l1, l2 = l2, l1
    if l1[0] == 'V':
        x = l1[1]; (px, py) = l2[1]; return (x, py + M * (x - px))
    (ax, ay), (bx, by) = l1[1], l2[1]
    raise ValueError('parallel bars')
def _ylin(l, x): (px, py) = l[1]; return py + M * (x - px)
def _barend(pb, pt, ctrls, lb, lt):
    """end curve from pb (on line lb) to pt (on line lt); chord direction kept"""
    dx, dy = pt[0] - pb[0], pt[1] - pb[1]
    def hit(p, l):   # point on line p + t*(dx,dy) meeting slanted line l
        (qx, qy) = l[1]
        t = ((qy + M * (p[0] - qx)) - p[1]) / (dy - M * dx)
        return (p[0] + t * dx, p[1] + t * dy)
    nb, nt = hit(pb, lb), hit(pt, lt)
    L0 = (dx * dx + dy * dy) ** 0.5; ndx, ndy = nt[0] - nb[0], nt[1] - nb[1]; L1 = (ndx * ndx + ndy * ndy) ** 0.5
    ux, uy = dx / L0, dy / L0; nx, ny = -uy, ux
    out = []
    for c in ctrls:
        u = ((c[0] - pb[0]) * ux + (c[1] - pb[1]) * uy) / L0; v = ((c[0] - pb[0]) * nx + (c[1] - pb[1]) * ny) * L1 / L0
        out.append((nb[0] + u * ndx + v * nx, nb[1] + u * ndy + v * ny))
    return nb, out, nt

def parametric(ds, db):
    Lm = {k: _moved(k, ds, db) for k in LINES}
    X = lambda a, b: _isect(Lm[a], Lm[b])
    P = pathops.Path(); pen = P.getPen()
    # main body
    b0, c, b1 = _barend((1085.73, 895.8), (1124.13, 752.43), [(1105.79, 851.33), (1119.05, 803.05)], Lm['Bb'], Lm['Bt'])
    pen.moveTo(b0); pen.curveTo(*c, b1)
    pen.lineTo(X('Bt', 'Ar')); pen.lineTo(X('Ar', 'Ab'))
    a0, c, a1 = _barend((1085.72, 625.45), (1124.12, 482.08), [(1105.78, 580.98), (1119.04, 532.70)], Lm['Ab'], Lm['At'])
    pen.lineTo(a0); pen.curveTo(*c, a1)
    pen.lineTo(X('At', 'Ar'))
    # alef top cut: x stretched to the new stem, y unchanged
    xl, xr = Lm['Al'][1], Lm['Ar'][1]
    fx = lambda x: xl + (x - 661.19) * (xr - xl) / (793.44 - 661.19)
    pen.lineTo((xr, 66.13)); pen.curveTo((fx(742.77), 94.58), (fx(697.77), 132.45), (xl, 177.12))
    pen.lineTo(X('Al', 'At')); pen.lineTo(X('At', 'Lr'))
    xl, xr = Lm['Ll'][1], Lm['Lr'][1]
    gx = lambda x: xl + (x - 396.69) * (xr - xl) / (528.94 - 396.69)
    pen.lineTo((xr, 0.0)); pen.curveTo((gx(478.27), 28.44), (gx(433.27), 66.32), (xl, 110.99))
    pen.lineTo(X('Ll', 'At'))
    t0, c, t1 = _barend((62.36, 842.93), (100.78, 699.56), [(67.45, 792.31), (80.72, 744.03)], Lm['Ab'], Lm['At'])
    pen.lineTo(t1); pen.curveTo(c[1], c[0], t0)
    pen.lineTo(X('Ab', 'Ll')); pen.lineTo(X('Ll', 'Ct'))
    e0, c, e1 = _barend((-0.01, 1161.65), (38.39, 1018.28), [(5.07, 1111.03), (18.33, 1062.75)], Lm['Cb'], Lm['Ct'])
    pen.lineTo(e1); pen.curveTo(c[1], c[0], e0)
    # lam bottom joint: slides with the lam's right edge along the lower bar
    T = (ds, db + M * ds)
    J = lambda p: (p[0] + T[0], p[1] + T[1])
    pen.lineTo(J((375.03, 1081.95))); pen.curveTo(J((405.56, 1075.60)), J((431.80, 1057.55)), J((448.86, 1032.71)))
    pen.lineTo(J((517.64, 930.72))); pen.curveTo(J((524.78, 920.17)), J((528.94, 907.45)), J((528.94, 893.75)))
    pen.lineTo(X('Lr', 'Ab')); pen.lineTo(X('Ab', 'Al')); pen.lineTo(X('Al', 'Bb'))
    pen.closePath()
    # yaa dots bar
    d0, c, d1 = _barend((661.22, 1256.39), (699.62, 1113.02), [(666.30, 1205.77), (679.56, 1157.50)], Lm['Db'], Lm['Dt'])
    f0, c2, f1 = _barend((1085.73, 1166.15), (1124.13, 1022.78), [(1105.79, 1121.67), (1119.04, 1073.40)], Lm['Db'], Lm['Dt'])
    pen.moveTo(d1); pen.curveTo(c[1], c[0], d0); pen.lineTo(f0); pen.curveTo(*c2, f1); pen.closePath()
    P.simplify(fix_winding=True)
    return P, (Lm['Lr'][1], Lm['Al'][1])

def build():
    ds = (WL / K - 131.25) / 2; db = (BAR / K - 135.2) / 2
    P, (xl, xr) = parametric(ds, db)
    # SVG (y down) -> font units: lam on the baseline, lam top at figure height
    P = transform(P, lambda x, y: (x * K, (1256.39 - y - LAM_BOT) * K))
    xl, xr = xl * K, xr * K
    insert = max(0.0, GAP_AL - (xr - xl))
    if insert > 0.5:
        SL = 70.33 / 330.68
        def ins(x, y):
            t = 0.0 if x <= xl + 0.01 else (1.0 if x >= xr - 0.01 else (x - xl) / (xr - xl))
            return x + t * insert, y + t * insert * SL
        P = transform(P, ins)
    P = roundoff(P, ROUND)
    P.simplify(fix_winding=True)
    return P, insert, (xr - xl) + insert

def main():
    P, insert, gap = build()
    tt = TTFont(OUT); gs = tt.getGlyphSet()
    b = P.bounds
    rsb = round(1.5 * gap if WT == 'Regular' else (1.35 if WT == 'Light' else 1.7) * gap)
    rsb = max(rsb, 110)
    shiftx = LSB - b[0]
    pen = TTGlyphPen(None)
    P2 = transform(P, lambda x, y: (x + shiftx, y))
    P2.draw(Cu2QuPen(pen, 1.0, reverse_direction=False))
    g = pen.glyph(); name = 'uni20C1'
    glyf = tt['glyf']
    if name not in tt.getGlyphOrder():
        order = tt.getGlyphOrder() + [name]; tt.setGlyphOrder(order)
    glyf[name] = g; g.recalcBounds(glyf)
    adv = round(LSB + (b[2] - b[0]) + rsb)
    tt['hmtx'][name] = (adv, g.xMin)
    for t in tt['cmap'].tables:
        if t.isUnicode(): t.cmap[0x20C1] = name
    if 'post' in tt and hasattr(tt['post'], 'extraNames'): pass
    tt['maxp'].numGlyphs = len(tt.getGlyphOrder())
    tt.save(OUT)
    print(WT, 'uni20C1 added: adv', adv, 'ink', [round(v) for v in P2.bounds], 'insert', round(insert), 'rsb', rsb)

if __name__ == '__main__':
    main()
