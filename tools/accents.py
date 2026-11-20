"""Latin accented letters + remaining old Latin/punctuation glyphs, rebuilt on the new design.
- decomposable letters (é, ñ, Å…): NEW base letter + the old accent, moved onto the new base (same relative x, clear gap above/below)
- everything else Latin/punctuation that is still old (Æ, Ø, ß, ( ), ! ? …): vertically mapped to the new ruler
  (old 520/700/735/-210 -> new LXH/LCAP/LASC/LDSC), stroke thickness kept by piecewise mapping."""
import sys, unicodedata, pathops
sys.path.insert(0, '/home/claude/fa')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from wt import OUT, BASE, WL, LXH, LCAP, LASC, LDSC, WT
from draw import set_glyph
OXH, OCAP, OASC, ODSC = 520, 700, 735, -210
new = TTFont(OUT); old = TTFont(BASE)
ngs, ogs = new.getGlyphSet(), old.getGlyphSet(); cmap = new.getBestCmap()
LAT_NEW = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
def contours(gs, n):
    rp = DecomposingRecordingPen(gs); gs[n].draw(rp); cs, cur = [], []
    for op, a in rp.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'): cs.append(cur); cur = []
    out = []
    for c in cs:
        b = BoundsPen(None)
        for op, a in c: getattr(b, op)(*a)
        if b.bounds: out.append((c, b.bounds))
    return out
def contours_p(pp):
    rp = RecordingPen(); pp.draw(rp); cs, cur = [], []
    for op, a in rp.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'): cs.append(cur); cur = []
    out = []
    for c in cs:
        b = BoundsPen(None)
        for op, a in c: getattr(b, op)(*a)
        if b.bounds: out.append((c, b.bounds))
    return out
def bbox(cs):
    return (min(b[0] for _, b in cs), min(b[1] for _, b in cs), max(b[2] for _, b in cs), max(b[3] for _, b in cs))
def fy(y):   # old -> new vertical ruler, piecewise (keeps baseline)
    if y <= 0: return y * LDSC / ODSC if y > ODSC else LDSC + (y - ODSC)
    if y <= OXH: return y * LXH / OXH
    if y <= OCAP: return LXH + (y - OXH) * (LCAP - LXH) / (OCAP - OXH)
    return LCAP + (y - OCAP)
def draw_cs(cs, pen, dx=0, dy=0, mapy=False):
    for c, _ in cs:
        for op, a in c:
            getattr(pen, op)(*[(x + dx, (fy(y) if mapy else y) + dy) for x, y in a])
done, mapped = [], []
GAP = 0.42 * WL
GAPC = 0.5 * WL + 12           # caps: a bit more air under accents (Ñ É in heavy weights)
for u, n in sorted(cmap.items()):
    if chr(u) in LAT_NEW or n in LAT_NEW or not (0x20 <= u <= 0x24F or 0x1E00 <= u <= 0x1EFF or 0x2000 <= u <= 0x20CF or u in (0x2116, 0x2122)): continue
    if n not in old['glyf'].keys() or new['glyf'][n].isComposite() or not new['glyf'][n].numberOfContours: continue
    ch = chr(u); dec = unicodedata.decomposition(ch).split()
    base_ch = chr(int(dec[0], 16)) if dec and not dec[0].startswith('<') else None
    ok = False
    if base_ch and (base_ch in LAT_NEW or base_ch in 'ı'):
        bname = cmap.get(ord(base_ch)); 
        if base_ch in 'ij' and ch.lower() != ch or base_ch in 'ij':
            pass
        ocs = contours(ogs, n); obase = contours(ogs, bname)
        if ocs and obase:
            ob = bbox(obase)
            acc = [(c, b) for c, b in ocs if b[1] >= ob[3] - 12 or b[3] <= ob[1] + 12]
            rest = [(c, b) for c, b in ocs if not (b[1] >= ob[3] - 12 or b[3] <= ob[1] + 12)]
            if base_ch in 'ij':   # i/j: the old dot is not part of the base; accent replaces it
                acc = [(c, b) for c, b in acc if not (abs(b[2] - b[0]) < 1.6 * WL and b[1] < OXH + 260 and b[1] > OXH and len([1 for cc, bb in acc if bb[1] > OXH]) > 1 and False)]
            nbase = contours(ngs, bname)
            if base_ch in 'ij' and acc:   # use the new i/j without its dot
                nbase = sorted(nbase, key=lambda t: -(t[1][3] - t[1][1]))[:1]
            if acc and nbase and len(rest) >= 1:
                nb = bbox(nbase)
                p = pathops.Path(); pen = p.getPen()
                draw_cs(nbase, pen)
                ocx, ncx = (ob[0] + ob[2]) / 2, (nb[0] + nb[2]) / 2
                kx = (nb[2] - nb[0]) / max(1, ob[2] - ob[0])
                above = [t for t in acc if t[1][1] >= ob[3] - 12]; below = [t for t in acc if t[1][3] <= ob[1] + 12]
                for grp, top in ((above, True), (below, False)):
                    if not grp: continue
                    gb = bbox(grp); gcx = (gb[0] + gb[2]) / 2
                    dx = ncx + (gcx - ocx) * kx - gcx
                    if top and gb[0] > ob[2] - 0.35 * (ob[2] - ob[0]) and ch.lower() in 'ďľťĺ' + 'ď':
                        dx = nb[2] + 0.35 * WL - gb[0]; dy = nb[3] - ob[3]          # side caron (ď ľ ť Ľ): beside the stem, clear gap
                    elif top:
                        og = gb[1] - ob[3]; _g = GAPC if base_ch.isupper() else GAP; dy = nb[3] + max(_g, og) - gb[1]
                        if base_ch.isupper() and nb[3] + max(GAP, og) + (gb[3] - gb[1]) > LASC + 230:   # caps: keep accents compact
                            dy = nb[3] + GAP - gb[1]
                    else:
                        og = ob[1] - gb[3]; dy = nb[1] - max(GAP * 0.6, og) - gb[3] if og > 0 else nb[1] - ob[1]
                    draw_cs(grp, pen, dx, dy)
                adv = new['hmtx'][bname][0]
                set_glyph(new, n, p, adv=adv); ok = True; done.append(n)
    if not ok and base_ch and (base_ch in LAT_NEW):
        # mark attached to / beside the letter (ogonek, cedilla, caron of d l t, accented i): old glyph minus old base
        bname = cmap.get(ord(base_ch)); obn = {'i': 'dotlessi', 'j': 'uni0237'}.get(base_ch, bname)
        if obn not in ogs: obn = bname
        po = pathops.Path(); ogs[n].draw(po.getPen()); pb = pathops.Path(); ogs[obn].draw(pb.getPen())
        mk = pathops.op(po, pb, pathops.PathOp.DIFFERENCE)
        from fontTools.pens.areaPen import AreaPen as _AP
        def _area(c):
            ap = _AP()
            for op, aa in c: getattr(ap, op)(*aa)
            return ap.value
        _all = contours_p(mk)
        _sg = 1 if _all and _area(max(_all, key=lambda t: abs(_area(t[0])))[0]) > 0 else -1
        mcs = [(c, b) for c, b in _all if _area(c) * _sg > 0 and min(b[2] - b[0], b[3] - b[1]) > 0.3 * WL and abs(_area(c)) > (0.4 * WL) ** 2]
        nbase = contours(ngs, bname)
        if base_ch in 'ij': nbase = sorted(nbase, key=lambda t: -(t[1][3] - t[1][1]))[:1]
        if mcs and nbase:
            ob = bbox(contours(ogs, obn)); nb = bbox(nbase)
            p = pathops.Path(); pen = p.getPen(); draw_cs(nbase, pen)
            for c, b in mcs:
                mcx = (b[0] + b[2]) / 2; fxr = (mcx - ob[0]) / max(1, ob[2] - ob[0])
                dx = nb[0] + fxr * (nb[2] - nb[0]) - mcx
                if b[1] >= ob[3] - 40: dy = nb[3] + max(GAP, b[1] - ob[3]) - b[1]
                elif b[3] <= ob[1] + 40 or b[1] < -5: dy = 0
                else: dy = (nb[3] - ob[3]) if b[3] > ob[3] - 60 else fy((b[1] + b[3]) / 2) - (b[1] + b[3]) / 2
                if b[1] > 0 and not (b[1] >= ob[3] - 40):   # side mark (caron of d l t L): keep clear of the stem, pieces move together
                    side = [bb for cc, bb in mcs if bb[1] > 0 and not (bb[1] >= ob[3] - 40)]
                    sx0 = min(bb[0] for bb in side); scx = (min(bb[0] for bb in side) + max(bb[2] for bb in side)) / 2
                    dx0 = nb[0] + (scx - ob[0]) / max(1, ob[2] - ob[0]) * (nb[2] - nb[0]) - scx
                    dx = max(dx0, nb[2] + 0.35 * WL - sx0)
                draw_cs([(c, b)], pen, dx, dy)
            p.simplify(); set_glyph(new, n, p, adv=new['hmtx'][bname][0]); ok = True; done.append(n)
    if not ok and not (0x600 <= u <= 0x6FF):
        cs = contours(ogs, n)
        if not cs: continue
        bb = bbox(cs)
        p = pathops.Path(); pen = p.getPen()
        if bb[3] > OXH + 40 and bb[1] >= -30 and bb[3] <= OCAP + 30:     # cap-height symbols (% & @ $ #): uniform scale keeps proportions
            for c, _ in cs:
                for op, aa in c: getattr(pen, op)(*[(x, y * LCAP / OCAP) for x, y in aa])
        else:
            draw_cs(cs, pen, mapy=True)
        try:
            set_glyph(new, n, p, adv=old['hmtx'][n][0]); mapped.append(n)
        except Exception as e: print('skip', n, e)
new.save(OUT)
print(WT, 'accented rebuilt', len(done), '| mapped to ruler', len(mapped))
import unicodedata as _u
print('MAPPED-DECOMPOSABLE', [n for n in mapped if any(not d.startswith('<') for d in _u.decomposition(chr([u for u,g in cmap.items() if g==n][0])).split()[:1])])
