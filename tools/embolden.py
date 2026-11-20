"""Bring the not-yet-redrawn v1.200 glyphs to the target stem W (offset outline by d=(W-old)/2),
keeping baseline stroke 0..W and the original tops (band-compress above the baseline stroke)."""
import sys, skia, pathops
sys.path.insert(0, '/home/claude/fa')
from wt import *
from draw import set_glyph, to_pathops
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen
from draw import parse, union
f = TTFont(OLDSRC)
d = (W - OLD) / 2
gs = f.getGlyphSet()
if abs(d) < 1.5:
    f.save(BASE); print('no embolden needed', WT); sys.exit()
from fontTools.pens.recordingPen import RecordingPen
def mapy(pp, fy):
    rp = RecordingPen(); pp.draw(rp)
    o = pathops.Path(); pen = o.getPen()
    for op, a in rp.value:
        getattr(pen, op)(*[(x, fy(y)) for x, y in a])
    return o
def offset_path(sp, d):
    paint = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=2 * d, AntiAlias=True)
    paint.setStrokeJoin(skia.Paint.kRound_Join)
    st = skia.Path(); paint.getFillPath(sp, st)
    return pathops.op(to_pathops(sp), to_pathops(st), pathops.PathOp.UNION)
n = 0
for g in f.getGlyphOrder():
    if g.startswith('.') or g in ('space', 'nbspace', 'uni00A0', 'uni200C', 'uni200D'): continue
    if f['glyf'][g].isComposite(): continue
    rp = DecomposingRecordingPen(gs); gs[g].draw(rp)
    if not rp.value: continue
    # split into contours, keep each contour's own fill for a robust offset
    sv = SVGPathPen(gs); gs[g].draw(sv)
    sp = parse(sv.getCommands().replace(',', ' '))
    sp.setFillType(skia.PathFillType.kWinding)
    b = BoundsPen(gs); gs[g].draw(b); bb = b.bounds
    big = (bb[3] - bb[1]) > 160 or (bb[2] - bb[0]) > 160
    out = offset_path(sp, d)
    if big:
        # baseline back to 0..W, tops back to original, compress the band between stroke and top
        top = bb[3]; lo = W + 30; hi = top - 90
        out = mapy(out, lambda y: y + d)
        if hi - lo > 100 and top > 250:
            def fy(y):
                if y <= lo: return y
                if y >= hi + 2 * d: return y - 2 * d
                return lo + (y - lo) * (hi - lo) / (hi + 2 * d - lo)
            out = mapy(out, fy)
    else:
        pass
    p = out if isinstance(out, pathops.Path) else to_pathops(out)
    rp2 = RecordingPen(); p.draw(rp2); cl = pathops.Path(); pen2 = cl.getPen(); cur = []
    for op, a in rp2.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'):
            xs = [pt[0] for _, aa in cur for pt in aa]; ys = [pt[1] for _, aa in cur for pt in aa]
            if xs and max(xs) - min(xs) > 6 and max(ys) - min(ys) > 6:
                for o, aa in cur: getattr(pen2, o)(*aa)
            cur = []
    p = cl
    adv = f['hmtx'][g][0]
    if adv > 0:
        # keep advance, but add the grown width to the sides only for non-joining shapes is handled by the h-ruler
        pass
    set_glyph(f, g, p, adv=adv)
    n += 1
f.save(BASE); print('emboldened', n, 'glyphs, d=', d, WT)
