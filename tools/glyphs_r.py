"""Regular-weight approval-sample redraws (W=77). Run: python3 glyphs_r.py -> sample/Ameer070-Regular-sample.ttf"""
import sys, pathops
sys.path.insert(0, '/home/claude/fa')
from draw import stroke, fill, union, subtract, to_pathops, set_glyph, copy_glyph
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.areaPen import AreaPen

from wt import W, K, WT, BASE, OUT, ALEX, DOTMAX, CFG
CFG_ALEXW = CFG['alex']
H = W / 2; Y = H            # baseline stroke centre
SRC = BASE
f = TTFont(SRC)
gs = f.getGlyphSet()

E = W - 79                      # weight growth vs the approved Regular
MINGAP = 50 + (W - 79) * 0.15          # dot <-> body clearance (Regular 50, Bold ~57)
def _ink(body, x0, y0, x1, y1):
    r = pathops.Path(); pn = r.getPen()
    pn.moveTo((x0, y0)); pn.lineTo((x1, y0)); pn.lineTo((x1, y1)); pn.lineTo((x0, y1)); pn.closePath()
    i = pathops.op(body, r, pathops.PathOp.INTERSECTION); bp = BoundsPen(None); i.draw(bp); return bp.bounds
def space_group(body, dots_):
    """keep every dot at least MINGAP from the letter body (up/down/left/right), moving dot groups together"""
    m = 4  # inset so a dot does not 'see' ink only at its very corner
    up = down = 0; side = 0
    for b in dots_:
        below = _ink(body, b[0] + m, -3000, b[2] - m, b[1])
        above = _ink(body, b[0] + m, b[3], b[2] - m, 3000)
        if below and above:   # dot inside a bowl (jeem): centre it vertically if crowded
            gb, ga = b[1] - below[3], above[1] - b[3]
            if min(gb, ga) < MINGAP:
                c = (ga - gb) / 2
                if c > 0: up = max(up, c)
                else: down = max(down, -c)
            below = above = None
        if below and b[1] - below[3] < MINGAP: up = max(up, MINGAP - (b[1] - below[3]))
        if above and above[1] - b[3] < MINGAP: down = max(down, MINGAP - (above[1] - b[3]))
        left = _ink(body, -3000, b[1] + m, b[0], b[3] - m)
        right = _ink(body, b[2], b[1] + m, 3000, b[3] - m)
        if left and b[0] - left[2] < MINGAP and not (right and right[0] - b[2] < MINGAP * 2):
            side = max(side, MINGAP - (b[0] - left[2]))
        if right and right[0] - b[2] < MINGAP and not (left and b[0] - left[2] < MINGAP * 2):
            side = min(side, -(MINGAP - (right[0] - b[2])))
    dy = up - down if (up and not down) or (down and not up) else 0
    return side, dy
def space_dots(body, dots_):
    if not dots_: return dots_
    side, dy = space_group(body, dots_)
    out = [(b[0] + side, b[1] + dy, b[2] + side, b[3] + dy) for b in dots_]
    if len(out) == 3:   # triangle (theh/sheen/tcheh): open it up around its centroid
        import itertools, math as _m
        cs = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in out]
        D = sum(b[2] - b[0] for b in out) / 3
        dmin = min(_m.dist(p, q) for p, q in itertools.combinations(cs, 2))
        need = D * (1.17 + 0.25 * max(0, K - 1))
        if dmin < need:
            s = need / dmin; gx = sum(c[0] for c in cs) / 3; gy = sum(c[1] for c in cs) / 3
            out = [(b[0] + (c[0] - gx) * (s - 1), b[1] + (c[1] - gy) * (s - 1), b[2] + (c[0] - gx) * (s - 1), b[3] + (c[1] - gy) * (s - 1)) for b, c in zip(out, cs)]
    # dot <-> dot: keep a small clear gap (references ~0.14 of the dot)
    xs = sorted(range(len(out)), key=lambda i: out[i][0])
    for a_, b_ in zip(xs, xs[1:]):
        A, B = out[a_], out[b_]
        if abs((A[1] + A[3]) - (B[1] + B[3])) / 2 < (A[3] - A[1]) * 0.5:
            need = (0.15 + 0.25 * max(0, K - 1)) * (A[2] - A[0]) - (B[0] - A[2])
            if need > 0:
                out[a_] = (A[0] - need / 2, A[1], A[2] - need / 2, A[3]); out[b_] = (B[0] + need / 2, B[1], B[2] + need / 2, B[3])
    return out

DOTIDS = {}
def _reg(p):
    DOTIDS[id(p)] = p; return p
from draw import union as _union
def _boxes(p):
    rp = RecordingPen(); p.draw(rp); bx = []; cur = []
    for op, a in rp.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'):
            bp = BoundsPen(None)
            for o, aa in cur: getattr(bp, o)(*aa)
            if bp.bounds: bx.append(bp.bounds)
            cur = []
    return bx
def union(*parts):
    """union that keeps placed dots clear of the letter body (weight-aware MINGAP)"""
    ds = [p for p in parts if id(p) in DOTIDS]
    if not ds: return _union(*parts)
    body = _union(*[p for p in parts if id(p) not in DOTIDS])
    outs = []
    for d in ds:
        bx = _boxes(d)
        if not bx: continue
        side, dy = space_group(body, bx)
        o = pathops.Path(); d.draw(TransformPen(o.getPen(), (1, 0, 0, 1, side, dy))); outs.append(o)
    return _union(body, *outs)

def rect(x0, y0, x1, y1):
    return fill(f'M {x0} {y0} L {x1} {y0} L {x1} {y1} L {x0} {y1} Z')

def clip(path, x0=-2000, y0=-2000, x1=4000, y1=4000):
    p = to_pathops(path) if not isinstance(path, pathops.Path) else path
    return pathops.op(p, to_pathops(rect(x0, y0, x1, y1)), pathops.PathOp.INTERSECTION)

def dots(name, dx=0, dy=0, maxh=DOTMAX):
    """small contours (dots) of an existing glyph, shifted"""
    rp = RecordingPen(); gs[name].draw(rp)
    cs, cur = [], []
    for op, a in rp.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'): cs.append(cur); cur = []
    out = pathops.Path(); pen = TransformPen(out.getPen(), (1, 0, 0, 1, dx, dy))
    for c in cs:
        bp = BoundsPen(None)
        for op, a in c: getattr(bp, op)(*a)
        b = bp.bounds
        ap = AreaPen()
        for op, a in c: getattr(ap, op)(*a)
        if b[3] - b[1] < maxh and b[2] - b[0] < maxh and ap.value < 0:
            for op, a in c: getattr(pen, op)(*a)
    return _reg(out)

def dotcenter(name, maxh=DOTMAX):
    p = dots(name, maxh=maxh); bp = BoundsPen(None); p.draw(bp); b = bp.bounds
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

new = {}
def shift(p, dx):
    p = to_pathops(p) if not isinstance(p, pathops.Path) else p
    out = pathops.Path(); p.draw(TransformPen(out.getPen(), (1, 0, 0, 1, dx, 0))); return out

# ---------- REH ----------
# isolated: vertical head (height matched to noon arms ~350) flowing into a curved tail
reh_isol = clip(stroke('M 250 420 L 250 90 C 250 -110 160 -225 -10 -268', W), y1=373)
new['reh.isol'] = (reh_isol, 330)
# final: baseline entry turns down in one smooth "lane change" curve
reh_fina = stroke(f'M 318 {Y} L 250 {Y} C 205 {Y} 190 10 185 -45 C 172 -170 100 -235 -20 -268', W)
reh_fina = union(reh_isol, stroke(f'M 250 {Y} L 338 {Y}', W))
new['reh.fina'] = (reh_fina, 330)
zc = dotcenter('zain.isol')
new['zain.isol'] = (union(reh_isol, dots('zain.isol', 250 - zc[0], 470 - zc[1])), 330)
new['zain.fina'] = (union(reh_fina, dots('zain.fina', 250 - dotcenter('zain.fina')[0], 470 - dotcenter('zain.fina')[1])), 330)

# ---------- KAF: long arm, soft 120deg vertex, leg curves back into the baseline (Alexandria/Plex structure) ----------
def kaf_core(entry_to=None):
    arm = clip(stroke('M 440 662 L 102 480 Q 40 446 84 404', W), x1=412)
    if entry_to:
        leg = stroke(f'M 84 404 L 292 205 Q 330 168 330 118 L 330 {Y}', W)
        parts = [arm, leg, stroke(f'M -8 {Y} L {entry_to} {Y}', W)]
    else:
        leg = stroke(f'M 84 404 L 292 205 C 338 160 345 {Y} 262 {Y} L -8 {Y}', W)
        parts = [arm, leg]
    return clip(union(*parts), y0=0)
new['kaf.init'] = (kaf_core(), 400)
new['kaf.medi'] = (kaf_core(448), 440)
# ---------- AIN medial: closed rounded triangle on the baseline ----------
_a, _t = E * (0.35 + 0.25 * (E > 50)), E * (0.6 + 0.3 * (E > 50))   # heavier weights: open the counter
def _x(v): return v + _a          # shift right so the wider shape stays inside its advance
ain_m = clip(union(stroke(f'M -8 {Y} L {448 + 2 * _a} {Y}', W),
              stroke(f'M {_x(250)} {Y} L {_x(292+_a)} {Y} Q {_x(318+_a)} {Y} {_x(328+_a)} {Y + 25} L {_x(398+_a)} {286+_t} Q {_x(409+_a)} {320+_t} {_x(374+_a)} {320+_t} L {_x(126-_a)} {320+_t} Q {_x(91-_a)} {320+_t} {_x(102-_a)} {286+_t} L {_x(172-_a)} {Y + 25} Q {_x(182-_a)} {Y} {_x(208-_a)} {Y} L {_x(250)} {Y}', W)), y0=0)
new['ain.medi'] = (ain_m, 440 + 2 * _a)
HEAD_A = f'M 455 368 C 410 376 330 388 270 388 C 170 388 113 340 113 270 C 113 190 140 120 165 {Y}'
BOWL_A = f'M 168 {Y} C 100 {Y} 76 -60 76 -130 C 76 -230 160 -278 280 -278 C 380 -278 450 -255 510 -215'
ain_i = union(stroke(HEAD_A, W), stroke(f'M 150 {Y} L 470 {Y}', W), stroke(BOWL_A, W))
new['ain.isol'] = (ain_i, 585)
ain_in = clip(union(stroke(HEAD_A, W), stroke(f'M -8 {Y} L 470 {Y}', W)), y0=0)
new['ain.init'] = (ain_in, 505)
TRAP = f'M {_x(250)} {Y} L {_x(292+_a)} {Y} Q {_x(318+_a)} {Y} {_x(328+_a)} {Y + 25} L {_x(398+_a)} {286+_t} Q {_x(409+_a)} {320+_t} {_x(374+_a)} {320+_t} L {_x(126-_a)} {320+_t} Q {_x(91-_a)} {320+_t} {_x(102-_a)} {286+_t} L {_x(172-_a)} {Y + 25} Q {_x(182-_a)} {Y} {_x(208-_a)} {Y} L {_x(250)} {Y}'
_fa = 440 + 2 * _a; _bx = _x(250) + 40 - (0.62 + 0.25 * min(1, max(0, E) / 86)) * (_x(250) - _x(198 - _a))
import draw as _dr2
_SA = 0.62 + 0.25 * min(1, max(0, E) / 86)   # heavier weights keep the final-ain counter open
_dr2.SKX = _SA; _tr = stroke(TRAP, W); _dr2.SKX = 1.0      # narrower, rounder head than the medial (so it never reads as hah)
_tc = _x(250) + 40
ain_f = union(shift(_tr, _tc - _SA * _x(250)), stroke(f'M {_tc} {Y} L {_fa + 8} {Y}', W),
              stroke(f'M {_tc} {Y} L {_bx} {Y} C {_bx - 95} {Y} 90 -45 90 -125 C 90 -228 175 -278 295 -278 C 395 -278 465 -255 525 -215', W))
new['ain.fina'] = (ain_f, _fa)


# ---------- HAH family: rounded head with angled entry tip (Alexandria/Plex structure, RunJari softness) ----------
HEAD = 'M 40 268 C 95 322 165 345 245 345 C 360 345 420 290 420 205'
hah_init = clip(stroke(HEAD + f' L 420 {Y} L -8 {Y}', W), y0=0)
new['hah.init'] = (hah_init, 470)
new['hah.medi'] = (clip(union(hah_init, stroke(f'M 300 {Y} L 478 {Y}', W)), y0=0), 470)
HEAD2 = 'M 82 300 C 120 330 170 345 245 345 C 360 345 420 290 420 205'
def hah_bowl():
    return union(stroke(HEAD2 + f' L 420 {Y} L 210 {Y}', W),
                 stroke(f'M 250 {Y} C 120 {Y} 60 -40 60 -120 C 60 -215 145 -262 265 -262 C 340 -262 395 -240 440 -205', W))
new['hah.isol'] = (clip(hah_bowl(), y0=-305), 500)
new['hah.fina'] = (clip(union(hah_bowl(), stroke(f'M 300 {Y} L 508 {Y}', W)), y0=-305), 500)
# jeem / khah reuse with dots
jc = dotcenter('jeem.init'); kc = dotcenter('khah.init')
new['jeem.init'] = (union(hah_init, dots('jeem.init', 215 - jc[0], -135 - jc[1])), 500)
new['khah.init'] = (union(hah_init, dots('khah.init', 230 - kc[0], 470 - kc[1])), 500)
jic = dotcenter('jeem.isol')
new['jeem.isol'] = (union(clip(hah_bowl(), y0=-301), dots('jeem.isol', 275 - jic[0], -95 - jic[1])), 520)

# ---------- TAH: upright stem, rounded bowl springing from the stem (Alexandria/Plex structure) ----------
TDX = round(max(0, K - 1) * 70); TDY = round(max(0, K - 1) * 45)   # heavy weights: open the tah counter
def tah(entry, exit_):
    R, T = 455 + TDX, 380 + TDY
    parts = [stroke(f'M 115 760 L 115 0', W), stroke(f'M 76 {Y} L 160 {Y}', W),
             stroke(f'M 117 {250 + TDY // 2} C 145 {335 + TDY} {210 + TDX // 3} {T} {295 + TDX // 2} {T} C {400 + TDX} {T} {R} {305 + TDY} {R} {200 + TDY // 2} L {R} {Y} L 115 {Y}', W)]
    if exit_: parts.append(stroke(f'M -8 {Y} L 120 {Y}', W))
    if entry: parts.append(stroke(f'M {440 + TDX} {Y} L {528 + TDX} {Y}', W))
    body = clip(union(*parts), y0=0, y1=715)
    return subtract(body, fill('M 40 690 L 200 714 L 200 760 L 40 760 Z'))
new['tah.init'] = (tah(False, True), 520 + TDX)
new['tah.medi'] = (tah(True, True), 520 + TDX)
new['tah.fina'] = (tah(True, False), 520 + TDX)
new['tah.isol'] = (tah(False, False), 540 + TDX)

# ---------- FEH / QAF init+medi: loop rises smoothly out of the baseline, no nubs ----------
LOOP = f'M -8 {Y} L 330 {Y} C 395 {Y} 420 120 420 205 C 420 315 355 378 275 378 C 190 378 128 318 128 225 C 128 120 160 {Y} 240 {Y}'
loop_init = clip(stroke(LOOP, W), y0=0)
loop_medi = clip(union(stroke(LOOP, W), stroke(f'M 300 {Y} L 478 {Y}', W)), y0=0)
qc = dotcenter('qaf.init'); fc = dotcenter('feh.init')
new['qaf.init'] = (union(loop_init, dots('qaf.init', 276 - qc[0], 515 - qc[1])), 470)
new['qaf.medi'] = (union(loop_medi, dots('qaf.medi', 276 - dotcenter('qaf.medi')[0], 515 - dotcenter('qaf.medi')[1])), 470)
new['feh.init'] = (union(loop_init, dots('feh.init', 276 - fc[0], 515 - fc[1])), 470)
new['feh.medi'] = (union(loop_medi, dots('feh.medi', 276 - dotcenter('feh.medi')[0], 515 - dotcenter('feh.medi')[1])), 470)
new['dotlessQaf.init'] = (loop_init, 470)

# ---------- WAW: round head on the reh body (same tail as reh) ----------
WDX = round(max(0, K - 1) * 40); WDY = round(max(0, K - 1) * 35)   # heavy weights: open the waw head
WAW_HEAD = f'M 322 {250 + WDY // 2} C 322 {318 + WDY} {272 - WDX // 2} {345 + WDY} {208 - WDX // 2} {345 + WDY} C {124 - WDX} {345 + WDY} {78 - WDX} {285 + WDY // 2} {78 - WDX} {195 + WDY // 3} C {78 - WDX} 102 {128 - WDX // 2} {Y} {208 - WDX // 2} {Y} L 322 {Y}'
WAW_STEM = f'M 322 {300 + WDY} L 322 40 C 322 -145 195 -232 -22 -255'
waw = union(stroke(WAW_HEAD, W), stroke(WAW_STEM, W))
new['waw.isol'] = (shift(waw, WDX), 405 + WDX)
new['waw.fina'] = (union(shift(waw, WDX), stroke(f'M {300 + WDX} {Y} L {413 + WDX} {Y}', W)), 405 + WDX)

# ---------- MEEM: low wide oval (clearly lower/wider than the tall feh/qaf egg) ----------
def oval(cx, w, h, y0=None):
    y0 = Y if y0 is None else y0
    x0, x1, yt = cx - w / 2, cx + w / 2, y0 + h
    k = 0.5523
    rx, ry = w / 2, h / 2; cy = y0 + ry
    return (f'M {cx} {y0} C {cx + k*rx} {y0} {x1} {cy - k*ry} {x1} {cy} '
            f'C {x1} {cy + k*ry} {cx + k*rx} {yt} {cx} {yt} C {cx - k*rx} {yt} {x0} {cy + k*ry} {x0} {cy} '
            f'C {x0} {cy - k*ry} {cx - k*rx} {y0} {cx} {y0} Z')
def softhex_head(cx, w, h, y0=None, t=0.38):
    y0 = Y if y0 is None else y0
    x0, x1, yt, cy = cx - w / 2, cx + w / 2, y0 + h, y0 + h / 2
    q = w * 0.24
    vs = [(cx - w/2 + q, y0), (cx + w/2 - q, y0), (x1, cy), (cx + w/2 - q, yt), (cx - w/2 + q, yt), (x0, cy)]
    d = ''
    for k in range(6):
        p0, p1, p2 = vs[k - 1], vs[k], vs[(k + 1) % 6]
        a = (p1[0] + (p0[0] - p1[0]) * t, p1[1] + (p0[1] - p1[1]) * t)
        b = (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
        d += (f'M {a[0]:.1f} {a[1]:.1f} ' if k == 0 else f'L {a[0]:.1f} {a[1]:.1f} ') + f'Q {p1[0]:.1f} {p1[1]:.1f} {b[0]:.1f} {b[1]:.1f} '
    return d + 'Z'
true_oval = oval
oval = softhex_head
MH = 235   # head height (centre-line) -> outer ~314, feh egg is ~418
def soft_poly(vs, t=0.32):
    d = ''
    for k in range(len(vs)):
        p0, p1, p2 = vs[k - 1], vs[k], vs[(k + 1) % len(vs)]
        a = (p1[0] + (p0[0] - p1[0]) * t, p1[1] + (p0[1] - p1[1]) * t)
        b = (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
        d += (f'M {a[0]:.1f} {a[1]:.1f} ' if k == 0 else f'L {a[0]:.1f} {a[1]:.1f} ') + f'Q {p1[0]:.1f} {p1[1]:.1f} {b[0]:.1f} {b[1]:.1f} '
    return fill(d + 'Z')
_m = max(0, (W - 79) * 0.7)      # heavy weights: taller meem head so its counter stays open
MEEM_TD = f'M -8 {Y} L 248 {Y} L 334 31 C 349 80 356 132 356 {200+_m} C 356 {256+_m} 332 {294+_m} 282 {294+_m} C {236-_m*0.3} {294+_m} {204-_m*0.55} {262+_m} {178-_m*0.65} {198+_m*0.7} C {150-_m*0.5} 128 125 {Y} 75 {Y} L 20 {Y}'
import draw as _dr
E = W - 79                      # weight growth vs approved Regular
SXM = 1 + E / 350               # open the small counters (meem/heh) in heavy weights
_dr.SKX = SXM
mi = stroke(MEEM_TD, W)
_dr.SKX = 1.0
new['meem.init'] = (mi, 420 * SXM)
_dr.SKX = SXM
new['meem.medi'] = (union(mi, stroke(f'M 468 {Y} L 400 {Y} C 372 {Y} 352 {Y - 8} 330 {Y - 12}', W)), 460 * SXM)
_dr.SKX = 1.0
new['meem.isol'] = (shift(clip(union(stroke(oval(330 + E * 0.4, 270 + E * 0.8, MH + E * 0.5), W), stroke(f'M {330 + E * 0.4} {Y} L 125 {Y} L 112 -330', W)), y0=-290), -24), 476 + E * 0.8)
new['meem.fina'] = (shift(clip(union(stroke(oval(300 + E * 0.4, 270 + E * 0.8, MH + E * 0.5), W), stroke(f'M {300 + E * 0.4} {Y} L {508 + E * 0.8} {Y}', W), stroke(f'M {300 + E * 0.4} {Y} L 175 {Y} L 165 -330', W)), y0=-290), -77), 423 + E * 0.8)

# ---------- HEH ----------
SXH = 1 + max(0, E) / 190        # initial heh needs more room than meem in heavy weights
_dr.SKX = SXH
heh_init = clip(union(stroke(f'M 44 320 L 70 340 L 290 340 C 375 340 425 285 425 200 C 425 110 375 {Y} 290 {Y} L -8 {Y}', W),
                      stroke(true_oval(198 - max(0, E) * 0.62, 150 + max(0, E) * 0.65, 240 + E * 0.3, y0=58), W)), y0=0)
_dr.SKX = 1.0
new['heh.init'] = (heh_init, 470 * SXH)
hm_up = true_oval(205 + E * 0.75, 205 + E * 1.5, 215 + E * 1.0, y0=Y)
hm_dn = true_oval(205 + E * 0.75, 175 + E * 1.5, 190 + E * 0.8, y0=Y - 190 - E * 0.8)
new['heh.medi'] = (union(stroke(hm_up, W), stroke(hm_dn, W), stroke(f'M -8 {Y} L {418 + E * 1.5} {Y}', W)), 410 + E * 1.5)

# ---------- TEH final: baseline flows up into a soft left horn ----------
beh_fina = clip(union(stroke(f'M 548 420 L 548 {Y} L 270 {Y} C 150 {Y} 82 110 80 250 L 80 420', W), stroke(f'M 520 {Y} L 608 {Y}', W)), y0=0, y1=373)
new['beh.fina'] = (union(beh_fina, dots('beh.fina', 314 - dotcenter('beh.fina')[0], 0)), 600)
tc = dotcenter('teh.fina')
new['teh.fina'] = (union(beh_fina, dots('teh.fina', 314 - tc[0], 470 - tc[1])), 600)

# ---------- TEH MARBUTA: compact loop on the baseline (no tail beyond the loop) ----------
_tms = 1 + max(0, E) / 230; _dr.SKX = _tms
tm_loop = stroke('M 235 38.5 C 125 38.5 90 110 90 180 C 90 270 160 335 250 335 C 345 335 405 270 405 190 C 405 110 360 38.5 235 38.5 Z', W)
mc = dotcenter('tehMarbuta.fina')
tm_fina = union(stroke(f'M 508 {Y} L 165 {Y}', W),
                stroke(f'M 175 {Y} C 115 {Y} 85 105 85 182 C 85 278 158 340 245 340 C 335 340 398 282 398 205 L 398 {Y}', W))
_dr.SKX = 1.0
new['heh.fina'] = (clip(tm_fina, y0=0), 500 * _tms)
new['tehMarbuta.fina'] = (clip(union(tm_fina, dots('tehMarbuta.fina', 242 * _tms - mc[0], 485 - 555)), y0=0), 500 * _tms)
ic = dotcenter('tehMarbuta.isol')
new['tehMarbuta.isol'] = (union(tm_loop, dots('tehMarbuta.isol', 248 * _tms - ic[0], 485 - 555)), 480 * _tms)

# ---------- YEH final ----------
YF = f'M 760 {Y} L 655 {Y} Q 612 {Y} 602 -18 C 588 -125 520 -290 360 -290 C 190 -290 92 -210 92 -95 C 92 -5 106 85 118 220'
yeh_body = clip(stroke(YF, W), y1=170)
new['alefMaksura.fina'] = (yeh_body, 752)
yc = dotcenter('yeh.fina')
new['yeh.fina'] = (union(yeh_body, dots('yeh.fina', 360 - yc[0], -420 - yc[1])), 752)

# ---------- HAMZA: Alexandria (OFL) outlines scaled to our metrics, corners softened (RunJari) ----------
from fontTools.pens.svgPathPen import SVGPathPen
AX = TTFont(ALEX); AXG = AX.getGlyphSet()
SC = 708 / 820
STRETCH = {'uni0621': (175, 270, 48), 'uni0654': (603, 652, 26), 'uni0655': (-150, -101, 26)}
_A400 = TTFont('/home/claude/fa/alex400.ttf').getGlyphSet()
def _ref400(name):
    from fontTools.pens.recordingPen import DecomposingRecordingPen as _D
    r = _D(_A400); _A400[name].draw(r); b = BoundsPen(None); r.replay(b); return b.bounds
def alex(name, sc=SC, dx=0, dy=0):
    from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen as RP
    dr = DecomposingRecordingPen(AXG); AXG[name].draw(dr)
    st = STRETCH.get(name)
    if st:   # the stretch band was tuned on Alexandria 400: re-map it proportionally to this instance
        ref = _ref400(name); bp_ = BoundsPen(None); dr.replay(bp_); cb = bp_.bounds
        k_ = (cb[3] - cb[1]) / (ref[3] - ref[1])
        st = (cb[1] + (st[0] - ref[1]) * k_, cb[1] + (st[1] - ref[1]) * k_, st[2] * k_)
    def fy(y):
        if not st: return y
        y1, y2, d = st
        if y <= y1: return y
        if y >= y2: return y + d
        return y + d * (y - y1) / (y2 - y1)
    rec = [(op, tuple((p[0], fy(p[1])) for p in a)) for op, a in dr.value]
    out = pathops.Path(); pen = TransformPen(out.getPen(), (sc, 0, 0, sc, dx, dy))
    for op, a in rec: getattr(pen, op)(*a)
    out.simplify(); return out
def bounds(p):
    bp = BoundsPen(None); p.draw(bp); return bp.bounds
def soften(p, r=9):
    sv = SVGPathPen(None); p.draw(sv)
    sk = fill(sv.getCommands().replace(',', ' '))
    er = subtract(sk, stroke(sv.getCommands().replace(',', ' '), 2 * r, join='round'))
    sv2 = SVGPathPen(None); er.draw(sv2)
    return union(er, stroke(sv2.getCommands().replace(',', ' '), 2 * r, join='round'))
HZ = 0.84; HM = 0.92                      # isolated hamza / hamza marks size vs Alexandria (ruler: avg of Alexandria & Plex)
_AXG0 = AXG
# isolated hamza: the Alexandria weight whose stroke at our size equals our own stroke (measured: 300->56, 380->75, 700->120, 900->150)
AXG = TTFont(f'/home/claude/fa/alex{ {300: 300, 400: 380, 700: 700, 900: 900}[CFG_ALEXW] }.ttf').getGlyphSet()
_hz = soften(alex('uni0621', SC * HZ))
AXG = TTFont(f'/home/claude/fa/alex{min(900, CFG_ALEXW + 100)}.ttf').getGlyphSet()   # marks keep the one-step heavier cut
_hb = bounds(_hz); _sb = 42 * (1 + E / 200)          # its own side bearings, so heavy weights never touch the neighbour
_hz = shift(_hz, _sb - _hb[0])
new['hamza.isol'] = (_hz, round(_hb[2] - _hb[0] + 2 * _sb))
def mark(cx, edge, below=False, k=1.0):
    m = alex('uni0655' if below else 'uni0654', SC * k * HM)
    b = bounds(m)
    dx = cx - (b[0] + b[2]) / 2
    dy = (edge - b[3]) if below else (edge - b[1])
    out = pathops.Path(); m.draw(TransformPen(out.getPen(), (1, 0, 0, 1, dx, dy)))
    return _reg(soften(out, 6))
new['uni0654'] = (mark(0, 7), 0)
new['uni0655'] = (mark(0, -7, below=True), 0)
def body_without(base, keep):
    body = pathops.Path(); pen = body.getPen()
    rp = RecordingPen(); gs[base].draw(rp)
    cs, cur = [], []
    for op, a_ in rp.value:
        cur.append((op, a_))
        if op in ('closePath', 'endPath'): cs.append(cur); cur = []
    for c in cs:
        bp = BoundsPen(None)
        for op, a_ in c: getattr(bp, op)(*a_)
        if keep(bp.bounds):
            for op, a_ in c: getattr(pen, op)(*a_)
    return body
for nm, cx in (('alefHamzaAbove.isol', 88), ('alefHamzaAbove.fina', 100)):
    new[nm] = (union(body_without(nm, lambda b: b[3] - b[1] > 300), mark(cx, 752)), f['hmtx'][nm][0])
for nm, cx in (('alefHamzaBelow.isol', 88), ('alefHamzaBelow.fina', 100)):
    new[nm] = (union(body_without(nm, lambda b: b[3] - b[1] > 300), mark(cx, -55, below=True)), f['hmtx'][nm][0])
for nm in ('yehHamza.init', 'yehHamza.medi'):
    bb = BoundsPen(None); gs[nm].draw(bb)
    body = body_without(nm, lambda b: b[1] < 400)
    tb = bounds(body)
    new[nm] = (union(body, mark(tb[2] - 75, 440)), f['hmtx'][nm][0])
# KAF isol/fina: the thin old zigzag replaced by our hamza-shaped mark (same family as the approved hamza)
for nm in ('kaf.isol', 'kaf.fina'):
    body = body_without(nm, lambda b: b[3] - b[1] > 300)
    old = body_without(nm, lambda b: b[3] - b[1] <= 300); ob = bounds(old)
    _AXG = AXG
    AXG = TTFont(f'/home/claude/fa/alex{ {300: 300, 400: 400, 700: 500, 900: 700}[CFG_ALEXW] }.ttf').getGlyphSet()
    km = mark(0, 0, k=0.82 + 0.1 * max(0, K - 1)); kb = bounds(km)
    AXG = _AXG
    o = pathops.Path(); km.draw(TransformPen(o.getPen(), (1, 0, 0, 1, (ob[0] + ob[2]) / 2 - (kb[0] + kb[2]) / 2, (ob[1] + ob[3]) / 2 - (kb[1] + kb[3]) / 2 + 10)))
    new[nm] = (union(body, _reg(o)), f['hmtx'][nm][0])
new['wawHamza.isol'] = (union(shift(waw, WDX), mark(200 + WDX // 2, 430 + WDY)), 405 + WDX)
new['wawHamza.fina'] = (union(shift(waw, WDX), stroke(f'M {300 + WDX} {Y} L {413 + WDX} {Y}', W), mark(200 + WDX // 2, 430 + WDY)), 405 + WDX)

new['yehHamza.fina'] = (union(yeh_body, mark(360, 120)), 752)


# ================= ROUND: remaining Arabic letters =================
def dot_from(name, cx, cy, maxh=DOTMAX):
    c = dotcenter(name, maxh)
    return dots(name, cx - c[0], cy - c[1], maxh)
# DAL / THAL: taller (top ~500), soft corner, Alexandria structure
DAL = f'M 140 470 L 282 318 C 338 258 400 222 400 140 L 400 {Y + 34} Q 400 {Y} 366 {Y} L 40 {Y}'
dal_i = stroke(DAL, W)
dal_f = union(dal_i, stroke(f'M 300 {Y} L 488 {Y}', W))
new['dal.isol'] = (dal_i, 480); new['dal.fina'] = (dal_f, 480)
new['thal.isol'] = (union(dal_i, dot_from('thal.isol', 215, 625)), 480)
new['thal.fina'] = (union(dal_f, dot_from('thal.fina', 215, 625)), 480)
# HAH family dotted forms
hah_medi = new['hah.medi'][0]; hah_isol = new['hah.isol'][0]; hah_fina = new['hah.fina'][0]
new['jeem.medi'] = (union(hah_medi, dot_from('jeem.medi', 215, -135)), 470)
new['khah.medi'] = (union(hah_medi, dot_from('khah.medi', 230, 470)), 470)
new['jeem.fina'] = (union(hah_fina, dot_from('jeem.fina', 262, -95)), 500)
new['khah.fina'] = (union(hah_fina, dot_from('khah.fina', 245, 470)), 500)
new['khah.isol'] = (union(hah_isol, dot_from('khah.isol', 245, 470)), 500)
# TCHEH (3 dots below)
def tri_dots(name, cx, cy):
    p = dots(name, 0, 0); bp = BoundsPen(None); p.draw(bp); b = bp.bounds
    out = pathops.Path(); p.draw(TransformPen(out.getPen(), (1, 0, 0, 1, cx - (b[0]+b[2])/2, cy - (b[1]+b[3])/2))); return _reg(out)
new['tcheh.init'] = (union(new['hah.init'][0], tri_dots('tcheh.init', 215, -160)), 470)
new['tcheh.medi'] = (union(hah_medi, tri_dots('tcheh.medi', 215, -160)), 470)
new['tcheh.fina'] = (union(hah_fina, tri_dots('tcheh.fina', 262, -110)), 500)
new['tcheh.isol'] = (union(hah_isol, tri_dots('tcheh.isol', 262, -110)), 500)
# ZAH = TAH + dot
for frm in ('init', 'medi', 'fina', 'isol'):
    tp, adv = new['tah.' + frm]
    new['zah.' + frm] = (union(tp, dot_from('zah.' + frm, 300 + TDX // 2, 560 + TDY)), adv)
# GHAIN medial = new ain medial + dot
new['ghain.medi'] = (union(new['ain.medi'][0], dot_from('ghain.medi', 250 + 2 * _a, 480 + _t)), 440 + 2 * _a)
new['ghain.isol'] = (union(new['ain.isol'][0], dot_from('ghain.isol', 285, 540)), 585)
new['ghain.init'] = (union(new['ain.init'][0], dot_from('ghain.init', 285, 540)), 505)
new['ghain.fina'] = (union(new['ain.fina'][0], dot_from('ghain.fina', _x(250) + 40, 480 + _t)), _fa)
# QAF fina/isol: loop over a round bowl
QAF = f'M 62 175 L 62 40 C 62 -150 168 -265 298 -265 C 428 -265 508 -150 508 20 L 508 205 C 508 315 445 378 368 378 C 282 378 225 318 225 228 C 225 125 262 {Y} 335 {Y} L 508 {Y}'
qaf_i = clip(stroke(QAF, W), y1=420)
new['qaf.isol'] = (union(qaf_i, dot_from('qaf.isol', 368, 515)), 580)
new['qaf.fina'] = (union(qaf_i, stroke(f'M 500 {Y} L 588 {Y}', W), dot_from('qaf.fina', 368, 515)), 580)
# FEH fina/isol: loop at the right, baseline runs left to a soft upturn
DX = 262
FEH = (f'M 48 178 C 48 88 86 {Y} 165 {Y} L {330+DX} {Y} C {395+DX} {Y} {420+DX} 120 {420+DX} 205 '
       f'C {420+DX} 315 {355+DX} 378 {275+DX} 378 C {190+DX} 378 {128+DX} 318 {128+DX} 225 C {128+DX} 120 {160+DX} {Y} {240+DX} {Y}')
feh_i = stroke(FEH, W)
new['feh.isol'] = (union(feh_i, dot_from('feh.isol', 275+DX, 515)), 420+DX+60)
new['feh.fina'] = (union(feh_i, stroke(f'M {400+DX} {Y} L {420+DX+68} {Y}', W), dot_from('feh.fina', 275+DX, 515)), 420+DX+60)
# BEH / TEH / THEH isolated: bowl with right tooth (same as final without the entry)
beh_i = clip(stroke(f'M 548 420 L 548 {Y} L 270 {Y} C 150 {Y} 82 110 80 250 L 80 420', W), y0=0, y1=373)
new['beh.isol'] = (union(beh_i, dot_from('beh.isol', 314, -130)), 610)
new['teh.isol'] = (union(beh_i, dots('teh.isol', 314 - dotcenter('teh.isol')[0], 470 - dotcenter('teh.isol')[1])), 610)
new['theh.isol'] = (union(beh_i, dots('theh.isol', 314 - dotcenter('theh.isol')[0], 520 - dotcenter('theh.isol')[1])), 610)
new['theh.fina'] = (union(beh_fina, dots('theh.fina', 314 - dotcenter('theh.fina')[0], 520 - dotcenter('theh.fina')[1])), 600)
# YEH / ALEF MAKSURA isolated: soft head at the right flowing into the same bowl as the final form
YI = 'M 728 335 C 690 385 640 402 585 402 C 480 402 405 370 405 310 C 405 245 480 228 560 205 C 660 176 700 120 700 30 C 700 -130 560 -200 400 -200 C 220 -200 100 -170 100 -80 C 100 0 102 100 110 210'
yeh_iso = stroke(YI, W)
new['alefMaksura.isol'] = (yeh_iso, 790)
new['yeh.isol'] = (union(yeh_iso, dot_from('yeh.isol', 400, -365)), 790)
new['yehHamza.isol'] = (union(yeh_iso, mark(235 - 0.3 * E, 255 + 0.8 * max(0, E), k=1 - 0.2 * max(0, K - 1))), 790)
# HEH isolated = teh marbuta isolated without dots
new['heh.isol'] = (tm_loop if isinstance(tm_loop, pathops.Path) else to_pathops(tm_loop), 480 * _tms)
# MADDA: a real wave
def madda(cx, cy, k=1.0):
    return stroke(f'M {cx-118*k} {cy-6*k} C {cx-80*k} {cy+40*k} {cx-38*k} {cy+40*k} {cx} {cy+6*k} C {cx+38*k} {cy-28*k} {cx+80*k} {cy-30*k} {cx+118*k} {cy+14*k}', 54*k*K)
for nm in ('alefMadda.isol', 'alefMadda.fina'):
    _b = body_without(nm, lambda b: b[1] < 700); _bb = bounds(_b)
    new[nm] = (union(_b, madda((_bb[0] + _bb[2]) / 2 + (8 if nm.endswith('fina') else 0), 800)), f['hmtx'][nm][0])
new['uni0653'] = (madda(0, 50, 0.9), 0)          # marks sit at y~0 (anchor 0,0)

# lam-alef ligatures: swap old madda / hamza marks for the new ones, same centre
def swap_mark(nm, kind):
    rp = RecordingPen(); gs[nm].draw(rp)
    cs, cur = [], []
    for op, a_ in rp.value:
        cur.append((op, a_))
        if op in ('closePath', 'endPath'): cs.append(cur); cur = []
    body = pathops.Path(); pen = body.getPen(); mk = None
    for c in cs:
        bp = BoundsPen(None)
        for op, a_ in c: getattr(bp, op)(*a_)
        b = bp.bounds
        is_mark = (b[1] > 560) if kind != 'below' else (b[3] < -25)
        if is_mark:
            mk = b if mk is None else (min(mk[0], b[0]), min(mk[1], b[1]), max(mk[2], b[2]), max(mk[3], b[3]))
            continue
        for op, a_ in c: getattr(pen, op)(*a_)
    if mk is None: return None
    cx = (mk[0] + mk[2]) / 2
    if kind == 'madda': m = madda(cx, 800)
    elif kind == 'above': m = mark(cx, 752)
    else: m = mark(cx, -55, below=True)
    return union(body, m)
for nm, kind in (('lamAlefMadda.isol', 'madda'), ('lamAlefMadda.fina', 'madda'),
                 ('lamAlefHamzaAbove.isol', 'above'), ('lamAlefHamzaAbove.fina', 'above'),
                 ('lamAlefHamzaBelow.isol', 'below'), ('lamAlefHamzaBelow.fina', 'below')):
    r = swap_mark(nm, kind)
    if r is not None: new[nm] = (r, f['hmtx'][nm][0])

# ---------- LATIN DIGITS (tabular 600) ----------
import draw as _dr
Wd = CFG['WL']; _dr.SKX, _dr.SKY = 1 - 0.06 * max(0, Wd - 86) / 78, CFG['sky']; Yd = Wd * CFG['sky'] / 2
from wt import LCAP as _LC
_dr.SYS, _dr.SYH = (_LC + 10 - 2 * Yd) / (700 - 2 * Yd), Yd     # draw the figures straight on the Latin ruler (no later squash)
T = 700 - Yd
five = stroke(f'M 520 {T} L 170 {T} L 152 392 C 200 425 255 440 315 440 C 455 440 540 355 540 228 C 540 100 450 {Yd} 315 {Yd} C 225 {Yd} 160 68 112 128', Wd)
new['five'] = (five, 600)
SIX = f'M 470 640 C 430 {T} 385 {T} 345 {T} C 190 {T} 100 520 100 300 C 100 125 190 {Yd} 300 {Yd} C 415 {Yd} 500 120 500 232 C 500 345 415 422 305 422 C 178 422 100 365 100 300'
six = stroke(SIX, Wd)
new['six'] = (six, 600)
from fontTools.pens.transformPen import TransformPen as _TP
_n = to_pathops(six); nine = pathops.Path(); _n.draw(_TP(nine.getPen(), (-1, 0, 0, -1, 600, 700)))
new['nine'] = (nine, 600)
two = clip(stroke(f'M 105 548 C 132 628 205 {T} 295 {T} C 405 {T} 478 598 478 505 C 478 430 440 382 375 325 L 112 {Yd} L 518 {Yd}', Wd), y0=0)
new['two'] = (two, 600)
_f4 = 212 - 0.35 * max(0, Wd - 86)
four = clip(stroke(f'M 560 {_f4} L 78 {_f4} L 388 {T} L 400 {T} L 400 -60', Wd), y0=0, y1=_LC + 10)
new['four'] = (four, 600)
_dr.SKX, _dr.SKY = 1.0, 1.0; _dr.SYS, _dr.SYH = 1.0, 0.0
# ---------- ARABIC DIGITS ٢ ٣ (tabular 600) ----------
two_ar = union(clip(stroke('M 205 0 L 205 640 C 205 545 255 520 330 520 C 410 520 445 590 450 700', W), y0=0, y1=700))
new['uni0662'] = (two_ar, 600)
three_ar = clip(stroke('M 165 0 L 165 640 C 165 545 200 520 255 520 C 325 520 350 565 352 640 C 352 560 378 520 430 520 C 480 520 505 590 508 700', W), y0=0, y1=700)
new['uni0663'] = (three_ar, 600)

def center_in(path, adv):
    bp = BoundsPen(None); path.draw(bp); b = bp.bounds
    dx = (adv - (b[2] - b[0])) / 2 - b[0]
    out = pathops.Path(); path.draw(TransformPen(out.getPen(), (1, 0, 0, 1, dx, 0))); return out

for n, (p, adv) in new.items():
    if not isinstance(p, pathops.Path): p = to_pathops(p)
    if n in ('five', 'four', 'six', 'nine', 'two', 'uni0662', 'uni0663'):
        p = center_in(p, adv)
    set_glyph(f, n, p, adv=adv)

# ---------- DOTS: soft hexagon (all corners rounded, near-circle; hexagon visible when enlarged) ----------
import math
from fontTools.pens.recordingPen import RecordingPen as _RP
from fontTools.pens.boundsPen import BoundsPen as _BP
def soft_hex(cx, cy, rx, ry, t=0.36):
    vs = [(cx + rx * math.cos(math.radians(90 + 60 * k)) / math.cos(math.radians(30)) * (1 if k % 3 else 1), 0) for k in range(6)]
    vs = []
    for k in range(6):
        a = math.radians(90 + 60 * k)
        vs.append((cx + rx / math.cos(math.radians(30)) * math.cos(a), cy + ry * math.sin(a)))
    d = ''
    for k in range(6):
        p0, p1, p2 = vs[k - 1], vs[k], vs[(k + 1) % 6]
        a = (p1[0] + (p0[0] - p1[0]) * t, p1[1] + (p0[1] - p1[1]) * t)
        b = (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)
        d += (f'M {a[0]:.1f} {a[1]:.1f} ' if k == 0 else f'L {a[0]:.1f} {a[1]:.1f} ') + f'Q {p1[0]:.1f} {p1[1]:.1f} {b[0]:.1f} {b[1]:.1f} '
    return fill(d + 'Z')
gs2 = f.getGlyphSet()
DOTGLYPHS = []
for gname in f.getGlyphOrder():
    if gname.startswith(('.', 'uni03', 'uni02', 'uni064', 'uni065', 'uni067', 'kaf', 'shadda', 'arabicComma', 'arabicSemicolon', 'arabicQuestion', 'comma', 'semicolon')) or 'amza' in gname or 'adda' in gname or len(gname) == 1 and gname.isalpha(): continue
    rp = _RP(); gs2[gname].draw(rp)
    cs, cur = [], []
    for op, a in rp.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'): cs.append(cur); cur = []
    keep, dots_ = [], []
    for c in cs:
        bp = _BP(None)
        for op, a in c: getattr(bp, op)(*a)
        b = bp.bounds
        if not b: continue
        w, h = b[2] - b[0], b[3] - b[1]
        npts = sum(1 for op, a in c if op in ('lineTo', 'qCurveTo', 'curveTo'))
        _ap = AreaPen()
        for op, a in c: getattr(_ap, op)(*a)
        if _ap.value > 0: keep.append(c); continue   # counter, not a dot
        D = {'Light': 81, 'Regular': 97, 'Bold': 133, 'Black': 163}[WT]
        if 0.72*D <= w <= 1.4*D and 0.8*D <= h <= 1.55*D and 0.7 <= w / h <= 1.1 and 8 <= npts <= 30:
            dots_.append(b)
        else:
            keep.append(c)
    if not dots_: continue
    out = pathops.Path(); pen = out.getPen()
    for c in keep:
        for op, a in c: getattr(pen, op)(*a)
    p = out
    dots_ = space_dots(out, dots_)
    for b in dots_:
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        _ds = {'Light': 1.0, 'Regular': 1.0, 'Bold': 0.97, 'Black': 0.9}[WT]   # heavy weights: slightly smaller dots so groups never fuse
        p = union(p, soft_hex(cx, cy, (b[2] - b[0]) / 2 * 1.04 * _ds, (b[3] - b[1]) / 2 * 0.98 * _ds))
    adv = f['hmtx'][gname][0]
    set_glyph(f, gname, p, adv=adv)
    DOTGLYPHS.append(gname)
print('dots replaced in', len(DOTGLYPHS))
# Arabic-Indic zero: always our soft-hex dot (never the old diamond), sized like the dots, centred at mid-height
_D = {'Light': 81, 'Regular': 97, 'Bold': 133, 'Black': 163}[WT]
set_glyph(f, 'uni0660', to_pathops(soft_hex(200, 290, _D * 0.62, _D * 0.66)), adv=400)

# sample only: drop pair kerning that touched the redrawn glyphs or digits
from fontTools.ttLib.tables import otTables
names = set(new) | {'zero', 'one', 'two', 'three', 'seven', 'eight', 'colon', 'period'}
import json as _j; _j.dump(sorted(names), open(f'/home/claude/fa/work/neutral_{WT}.json', 'w'))
for lk in f['GPOS'].table.LookupList.Lookup:
    sts = [x.ExtSubTable for x in lk.SubTable] if lk.LookupType == 9 else lk.SubTable
    for st in sts:
        if type(st).__name__ == 'PairPos' and st.Format == 1:
            for i, g in enumerate(st.Coverage.glyphs):
                for pvr in st.PairSet[i].PairValueRecord:
                    if g in names or pvr.SecondGlyph in names:
                        for v in (pvr.Value1, getattr(pvr, 'Value2', None)):
                            if v is not None:
                                for a in ('XAdvance', 'XPlacement'):
                                    if hasattr(v, a): setattr(v, a, 0)
for lk in f['GPOS'].table.LookupList.Lookup:
    sts = lk.SubTable
    if lk.LookupType == 9: sts = [x.ExtSubTable for x in sts]
    for st in sts:
        if getattr(st, 'LookupType', 2) != 2 and lk.LookupType != 9: pass
        if hasattr(st, 'Class1Record'):
            c1 = st.ClassDef1.classDefs; c2 = st.ClassDef2.classDefs
            cov = set(st.Coverage.glyphs)
            k1 = {c1.get(g, 0) for g in names if g in cov}
            k2 = {c2.get(g, 0) for g in names if g in c2}
            for i, r1 in enumerate(st.Class1Record):
                for j, r2 in enumerate(r1.Class2Record):
                    if i in k1 or j in k2:
                        for v in (r2.Value1, getattr(r2, 'Value2', None)):
                            if v is not None:
                                for a in ('XAdvance', 'XPlacement'):
                                    if hasattr(v, a): setattr(v, a, 0)
for lk in f['GPOS'].table.LookupList.Lookup:
    if lk.LookupType != 1: continue
    for st in lk.SubTable:
        gl = st.Coverage.glyphs
        if st.Format == 1:
            if any(g in names for g in gl):
                # split: drop redrawn glyphs from coverage
                st.Coverage.glyphs = [g for g in gl if g not in names]
        else:
            keep = [(g, v) for g, v in zip(gl, st.Value) if g not in names]
            st.Coverage.glyphs = [g for g, _ in keep]; st.Value = [v for _, v in keep]; st.ValueCount = len(keep)
# tabular widths for the remaining digits in the sample
for d in ['zero', 'one', 'three', 'seven', 'eight']:
    g = f['glyf'][d]; adv, lsb = f['hmtx'][d]; w = g.xMax - g.xMin
    shift = (600 - w) / 2 - g.xMin
    g.coordinates.translate((shift, 0)); g.recalcBounds(f['glyf'])
    f['hmtx'][d] = (600, g.xMin)
f['name'].setName('Ameer070 Sample', 1, 3, 1, 0x409)
import os; os.makedirs('/home/claude/fa/sample', exist_ok=True)
f.save(OUT)

print('ok', len(new))
