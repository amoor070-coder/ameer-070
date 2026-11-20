"""Latin a–z / A–Z redraw (Regular, monoline, Alexandria/Plex proportions, RunJari soft joins).
Run after glyphs_r.py: python3 latin_r.py  (rewrites sample/Ameer070-Regular-sample.ttf)"""
import sys, math, pathops
sys.path.insert(0, '/home/claude/fa')
from draw import stroke, fill, union, subtract, to_pathops, set_glyph
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen

from wt import OUT as F, WL, CFG
import draw as _dr; _dr.SKX = CFG['skx']; _dr.SKY = CFG['sky']
f = TTFont(F)
W = WL; H = W * CFG['sky'] / 2      # vertical half-thickness of horizontals
XH, CAP, ASC, DSC, OS = 520, 700, 735, -210, 10      # design metrics of the skeletons below
from wt import LXH, LCAP, LASC, LDSC, WT
_s = (LCAP - 2 * H) / (CAP - 2 * H)                    # skeleton y-scale so caps land on the ruler, baseline stays
_dr.SYS, _dr.SYH = _s, H
def MY(v): return H + (v - H) * _s                     # centre-line mapping
def MEt(v): return MY(v - H) + H                       # top edge mapping
def MEb(v): return MY(v + H) - H                       # bottom edge mapping

def rect(x0, y0, x1, y1):
    return fill(f'M {x0} {y0} L {x1} {y0} L {x1} {y1} L {x0} {y1} Z')
def clip(p, x0=-3000, y0=-3000, x1=5000, y1=5000):
    y0, y1 = MEb(y0), MEt(y1)                          # clip edges follow the ruler mapping
    p = p if isinstance(p, pathops.Path) else to_pathops(p)
    return pathops.op(p, to_pathops(rect(x0, y0, x1, y1)), pathops.PathOp.INTERSECTION)
def S(d, join='round'):
    return stroke(d, W, join=join)
def arc(cx, cy, rx, ry, a0, a1, move=True):
    """cubic arc, angles in degrees, counter-clockwise if a1>a0"""
    segs = max(1, int(math.ceil(abs(a1 - a0) / 90)))
    da = (a1 - a0) / segs
    d = ''
    for i in range(segs):
        t0 = math.radians(a0 + da * i); t1 = math.radians(a0 + da * (i + 1))
        k = 4 / 3 * math.tan((t1 - t0) / 4)
        p0 = (cx + rx * math.cos(t0), cy + ry * math.sin(t0))
        p3 = (cx + rx * math.cos(t1), cy + ry * math.sin(t1))
        p1 = (p0[0] - k * rx * math.sin(t0), p0[1] + k * ry * math.cos(t0))
        p2 = (p3[0] + k * rx * math.sin(t1), p3[1] - k * ry * math.cos(t1))
        if i == 0 and move: d += f'M {p0[0]:.1f} {p0[1]:.1f} '
        d += f'C {p1[0]:.1f} {p1[1]:.1f} {p2[0]:.1f} {p2[1]:.1f} {p3[0]:.1f} {p3[1]:.1f} '
    return d
def ell(cx, cy, rx, ry):
    return arc(cx, cy, rx, ry, 0, 360) + 'Z'
def softdot(cx, cy, r=50, t=0.36):
    cx = cx * _dr.SKX; r = r * (W / 82) ** 0.8
    if abs(cy - 672) < 1:   # i/j dot: clear gap above x-height, top never above the cap line
        lo = MEt(XH) + 0.42 * W; hi = LCAP + 12
        r = min(r, (hi - lo) / 2); cy = min(lo + r + 0.2 * W, hi - r)
    else: cy = MY(cy)
    vs = [(cx + r * math.cos(math.radians(90 + 60 * k)) / math.cos(math.radians(30)) * 0.87, cy + r * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
    d = ''
    for k in range(6):
        p0, p1, p2 = vs[k - 1], vs[k], vs[(k + 1) % 6]
        a = (p1[0] + (p0[0] - p1[0]) * t, p1[1] + (p0[1] - p1[1]) * t)
        b = (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
        d += (f'M {a[0]:.1f} {a[1]:.1f} ' if k == 0 else f'L {a[0]:.1f} {a[1]:.1f} ') + f'Q {p1[0]:.1f} {p1[1]:.1f} {b[0]:.1f} {b[1]:.1f} '
    return fill(d + 'Z')

# centre-line helpers
xb = H - OS          # bowl bottom centre-line  (outer -10)
xt = XH + OS - H     # bowl top centre-line     (outer 530)
cyx = (xb + xt) / 2; ryx = (xt - xb) / 2
cb, ct = H - OS, CAP + OS - H          # caps rounds
cyc = (cb + ct) / 2; ryc = (ct - cb) / 2
G = {}   # name -> (path, lsb, rsb)
ST, RD, DG = 74, 46, 16                # side-bearing families

def U(*ps):
    out = ps[0] if isinstance(ps[0], pathops.Path) else to_pathops(ps[0])
    for p in ps[1:]: out = union(out, p)
    return out

# ---------------- lowercase ----------------
G['o'] = lambda: (S(ell(255, cyx, 216, ryx)), RD, RD)
_ap = 14 * max(0, W / 82 - 1)
G['c'] = lambda: (S(arc(255, cyx, 216, ryx, 42 + _ap * 0.6, 318 - _ap * 0.6)), RD, 38)
_ap = 26 * max(0, W / 82 - 1)      # heavier weights: open the e/c apertures
_kb = 1.0 if W <= 90 else max(0.64, 1 - (W - 90) * 0.005)   # heavy weights: thinner e bar keeps the eye open
def _e_heavy():
    by = cyx + _ap * 0.35
    ring = S(ell(255, cyx, 216, ryx)); bar = stroke(f'M 39 {by} L 462 {by}', W * _kb)
    yb = MY(by) - W * _kb * CFG['sky'] / 2                       # bar bottom edge (final coordinates)
    cx, cy = 255 * _dr.SKX, MY(cyx); t = math.radians(318 - _ap)
    tx, ty = cx + 3 * 216 * _dr.SKX * math.cos(t), cy + 3 * ryx * _s * math.sin(t)
    xc = cx + 216 * _dr.SKX * math.cos(t)                      # vertical terminal (no beak)
    cut = fill(f'M {xc} {yb} L {cx + 2000} {yb} L {cx + 2000} -2000 L {xc} -2000 Z')
    return subtract(U(ring, bar), cut)
G['e'] = lambda: (_e_heavy(), RD, 40)       # ring + bar + clean vertical terminal in every weight (no step where bar meets bowl)
bowl_a = ell(238, cyx, 197, ryx)
G['a'] = lambda: (U(S(bowl_a), clip(S(f'M 435 {XH+60} L 435 -60'), y0=0, y1=XH)), RD, ST)
G['d'] = lambda: (U(S(bowl_a), clip(S(f'M 435 {ASC+60} L 435 -60'), y0=0, y1=ASC)), RD, ST)
bowl_b = ell(238, cyx, 197, ryx)
G['b'] = lambda: (U(S(bowl_b), clip(S(f'M 41 {ASC+60} L 41 -60'), y0=0, y1=ASC)), ST, RD)
G['p'] = lambda: (U(S(bowl_b), clip(S(f'M 41 {XH+60} L 41 {DSC-60}'), y0=DSC, y1=XH)), ST, RD)
G['q'] = lambda: (U(S(bowl_a), clip(S(f'M 435 {XH+60} L 435 {DSC-60}'), y0=DSC, y1=XH)), RD, ST)
G['g'] = lambda: (U(S(bowl_a), clip(S(f'M 435 {XH+60} L 435 -30 C 435 -150 350 -170 235 -170 C 160 -170 105 -150 68 -112'), y1=XH)), RD, ST)
N_ARCH = lambda x0, x1: f'M {x0} 330 C {x0+18} 440 {x0+90} {xt} {(x0+x1)/2+8} {xt} C {x1-40} {xt} {x1} 440 {x1} 330 L {x1} -60'
G['n'] = lambda: (U(clip(S(f'M 41 {XH+60} L 41 -60'), y0=0, y1=XH), clip(S(N_ARCH(41, 391)), y0=0)), ST, ST)
G['h'] = lambda: (U(clip(S(f'M 41 {ASC+60} L 41 -60'), y0=0, y1=ASC), clip(S(N_ARCH(41, 391)), y0=0)), ST, ST)
G['m'] = lambda: (U(clip(S(f'M 41 {XH+60} L 41 -60'), y0=0, y1=XH), clip(S(N_ARCH(41, 333)), y0=0), clip(S(N_ARCH(333, 625)), y0=0)), ST, ST)
G['u'] = lambda: (U(clip(S(f'M 41 {XH+60} L 41 190 C 41 82 102 {xb} 216 {xb} C 330 {xb} 391 82 391 200'), y1=XH), clip(S(f'M 391 {XH+60} L 391 -60'), y0=0, y1=XH)), ST, ST)
G['r'] = lambda: (U(clip(S(f'M 41 {XH+60} L 41 -60'), y0=0, y1=XH), S(f'M 41 330 C 60 440 130 {xt} 220 {xt} C 250 {xt} 275 486 295 478' if W <= 100 else f'M 41 330 C 60 440 130 {xt} 220 {xt} L 285 {xt}')), ST, 26)
G['i'] = lambda: (U(clip(S(f'M 41 {XH+60} L 41 -60'), y0=0, y1=XH), softdot(41, 672, 54)), ST, ST)
G['j'] = lambda: (U(clip(S(f'M 160 {XH+60} L 160 -60 C 160 -150 120 {DSC+OS+H-10} 50 {DSC+OS+H-10} L 10 {DSC+OS+H-10}'), y1=XH), softdot(160, 672, 54)), 10, ST)
G['l'] = lambda: (clip(S(f'M 41 {ASC+60} L 41 -60'), y0=0, y1=ASC), ST, ST)
G['t'] = lambda: (U(clip(S(f'M 100 650 L 100 165 C 100 78 150 {xb} 225 {xb} L 300 {xb}'), y1=650), S(f'M -10 {XH-H} L 260 {XH-H}', join='miter')), 18, 24)
G['f'] = lambda: (U(clip(S(f'M 100 -60 L 100 560 C 100 660 150 {ASC-H} 240 {ASC-H} L 300 {ASC-H}'), y0=0), S(f'M -10 {XH-H} L 270 {XH-H}', join='miter')), 18, 10)
G['k'] = lambda: (U(clip(S(f'M 41 {ASC+60} L 41 -60'), y0=0, y1=ASC), clip(S(f'M 400 {XH+40} L 41 190'), y1=XH), clip(S(f'M 175 300 L 420 -50'), y0=0)), ST, 22)
G['v'] = lambda: (clip(S(f'M -30 {XH+80} L 210 {H} L 450 {XH+80}'), y1=XH), 20, 20)
G['w'] = lambda: (clip(S(f'M -30 {XH+80} L 160 {H} L 330 {XH-H} L 500 {H} L 690 {XH+80}'), y1=XH), 20, 20)
G['x'] = lambda: (U(clip(S(f'M -50 {XH+62} L 470 -62'), y0=0, y1=XH), clip(S(f'M 470 {XH+62} L -50 -62'), y0=0, y1=XH)), 20, 20)
G['y'] = lambda: (U(clip(S(f'M -30 {XH+80} L 210 10'), y0=0, y1=XH), clip(S(f'M 450 {XH+80} L 120 {DSC-60}'), y0=DSC, y1=XH)), DG, DG)
G['z'] = lambda: (S(f'M 20 {XH-H} L 390 {XH-H} L 30 {H} L 400 {H}'), 34, 34)
G['s'] = lambda: (S(f'M 352 440 C 320 {xt-5} 270 {xt} 210 {xt} C 115 {xt} 58 448 58 382 C 58 318 115 292 205 272 C 318 247 372 216 372 145 C 372 72 300 {xb} 205 {xb} C 128 {xb} 68 60 36 112'), 40, 40)

# ---------------- uppercase ----------------
G['H'] = lambda: (U(clip(S(f'M 41 {CAP+60} L 41 -60'), y0=0, y1=CAP), clip(S(f'M 521 {CAP+60} L 521 -60'), y0=0, y1=CAP), S(f'M 41 352 L 521 352')), ST, ST)
G['I'] = lambda: (clip(S(f'M 41 {CAP+60} L 41 -60'), y0=0, y1=CAP), ST, ST)
G['L'] = lambda: (clip(S(f'M 41 {CAP+60} L 41 {H} L 430 {H}'), y0=0, y1=CAP), ST, 30)
G['E'] = lambda: (U(clip(S(f'M 430 {CAP-H} L 41 {CAP-H} L 41 {H} L 445 {H}'), y0=0, y1=CAP), S(f'M 41 360 L 405 360')), ST, 34)
G['F'] = lambda: (U(clip(S(f'M 430 {CAP-H} L 41 {CAP-H} L 41 -60'), y0=0, y1=CAP), S(f'M 41 360 L 400 360')), ST, 30)
G['T'] = lambda: (U(S(f'M 0 {CAP-H} L 540 {CAP-H}'), clip(S(f'M 270 {CAP} L 270 -60'), y0=0)), 18, 18)
G['O'] = lambda: (S(ell(352, cyc, 311, ryc)), RD, RD)
G['C'] = lambda: (S(arc(352, cyc, 311, ryc, 40, 320)), RD, 30)
G['G'] = lambda: (S(arc(352, cyc, 311, ryc, 40 + 0.25 * max(0, W - 86), 360) + f'L {410 + 0.5 * max(0, W - 86)} {cyc}'), RD, RD)
G['Q'] = lambda: (U(S(ell(352, cyc, 311, ryc)), clip(S(f'M 430 200 L {680 - 0.6 * max(0, W - 86)} {-70 + 0.5 * max(0, W - 86)}'), y0=-120 + 0.8 * max(0, W - 86))), RD, RD)
G['D'] = lambda: (clip(S(f'M 41 -60 L 41 {CAP-H} L 270 {CAP-H} C 480 {CAP-H} 600 545 600 350 C 600 155 480 {H} 270 {H} L 41 {H}'), y0=0), ST, RD)
G['P'] = lambda: (clip(S(f'M 41 -60 L 41 {CAP-H} L 330 {CAP-H} C 450 {CAP-H} 520 600 520 505 C 520 410 450 320 330 320 L 41 320'), y0=0), ST, 34)
G['R'] = lambda: (U(G['P'][0], clip(S('M 300 320 L 560 -60'), y0=0)), ST, 18)
G['B'] = lambda: (clip(S(f'M 41 -60 L 41 {CAP-H} L 320 {CAP-H} C 430 {CAP-H} 500 610 500 525 C 500 440 430 372 320 372 L 41 372 L 345 372 C 470 372 545 300 545 205 C 545 105 470 {H} 345 {H} L 41 {H}'), y0=0), ST, RD)
G['U'] = lambda: (clip(S(f'M 41 {CAP+60} L 41 250 C 41 105 150 {cb} 300 {cb} C 450 {cb} 559 105 559 250 L 559 {CAP+60}'), y1=CAP), ST, ST)
G['J'] = lambda: (clip(S(f'M 400 {CAP+60} L 400 230 C 400 100 320 {cb} 215 {cb} C 120 {cb} 60 80 30 160'), y1=CAP), 26, ST)
G['K'] = lambda: (U(clip(S(f'M 41 {CAP+60} L 41 -60'), y0=0, y1=CAP), clip(S(f'M 560 {CAP+60} L 41 245'), y1=CAP), clip(S('M 215 405 L 580 -70'), y0=0)), ST, 24)
G['M'] = lambda: (clip(S(f'M 41 -60 L 41 {CAP-H} L 360 150 L 679 {CAP-H} L 679 -60'), y0=0), ST, ST)
G['N'] = lambda: (clip(S(f'M 41 -60 L 41 {CAP-H} L 541 {H} L 541 {CAP+60}'), y0=0, y1=CAP), ST, ST)
G['V'] = lambda: (clip(S(f'M -30 {CAP+90} L 310 {H} L 650 {CAP+90}'), y1=CAP), 20, 20)
G['W'] = lambda: (clip(S(f'M -30 {CAP+90} L 215 {H} L 450 {CAP-60} L 685 {H} L 930 {CAP+90}'), y1=CAP), 20, 20)
G['A'] = lambda: (U(clip(S(f'M -40 -90 L 310 {CAP-H} L 660 -90'), y0=0), S(f'M 103 {215 - 0.45 * max(0, W - 86)} L 517 {215 - 0.45 * max(0, W - 86)}')), DG, DG)
G['X'] = lambda: (U(clip(S(f'M -50 {CAP+60} L 630 -60'), y0=0, y1=CAP), clip(S(f'M 630 {CAP+60} L -50 -60'), y0=0, y1=CAP)), 20, 20)
G['Y'] = lambda: (U(clip(S(f'M -20 {CAP+40} L 290 330 L 600 {CAP+40}'), y1=CAP), clip(S('M 290 340 L 290 -60'), y0=0)), DG, DG)
G['Z'] = lambda: (S(f'M 30 {CAP-H} L 545 {CAP-H} L 40 {H} L 560 {H}'), 34, 34)
G['S'] = lambda: (S(f'M 520 590 C 480 {ct-10} 405 {ct} 320 {ct} C 175 {ct} 85 612 85 520 C 85 430 165 395 300 368 C 455 337 535 290 535 190 C 535 85 440 {cb} 315 {cb} C 215 {cb} 135 60 92 118'), 42, 42)

T_ = CAP + OS - H; B_ = H - OS
_dr.SKX = _base_skx_d = _dr.SKX * (1 - 0.06 * max(0, W - 86) / 78)
DIG = {
 'zero': S(ell(300, (T_+B_)/2, 214 - 0.45 * max(0, W - 86), (T_-B_)/2)),
 'one': clip(S(f'M 172 560 L 330 {CAP-H} L 330 -60'), y0=0),
 'three': U(S(f'M 118 590 C 155 665 225 {T_} 300 {T_} C 405 {T_} 468 612 468 528 C 468 445 405 388 300 388 L 245 388'),
            S(f'M 245 388 L 312 388 C 430 388 490 322 490 216 C 490 103 410 {B_} 300 {B_} C 208 {B_} 138 72 104 140')),
 'seven': clip(S(f'M 92 {CAP-H} L 505 {CAP-H} L 230 -80'), y0=0),
 'eight': U(S(ell(300, 528, 172, T_-528)), S(ell(300, 205, 196, 205-B_))),
}
for n, p in DIG.items():
    p = p if isinstance(p, pathops.Path) else to_pathops(p)
    bp = BoundsPen(None); p.draw(bp); b = bp.bounds
    G[n] = (p, (600 - (b[2]-b[0])) / 2, (600 - (b[2]-b[0])) / 2)
import json, os
_LR = f'/home/claude/fa/work/latin_ruler_{WT}.json'
LR = json.load(open(_LR)) if os.path.exists(_LR) else {}
_base_skx = _dr.SKX
for _n in list(G):
    if callable(G[_n]):
        _dr.SKX = _base_skx * LR.get(_n, {}).get('sx', 1.0)
        G[_n] = G[_n]()
        _dr.SKX = _base_skx
        if 'lsb' in LR.get(_n, {}): G[_n] = (G[_n][0], LR[_n]['lsb'], LR[_n]['rsb'])
lat_names = set(G)
for n, (p, lsb, rsb) in G.items():
    p = p if isinstance(p, pathops.Path) else to_pathops(p)
    bp = BoundsPen(None); p.draw(bp); b = bp.bounds
    out = pathops.Path(); p.draw(TransformPen(out.getPen(), (1, 0, 0, 1, lsb - b[0], 0)))
    set_glyph(f, n, out, adv=(b[2] - b[0]) + lsb + rsb)

# neutralise old Latin kerning for the redrawn letters (sample)
for lk in f['GPOS'].table.LookupList.Lookup:
    sts = [x.ExtSubTable for x in lk.SubTable] if lk.LookupType == 9 else lk.SubTable
    for st in sts:
        if type(st).__name__ != 'PairPos': continue
        if st.Format == 1:
            for i, g in enumerate(st.Coverage.glyphs):
                for pvr in st.PairSet[i].PairValueRecord:
                    if g in lat_names or pvr.SecondGlyph in lat_names:
                        for v in (pvr.Value1, getattr(pvr, 'Value2', None)):
                            if v is not None:
                                for a in ('XAdvance', 'XPlacement'):
                                    if hasattr(v, a): setattr(v, a, 0)
        else:
            c1 = st.ClassDef1.classDefs; c2 = st.ClassDef2.classDefs; cov = set(st.Coverage.glyphs)
            k1 = {c1.get(g, 0) for g in lat_names if g in cov}; k2 = {c2.get(g, 0) for g in lat_names if g in c2}
            for i, r1 in enumerate(st.Class1Record):
                for j, r2 in enumerate(r1.Class2Record):
                    if i in k1 or j in k2:
                        for v in (r2.Value1, getattr(r2, 'Value2', None)):
                            if v is not None:
                                for a in ('XAdvance', 'XPlacement'):
                                    if hasattr(v, a): setattr(v, a, 0)
f.save(F)
print('latin ok', len(G))
