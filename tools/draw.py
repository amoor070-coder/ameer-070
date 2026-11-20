"""Skeleton + monoline stroke toolkit for Ameer 070 glyph redraws (font units, y up)."""
import re, skia, pathops
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen

def parse(d):
    p = skia.Path()
    toks = re.findall(r'[MLCQHVZ]|-?\d+(?:\.\d+)?', d)
    i = 0; cmd = None; cur = (0, 0)
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        t = toks[i]
        if t in 'MLCQHVZ':
            cmd = t; i += 1
            if cmd == 'Z':
                p.close(); continue
        if cmd == 'M':
            cur = (num(), num()); p.moveTo(*cur); cmd = 'L'
        elif cmd == 'L':
            cur = (num(), num()); p.lineTo(*cur)
        elif cmd == 'H':
            cur = (num(), cur[1]); p.lineTo(*cur)
        elif cmd == 'V':
            cur = (cur[0], num()); p.lineTo(*cur)
        elif cmd == 'C':
            a = [num() for _ in range(6)]; p.cubicTo(*a); cur = (a[4], a[5])
        elif cmd == 'Q':
            a = [num() for _ in range(4)]; p.quadTo(*a); cur = (a[2], a[3])
    return p

SKX = 1.0   # skeleton x-scale (Latin widening for heavy weights)
SKY = 1.0   # stroke contrast: horizontal strokes = W*SKY (Latin heavy weights)
SYS, SYH = 1.0, 0.0   # skeleton vertical scale about y=SYH (Latin ruler), stroke width untouched
def stroke(d, w, join='round', cap='butt', miter=4):
    paint = skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=w, AntiAlias=True)
    paint.setStrokeCap({'butt': skia.Paint.kButt_Cap, 'round': skia.Paint.kRound_Cap, 'square': skia.Paint.kSquare_Cap}[cap])
    paint.setStrokeJoin({'round': skia.Paint.kRound_Join, 'miter': skia.Paint.kMiter_Join, 'bevel': skia.Paint.kBevel_Join}[join])
    paint.setStrokeMiter(miter)
    dst = skia.Path()
    sk = parse(d)
    if SYS != 1.0:
        m = skia.Matrix(); m.setScale(1, SYS, 0, SYH); sk.transform(m)
    if SKX != 1.0 or SKY != 1.0: sk.transform(skia.Matrix.Scale(SKX, 1 / SKY))
    paint.getFillPath(sk, dst)
    if SKY != 1.0: dst.transform(skia.Matrix.Scale(1, SKY))
    return dst

def fill(d):
    return parse(d)

def to_pathops(sp):
    out = pathops.Path()
    pen = out.getPen()
    it = skia.Path.Iter(sp, True)
    open_ = False
    while True:
        verb, pts = it.next()
        if verb == skia.Path.kDone_Verb:
            break
        if verb == skia.Path.kMove_Verb:
            if open_: pen.closePath()
            pen.moveTo((pts[0].x(), pts[0].y())); open_ = True
        elif verb == skia.Path.kLine_Verb:
            pen.lineTo((pts[1].x(), pts[1].y()))
        elif verb == skia.Path.kQuad_Verb:
            pen.qCurveTo((pts[1].x(), pts[1].y()), (pts[2].x(), pts[2].y()))
        elif verb == skia.Path.kConic_Verb:
            quads = skia.Path.ConvertConicToQuads(pts[0], pts[1], pts[2], it.conicWeight(), 2)
            for k in range(1, len(quads) - 1, 2):
                pen.qCurveTo((quads[k].x(), quads[k].y()), (quads[k + 1].x(), quads[k + 1].y()))
        elif verb == skia.Path.kCubic_Verb:
            pen.curveTo(*[(q.x(), q.y()) for q in pts[1:4]])
        elif verb == skia.Path.kClose_Verb:
            pen.closePath(); open_ = False
    if open_: pen.closePath()
    return out

def union(*parts):
    ps = [to_pathops(p) if isinstance(p, skia.Path) else p for p in parts]
    res = pathops.op(ps[0], ps[0], pathops.PathOp.UNION) if len(ps) == 1 else ps[0]
    for q in ps[1:]:
        res = pathops.op(res, q, pathops.PathOp.UNION)
    res.simplify()
    return res

def subtract(a, b):
    a = to_pathops(a) if isinstance(a, skia.Path) else a
    b = to_pathops(b) if isinstance(b, skia.Path) else b
    return pathops.op(a, b, pathops.PathOp.DIFFERENCE)

def hexdot(cx, cy, r):
    """flat-top hexagon dot like the font's existing dots"""
    import math
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    return fill('M ' + ' L '.join(f'{x} {y}' for x, y in pts) + ' Z')

def copy_glyph(font, name):
    """return existing glyph outline as pathops path (for reusing dots etc.)"""
    gs = font.getGlyphSet(); out = pathops.Path(); gs[name].draw(out.getPen()); return out

def set_glyph(font, name, path, adv=None, rsb=None):
    pen = TTGlyphPen(None)
    if isinstance(path, pathops.Path):
        path = pathops.Path(path)
        try: path.simplify(fix_winding=True, keep_starting_points=False)
        except Exception: pass
        rev = path.clockwise is False if hasattr(path, 'clockwise') else True
    path.draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
    g = pen.glyph(); g.recalcBounds(font['glyf'])
    font['glyf'][name] = g
    xmin = getattr(g, 'xMin', 0)
    if adv is None:
        adv = (g.xMax if hasattr(g, 'xMax') else 0) + (rsb or 0)
    font['hmtx'][name] = (int(round(adv)), int(xmin))

def disable_kern_for(font, names):
    """neutralise pair kerning touching redrawn glyphs (sample only)"""
    from fontTools.ttLib.tables import otTables
    gpos = font['GPOS'].table
    names = set(names)
    for lk in gpos.LookupList.Lookup:
        if lk.LookupType != 2: continue
        for st in lk.SubTable:
            if st.Format == 1:
                for i, g in enumerate(st.Coverage.glyphs):
                    ps = st.PairSet[i]
                    for pvr in ps.PairValueRecord:
                        if g in names or pvr.SecondGlyph in names:
                            for attr in ('Value1', 'Value2'):
                                v = getattr(pvr, attr, None)
                                if v is not None:
                                    for f in ('XAdvance', 'XPlacement'):
                                        if hasattr(v, f): setattr(v, f, 0)
            elif st.Format == 2:
                c1 = st.ClassDef1.classDefs; c2 = st.ClassDef2.classDefs
                for n in names:
                    pass  # class kerning left as is; reported separately
