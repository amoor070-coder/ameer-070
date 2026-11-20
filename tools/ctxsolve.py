"""Contextual tashkeel solver.
Shapes a vocalised corpus with the built font, finds marks whose ink comes within GAP of another glyph's ink
(neighbour letters, their marks), and finds the cheapest shift (sideways away from the neighbour, then up/down)
that clears it. Emits FEA chain-context rules keyed by (base, mark, neighbour base, side).
usage: ctxsolve.py font.ttf corpus.txt [corpus2 ...] -o rules.fea
"""
import sys, json, collections
import uharfbuzz as hb, skia, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

S = 0.1
import os
GAP = int(os.environ.get('GAP', 24))   # font units, generic clearance (heavier weights need more air)
GAP_ARM = 70        # extra clearance from kaf/gaf/keheh arms (avoid the gaf look)
ARM = ('kaf.init', 'kaf.medi', 'gaf.init', 'gaf.medi', 'keheh.init', 'keheh.medi')

args = sys.argv[1:]
out = args[args.index('-o') + 1]; args = args[:args.index('-o')]
path, corpora = args[0], args[1:]
t = TTFont(path); go = t.getGlyphOrder(); gs = t.getGlyphSet()
gdef = t['GDEF'].table.GlyphClassDef.classDefs
face = hb.Face(hb.Blob.from_file_path(path)); font = hb.Font(face)
fea_src = None
cache = {}

def gpath(n):
    if n in cache: return cache[n]
    rp = RecordingPen(); gs[n].draw(rp); sp = skia.Path()
    for op, a in rp.value:
        if op == 'moveTo': sp.moveTo(*a[0])
        elif op == 'lineTo': sp.lineTo(*a[0])
        elif op == 'qCurveTo':
            pp = list(a)
            while len(pp) > 2:
                mid = ((pp[0][0] + pp[1][0]) / 2, (pp[0][1] + pp[1][1]) / 2); sp.quadTo(*pp[0], *mid); pp = pp[1:]
            sp.quadTo(*pp[0], *pp[1])
        elif op == 'curveTo': sp.cubicTo(*a[0], *a[1], *a[2])
        elif op == 'closePath': sp.close()
    cache[n] = sp; return sp

def is_mark(n): return gdef.get(n) == 3

def shape(text):
    b = hb.Buffer(); b.add_str(text); b.guess_segment_properties(); hb.shape(font, b)
    items = []; x = 0
    for i, p in zip(b.glyph_infos, b.glyph_positions):
        n = go[i.codepoint]; items.append({'n': n, 'mark': is_mark(n), 'cl': i.cluster, 'x': x + p.x_offset, 'y': p.y_offset}); x += p.x_advance
    # logical order: RTL output is visual (left->right) => reverse
    items = items[::-1]
    base = None
    for k, it in enumerate(items):
        if not it['mark']: base = k
        it['base'] = base if it['mark'] else k
    return items, x

def masks(items, W):
    H = int(2800 * S)
    res = []
    for it in items:
        surf = skia.Surface(W, H); c = surf.getCanvas(); c.clear(0)
        m = skia.Matrix(); m.setAll(S, 0, S * it['x'] + 30, 0, -S, S * (1700 - it['y']), 0, 0, 1)
        c.concat(m); c.drawPath(gpath(it['n']), skia.Paint(AntiAlias=False, Color=0xFFFFFFFF))
        res.append(surf.toarray()[:, :, 0] > 0)
    return res

def dil(a, r):
    out = a.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r: out |= np.roll(np.roll(a, dx, 1), dy, 0)
    return out

def shifted(m, dx, dy):
    return np.roll(np.roll(m, int(round(dx * S)), 1), -int(round(dy * S)), 0)

def gap_for(items, k, j):
    nb = items[items[j]['base']]['n']
    if not items[j]['mark'] and nb in ARM and items[k]['n'] not in BOTTOM: return GAP_ARM
    return GAP

BOTTOM = {'kasra', 'kasratan', 'uni0655', 'uni0656', 'shaddaKasra', 'shaddaKasratan'}
BOTTOM_TRUE = {'kasra', 'kasratan', 'uni0655', 'uni0656'}

def hits(items, ms, k, dx=0, dy=0, dmask={}):
    """indices j whose ink is within the clearance of mark k (shifted)"""
    mk = shifted(ms[k], dx, dy)
    out = []
    for j, it in enumerate(items):
        if j == k or j == items[k]['base']: continue
        if it['mark'] and it['base'] == items[k]['base']: continue   # own stacked marks (mkmk handles)
        r = max(1, int(round(gap_for(items, k, j) * S)))
        mj = dmask.get(j, ms[j])
        if (dil(mk, r) & mj).any(): out.append(j)
    return out

def candidates(side, bottom):
    sx = 1 if side == 'L' else -1          # neighbour on the visual left -> move right
    sy = -1 if bottom else 1
    c = []
    for dx in (0, 20, 40, 60, 80):
        for dy in (0, 40, 80, 120, 160, 200, 240):
            if dx == dy == 0: continue
            c.append((dx + 1.6 * dy, sx * dx, sy * dy))
    return sorted(c)

rules = collections.defaultdict(lambda: [0, 0])     # key -> (dx, dy) max magnitude
unsolved = []
words = []
for cp in corpora: words += open(cp).read().split()
for w in words:
    items, tot = shape(w)
    W = int(tot * S) + 60
    ms = masks(items, W)
    moved = {}
    for _round in range(3):
        bad = [(k, j) for k, it in enumerate(items) if it['mark'] for j in hits(items, ms, k, *moved.get(k, (0, 0)), {q: shifted(ms[q], *moved[q]) for q in moved})]
        if not bad: break
        k, j = bad[0]
        opts = []
        for mv, other in ((k, j), (j, k)):
            if not items[mv]['mark']: continue
            bmv = items[mv]['base']; bot = items[bmv]['base']
            ob = items[other]['base']
            if ob == bmv: continue
            # logical order: index greater = later in text = visual left (RTL)
            side = 'L' if ob > bmv else 'R'
            bottom = items[mv]['n'] in BOTTOM_TRUE
            cur = moved.get(mv, (0, 0))
            dm = {q: shifted(ms[q], *moved[q]) for q in moved if q != mv}
            for cost, dx, dy in candidates(side, bottom):
                nd = (cur[0] + dx, cur[1] + dy)
                if not hits(items, ms, mv, *nd, dm):
                    opts.append((cost, mv, ob, side, nd)); break
        if not opts:
            unsolved.append(w); break
        cost, mv, ob, side, nd = min(opts)
        moved[mv] = nd
        key = (side, items[items[mv]['base']]['n'], items[mv]['n'], items[ob]['n'])
        r = rules[key]
        if abs(nd[0]) > abs(r[0]): r[0] = nd[0]
        if abs(nd[1]) > abs(r[1]): r[1] = nd[1]

# ---- FEA
marks_top = sorted({n for n in go if is_mark(n)})
lines = ['@SOLVE_ANYMARK = [' + ' '.join(marks_top) + '];']
adj = set(tuple(v) for v in rules.values())
for dx, dy in sorted(adj):
    nm = f'SOLVE_ADJ_{dx}_{dy}'.replace('-', 'm')
    lines.append(f'lookup {nm} {{ pos @SOLVE_ANYMARK <{dx} {dy} 0 0>; }} {nm};')
lines.append('lookup SOLVE_CTX {')
for (side, b, m, nb), (dx, dy) in sorted(rules.items()):
    nm = f'SOLVE_ADJ_{dx}_{dy}'.replace('-', 'm')
    if side == 'L':      # neighbour comes after the base (logically next)
        lines.append(f"    pos {b}' {m}' lookup {nm} {nb};")
        lines.append(f"    pos {b}' {m}' lookup {nm} @SOLVE_ANYMARK {nb};")
    else:                # neighbour comes before the base
        lines.append(f"    pos {nb} {b}' {m}' lookup {nm};")
        lines.append(f"    pos {nb} @SOLVE_ANYMARK {b}' {m}' lookup {nm};")
lines.append('} SOLVE_CTX;')
lines.append('feature mark {\n  script arab;\n    lookup SOLVE_CTX;\n} mark;')
open(out, 'w').write('\n'.join(lines) + '\n')
print(path.split('/')[-1], 'words', len(words), 'rules', len(rules), 'unsolved', len(unsolved), unsolved[:8])
